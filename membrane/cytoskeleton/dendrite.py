#!/usr/bin/env python3
"""dendrite.py — consolidated PostToolUse hook.

Replaces 17 hooks (7 JS + 10 Python) with a single process.
Routes by tool name and file path internally.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
HOME_BIN_PATTERN = re.escape(f"{HOME}/bin/")
HOOKS_DIR = HOME / ".claude" / "hooks"

# Repo root: hooks → claude → vivesca
_VIVESCA_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(HOOKS_DIR))


# ── chaperone_py: ruff + py_compile + test discovery ───────


def chaperone_py(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp or not fp.endswith(".py") or "/notes/" in fp or "/chromatin/" in fp:
        return

    d = os.path.dirname(fp)

    # ruff format + check
    for subcmd in ["format", "check --fix"]:
        with contextlib.suppress(Exception):
            subprocess.run(
                f'ruff {subcmd} "{fp}"', shell=True, cwd=d, capture_output=True, timeout=10
            )

    # py_compile
    try:
        r = subprocess.run(
            ["python3", "-m", "py_compile", fp], capture_output=True, text=True, timeout=5
        )
        if r.returncode != 0 and r.stderr.strip():
            print(f"[chaperone-py] Compile error: {r.stderr.strip()[:300]}", file=sys.stderr)
    except Exception:
        pass

    # Test discovery
    basename = os.path.splitext(os.path.basename(fp))[0]
    if basename.startswith("test_") or basename.startswith(".") or "/hooks/" in fp:
        return

    # Also check assays/ relative to germline root
    germline_assays = os.path.join(str(_VIVESCA_ROOT), "assays")
    candidates = [
        os.path.join(d, f"test_{basename}.py"),
        os.path.join(d, "tests", f"test_{basename}.py"),
        os.path.join(d, "..", "tests", f"test_{basename}.py"),
        os.path.join(germline_assays, f"test_{basename}.py"),
    ]
    test_file = next((f for f in candidates if os.path.exists(f)), None)
    if not test_file:
        # Nudge for organelles and enzymes — these MUST have tests
        if "/organelles/" in fp or "/enzymes/" in fp:
            print(
                json.dumps(
                    {
                        "output": f"[assay-missing] No test file for `{basename}.py`. "
                        f"Genome rule: assays ship with code. "
                        f"Expected: `assays/test_{basename}.py`"
                    }
                )
            )
        return

    # Find project root
    proj = d
    check = d
    while check != os.path.dirname(check):
        if os.path.exists(os.path.join(check, "pyproject.toml")) or os.path.exists(
            os.path.join(check, "setup.py")
        ):
            proj = check
            break
        check = os.path.dirname(check)

    try:
        r = subprocess.run(
            f'uv run pytest "{test_file}" -x -q 2>&1 || true',
            shell=True,
            cwd=proj,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if "FAILED" in r.stdout or "ERROR" in r.stdout:
            lines = [
                line
                for line in r.stdout.split("\n")
                if "FAILED" in line or "ERROR" in line or "assert" in line
            ][:5]
            print(
                f"[chaperone-py] Test regression in {os.path.basename(test_file)}:\n"
                + "\n".join(lines),
                file=sys.stderr,
            )
    except Exception:
        pass


# ── chaperone_js: prettier ─────────────────────────────────


def chaperone_js(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if (
        not fp
        or not re.search(r"\.(js|jsx|ts|tsx)$", fp)
        or "/notes/" in fp
        or "/chromatin/" in fp
    ):
        return
    if not os.path.exists(fp):
        return

    d = os.path.dirname(fp)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "package.json")):
            break
        d = os.path.dirname(d)

    prettier = os.path.join(d, "node_modules", ".bin", "prettier")
    if not os.path.exists(prettier):
        return

    try:
        subprocess.run([prettier, "--write", fp], cwd=d, capture_output=True, timeout=10)
        print(f"[PostEdit] Formatted: {os.path.basename(fp)}", file=sys.stderr)
    except Exception:
        pass


# ── chaperone_ts: tsc type check ───────────────────────────


def chaperone_ts(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp or not re.search(r"\.(ts|tsx)$", fp):
        return
    if not os.path.exists(fp):
        return

    d = os.path.dirname(fp)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "tsconfig.json")):
            break
        d = os.path.dirname(d)

    if not os.path.exists(os.path.join(d, "tsconfig.json")):
        return

    local_tsc = os.path.join(d, "node_modules", ".bin", "tsc")
    if not os.path.exists(local_tsc):
        return
    tsc_bin = f'"{local_tsc}"'
    try:
        r = subprocess.run(
            f"{tsc_bin} --noEmit --incremental --pretty false 2>&1",
            shell=True,
            cwd=d,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return

    if r.returncode != 0:
        errors = [
            line
            for line in (r.stdout or "").split("\n")
            if fp in line or os.path.basename(fp) in line
        ][:5]
        if errors:
            print(f"[TypeCheck] Errors in {os.path.basename(fp)}:", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)


# ── chaperone_rs: rustfmt ──────────────────────────────────


def chaperone_rs(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp or not fp.endswith(".rs"):
        return

    d = os.path.dirname(fp)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "Cargo.toml")):
            break
        d = os.path.dirname(d)

    if not os.path.exists(os.path.join(d, "Cargo.toml")):
        return

    try:
        subprocess.run(["rustfmt", fp], cwd=d, capture_output=True, timeout=10)
        print(f"[PostEdit] Formatted: {os.path.basename(fp)}", file=sys.stderr)
    except Exception:
        pass


# ── perseveration: stuck/loop detection ────────────────────

PERSEV_LOG = HOME / ".claude" / "tool-call-log.jsonl"
PERSEV_MAX = 200
PERSEV_WINDOW = 20


def mod_perseveration(data):
    tool = data.get("tool_name", data.get("tool", "unknown"))
    args = data.get("tool_input", {})
    result = data.get("tool_output", data.get("tool_result", ""))
    has_error = (
        isinstance(result, str) and any(w in result.lower() for w in ("error", "failed"))
    ) or (isinstance(result, str) and result.startswith("Exit code"))

    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "tool": tool,
        "args": args,
        "hasError": has_error,
    }

    # Read recent
    recent = []
    if PERSEV_LOG.exists():
        try:
            lines = [line for line in PERSEV_LOG.read_text().split("\n") if line.strip()]
            if len(lines) >= PERSEV_MAX:
                PERSEV_LOG.write_text("")
                lines = []
            for line in lines[-PERSEV_WINDOW:]:
                with contextlib.suppress(json.JSONDecodeError):
                    recent.append(json.loads(line))
        except Exception:
            pass

    # Append
    try:
        with PERSEV_LOG.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

    def hash_call(e):
        return f"{e.get('tool')}::{json.dumps(e.get('args', {}))}"

    all_entries = [*recent, entry]
    cur_hash = hash_call(entry)

    # Same call repeated
    repeat = 0
    for e in reversed(all_entries):
        if hash_call(e) == cur_hash:
            repeat += 1
        else:
            break
    if repeat >= 3:
        print(
            f"[stuck-detector] Same {tool} call repeated {repeat}x. Consider different approach or /compact.",
            file=sys.stderr,
        )

    # Same tool error repeated
    if has_error:
        err_repeat = 0
        for e in reversed(all_entries):
            if e.get("tool") == tool and e.get("hasError"):
                err_repeat += 1
            else:
                break
        if err_repeat >= 2:
            print(
                f"[stuck-detector] {tool} errored {err_repeat}x consecutively. Try a different method.",
                file=sys.stderr,
            )

    # Alternating A-B pattern
    if len(all_entries) >= 6:
        tail = all_entries[-6:]
        hashes = [hash_call(e) for e in tail]
        uniq = set(hashes)
        if len(uniq) == 2:
            alternating = all(hashes[i] == hashes[i + 2] for i in range(4))
            if alternating:
                print(
                    "[stuck-detector] Alternating loop detected for 6 steps. Break out with different strategy.",
                    file=sys.stderr,
                )


# ── chromatin: MEMORY.md budget check ──────────────────────

_PROJECT_SLUG = "-" + str(HOME).lstrip("/").replace(
    "/", "-"
)  # e.g. /home/vivesca -> -home-vivesca
CHROMATIN_PATH = HOME / ".claude" / "projects" / _PROJECT_SLUG / "memory" / "MEMORY.md"
CHROMATIN_BUDGET = 150


def mod_chromatin(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if "MEMORY.md" not in fp:
        return
    try:
        lc = CHROMATIN_PATH.read_text().count("\n") + 1
        if lc > CHROMATIN_BUDGET:
            print(
                f"MEMORY.md is {lc} lines (budget: {CHROMATIN_BUDGET}). Downregulate lowest-recurrence entries.",
                file=sys.stderr,
            )
    except Exception:
        pass


# ── recurrence: track memory file access for downregulation signal ────

MEMORY_DIR = HOME / ".claude" / "projects" / _PROJECT_SLUG / "memory"


def mod_recurrence(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return
    p = Path(fp)
    if not str(p).startswith(str(MEMORY_DIR)) or p.name == "MEMORY.md":
        return
    if not p.exists() or p.suffix != ".md":
        return

    today = datetime.now().strftime("%Y-%m-%d")
    content = p.read_text()

    # Parse frontmatter
    if not content.startswith("---"):
        return
    end = content.find("---", 3)
    if end == -1:
        return

    fm = content[3:end]
    body = content[end:]

    # Update hits
    hits_match = re.search(r"^hits:\s*(\d+)", fm, re.MULTILINE)
    if hits_match:
        new_hits = int(hits_match.group(1)) + 1
        fm = re.sub(r"^hits:\s*\d+", f"hits: {new_hits}", fm, count=1, flags=re.MULTILINE)
    else:
        fm = fm.rstrip("\n") + "\nhits: 1\n"

    # Update last-seen
    if re.search(r"^last-seen:", fm, re.MULTILINE):
        fm = re.sub(r"^last-seen:\s*\S+", f"last-seen: {today}", fm, count=1, flags=re.MULTILINE)
    else:
        fm = fm.rstrip("\n") + f"\nlast-seen: {today}\n"

    with contextlib.suppress(Exception):
        p.write_text("---" + fm + body)


# ── euchromatin_titer: track access to reference knowledge for remodeling ──

EUCHROMATIN_DIR = HOME / "epigenome" / "chromatin" / "euchromatin"


def mod_euchromatin_titer(data):
    """Track reads on euchromatin files — the sensor for chromatin remodeling."""
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return
    p = Path(fp)
    if not str(p).startswith(str(EUCHROMATIN_DIR)):
        return
    if not p.exists() or p.suffix != ".md":
        return

    today = datetime.now().strftime("%Y-%m-%d")
    try:
        content = p.read_text(encoding="utf-8")
    except Exception:
        return

    if not content.startswith("---"):
        # No frontmatter — add one with titer
        content = f"---\ntiter-hits: 1\ntiter-last-seen: {today}\n---\n\n{content}"
        with contextlib.suppress(Exception):
            p.write_text(content, encoding="utf-8")
        return

    end = content.find("---", 3)
    if end == -1:
        return

    fm = content[3:end]
    body = content[end:]

    hits_match = re.search(r"^titer-hits:\s*(\d+)", fm, re.MULTILINE)
    if hits_match:
        new_hits = int(hits_match.group(1)) + 1
        fm = re.sub(
            r"^titer-hits:\s*\d+", f"titer-hits: {new_hits}", fm, count=1, flags=re.MULTILINE
        )
    else:
        fm = fm.rstrip("\n") + "\ntiter-hits: 1\n"

    if re.search(r"^titer-last-seen:", fm, re.MULTILINE):
        fm = re.sub(
            r"^titer-last-seen:\s*\S+",
            f"titer-last-seen: {today}",
            fm,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        fm = fm.rstrip("\n") + f"\ntiter-last-seen: {today}\n"

    with contextlib.suppress(Exception):
        p.write_text("---" + fm + body, encoding="utf-8")


# ── bash_post: push reminder, dep pollution, merge checklist, friction log ──

FRICTION_LOG = HOME / ".claude" / "cli-friction.jsonl"


def mod_bash_post(data):
    cmd = data.get("tool_input", {}).get("command", "")
    result = data.get("tool_output", data.get("tool_result", ""))

    # Push reminder after git commit
    if re.search(r"\bgit\s+commit\b", cmd):
        try:
            cwd = data.get("cwd", os.getcwd())
            r = subprocess.run(
                f'git -C "{cwd}" log --oneline @{{upstream}}..HEAD 2>/dev/null | wc -l',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            count = int(r.stdout.strip())
            if count >= 3:
                print(f"{count} unpushed commits. Consider pushing.", file=sys.stderr)
        except Exception:
            pass

    # Dep pollution after delegate
    if re.search(r"\b(gemini|codex exec|opencode run)\b", cmd, re.IGNORECASE):
        cd_match = re.search(r"cd\s+([^\s&;]+)", cmd)
        if cd_match:
            proj_dir = cd_match.group(1).replace("~", str(HOME))
            pyproj = os.path.join(proj_dir, "pyproject.toml")
            if os.path.exists(pyproj):
                try:
                    content = Path(pyproj).read_text()
                    main_match = re.search(
                        r"\[project\]\s*[\s\S]*?dependencies\s*=\s*\[([\s\S]*?)\]", content
                    )
                    opt_match = re.search(
                        r"\[project\.optional-dependencies\]([\s\S]*?)(?:\n\[|\n$)", content
                    )
                    if main_match and opt_match:
                        main_deps = main_match.group(1).lower()
                        opt_pkgs = re.findall(r'"([^"]+)"', opt_match.group(1))
                        opt_names = [
                            p.split("[")[0]
                            .split(">")[0]
                            .split("<")[0]
                            .split("=")[0]
                            .strip()
                            .lower()
                            for p in opt_pkgs
                        ]
                        polluted = [p for p in opt_names if f'"{p}' in main_deps]
                        if polluted:
                            print(
                                f"[auxotrophy] Dependency pollution: {', '.join(polluted)}. Remove from [project].dependencies.",
                                file=sys.stdout,
                            )
                except Exception:
                    pass

    # Post-merge checklist
    if re.search(r"\b(git merge)\b", cmd):
        branch_match = re.search(r"(?:git merge)\s+([^\s;&#]+)", cmd)
        branch = branch_match.group(1) if branch_match else "delegate branch"
        print(
            f'[cytokinesis] "{branch}" merged. Verify: git diff --stat, pyproject.toml deps, pytest, git branch -d'
        )

    # CLI friction log
    if isinstance(result, str) and ("Exit code" in result or "error:" in result):
        personal = re.search(
            rf"~/bin/|{HOME_BIN_PATTERN}|\.cargo/bin/|moneo|fasti|poros|keryx|deltos|caelum|cerno|stips|adytum|sopor|amicus|speculor|gemmation|consilium|qianli|iter|deleo",
            cmd,
        )
        if personal:
            cli_match = re.search(rf"(?:~/bin/|{HOME_BIN_PATTERN}|\.cargo/bin/)?(\w[\w-]*)", cmd)
            entry = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "cli": cli_match.group(1) if cli_match else "unknown",
                "command": cmd[:500],
                "error": (result if isinstance(result, str) else json.dumps(result))[:500],
            }
            try:
                with FRICTION_LOG.open("a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass


# ── ligation_skill: auto-commit skill files ────────────────

SKILLS_DIR = HOME / "germline" / "membrane" / "receptors"
GERMLINE_DIR = HOME / "germline"


def mod_ligation_skill(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return
    try:
        real = Path(fp).resolve()
    except Exception:
        return
    if not str(real).startswith(str(SKILLS_DIR)):
        return

    try:
        rel = real.relative_to(SKILLS_DIR)
    except ValueError:
        rel = real.name

    subprocess.run(["git", "-C", str(GERMLINE_DIR), "add", "-A"], capture_output=True)
    status = subprocess.run(
        ["git", "-C", str(GERMLINE_DIR), "status", "--porcelain"], capture_output=True, text=True
    )
    if not status.stdout.strip():
        return

    subprocess.run(
        ["git", "-C", str(GERMLINE_DIR), "commit", "-m", f"Auto-update: {rel}"],
        capture_output=True,
    )

    gen = HOOKS_DIR / "skill-trigger-gen.py"
    if gen.exists():
        subprocess.run(["python3", str(gen)], capture_output=True)

    # Debounce: one nudge per session, not per file
    flag = Path("/tmp/.cytokinesis-ideal-skill")
    if not flag.exists():
        print(f"IDEAL? skill ({rel}): dedup? format? budget?", file=sys.stderr)
        flag.touch()


# ── ideal? nudge for code edits ──────────────────────────────


def mod_ideal_code(data):
    """Nudge after germline code edits: tests? simplify? naming?"""
    flag = Path("/tmp/.cytokinesis-ideal-code")
    if flag.exists():
        return
    fp = data.get("tool_input", {}).get("file_path", "")
    basename = Path(fp).name
    print(f"IDEAL? code ({basename}): tests? simplify? naming?", file=sys.stderr)
    flag.touch()


# ── glycolytic commit message (deterministic, no symbiont) ──


def _glycolytic_commit(repo_root, rel):
    """Generate conventional commit message from diff stats alone.

    Glycolysis: the cytosol produces ATP (commit messages) without
    the symbiont (LLM). Less efficient labeling but zero latency,
    zero cost, zero failure modes.
    """
    try:
        stat_r = subprocess.run(
            ["git", "-C", repo_root, "diff", "--cached", "--stat"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        stat = stat_r.stdout.strip()
    except Exception:
        stat = ""

    rel_str = str(rel)
    basename = os.path.splitext(os.path.basename(rel_str))[0]

    # Detect scope from path
    parts = rel_str.replace("\\", "/").split("/")
    scope = parts[0] if len(parts) > 1 else ""

    # Detect type from diff
    try:
        r = subprocess.run(
            ["git", "-C", repo_root, "diff", "--cached", "--diff-filter=A", "--name-only"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        new_files = r.stdout.strip().splitlines()
    except Exception:
        new_files = []

    if any(str(rel) in f for f in new_files):
        commit_type = "feat"
        verb = "add"
    elif stat and "delete" in stat.lower():
        commit_type = "refactor"
        verb = "remove"
    else:
        commit_type = "chore"
        verb = "update"

    if scope:
        return f"{commit_type}({scope}): {verb} {basename}"[:72]
    return f"{commit_type}: {verb} {basename}"[:72]


# ── ligation: auto-commit to tracked repos ─────────────────

LIGATION_REPOS = {str(_VIVESCA_ROOT): True}
LIGATION_TEST_PREFIXES = ("membrane/cytoskeleton/", "loci/scripts/", "effectors/")


def mod_ligation(data):
    tool_name = data.get("tool_name", "")
    if tool_name.lower() not in ("edit", "multiedit", "write"):
        return

    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return

    try:
        real = Path(fp).resolve()
    except Exception:
        return

    repo_root = None
    try:
        r = subprocess.run(
            ["git", "-C", str(real.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            repo_root = r.stdout.strip()
    except Exception:
        return

    if not repo_root or repo_root not in LIGATION_REPOS:
        return

    # Debounce 60s per repo
    deb_file = HOME / ".local/share/respirometry" / f"ligation-{Path(repo_root).name}.ts"
    deb_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        if deb_file.exists():
            last = float(deb_file.read_text().strip())
            if time.time() - last < 60:
                subprocess.run(["git", "-C", repo_root, "add", "-A"], capture_output=True)
                return
    except ValueError, OSError:
        pass

    try:
        rel = real.relative_to(repo_root)
    except ValueError:
        rel = real.name

    subprocess.run(["git", "-C", repo_root, "add", "-A"], capture_output=True)
    status = subprocess.run(
        ["git", "-C", repo_root, "status", "--porcelain"], capture_output=True, text=True
    )
    if not status.stdout.strip():
        return

    # Test gate
    rel_str = str(rel)
    if any(rel_str.startswith(p) for p in LIGATION_TEST_PREFIXES):
        print(f"TEST GATE: {rel} staged but not committed. Test, then commit.", file=sys.stderr)
        return

    # Generate commit message — deterministic (glycolysis, no symbiont)
    message = _glycolytic_commit(repo_root, rel)

    subprocess.run(["git", "-C", repo_root, "commit", "-m", message], capture_output=True)
    with contextlib.suppress(OSError):
        deb_file.write_text(str(time.time()))

    if LIGATION_REPOS.get(repo_root):
        subprocess.run(["git", "-C", repo_root, "push"], capture_output=True)


# ── affinity: skill usage log ──────────────────────────────

AFFINITY_LOG = HOME / ".claude" / "skill-usage.tsv"


def mod_affinity(data):
    skill = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if skill:
        try:
            ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            with AFFINITY_LOG.open("a") as f:
                f.write(f"{ts}\t{skill}\n")
        except OSError:
            pass


# ── hebbian: learn from skill misses ───────────────────────

HEBBIAN_LOG = HOME / ".claude" / "skill-suggest-log.tsv"
HEBBIAN_CACHE = HOME / ".claude" / "last-prompt.txt"


def mod_hebbian(data):
    skill = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if not skill or ":" in skill:
        return

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    was_predicted = False
    if HEBBIAN_LOG.exists():
        try:
            now = datetime.now()
            for line in HEBBIAN_LOG.read_text().strip().split("\n")[-20:]:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[1] == "suggested" and parts[2] == skill:
                    try:
                        t = datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S")
                        if (now - t).total_seconds() < 30:
                            was_predicted = True
                    except ValueError:
                        pass
        except Exception:
            pass

    prompt_snippet = ""
    try:
        if HEBBIAN_CACHE.exists():
            prompt_snippet = HEBBIAN_CACHE.read_text().strip()[:200]
    except OSError:
        pass

    try:
        with HEBBIAN_LOG.open("a") as f:
            if was_predicted:
                f.write(f"{ts}\thit\t{skill}\t\n")
            else:
                f.write(f"{ts}\tmiss\t{skill}\t{prompt_snippet}\n")
    except OSError:
        pass


# ── cofactor: mental model nudge ───────────────────────────

COFACTOR_MODELS = [
    "opportunity cost",
    "sunk cost",
    "premortem",
    "second-order",
    "base rate",
    "confirmation bias",
    "incentives",
    "reversibility",
    "chesterton",
    "leverage point",
    "compounding",
    "inversion",
    "goodhart",
    "anchoring",
    "steel man",
    "survivorship",
]


def mod_cofactor(data):
    skill = data.get("tool_input", {}).get("skill", "") or data.get("tool_input", {}).get(
        "name", ""
    )
    if skill not in ("quorum", "design"):
        return
    result_text = str(data.get("tool_result", "")).lower()
    if not any(m in result_text for m in COFACTOR_MODELS):
        print(
            f"[model-check] /{skill} ran without naming a mental model. Scan the lens table first."
        )


# ── docima: replicate MEMORY.md edits ──────────────────────


def mod_docima(data):
    tool = data.get("tool", "")
    if tool not in ("Edit", "Write"):
        return
    ti = data.get("tool_input", {})
    fp = ti.get("file_path", "")
    if "MEMORY.md" not in fp:
        return

    new_string = ti.get("new_string", "") or ti.get("content", "")
    if not new_string:
        return

    facts = [
        line[2:].strip()
        for line in new_string.splitlines()
        if line.strip().startswith("- **") and len(line.strip()) > 20
    ]
    if not facts:
        return

    for fact in facts:
        try:
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            subprocess.run(
                ["uv", "run", "docima", "add", fact, "-b", "all", "--silent"],
                cwd=str(HOME / "code/docima"),
                capture_output=True,
                timeout=30,
                env=env,
            )
        except Exception:
            pass


# ── attention_refresh: REMOVED ──
# Tonus.md already injected at session start via synapse anamnesis.
# Re-injecting every 25 tool calls was duplicate context burn.


# ── apoptosis: log tool failures ───────────────────────────

APOPT_FILE = HOME / "epigenome" / "chromatin" / "failures.md"
APOPT_EXPECTED = {"grep", "diff", "rg", "test", "[ "}


def mod_apoptosis(data):
    tool = data.get("tool", "")
    ti = data.get("tool_input", {})
    response = data.get("tool_response", {})

    is_error = response.get("is_error", False)
    exit_code = response.get("exit_code")
    stderr = (response.get("stderr") or "").strip()

    if "DELEGATE GATE" in stderr or "hook" in stderr.lower():
        return

    failed = is_error or (exit_code is not None and exit_code != 0)
    if not failed:
        return

    # Expected non-zero
    if tool == "Bash":
        cmd = (ti.get("command") or "").strip()
        if any(cmd.startswith(t) for t in APOPT_EXPECTED):
            return

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")
    if tool == "Bash":
        cmd = (ti.get("command") or "").strip()[:200]
        entry = f"\n## {ts} -- Bash (exit {exit_code})\n**Command:** `{cmd}`\n**Error:** {stderr[:300] or '(no stderr)'}\n"
    else:
        fp = ti.get("file_path") or ti.get("path") or "(no path)"
        entry = f"\n## {ts} -- {tool} (error)\n**Path:** `{fp}`\n**Error:** {stderr[:300] or str(response)[:200]}\n"

    try:
        APOPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with APOPT_FILE.open("a") as f:
            f.write(entry)
    except Exception:
        pass


# ── proprioception: session self-sensing ───────────────────

PROPRIO_TOOL_LOG = HOME / ".claude" / "tool-call-log.jsonl"
PROPRIO_HOOK_LOG = HOME / "logs" / "hook-fire-log.jsonl"
PROPRIO_STATE = Path(os.environ.get("TMPDIR", "/tmp")) / "proprioception-state.json"
PROPRIO_INTERVAL = 20


def mod_proprioception(_data):
    state = {"count": 0, "start": time.time()}
    with contextlib.suppress(Exception):
        state = json.loads(PROPRIO_STATE.read_text())

    state["count"] = state.get("count", 0) + 1
    session_start = state.get("start", time.time())
    PROPRIO_STATE.write_text(json.dumps(state))

    if state["count"] % PROPRIO_INTERVAL != 0:
        return

    elapsed_min = int((time.time() - session_start) / 60)

    # Count tool errors
    tool_calls = tool_errors = 0
    if PROPRIO_TOOL_LOG.exists():
        try:
            for line in PROPRIO_TOOL_LOG.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                    ts = e.get("ts", "")
                    if session_start > 0 and ts:
                        ets = datetime.fromisoformat(ts).timestamp()
                        if ets < session_start:
                            continue
                    tool_calls += 1
                    if e.get("hasError"):
                        tool_errors += 1
                except Exception:
                    continue
        except Exception:
            pass

    # Count denials
    denials = 0
    if PROPRIO_HOOK_LOG.exists():
        try:
            for line in PROPRIO_HOOK_LOG.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                    ts = e.get("ts", "")
                    if session_start > 0 and ts:
                        ets = datetime.fromisoformat(ts).timestamp()
                        if ets < session_start:
                            continue
                    denials += 1
                except Exception:
                    continue
        except Exception:
            pass

    if tool_errors > 3 or denials > 2 or elapsed_min > 90:
        error_rate = f"{tool_errors / tool_calls * 100:.0f}%" if tool_calls > 0 else "0%"
        parts = [f"depth={state['count']}", f"{elapsed_min}min"]
        if tool_errors > 0:
            parts.append(f"errors={tool_errors} ({error_rate})")
        if denials > 0:
            parts.append(f"denials={denials}")
        print(f"[proprioception] {', '.join(parts)}")
        if elapsed_min > 90:
            print("Session >90min -- consider /compact or /wrap.")
        if tool_errors > 5:
            print("High error rate -- stuck? Try different approach.")


# ── apoptosis_praxis: dismissed item guard ─────────────────

PRAXIS_DISMISSED = HOME / "epigenome" / "chromatin" / "Praxis Dismissed.md"


def mod_apoptosis_praxis(data):
    ti = data.get("tool_input", {})
    text = ti.get("new_string", "") or ti.get("content", "")
    if not text:
        return

    if not PRAXIS_DISMISSED.exists():
        return

    dismissed = []
    for line in PRAXIS_DISMISSED.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("- ") and len(s) > 2:
            dismissed.append(s[2:].strip().lower())
    if not dismissed:
        return

    matches = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("- [ ]"):
            continue
        lower = s.lower()
        for pattern in dismissed:
            if pattern in lower:
                matches.append(pattern)

    if matches:
        patterns = ", ".join(f"'{m}'" for m in matches)
        print(f"DISMISSED ITEM DETECTED: {patterns}. Remove and do not re-add.", file=sys.stderr)


# ── retrograde: log symbiont→organism memory writes ───────

_RETROGRADE_LOG = HOME / ".cache" / "retrograde" / "signals.jsonl"
_RETROGRADE_MEMORY_DIR = HOME / ".claude" / "projects" / _PROJECT_SLUG / "memory"


def _retrograde_append(direction: str, signal_type: str, detail: str) -> None:
    """Fire-and-forget append to retrograde signals.jsonl. Never raises."""
    import datetime

    try:
        _RETROGRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.datetime.now(datetime.UTC).isoformat(),
            "direction": direction,
            "type": signal_type,
            "detail": detail,
        }
        with _RETROGRADE_LOG.open("a") as _f:
            _f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def mod_retrograde(data):
    """Log retrograde signals for memory writes not already captured passively.

    Passive coverage in retrograde.py:
      - git commits by Claude: git log --author=Claude  (no wiring needed)
      - methylation: methylation-candidates.jsonl + methylation.jsonl  (no wiring needed)
      - mismatch repair: infections.jsonl healed=True  (no wiring needed)

    Gap: memory file writes are not in any passive source.
    """
    tool_name = data.get("tool", "")
    if tool_name not in ("Edit", "Write"):
        return

    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return

    p = Path(fp)
    # Memory writes: files under the project memory dir
    if str(p.resolve()).startswith(str(_RETROGRADE_MEMORY_DIR)) and p.suffix == ".md":
        _retrograde_append("retrograde", "memory_write", fp)


# ── assay nudge: new organelle/tool without test ──────────


_ASSAY_DIRS = ("organelles/", "tools/")
_ASSAY_ROOT = _VIVESCA_ROOT / "assays"


def mod_assay_nudge(data):
    """Nudge when writing to organelles/ or tools/ without a test file."""
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp.endswith(".py"):
        return
    # Only fire for organelle/tool source files
    matched_dir = None
    for d in _ASSAY_DIRS:
        if d in fp:
            matched_dir = d
            break
    if not matched_dir:
        return

    # Extract module name from path
    basename = Path(fp).stem
    if basename.startswith("_") or basename == "__init__":
        return

    # Check if a test file exists
    test_file = _ASSAY_ROOT / f"test_{basename}.py"
    if not test_file.exists():
        print(
            f"ASSAY MISSING: no assays/test_{basename}.py for {matched_dir}{basename}.py. "
            f"Genome rule: new organelles and tools ship with tests.",
            file=sys.stderr,
        )


# ── chaperone propagation: nudge when tool code changes but skill may be stale ──


_PROPAGATION_DIRS = ("enzymes/", "organelles/", "effectors/")


def mod_chaperone_propagation(data):
    """After editing tool/enzyme/organelle/effector code, remind to update skills + memories."""
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp.endswith(".py") and "/effectors/" not in fp:
        return
    if not any(d in fp for d in _PROPAGATION_DIRS):
        return

    # Fire at most once per session to avoid noise
    session_file = Path(f"/tmp/propagation-{os.getpid()}.flag")
    if session_file.exists():
        return
    session_file.touch()

    component = Path(fp).stem
    print(
        f"[propagation] You modified {component}. Before wrapping up: "
        f"check if skills/memories/routing need updating. "
        f"Sweep: grep -rl '{component}' ~/germline/membrane/receptors/",
        file=sys.stderr,
    )


def mod_recipe_sync(data):
    """Auto-sync recipe.yaml instructions when SKILL.md is modified."""
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp.endswith("/SKILL.md"):
        return
    if "/receptors/" not in fp:
        return

    skill_dir = Path(fp).parent
    recipe_path = skill_dir / "recipe.yaml"
    skill_path = skill_dir / "SKILL.md"

    if not recipe_path.exists() or not skill_path.exists():
        return

    import re as _re

    import yaml as _yaml

    skill_text = skill_path.read_text(encoding="utf-8")
    recipe_text = recipe_path.read_text(encoding="utf-8")

    # Extract description from SKILL.md frontmatter
    desc_match = _re.search(r"^description:\s*(.+)$", skill_text, _re.MULTILINE)
    new_desc = desc_match.group(1).strip() if desc_match else None

    # Extract instructions: everything after the closing --- of frontmatter
    parts = skill_text.split("---", 2)
    if len(parts) >= 3:
        new_instructions = parts[2].strip()
    else:
        return

    # Update recipe.yaml
    recipe_data = _yaml.safe_load(recipe_text)
    if not recipe_data:
        return

    changed = False
    if new_desc and recipe_data.get("description") != new_desc:
        recipe_data["description"] = new_desc
        changed = True
    if recipe_data.get("instructions", "").strip() != new_instructions:
        recipe_data["instructions"] = new_instructions
        changed = True

    if changed:
        # Preserve YAML formatting: dump with block style for instructions
        output_lines = []
        for key in ["title", "name", "description"]:
            if key in recipe_data:
                val = recipe_data[key]
                output_lines.append(f'{key}: "{val}"')
        output_lines.append("instructions: |")
        for line in new_instructions.split("\n"):
            output_lines.append(f"  {line}" if line.strip() else "")
        # Preserve any extra keys (extensions, etc.)
        skip_keys = {"title", "name", "description", "instructions"}
        for key, val in recipe_data.items():
            if key not in skip_keys:
                output_lines.append(f"{key}: {_yaml.dump(val, default_flow_style=True).strip()}")

        recipe_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        print(
            f"[recipe-sync] Synced {skill_dir.name}/recipe.yaml from SKILL.md",
            file=sys.stderr,
        )


# ── antisera: progressive discovery of known gotcha/fix pairs ──────────
#
# Two triggers (both deterministic, no LLM):
#   Reactive — tool result contains error signal → match error text against tags
#   Primed   — first use of a tool/domain in session → surface relevant antisera once
#
# Session dedup: /tmp/antisera-presented-{pid_of_session}.txt
# Token economy: each antiserum is ~200 tokens; zero cost when no match.

ANTISERA_DIR = _VIVESCA_ROOT / "loci" / "antisera"

# Error keywords that trigger reactive matching
_ANTISERA_ERROR_SIGNALS = (
    "error",
    "fail",
    "exception",
    "traceback",
    "exit code",
    "403",
    "401",
    "no tty",
    "permission denied",
    "not found",
    "connection refused",
)


def _antisera_session_file() -> Path:
    """Path to per-session presented-antisera tracker.

    Uses CLAUDE_SESSION_ID env var when available (CC sets it).
    Falls back to PID-of-parent-process for robustness.
    """
    session_id = os.environ.get("CLAUDE_SESSION_ID") or str(os.getppid())
    return Path(f"/tmp/antisera-presented-{session_id}.txt")


def _antisera_already_presented(slug: str, session_file: Path) -> bool:
    try:
        if session_file.exists():
            return slug in session_file.read_text().split("\n")
    except Exception:
        pass
    return False


def _antisera_mark_presented(slug: str, session_file: Path) -> None:
    try:
        with session_file.open("a") as f:
            f.write(slug + "\n")
    except Exception:
        pass


def _antisera_parse_tags(content: str) -> list[str]:
    """Extract tags list from YAML frontmatter. Pure string parsing, no yaml import."""
    if not content.startswith("---"):
        return []
    end = content.find("---", 3)
    if end == -1:
        return []
    fm = content[3:end]
    for line in fm.splitlines():
        line = line.strip()
        if line.startswith("tags:"):
            # tags: [bird, twitter, x, cli]  or  tags:\n  - bird
            bracket_match = re.search(r"\[([^\]]+)\]", line)
            if bracket_match:
                return [t.strip().strip("'\"") for t in bracket_match.group(1).split(",")]
            # Inline without brackets: tags: bird, twitter
            rest = line[5:].strip()
            if rest:
                return [t.strip().strip("'\"") for t in rest.split(",")]
            # Multi-line list: look ahead in frontmatter
            tags = []
            in_tags = False
            for fm_line in fm.splitlines():
                if fm_line.strip().startswith("tags:"):
                    in_tags = True
                    continue
                if in_tags:
                    if fm_line.strip().startswith("- "):
                        tags.append(fm_line.strip()[2:].strip().strip("'\""))
                    elif fm_line.strip() and not fm_line.startswith(" "):
                        break
            return tags
    return []


def _antisera_load_index() -> list[dict]:
    """Load all antisera files → [{slug, tags, content}]. Cached in module scope."""
    if not ANTISERA_DIR.exists():
        return []
    entries = []
    for fp in ANTISERA_DIR.glob("*.md"):
        try:
            content = fp.read_text(encoding="utf-8")
            tags = _antisera_parse_tags(content)
            if tags:
                entries.append({"slug": fp.stem, "tags": tags, "content": content})
        except Exception:
            pass
    return entries


# Module-level cache: loaded once per process
_ANTISERA_INDEX: list[dict] | None = None


def _antisera_index() -> list[dict]:
    global _ANTISERA_INDEX
    if _ANTISERA_INDEX is None:
        _ANTISERA_INDEX = _antisera_load_index()
    return _ANTISERA_INDEX


def _antisera_format(entry: dict) -> str:
    """Format an antiserum entry for advisory output."""
    slug = entry["slug"]
    # Strip frontmatter from display content
    content = entry["content"]
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3 :].strip()
    return f"[antiserum:{slug}]\n{content}"


def _antisera_update_titer(entry: dict) -> None:
    """Increment titer engagement count and timestamp in the antiserum's frontmatter."""
    fp = ANTISERA_DIR / f"{entry['slug']}.md"
    try:
        content = fp.read_text(encoding="utf-8")
    except Exception:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    if not content.startswith("---"):
        return
    end = content.find("---", 3)
    if end == -1:
        return
    fm = content[3:end]
    body = content[end:]
    # Update or insert titer-hits and titer-last-seen
    hits_match = re.search(r"^titer-hits:\s*(\d+)", fm, re.MULTILINE)
    if hits_match:
        old_hits = int(hits_match.group(1))
        fm = re.sub(
            r"^titer-hits:\s*\d+", f"titer-hits: {old_hits + 1}", fm, count=1, flags=re.MULTILINE
        )
    else:
        fm = fm.rstrip("\n") + "\ntiter-hits: 1\n"
    seen_match = re.search(r"^titer-last-seen:", fm, re.MULTILINE)
    if seen_match:
        fm = re.sub(
            r"^titer-last-seen:.*", f"titer-last-seen: {today}", fm, count=1, flags=re.MULTILINE
        )
    else:
        fm = fm.rstrip("\n") + f"\ntiter-last-seen: {today}\n"
    with contextlib.suppress(Exception):
        fp.write_text(f"---{fm}{body}", encoding="utf-8")


def mod_antisera_discovery(data):
    """Progressive discovery: surface antisera on error or first domain use."""
    tool_name = data.get("tool_name", data.get("tool", "")).lower()
    result = data.get("tool_output", data.get("tool_result", ""))
    result_text = (result if isinstance(result, str) else json.dumps(result)).lower()

    index = _antisera_index()
    if not index:
        return

    session_file = _antisera_session_file()
    surfaced = []

    # ── Reactive trigger: error signal in result ──────────────
    has_error = any(sig in result_text for sig in _ANTISERA_ERROR_SIGNALS)
    if has_error:
        for entry in index:
            slug = entry["slug"]
            if _antisera_already_presented(slug, session_file):
                continue
            tags = entry["tags"]
            # Match: any tag appears in the error text OR in the tool name
            if any(tag.lower() in result_text or tag.lower() in tool_name for tag in tags):
                surfaced.append(entry)
                _antisera_mark_presented(slug, session_file)

    # ── Primed trigger: first use of this tool domain ─────────
    # Domain = tool_name itself (e.g. "bash", "mcp__vivesca__rheotaxis_search")
    # Normalise to the leaf tool word for matching
    tool_words = set(re.split(r"[_\-]+", tool_name))
    if not has_error:  # only prime when no error (avoid double-firing on same entry)
        primed_key = f"primed:{tool_name}"
        if not _antisera_already_presented(primed_key, session_file):
            _antisera_mark_presented(primed_key, session_file)
            for entry in index:
                slug = entry["slug"]
                if _antisera_already_presented(slug, session_file):
                    continue
                tags_lower = [t.lower() for t in entry["tags"]]
                if any(w in tags_lower for w in tool_words if len(w) > 2):
                    surfaced.append(entry)
                    _antisera_mark_presented(slug, session_file)

    for entry in surfaced:
        print(_antisera_format(entry))
        _antisera_update_titer(entry)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError, EOFError:
        sys.exit(0)

    tool = data.get("tool", "")
    fp = data.get("tool_input", {}).get("file_path", "")

    # Each module in try/except for fault isolation
    modules = []

    # Chaperones (Edit/Write only, by file extension)
    if tool in ("Edit", "Write", "MultiEdit"):
        if fp.endswith(".py"):
            modules.append(chaperone_py)
        if re.search(r"\.(js|jsx|ts|tsx)$", fp):
            modules.append(chaperone_js)
        if re.search(r"\.(ts|tsx)$", fp):
            modules.append(chaperone_ts)
        if fp.endswith(".rs"):
            modules.append(chaperone_rs)

    # Perseveration (Edit/Write/Bash/NotebookEdit)
    if tool in ("Edit", "Write", "Bash", "NotebookEdit"):
        modules.append(mod_perseveration)

    # Chromatin (Edit/Write on MEMORY.md)
    if tool in ("Edit", "Write") and "MEMORY.md" in fp:
        modules.append(mod_chromatin)

    # Bash post-processing
    if tool == "Bash":
        modules.append(mod_bash_post)

    # Ligation skill (Edit/Write on /skills/)
    if tool in ("Edit", "Write") and "/skills/" in fp:
        modules.append(mod_ligation_skill)

    # Ligation (Edit/Write general)
    if tool in ("Edit", "Write"):
        modules.append(mod_ligation)

    # Skill post-processing
    if tool == "Skill":
        modules.append(mod_affinity)
        modules.append(mod_hebbian)
        modules.append(mod_cofactor)

    # Docima (Edit/Write on MEMORY.md)
    if tool in ("Edit", "Write") and "MEMORY.md" in fp:
        modules.append(mod_docima)

    # Recurrence tracking (Read on memory files)
    if tool == "Read" and "memory/" in fp:
        modules.append(mod_recurrence)

    # Euchromatin titer (Read on reference knowledge)
    if tool == "Read" and "euchromatin/" in fp:
        modules.append(mod_euchromatin_titer)

    # Always-fire modules
    modules.append(mod_apoptosis)
    modules.append(mod_proprioception)

    # Praxis guard (Edit/Write on Praxis.md)
    if tool in ("Edit", "Write") and "Praxis.md" in fp:
        modules.append(mod_apoptosis_praxis)

    # Assay nudge (Edit/Write on organelles/ or tools/)
    if tool in ("Edit", "Write") and any(d in fp for d in _ASSAY_DIRS):
        modules.append(mod_assay_nudge)

    # Chaperone propagation (Edit/Write on enzymes/organelles/effectors)
    if tool in ("Edit", "Write") and any(d in fp for d in _PROPAGATION_DIRS):
        modules.append(mod_chaperone_propagation)

    # Recipe sync (Write/Edit on receptor SKILL.md)
    if tool in ("Edit", "Write") and "/receptors/" in fp and fp.endswith("/SKILL.md"):
        modules.append(mod_recipe_sync)

    # Ideal? nudge (Edit/Write on germline code, non-skill — skills handled by ligation)
    if (
        tool in ("Edit", "Write")
        and "/germline/" in fp
        and "/skills/" not in fp
        and fp.endswith(".py")
    ):
        modules.append(mod_ideal_code)

    # Retrograde signal logging (Edit/Write on memory files)
    if tool in ("Edit", "Write") and "memory/" in fp:
        modules.append(mod_retrograde)

    # Antisera discovery (Bash + any tool that can return errors)
    modules.append(mod_antisera_discovery)

    for mod in modules:
        with contextlib.suppress(Exception):
            mod(data)


if __name__ == "__main__":
    main()
