"""mitosis — asymmetric cell division for disaster recovery.

The iMac is the self-renewing daughter cell. Lucerna (fly.io, nrt) is the
differentiated standby — kept synchronized via one-way push, activated only
when the primary dies.

Sync is git-based and unidirectional: Mac pushes to GitHub, lucerna pulls.
No direct SSH or rsync needed — all remote commands go through `fly ssh console`.

State divergence is impossible by design: Mac is always authoritative.

Core functions: sync, status, setup.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

# Lucerna coordinates
LUCERNA_APP = "lucerna"  # fly.io app name
LUCERNA_USER = "terry"
LUCERNA_HOME = f"/home/{LUCERNA_USER}"

# Sync targets: git repos that get pushed locally then pulled on lucerna.
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
    {
        "name": "officina",
        "local": "~/officina",
        "remote": f"{LUCERNA_HOME}/officina",
        "repo": "terry-li-hm/officina",
        "critical": False,
    },
    {
        "name": "scripts",
        "local": "~/scripts",
        "remote": f"{LUCERNA_HOME}/scripts",
        "repo": "terry-li-hm/scripts",
        "critical": False,
    },
]


@dataclass
class SyncResult:
    target: str
    success: bool
    elapsed_s: float
    message: str = ""


@dataclass
class SyncReport:
    results: list[SyncResult] = field(default_factory=list)
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
    """Run a command on lucerna via fly ssh console.

    Wraps in bash -c "..." so pipes, variables, and semicolons work.
    The -C flag takes a single string which fly passes to the remote shell.
    """
    # Double-quote the command inside bash -c so $VARS expand on remote
    wrapped = f'bash -c "{cmd}"'
    return subprocess.run(
        ["fly", "ssh", "console", "-a", LUCERNA_APP, "-u", LUCERNA_USER,
         "-q", "-C", wrapped],
        capture_output=True, text=True, timeout=timeout,
    )


def _is_lucerna_reachable() -> bool:
    """Check if lucerna machine is running via fly status."""
    try:
        result = subprocess.run(
            ["fly", "status", "-a", LUCERNA_APP],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode == 0 and "started" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _git_push(local_path: str) -> tuple[bool, str]:
    """Stage, commit, and push local changes. Returns (success, message)."""
    local = _expand(local_path)
    if not Path(local).joinpath(".git").exists():
        return False, "not a git repo"

    # Stage all changes
    subprocess.run(
        ["git", "-C", local, "add", "-A"],
        capture_output=True, text=True, timeout=30,
    )

    # Commit if there are changes (ignore exit code if nothing to commit)
    result = subprocess.run(
        ["git", "-C", local, "commit", "-m", "mitosis: sync checkpoint"],
        capture_output=True, text=True, timeout=30,
    )

    # Push
    result = subprocess.run(
        ["git", "-C", local, "push"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "Everything up-to-date" in stderr or "Everything up-to-date" in result.stdout:
            return True, "up-to-date"
        return False, stderr[:200]
    return True, "pushed"


def _git_pull_remote(remote_path: str) -> tuple[bool, str]:
    """Pull latest on lucerna. Returns (success, message)."""
    try:
        result = _fly_cmd(
            f"cd {remote_path} && git pull --ff-only 2>&1",
            timeout=120,
        )
        stdout = result.stdout.strip()
        # fly ssh console mixes warnings into output
        lines = [l for l in stdout.splitlines()
                 if not l.startswith("Connecting to") and not l.startswith("Warning:")]
        clean = "\n".join(lines).strip()

        if result.returncode != 0:
            return False, clean[:200]
        return True, clean[:100]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:200]


def _sync_target(target: dict) -> SyncResult:
    """Sync one target: push local, pull remote."""
    t0 = time.monotonic()

    # Push local
    ok, msg = _git_push(target["local"])
    if not ok:
        return SyncResult(target["name"], False, time.monotonic() - t0, f"push failed: {msg}")

    # Pull on lucerna
    ok, msg = _git_pull_remote(target["remote"])
    elapsed = time.monotonic() - t0
    if not ok:
        return SyncResult(target["name"], False, elapsed, f"pull failed: {msg}")

    return SyncResult(target["name"], True, elapsed, msg)


def sync(targets: list[str] | None = None) -> SyncReport:
    """Push current state to lucerna.

    Workflow per target: git add+commit+push locally, git pull on lucerna.

    Args:
        targets: Specific target names to sync. None = all.
    """
    report = SyncReport(started=time.monotonic())

    if not _is_lucerna_reachable():
        report.finished = time.monotonic()
        report.results.append(SyncResult("connectivity", False, 0, "lucerna not running"))
        return report

    manifest = SYNC_TARGETS
    if targets:
        manifest = [t for t in SYNC_TARGETS if t["name"] in targets]

    for target in manifest:
        report.results.append(_sync_target(target))

    report.finished = time.monotonic()
    return report


def status() -> dict:
    """Check lucerna health and sync freshness."""
    info: dict = {
        "reachable": False,
        "machine_state": "unknown",
        "targets": {},
    }

    info["reachable"] = _is_lucerna_reachable()
    if not info["reachable"]:
        return info

    info["machine_state"] = "started"

    # Check each repo's last commit time on lucerna in one SSH call
    stat_parts = []
    for target in SYNC_TARGETS:
        # Get epoch of last commit
        stat_parts.append(
            f"cd {target['remote']} 2>/dev/null "
            f"&& git log -1 --format=%ct 2>/dev/null "
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
    """Bootstrap lucerna with required repos and vivesca install.

    Idempotent — safe to run repeatedly.
    """
    steps: list[dict] = []

    if not _is_lucerna_reachable():
        return {"success": False, "error": "lucerna not running", "steps": steps}

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
                steps.append({
                    "name": f"clone-{target['name']}",
                    "success": ok,
                    "message": "cloned" if ok else result.stdout.strip()[-200:],
                })
            else:
                steps.append({
                    "name": f"clone-{target['name']}",
                    "success": True,
                    "message": "already present",
                })
        except Exception as e:
            steps.append({
                "name": f"clone-{target['name']}",
                "success": False,
                "message": str(e)[:200],
            })

    # Create directories for non-git state
    dirs = [
        f"{LUCERNA_HOME}/.claude/projects/-home-terry/memory",
        f"{LUCERNA_HOME}/.config/vivesca",
        f"{LUCERNA_HOME}/.local/share/oghma",
    ]
    try:
        result = _fly_cmd(f"mkdir -p {' '.join(dirs)}")
        steps.append({
            "name": "create-dirs",
            "success": result.returncode == 0,
            "message": "ok",
        })
    except Exception as e:
        steps.append({"name": "create-dirs", "success": False, "message": str(e)[:200]})

    # Install metabolon
    try:
        result = _fly_cmd(
            f"cd {LUCERNA_HOME}/germline && ~/.local/bin/uv sync 2>&1 | tail -3",
            timeout=300,
        )
        steps.append({
            "name": "install-metabolon",
            "success": result.returncode == 0,
            "message": result.stdout.strip()[-200:],
        })
    except Exception as e:
        steps.append({"name": "install-metabolon", "success": False, "message": str(e)[:200]})

    # Symlink vivesca config from epigenome
    try:
        result = _fly_cmd(
            f"ln -sfn {LUCERNA_HOME}/epigenome/phenotype/vivesca {LUCERNA_HOME}/.config/vivesca"
        )
        steps.append({
            "name": "symlink-config",
            "success": result.returncode == 0,
            "message": "ok",
        })
    except Exception as e:
        steps.append({"name": "symlink-config", "success": False, "message": str(e)[:200]})

    all_ok = all(s["success"] for s in steps)
    return {"success": all_ok, "steps": steps}
