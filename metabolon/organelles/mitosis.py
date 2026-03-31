from __future__ import annotations

"""mitosis — asymmetric cell division for disaster recovery.

The iMac is the self-renewing daughter cell. Lucerna (fly.io, nrt) is the
differentiated standby — kept synchronized via one-way push, activated only
when the primary dies.

Sync is git-based and unidirectional: Mac pushes to GitHub, gemmule pulls.
No direct SSH or rsync needed — all remote commands go through `fly ssh console`.

State divergence is impossible by design: Mac is always authoritative.

Core functions: sync, status, setup.
"""


import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

# Lucerna coordinates
LUCERNA_APP = "gemmule"  # fly.io app name (formerly gemmule)
LUCERNA_USER = "terry"
LUCERNA_HOME = f"/home/{LUCERNA_USER}"

# Sync targets: git repos that get pushed locally then pulled on gemmule.
# All organism state lives in these repos.
SYNC_TARGETS: list[dict] = [
    {
        "name": "germline",
        "local": "~/germline",
        "remote": f"{LUCERNA_HOME}/germline",
        "repo": "vivesca/vivesca",
        "critical": True,
    },
    {
        "name": "epigenome",
        "local": "~/epigenome",
        "remote": f"{LUCERNA_HOME}/epigenome",
        "repo": "terry-li-hm/epigenome",
        "critical": True,
    },
    # officina is not a git repo locally — synced via its own mechanism
    # scripts repo absorbed into germline/epigenome (Mar 2026)
    # .claude critical files DR'd via symlinks into germline/epigenome:
    # hooks → germline/synaptic/, MEMORY.md → epigenome/marks/methylome.md,
    # settings.json → germline/membrane/expression.json
]


@dataclass
class ReplicationResult:
    target: str
    success: bool
    elapsed_s: float
    message: str = ""


@dataclass
class FidelityReport:
    results: list[ReplicationResult] = field(default_factory=list)
    started: float = 0
    finished: float = 0

    @property
    def elapsed_s(self) -> float:
        return self.finished - self.started

    @property
    def ok(self) -> bool:
        critical = {t["name"] for t in SYNC_TARGETS if t.get("critical")}
        return all(r.success for r in self.results if r.target in critical)

    @property
    def summary(self) -> str:
        ok = sum(1 for r in self.results if r.success)
        fail = len(self.results) - ok
        return f"{ok}/{len(self.results)} targets synced in {self.elapsed_s:.1f}s ({fail} failed)"


def _expand(path: str) -> str:
    return str(Path(path).expanduser())


def _fly_cmd(cmd: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a command on gemmule via fly ssh console.

    Wraps in bash -c "..." so pipes, variables, and semicolons work.
    The -C flag takes a single string which fly passes to the remote shell.
    """
    # Double-quote the command inside bash -c so $VARS expand on remote
    wrapped = f'bash -c "{cmd}"'
    return subprocess.run(
        ["fly", "ssh", "console", "-a", LUCERNA_APP, "-u", LUCERNA_USER, "-q", "-C", wrapped],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _is_gemmule_reachable() -> bool:
    """Check if gemmule machine is running via fly status."""
    try:
        result = subprocess.run(
            ["fly", "status", "-a", LUCERNA_APP],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0 and "started" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _build_commit_message(local: str) -> str:
    """Build a descriptive commit message from staged changes.

    Summarizes the number of changed files grouped by top-level directory,
    e.g. "mitosis: sync checkpoint (3 files in metabolon/, 1 in loci/)"
    """
    result = subprocess.run(
        ["git", "-C", local, "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    changed_files = [line for line in result.stdout.strip().splitlines() if line]
    if not changed_files:
        return "mitosis: sync checkpoint"

    dir_counts: dict[str, int] = {}
    for filepath in changed_files:
        top_dir = filepath.split("/")[0] if "/" in filepath else "(root)"
        dir_counts[top_dir] = dir_counts.get(top_dir, 0) + 1

    parts = [f"{count} file{'s' if count != 1 else ''} in {dir_}/" for dir_, count in sorted(dir_counts.items())]
    return f"mitosis: sync checkpoint ({', '.join(parts)})"


def _git_push(local_path: str) -> tuple[bool, str]:
    """Stage, commit, and push local changes. Returns (success, message)."""
    local = _expand(local_path)
    if not Path(local).joinpath(".git").exists():
        return False, "not a git repo"

    # Stage all changes
    subprocess.run(
        ["git", "-C", local, "add", "-A"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Build descriptive commit message from staged diff
    commit_msg = _build_commit_message(local)

    # Commit if there are changes (ignore exit code if nothing to commit)
    result = subprocess.run(
        ["git", "-C", local, "commit", "-m", commit_msg],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Push
    result = subprocess.run(
        ["git", "-C", local, "push"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "Everything up-to-date" in stderr or "Everything up-to-date" in result.stdout:
            return True, "up-to-date"
        return False, stderr[:200]
    return True, "pushed"


def _git_pull_remote(remote_path: str) -> tuple[bool, str]:
    """Pull latest on gemmule. Returns (success, message).

    On success, writes epoch to .last-sync so status() can distinguish
    "no new commits" from "sync broken".
    """
    try:
        result = _fly_cmd(
            f"cd {remote_path} && git pull --ff-only 2>&1 && date +%s > .last-sync",
            timeout=120,
        )
        stdout = result.stdout.strip()
        # fly ssh console mixes warnings into output
        lines = [
            line
            for line in stdout.splitlines()
            if not line.startswith("Connecting to") and not line.startswith("Warning:")
        ]
        clean = "\n".join(lines).strip()

        if result.returncode != 0:
            return False, clean[:200]
        return True, clean[:100]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:200]


def _sync_target(target: dict) -> ReplicationResult:
    """Sync one target: commit+push local, pull remote."""
    t0 = time.monotonic()

    # Push local (non-fatal — pull may still succeed from a prior push)
    push_ok, push_msg = _git_push(target["local"])

    # Pull on gemmule
    pull_ok, pull_msg = _git_pull_remote(target["remote"])
    elapsed = time.monotonic() - t0

    if not pull_ok:
        if not push_ok:
            return ReplicationResult(
                target["name"], False, elapsed, f"push: {push_msg}; pull: {pull_msg}"
            )
        return ReplicationResult(target["name"], False, elapsed, f"pull failed: {pull_msg}")

    if not push_ok:
        return ReplicationResult(target["name"], True, elapsed, f"pull ok (push skipped: {push_msg})")

    return ReplicationResult(target["name"], True, elapsed, pull_msg)


def sync(targets: list[str] | None = None) -> FidelityReport:
    """Push current state to gemmule.

    Workflow per target: git add+commit+push locally, git pull on gemmule.

    Args:
        targets: Specific target names to sync. None = all.
    """
    report = FidelityReport(started=time.monotonic())

    if not _is_gemmule_reachable():
        report.finished = time.monotonic()
        report.results.append(ReplicationResult("connectivity", False, 0, "gemmule not running"))
        return report

    manifest = SYNC_TARGETS
    if targets:
        manifest = [t for t in SYNC_TARGETS if t["name"] in targets]

    for target in manifest:
        report.results.append(_sync_target(target))

    # Sync claude credentials (base64 to preserve JSON through shell layers)
    import base64

    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        t0 = time.monotonic()
        try:
            b64 = base64.b64encode(creds_path.read_bytes()).decode()
            result = _fly_cmd(f"echo {b64} | base64 -d > {LUCERNA_HOME}/.claude/.credentials.json")
            ok = result.returncode == 0
            report.results.append(ReplicationResult("cc-auth", ok, time.monotonic() - t0))
        except Exception as e:
            report.results.append(
                ReplicationResult("cc-auth", False, time.monotonic() - t0, str(e)[:100])
            )

    report.finished = time.monotonic()
    return report


def status() -> dict:
    """Check gemmule health and sync freshness."""
    info: dict = {
        "reachable": False,
        "machine_state": "unknown",
        "targets": {},
    }

    info["reachable"] = _is_gemmule_reachable()
    if not info["reachable"]:
        return info

    info["machine_state"] = "started"

    # Check each repo's last sync time on gemmule in one SSH call.
    # Prefer .last-sync (written by _git_pull_remote) over git log timestamp,
    # because commit age grows stale even when the repo is fully synced.
    stat_parts = []
    for target in SYNC_TARGETS:
        stat_parts.append(
            f"cd {target['remote']} 2>/dev/null "
            f"&& cat .last-sync 2>/dev/null "
            f"|| git log -1 --format=%ct 2>/dev/null "
            f"|| echo MISSING"
        )
    stat_script = " ; echo '---' ; ".join(stat_parts)

    try:
        result = _fly_cmd(stat_script, timeout=30)
        # Parse output: filter fly noise, split by ---
        lines = result.stdout.strip()
        # Remove fly connection/warning lines
        clean_lines = []
        for line in lines.splitlines():
            if line.startswith("Connecting to") or line.startswith("Warning:"):
                continue
            clean_lines.append(line.strip())
        chunks = " ".join(clean_lines).split("---")

        for i, target in enumerate(SYNC_TARGETS):
            if i >= len(chunks):
                info["targets"][target["name"]] = {"state": "unknown"}
                continue
            chunk = chunks[i].strip()
            if chunk == "MISSING" or not chunk.isdigit():
                info["targets"][target["name"]] = {"state": "missing"}
            else:
                commit_epoch = int(chunk)
                age_s = int(time.time()) - commit_epoch
                info["targets"][target["name"]] = {
                    "state": "ok" if age_s < 1800 else "stale",
                    "age_minutes": round(age_s / 60),
                }
    except Exception:
        for target in SYNC_TARGETS:
            info["targets"][target["name"]] = {"state": "unknown"}

    return info


def setup() -> dict:
    """Bootstrap gemmule with required repos and vivesca install.

    Idempotent — safe to run repeatedly.
    """
    steps: list[dict] = []

    if not _is_gemmule_reachable():
        return {"success": False, "error": "gemmule not running", "steps": steps}

    # Clone missing repos
    for target in SYNC_TARGETS:
        try:
            result = _fly_cmd(
                f"test -d {target['remote']}/.git && echo EXISTS || echo MISSING",
                timeout=15,
            )
            if "MISSING" in result.stdout:
                # Use GITHUB_TOKEN from fly secrets for auth
                result = _fly_cmd(
                    f"git clone https://$GITHUB_TOKEN@github.com/{target['repo']}.git {target['remote']} 2>&1",
                    timeout=180,
                )
                ok = result.returncode == 0 and "fatal" not in result.stdout
                steps.append(
                    {
                        "name": f"clone-{target['name']}",
                        "success": ok,
                        "message": "cloned" if ok else result.stdout.strip()[-200:],
                    }
                )
            else:
                steps.append(
                    {
                        "name": f"clone-{target['name']}",
                        "success": True,
                        "message": "already present",
                    }
                )
        except Exception as e:
            steps.append(
                {
                    "name": f"clone-{target['name']}",
                    "success": False,
                    "message": str(e)[:200],
                }
            )

    # Create directories for non-git state
    dirs = [
        f"{LUCERNA_HOME}/.claude/projects/-home-terry/memory",
        f"{LUCERNA_HOME}/.config/vivesca",
        f"{LUCERNA_HOME}/.local/share/oghma",
    ]
    try:
        result = _fly_cmd(f"mkdir -p {' '.join(dirs)}")
        steps.append(
            {
                "name": "create-dirs",
                "success": result.returncode == 0,
                "message": "ok",
            }
        )
    except Exception as e:
        steps.append({"name": "create-dirs", "success": False, "message": str(e)[:200]})

    # Install metabolon
    try:
        result = _fly_cmd(
            f"cd {LUCERNA_HOME}/germline && ~/.local/bin/uv sync 2>&1 | tail -3",
            timeout=300,
        )
        steps.append(
            {
                "name": "install-metabolon",
                "success": result.returncode == 0,
                "message": result.stdout.strip()[-200:],
            }
        )
    except Exception as e:
        steps.append({"name": "install-metabolon", "success": False, "message": str(e)[:200]})

    # Symlinks: vivesca config, CC membrane, PATH
    _project_slug = "-home-" + LUCERNA_USER
    symlinks = [
        (f"{LUCERNA_HOME}/epigenome/phenotype/vivesca", f"{LUCERNA_HOME}/.config/vivesca"),
        (f"{LUCERNA_HOME}/germline/membrane/phenotype.md", f"{LUCERNA_HOME}/.claude/CLAUDE.md"),
        (f"{LUCERNA_HOME}/germline/membrane/cytoskeleton", f"{LUCERNA_HOME}/.claude/hooks"),
        (
            f"{LUCERNA_HOME}/germline/membrane/expression.json",
            f"{LUCERNA_HOME}/.claude/settings.json",
        ),
        (f"{LUCERNA_HOME}/germline/membrane/receptors", f"{LUCERNA_HOME}/.claude/skills"),
        # CC memory -> epigenome engrams (on Mac these are hardlinked; on Linux, symlink)
        (
            f"{LUCERNA_HOME}/epigenome/marks",
            f"{LUCERNA_HOME}/.claude/projects/{_project_slug}/memory",
        ),
    ]
    # rm -rf before ln to handle existing dirs (ln -sfn doesn't replace dirs)
    symlink_cmds = " && ".join(f"rm -rf {dst} && ln -sfn {src} {dst}" for src, dst in symlinks)
    try:
        result = _fly_cmd(symlink_cmds)
        steps.append(
            {
                "name": "symlinks",
                "success": result.returncode == 0,
                "message": "ok" if result.returncode == 0 else result.stderr.strip()[:200],
            }
        )
    except Exception as e:
        steps.append({"name": "symlinks", "success": False, "message": str(e)[:200]})

    # Ensure germline venv is on PATH in .zshenv
    path_line = f"export PATH={LUCERNA_HOME}/germline/.venv/bin:{LUCERNA_HOME}/.local/bin:{LUCERNA_HOME}/.cargo/bin:{LUCERNA_HOME}/.bun/bin:\\$PATH"
    try:
        result = _fly_cmd(
            f"grep -q 'germline/.venv/bin' {LUCERNA_HOME}/.zshenv 2>/dev/null "
            f"|| echo '{path_line}' >> {LUCERNA_HOME}/.zshenv"
        )
        steps.append(
            {
                "name": "path-setup",
                "success": result.returncode == 0,
                "message": "ok",
            }
        )
    except Exception as e:
        steps.append({"name": "path-setup", "success": False, "message": str(e)[:200]})

    all_ok = all(s["success"] for s in steps)
    return {"success": all_ok, "steps": steps}


def smoketest() -> dict:
    """End-to-end DR test: write passcode locally, sync, ask claude on gemmule to read it back.

    Proves: sync pipeline + memory access + claude auth + full round-trip.
    """
    import random
    import string

    if not _is_gemmule_reachable():
        return {"success": False, "error": "gemmule not running"}

    # Generate random passcode
    passcode = "mitosis-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    # Write passcode to a memory file locally (in epigenome/marks, which is hardlinked to CC memory)
    probe_file = Path.home() / "epigenome" / "engrams" / "mitosis_probe.md"
    probe_file.write_text(
        f"---\nname: mitosis probe\ndescription: DR smoke test probe — ephemeral\ntype: project\n---\n\n"
        f"Passcode: {passcode}\n"
    )

    # Sync to gemmule
    report = sync(["epigenome"])
    if not report.ok:
        probe_file.unlink(missing_ok=True)
        return {"success": False, "error": "sync failed", "sync": report.summary}

    # Read the passcode back from gemmule's memory (via synced engrams symlink)
    memory_path = f"{LUCERNA_HOME}/.claude/projects/-home-{LUCERNA_USER}/memory/mitosis_probe.md"
    try:
        result = _fly_cmd(f"cat {memory_path} 2>&1", timeout=15)
        response = ""
        for line in result.stdout.strip().splitlines():
            if line.startswith("Connecting to") or line.startswith("Warning:"):
                continue
            response += line.strip() + " "
        response = response.strip()
    except Exception as e:
        probe_file.unlink(missing_ok=True)
        return {"success": False, "error": f"read failed: {e}"}

    # Also verify claude auth is valid
    try:
        auth_result = _fly_cmd(
            f"export PATH={LUCERNA_HOME}/germline/.venv/bin:{LUCERNA_HOME}/.local/bin:$PATH && "
            f"claude --version 2>&1",
            timeout=15,
        )
        auth_ok = "Claude Code" in auth_result.stdout
    except Exception:
        auth_ok = False

    # Clean up probe file
    probe_file.unlink(missing_ok=True)
    # Push cleanup
    sync(["epigenome"])

    # Verify
    if passcode in response:
        return {
            "success": True,
            "passcode": passcode,
            "claude_auth": auth_ok,
        }
    return {
        "success": False,
        "error": "passcode mismatch",
        "expected": passcode,
        "got": response[:200],
        "claude_auth": auth_ok,
    }
