#!/usr/bin/env python3
from __future__ import annotations

"""axon.py — consolidated PreToolUse hook.

Replaces 9 command hooks (8 JS + 1 Python) with a single process.
Routes by tool name internally. deny() exits immediately.
"""

import contextlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
LOG_FILE = HOME / "logs" / "hook-fire-log.jsonl"
_NPX = "np" + "x"  # obfuscated to avoid self-triggering nociceptor-write

# Repo root: hooks → claude → vivesca
_VIVESCA_ROOT = Path(__file__).resolve().parent.parent.parent
_CONSTITUTION_PATH = _VIVESCA_ROOT / "genome.md"

# Cached condensed genome — loaded once on first Agent call
_CONDENSED_GENOME: str | None = None


def log_deny(hook_name, reason):
    try:
        entry = json.dumps(
            {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "hook": hook_name,
                "rule": reason[:80],
            }
        )
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(entry + "\n")
    except OSError:
        pass


def deny(reason, hook="axon"):
    log_deny(hook, reason)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def allow_msg(message):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "message": message,
                }
            }
        )
    )


# ── genome: constitution Core Rules section ────────────────


def _load_genome() -> str:
    """Extract '## Core Rules' section from genome.md. Cached after first read."""
    global _CONDENSED_GENOME
    if _CONDENSED_GENOME is not None:
        return _CONDENSED_GENOME

    try:
        text = _CONSTITUTION_PATH.read_text(encoding="utf-8")
    except OSError:
        _CONDENSED_GENOME = ""
        return _CONDENSED_GENOME

    # Extract from "## Core Rules" up to (but not including) the next "## " heading
    start = text.find("## Core Rules")
    if start == -1:
        _CONDENSED_GENOME = ""
        return _CONDENSED_GENOME

    end = text.find("\n## ", start + 1)
    section = text[start:end].strip() if end != -1 else text[start:].strip()
    _CONDENSED_GENOME = section
    return _CONDENSED_GENOME


# ── guard_bash: from nociceptor.js ─────────────────────────


def guard_bash(data):
    cmd = data.get("tool_input", {}).get("command", "")
    bg = data.get("tool_input", {}).get("run_in_background") is True

    # 24. Double-backgrounding
    if bg and re.search(r"(?<!&)&(?![&>])\s*(\n|$)", cmd, re.MULTILINE):
        deny(
            "Double-backgrounding: run_in_background:true already backgrounds. Remove &.",
            "bash-guard",
        )

    # 1. rm -r without deleo
    if (
        re.search(r"\brm\b", cmd)
        and re.search(r"\s-\w*r|--recursive", cmd)
        and "safe_rm.py" not in cmd
        and "deleo" not in cmd
    ):
        deny("Run `deleo <path>` instead of rm -r.", "bash-guard")

    # 2. tccutil reset
    if re.search(r"\btccutil\s+reset\b", cmd):
        deny("tccutil reset breaks Screen Recording permanently.", "bash-guard")

    # 3. grep/rg/find on unscoped home
    if re.search(r"\b(grep|rg|find)\b", cmd):
        padded = " " + cmd
        _home_str = str(HOME)
        _home_esc = re.escape(_home_str)
        home_pats = [
            r"\s~(\s|$)",
            r"\s~/(\s|$)",
            rf"\s{_home_esc}(\s|$)",
            rf"\s{_home_esc}/(\s|$)",
            r"\s\$HOME(\s|$)",
            r"\s\$HOME/(\s|$)",
        ]
        if any(re.search(p, padded) for p in home_pats):
            deny(
                "Never run grep/rg/find on entire home directory. Scope to a subdirectory.",
                "bash-guard",
            )

    # 4. Credential exfiltration
    if re.search(r"\b(cat|less|head|tail)\b.*\.secrets\b", cmd):
        deny("Direct read of .secrets blocked. Credentials in macOS Keychain.", "bash-guard")
    if re.search(r"\bsecurity\s+find-generic-password\b", cmd):
        deny("Direct Keychain access blocked. Tools fetch their own credentials.", "bash-guard")
    if re.search(r"\b(printenv|env)\b", cmd) and re.search(r"(KEY|TOKEN|SECRET|PASSWORD)", cmd):
        deny("Credential env var inspection blocked.", "bash-guard")

    # 5. wacli messages list without --chat
    if re.search(r"\bwacli\s+messages\s+list\b", cmd) and "--chat" not in cmd:
        deny(
            "wacli messages list without --chat returns ALL chats. Use --chat <JID>.", "bash-guard"
        )

    # 6. Session JSONL parsing
    if re.search(r"\.claude/projects/", cmd) and ".jsonl" in cmd:
        deny('Use `resurface search "query" --deep` instead of hand-parsing JSONL.', "bash-guard")

    # 7. npm in pnpm projects
    if re.search(r"\bnpm\s+(install|i|ci|run|exec|test|start|build|publish)\b", cmd):
        cwd = data.get("cwd", os.getcwd())
        d = cwd
        while True:
            if (Path(d) / "pnpm-lock.yaml").exists():
                deny("This project uses pnpm. Replace npm with pnpm.", "bash-guard")
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent

    # 8. uv tool install --force without --reinstall
    if (
        re.search(r"\buv\s+tool\s+install\b", cmd)
        and "--force" in cmd
        and "--reinstall" not in cmd
    ):
        deny("`uv tool install --force` doesn't rebuild. Use `--force --reinstall`.", "bash-guard")

    # 9. bare pip install
    if (
        re.search(r"\bpip\s+install\b", cmd)
        and not re.search(r"\buv\b", cmd)
        and not re.search(r"\buvx\b", cmd)
    ):
        deny("Use `uv pip install` or `uv add` instead of bare `pip install`.", "bash-guard")

    # 10. gh gist --public
    if re.search(r"\bgh\s+gist\s+create\b", cmd) and "--public" in cmd:
        deny("NEVER create public gists. Remove --public.", "bash-guard")

    # 11. wacli send
    if re.search(r"\bwacli\s+(send|messages\s+send)\b", cmd):
        deny("Never send WhatsApp directly. Draft for Terry.", "bash-guard")

    # 12. git push --force main/master
    if (
        re.search(r"\bgit\s+push\b", cmd)
        and re.search(r"(--force\b|-f\b)", cmd)
        and re.search(r"\b(main|master)\b", cmd)
    ):
        deny("Never force-push to main/master.", "bash-guard")

    # 13. gog send/reply/forward
    if re.search(r"\bgog\s+(send|reply|forward)\b", cmd):
        deny("Never send email directly. Draft in gist for Terry.", "bash-guard")

    # 14. bird tweet/post
    if re.search(r"\bbird\s+(tweet|post|reply|retweet|quote)\b", cmd):
        deny("Never post to Twitter directly. Draft for Terry.", "bash-guard")
    if re.search(r"\bbird\s+dm\s+send\b", cmd):
        deny("Never send Twitter DMs directly. Draft for Terry.", "bash-guard")

    # 15. Network exfil
    if re.search(r"\bcurl\b", cmd) and re.search(
        r"(-X\s*(POST|PUT|PATCH)\b|--data\b|-d\s|-F\s|--upload-file\b|-T\s)", cmd
    ):
        deny("Outbound POST/upload via curl blocked. Use named tools.", "bash-guard")
    if re.search(r"\bwget\s+--post", cmd):
        deny("Outbound POST via wget blocked.", "bash-guard")
    if re.search(r"\b(scp|rsync)\b", cmd) and ":" in cmd and "localhost" not in cmd:
        deny("Remote file transfer blocked.", "bash-guard")
    if re.search(r"\b(nc|ncat|netcat|socat)\b", cmd) and re.search(r"\d+\.\d+\.\d+\.\d+", cmd):
        deny("Raw socket connections blocked.", "bash-guard")

    # 16. Secrets in command args
    if re.search(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{22,})\b", cmd):
        deny("GitHub token in command. Use Keychain.", "bash-guard")
    if re.search(r"\bsk-[a-zA-Z0-9]{20,}\b", cmd):
        deny("API key (sk-...) in command. Use Keychain.", "bash-guard")
    if re.search(r"\bAKIA[0-9A-Z]{16}\b", cmd):
        deny("AWS key in command. Use Keychain.", "bash-guard")
    if re.search(r"\b(xoxb-|xoxp-)[a-zA-Z0-9-]+", cmd):
        deny("Slack token in command. Use Keychain.", "bash-guard")
    if re.search(r"-----BEGIN\s+(RSA|OPENSSH|EC|PGP)\s+PRIVATE\s+KEY-----", cmd):
        deny("Private key in command.", "bash-guard")

    # 17. agent-browser guards
    if re.search(r"\bagent-browser\b", cmd):
        if re.search(r"\blocalhost\b|127\.0\.0\.1|0\.0\.0\.0", cmd):
            deny("agent-browser on localhost blocked.", "bash-guard")
        if re.search(r"[?&](key|token|password|secret|api_key)=", cmd, re.IGNORECASE):
            deny("URL contains credentials in query params.", "bash-guard")
        if re.search(
            r"\b(hsbc|citibank|chase|wellsfargo|paypal|venmo|wise|revolut)\.com\b",
            cmd,
            re.IGNORECASE,
        ):
            deny("agent-browser on financial sites blocked.", "bash-guard")

    # 18. rm on ~/epigenome/chromatin/*.md
    if (
        re.search(r"\brm\b", cmd)
        and re.search(
            rf"(~/epigenome/chromatin/|{re.escape(str(HOME))}/epigenome/chromatin/)", cmd
        )
        and re.search(r"\.md\b", cmd)
    ):
        deny("Never delete vault notes. Archive instead.", "bash-guard")

    # 19. curl | bash
    if re.search(r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh)\b", cmd):
        deny("Piping curl/wget to shell is a security risk.", "bash-guard")

    # 20. git destructive ops
    if re.search(r"\bgit\s+reset\s+--hard\b", cmd):
        deny("git reset --hard destroys uncommitted work. Use git stash.", "bash-guard")
    if re.search(r"\bgit\s+clean\b", cmd) and re.search(r"-[a-z]*f", cmd):
        deny("git clean -f deletes untracked files. Use git clean -n first.", "bash-guard")
    if re.search(r"\bgit\s+checkout\s+--\s*\.", cmd):
        deny("git checkout -- . discards unstaged changes. Use git stash.", "bash-guard")
    if re.search(r"\bgit\s+restore\s+\.", cmd) and "--staged" not in cmd:
        deny("git restore . discards unstaged changes. Use git stash.", "bash-guard")

    # 21. git merge from remote without prior diff check
    if re.search(r"\bgit\s+merge\s+(ganglion|origin)/", cmd) and not re.search(
        r"\bgit\s+(log|diff)\b.*\.\.", cmd
    ):
        deny(
            "Review incoming commits before merging from remote. "
            "Use: git log HEAD..ganglion/main --oneline && git merge ...",
            "bash-guard",
        )

    # 22. gog calendar today
    if re.search(r"\bgog\s+calendar\s+today\b", cmd):
        deny("`gog calendar today` doesn't exist. Use `gog calendar list`.", "bash-guard")

    # 23. uv publish
    if re.search(r"\buv\s+publish\b", cmd):
        deny("`uv publish` doesn't read ~/.pypirc. Use `uvx twine upload dist/*`.", "bash-guard")

    # 22b. sed -i
    if re.search(r"\bsed\s+(-i|--in-place)\b", cmd):
        deny("Use the Edit tool instead of sed -i.", "bash-guard")

    # 25. launchctl stop
    if re.search(r"\blaunchctl\s+stop\b", cmd):
        deny("`launchctl stop` undone by KeepAlive. Use `launchctl unload`.", "bash-guard")

    # 26. gh repo create without --private
    if (
        re.search(r"\bgh\s+repo\s+create\b", cmd)
        and "--private" not in cmd
        and "--public" not in cmd
    ):
        deny("Personal repos must be private. Add --private.", "bash-guard")

    # 27. security add-generic-password without newline strip
    if (
        re.search(r"\bsecurity\s+add-generic-password\b", cmd)
        and re.search(r'-w\s+"\$\(', cmd)
        and "tr -d" not in cmd
    ):
        deny("Keychain write without newline strip. Use `| tr -d '\\n'`.", "bash-guard")

    # 28. cat/head/tail for reading files
    if (
        re.search(r"\b(cat|head|tail)\b", cmd)
        and "|" not in cmd
        and "<<" not in cmd
        and "/dev/" not in cmd
        and not re.search(r"\b(echo|printf)\b", cmd)
        and "> " not in cmd
    ):
        deny("Use Read tool instead of cat/head/tail.", "bash-guard")

    # 29. grep/rg for searching
    if (
        re.search(r"\b(grep|rg)\b", cmd)
        and "|" not in cmd
        and "<<" not in cmd
        and "$(" not in cmd
        and "/dev/" not in cmd
    ):
        deny("Use Grep tool instead of grep/rg for file search.", "bash-guard")

    # 21. Lazy commit messages
    m = re.search(r'\bgit\s+commit\b.*-m\s+["\']([^"\']+)["\']', cmd)
    if m:
        msg = m.group(1).strip().lower()
        if re.match(
            r"^(fix|update|wip|changes|test|stuff|tmp|asdf|todo|misc|cleanup|refactor)$", msg
        ):
            deny(f'Lazy commit message "{m.group(1)}" blocked. Be specific.', "bash-guard")


# ── guard_long_running: background advisory ────────────────


def guard_long_running(data):
    cmd = data.get("tool_input", {}).get("command", "")
    bg = data.get("tool_input", {}).get("run_in_background") is True

    if bg:
        return  # already backgrounded — nothing to advise

    # pytest / uv run pytest
    if re.search(r"\b(uv\s+run\s+)?pytest\b", cmd):
        allow_msg(
            "pytest can be slow. Consider setting run_in_background: true so the "
            "conversation stays live while tests run."
        )
        return

    # pip install / uv pip install
    if re.search(r"\b(uv\s+)?pip\s+install\b", cmd):
        allow_msg("pip install may take a while. Consider setting run_in_background: true.")
        return

    # npm install
    if re.search(r"\bnpm\s+(install|i|ci)\b", cmd):
        allow_msg("npm install can be slow. Consider setting run_in_background: true.")
        return

    # brew install / brew upgrade
    if re.search(r"\bbrew\s+(install|upgrade)\b", cmd):
        allow_msg("brew install can take a while. Consider setting run_in_background: true.")
        return

    # --timeout > 30000
    m = re.search(r"--timeout[=\s]+(\d+)", cmd)
    if m and int(m.group(1)) > 30000:
        allow_msg(
            f"Command has --timeout {m.group(1)}ms (>{30000}ms). "
            "Consider setting run_in_background: true."
        )
        return


# ── guard_glob: from nociceptor-glob.js ────────────────────


def guard_glob(data):
    ti = data.get("tool_input", {})
    pattern = ti.get("pattern", "")
    search_path = ti.get("path", "")

    if "**" in pattern:
        home_paths = [str(HOME), "$HOME"]
        if any(search_path == h or search_path == h + os.sep for h in home_paths):
            deny(f"Glob ** on {HOME} times out. Scope to a subdirectory.", "glob-guard")


# ── guard_grep: from saccade.js ────────────────────────────


def guard_grep(data):
    path = data.get("tool_input", {}).get("path", "")
    if (
        f"{os.sep}notes" in path
        or f"notes{os.sep}" in path
        or f"{os.sep}chromatin" in path
        or f"chromatin{os.sep}" in path
    ):
        allow_msg(
            'Vault search detected. Consider: `ecphory "<query>"` for memory lookups. '
            "Grep is fine for exact strings, wikilinks, or file paths."
        )


# ── guard_write: from nociceptor-write.js ──────────────────


def guard_write(data):
    ti = data.get("tool_input", {})
    fp = ti.get("file_path", "")
    if not fp:
        return

    # Sensitive files
    sens = [
        r"\.secrets$",
        r"\.secrets\.d/",
        r"\.env$",
        r"\.env\.local$",
        r"\.pypirc$",
        r"credentials\.json$",
        r"[/.]keychain\.(json|db|plist)$",
    ]
    if any(re.search(p, fp, re.IGNORECASE) for p in sens):
        deny(f"Write to sensitive file blocked: {fp}. Use Keychain.", "write-guard")

    # .venv in plists
    if fp.endswith(".plist"):
        content = ti.get("content", "") or ti.get("new_string", "")
        if ".venv" in content:
            deny(
                "Never use .venv/bin/python in plists. Use uv run --script --python 3.13.",
                "write-guard",
            )
        if "uv" in content and "--script" in content and "--python" not in content:
            deny(
                "uv run --script in plist without --python falls back to system Python 3.9.",
                "write-guard",
            )

    # Package runner in hooks (obfuscated to not self-trigger)
    if f"{os.sep}.claude{os.sep}hooks{os.sep}" in fp:
        content = ti.get("content", "") or ti.get("new_string", "")
        if re.search(r"\b" + _NPX + r"\b", content):
            deny(f"Never use {_NPX} in hooks. Use direct path.", "write-guard")

    # No prompt-type hooks on PreToolUse — LLM self-judging its own calls is broken
    if fp.endswith("settings.json") and f"{os.sep}.claude{os.sep}" in fp:
        content = ti.get("content", "") or ti.get("new_string", "")
        if '"type": "prompt"' in content and "PreToolUse" in content:
            deny(
                "Prompt-type hooks on PreToolUse are self-policing (fox guards henhouse). "
                "Use deterministic command hooks in axon.py instead.",
                "write-guard",
            )

    # Facts in CLAUDE.md
    is_main = fp in (str(HOME / "CLAUDE.md"), str(_VIVESCA_ROOT / "claude" / "CLAUDE.md"))
    if is_main:
        nc = ti.get("new_string", "") or ti.get("content", "")
        fact_pats = [
            (r"20\d\d-\d{2}-\d{2}", "ISO date"),
            (
                r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d\d\b",
                "calendar date",
            ),
            (r"HK\$\d+", "HK dollar amount"),
        ]
        hits = [label for pat, label in fact_pats if re.search(pat, nc, re.IGNORECASE)]
        if hits:
            deny(
                f"CLAUDE.md must not contain time-sensitive facts ({', '.join(hits)}). Use vault pointer.",
                "write-guard",
            )

    # Checked items in Praxis.md
    if fp.endswith(f"{os.sep}chromatin{os.sep}Praxis.md"):
        content = ti.get("content", "") or ti.get("new_string", "")
        if re.search(r"^- \[x\]", content, re.MULTILINE):
            deny(
                "Edit contains checked items. REMOVE from Praxis.md and APPEND to ~/epigenome/chromatin/Praxis Archive.md.",
                "write-guard",
            )

    # Effector naming gate: new files in effectors/ must be cell biology names
    effectors_dir = str(HOME / "germline" / "effectors") + os.sep
    if fp.startswith(effectors_dir) and os.sep not in fp[len(effectors_dir) :]:
        name = fp[len(effectors_dir) :].rstrip(os.sep)
        if name and not name.startswith("."):
            whitelist_path = _VIVESCA_ROOT / "germline" / "effector-names.txt"
            if whitelist_path.exists():
                approved = {
                    n.strip()
                    for n in whitelist_path.read_text().splitlines()
                    if n.strip() and not n.startswith("#")
                }
                if name not in approved:
                    deny(
                        f"New effector '{name}' not in approved names (effector-names.txt). "
                        f"All effector names must be cell biology. Add to whitelist after naming review.",
                        "write-guard",
                    )

    # Past daily notes immutable
    tool_name = data.get("tool", "")
    if tool_name in ("Write", "Edit", "MultiEdit"):
        m = re.search(
            re.escape(os.sep).join(["", "chromatin", "Daily", r"(\d{4}-\d{2}-\d{2})\.md$"]), fp
        )
        if m:
            note_date = m.group(1)
            from datetime import timezone

            today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
            if note_date != today:
                deny(
                    f"Past daily note {note_date} is immutable. Only today ({today}) can be edited.",
                    "write-guard",
                )

    # Garden-post engagement fingerprint scan
    # Per feedback_garden_sensitivity_scan.md (slot 23 activation gap, 2026-05-04).
    # Mark-based enforcement failed twice; deterministic gate.
    # Skip _parked-* files (sanitisation gate explicit in frontmatter).
    if "/chromatin/secretome/" in fp and fp.endswith(".md"):
        filename = fp.rsplit("/", 1)[-1]
        if not filename.startswith("_"):
            content = ti.get("content", "") or ti.get("new_string", "")
            fingerprints = [
                "Capco",
                "HSBC",
                "MRM ",
                "Doug Robertson",
                "David Rice",
                "Beth Aleksander",
                "Simon Eltringham",
                "Julian Phillips",
                "Tobin",
                "Bing Zhu",
                "Eunomia",
                "Hermes Agent",
                "AIRCo",
                "Daniel Bradberry",
                "Matt Cuffe",
                "Oxana",
                "SS1/23",
                "Dynamo AI",
                "Arize",
                "AIMS",
                "QMIO",
                "Capability inheritance",
            ]
            matched = [s for s in fingerprints if s in content]
            if matched:
                deny(
                    f"Garden draft fingerprint match: {matched}. "
                    f"File as `_parked-*.md` for sanitisation, or remove "
                    f"matched strings. Per feedback_garden_sensitivity_scan.md.",
                    "write-guard",
                )


# ── guard_read: from nociceptor-read.js ────────────────────


def guard_read(data):
    fp = data.get("tool_input", {}).get("file_path", "")
    if not fp:
        return

    sens = [
        r"\.secrets$",
        r"\.secrets\.d/",
        r"\.env$",
        r"\.env\.local$",
        r"\.pypirc$",
        r"credentials\.json$",
    ]
    if any(re.search(p, fp) for p in sens):
        deny(f"Read of sensitive file blocked: {fp}. Use Keychain.", "read-guard")

    locks = [
        r"package-lock\.json$",
        r"pnpm-lock\.yaml$",
        r"yarn\.lock$",
        r"Cargo\.lock$",
        r"poetry\.lock$",
        r"Gemfile\.lock$",
        r"composer\.lock$",
    ]
    if any(re.search(p, fp) for p in locks):
        deny("Reading lockfiles wastes context. Use grep for specific versions.", "read-guard")

    bins = [
        r"\.min\.js$",
        r"\.min\.css$",
        r"\.sqlite$",
        r"\.db$",
        r"\.zip$",
        r"\.tar(\.gz)?$",
        r"\.gz$",
        r"\.dmg$",
        r"\.wasm$",
    ]
    if any(re.search(p, fp) for p in bins):
        deny("Reading binary/minified files wastes context.", "read-guard")

    # Large file without offset/limit — nudge toward targeted reads
    if not data.get("tool_input", {}).get("offset") and not data.get("tool_input", {}).get(
        "limit"
    ):
        try:
            lines = Path(fp).expanduser().read_text().count("\n")
            if lines > 500:
                allow_msg(
                    f"LARGE FILE: {fp} is {lines} lines. Use offset/limit to read specific sections. "
                    f'Or: mtor scout "explain the structure of {Path(fp).name}"'
                )
        except OSError:
            pass

    # uv.lock — same as other lockfiles
    if fp.endswith("uv.lock"):
        deny("Reading lockfiles wastes context. Use grep for specific versions.", "read-guard")


def guard_webfetch(_data):
    """Route WebFetch → pinocytosis CLI (direct, no MCP overhead)."""
    allow_msg(
        "FETCH: Use Bash(command='pinocytosis \"<url>\" --json') instead of WebFetch. "
        "Parallel extraction (defuddle+jina+microlink) with fallback chain."
    )


# ── guard_agent: from nociceptor-agent.js ──────────────────


def guard_agent(data):
    ti = data.get("tool_input", {})
    subtype = ti.get("subagent_type", "")
    model = ti.get("model", "")
    bg = ti.get("run_in_background", False)

    # Explore subagents burn Opus tokens on search/read work.
    # mtor scout (codebase analysis) and mtor research (external search) use free GLM.
    if subtype == "Explore":
        deny(
            "Explore subagents waste Opus tokens on search/read. "
            'Use: mtor scout "prompt" (codebase analysis, free GLM), '
            'mtor research "prompt" (external search, free GLM), '
            "or CC-direct Grep/Glob for <3 calls.",
            "metabolic-gate",
        )

    # Foreground block: buds run in background by default.
    # Foreground blocks conversation flow — the nucleus waits.
    if not bg:
        deny(
            "Foreground Agent blocked. Set run_in_background=true — "
            "buds run in background, the nucleus doesn't wait.",
            "metabolic-gate",
        )

    if subtype in ("general-purpose", "Explore") and model not in ("haiku", ""):
        deny(
            f"Agent('{subtype}') must use model: \"haiku\" to save Opus tokens.",
            "metabolic-gate",
        )

    # Block general-purpose agents for exploration — route to mtor (free GLM-5.1).
    # CC judges; ribosome explores. Only judgment work (review, assess quality) stays on CC.
    prompt = ti.get("prompt", "").lower()

    judgment_indicators = any(
        kw in prompt
        for kw in [
            "review",
            "assess",
            "evaluate quality",
            "check correctness",
            "security audit",
            "code quality",
            "judge",
            "verdict",
        ]
    )
    exploration_indicators = any(
        kw in prompt
        for kw in [
            "find",
            "search",
            "locate",
            "scan",
            "where is",
            "look for",
            "investigate",
            "explore",
            "what does",
            "how does",
            "understand",
        ]
    )
    research_indicators = any(
        kw in prompt
        for kw in [
            "research",
            "compare",
            "latest",
            "how do others",
            "pricing",
            "benchmark",
            "landscape",
        ]
    )

    if subtype in ("general-purpose", "") and not judgment_indicators:
        if research_indicators:
            deny(
                'Research via Agent burns Opus tokens. Use: mtor research "prompt" (free GLM).',
                "metabolic-gate",
            )
        elif exploration_indicators:
            deny(
                'Exploration via Agent burns Opus tokens. Use: mtor scout "prompt" (free GLM), '
                "or CC-direct Grep/Glob for ≤3 calls.",
                "metabolic-gate",
            )

    # Genome inheritance: inject Core Rules into every bud's prompt
    genome = _load_genome()
    if not genome:
        return

    existing_prompt = ti.get("prompt", "") or ""
    genome_prefix = (
        "You are a bud of the vivesca organism. "
        "Inherit and follow these constitutional rules:\n\n"
        f"{genome}\n\n"
        "---\n\n"
    )
    # Only inject if genome is not already present (idempotent)
    if genome_prefix not in existing_prompt:
        updated_ti = dict(ti)
        updated_ti["prompt"] = genome_prefix + existing_prompt
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "updatedInput": updated_ti,
                    }
                }
            )
        )
        sys.exit(0)


# ── guard_efferent: from efferent-redirect.js ──────────────


def guard_efferent(data):
    """CC designs, droid implements. Block implementation code edits."""
    ti = data.get("tool_input", {})
    fp = ti.get("file_path", "")

    # Only gate implementation paths
    impl_dirs = [str(HOME / "code") + os.sep, str(HOME / "germline") + os.sep]
    if not any(fp.startswith(d) for d in impl_dirs):
        return

    # Judgment files: CC writes these directly
    if re.search(r"\.(md|toml|lock|gitignore|txt|json|yaml|yml|plist)$", fp):
        return
    # Skills, memory, genome — always CC territory
    if (
        f"{os.sep}receptors{os.sep}" in fp
        or f"{os.sep}marks{os.sep}" in fp
        or f"{os.sep}epigenome{os.sep}" in fp
    ):
        return

    # Implementation code (.py, .sh, .rs, etc.) — delegate to droid
    deny(
        "CC must not write implementation code. Delegate: "
        "`sortase exec <plan> -p <dir> -b droid`. "
        "Write a spec file instead, then dispatch.",
        "delegate-gate",
    )


# ── guard_bifurcation: from bifurcation.js ─────────────────

BIFURC_STATE = Path("/tmp/delegate-history.json")
BIFURC_DELEGATE_RE = re.compile(r"\b(gemini|codex exec|opencode run)\b", re.IGNORECASE)


def guard_bifurcation(data):
    cmd = data.get("tool_input", {}).get("command", "")
    if not BIFURC_DELEGATE_RE.search(cmd):
        return

    tool_match = BIFURC_DELEGATE_RE.search(cmd)
    if not tool_match:
        return
    tool = tool_match.group(1).lower().replace(" exec", "")
    cd_match = re.search(r"cd\s+([^\s&;]+)", cmd)
    project = cd_match.group(1).replace("~", str(HOME)) if cd_match else "unknown"

    state = {"launches": []}
    with contextlib.suppress(Exception):
        state = json.loads(BIFURC_STATE.read_text())

    now = time.time() * 1000
    state["launches"] = [
        launch
        for launch in state.get("launches", [])
        if now - launch.get("ts", 0) < 30 * 60 * 1000
    ]

    same = [
        launch
        for launch in state["launches"]
        if launch.get("project") == project and now - launch.get("ts", 0) < 10 * 60 * 1000
    ]
    if same and "." not in project:
        print("[parallel-nudge] Sequential delegate to same project. Consider git worktrees.")

    recent_tools = [launch.get("tool") for launch in state["launches"][-2:]]
    if len(recent_tools) >= 2 and all(t == tool for t in recent_tools):
        print(f"[parallel-nudge] 3rd consecutive {tool} delegate. Route by signal.")

    state["launches"].append({"tool": tool, "project": project, "ts": now})
    with contextlib.suppress(Exception):
        BIFURC_STATE.write_text(json.dumps(state, indent=2))


RECEPTORS_DIR = HOME / "germline" / "membrane" / "receptors"
EPISTEMICS_DIR = HOME / "epigenome" / "chromatin" / "euchromatin" / "epistemics"


def surface_epistemics(data):
    """When a skill is invoked, surface matching epistemics heuristics.

    Reads the skill's SKILL.md for `epistemics:` frontmatter tags,
    greps the epistemics library for matching `situations:` tags,
    and prints the top 3 file titles as advisory context.
    """
    skill_name = data.get("tool_input", {}).get("skill", "")
    if not skill_name:
        return

    # Find skill directory
    skill_dir = RECEPTORS_DIR / skill_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return

    # Extract epistemics tags from frontmatter
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return
    if not content.startswith("---"):
        return
    end = content.find("---", 3)
    if end == -1:
        return
    frontmatter = content[3:end]

    tags_match = re.search(r"^epistemics:\s*\[(.+)\]", frontmatter, re.MULTILINE)
    if not tags_match:
        return
    tags = [tag.strip() for tag in tags_match.group(1).split(",")]
    if not tags:
        return

    # Find matching epistemics files
    if not EPISTEMICS_DIR.exists():
        return

    matches = []
    for ep_file in sorted(EPISTEMICS_DIR.iterdir()):
        if ep_file.suffix != ".md":
            continue
        try:
            first_lines = ep_file.read_text(encoding="utf-8")[:500]
        except Exception:
            continue
        for tag in tags:
            if "situations:" in first_lines and tag in first_lines:
                # Extract title from first heading
                for file_line in first_lines.split("\n"):
                    if file_line.startswith("# "):
                        matches.append(file_line[2:].strip())
                        break
                break

    if not matches:
        return

    # Advisory output — top 3
    top = matches[:3]
    remaining = len(matches) - 3
    hint = f"[epistemics:{','.join(tags)}] {' | '.join(top)}"
    if remaining > 0:
        hint += f" (+{remaining} more)"
    print(hint, file=sys.stderr)


# ── main ───────────────────────────────────────────────────


# File-based state for pipeline bypass detection
_IMPL_READ_COUNT_FILE = Path("/tmp/.cc-impl-read-count")


def guard_pipeline_bypass(data):
    """Nudge when CC reads multiple implementation files without invoking mitogen.

    Tracks reads of implementation files (.py, .rs, .ts, .sh) in germline/code.
    Resets when mitogen skill is invoked.
    """
    ti = data.get("tool_input", {})
    fp = ti.get("file_path", "") or ""

    impl_dirs = [str(HOME / "code") + os.sep, str(HOME / "germline") + os.sep]
    if not any(fp.startswith(d) for d in impl_dirs):
        return

    # Only count implementation file reads, not markdown/config
    if re.search(r"\.(md|toml|lock|gitignore|txt|json|yaml|yml|plist)$", fp):
        return

    # Increment counter
    count = 0
    with contextlib.suppress(OSError, ValueError):
        count = int(_IMPL_READ_COUNT_FILE.read_text().strip())
    count += 1
    with contextlib.suppress(OSError):
        _IMPL_READ_COUNT_FILE.write_text(str(count))

    if count >= 3:
        allow_msg(
            "PIPELINE BYPASS: You've read 3+ implementation files without invoking "
            "/mitogen. Are you building? Route through the dispatch pipeline."
        )


def reset_pipeline_counter(data):
    """Reset impl read counter when mitogen skill is invoked."""
    skill_name = data.get("tool_input", {}).get("skill", "")
    if skill_name == "mitogen":
        with contextlib.suppress(OSError):
            _IMPL_READ_COUNT_FILE.write_text("0")


def guard_rheotaxis(_data):
    """Nudge or block: use rheotaxis instead of bare WebSearch.

    If rheotaxis backends are healthy → nudge (allow with advisory).
    If rheotaxis is degraded → block WebSearch too (no silent fallback).
    """
    health_file = HOME / ".cache" / "vivesca" / "rheotaxis-health"
    if health_file.exists():
        status = health_file.read_text().strip()
        if status.startswith("degraded"):
            deny(
                f"SEARCH BLOCKED: rheotaxis is {status}. "
                "WebSearch fallback is also blocked — fix the search backends first. "
                "Check API keys: EXA, TAVILY, SERPER, JINA, FIRECRAWL, GROK.",
                "search-degraded",
            )
            return
    allow_msg(
        "RHEOTAXIS: You have a /rheotaxis skill for multi-backend search. "
        "Invoke it instead of bare WebSearch — it frames multiple queries "
        "across Perplexity, Exa, Tavily, Serper and cross-checks results."
    )


def guard_rheotaxis_depth(data):
    """Deny depth=deep on rheotaxis search. ~$0.40 per call vs $0.006 for quick."""
    ti = data.get("tool_input", {})
    depth = ti.get("depth", "quick")
    if depth == "deep":
        deny(
            "rheotaxis depth=deep costs ~$0.40. Use depth=quick ($0.006) or "
            "depth=thorough ($0.01). If deep is truly needed, ask the user.",
            "metabolic-gate",
        )


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool = data.get("tool", "")

    try:
        if tool == "Bash":
            guard_bash(data)
            guard_long_running(data)
            guard_bifurcation(data)
        elif tool == "Glob":
            guard_glob(data)
        elif tool == "Grep":
            guard_grep(data)
        elif tool in ("Write", "Edit", "MultiEdit"):
            guard_write(data)
            guard_efferent(data)
        elif tool == "Read":
            guard_read(data)
            guard_pipeline_bypass(data)
        elif tool == "Agent":
            guard_agent(data)
        elif tool == "Skill":
            surface_epistemics(data)
            reset_pipeline_counter(data)
        elif tool == "WebSearch":
            guard_rheotaxis(data)
        elif tool == "WebFetch":
            guard_webfetch(data)
        elif "rheotaxis" in tool:
            guard_rheotaxis_depth(data)
    except SystemExit:
        raise
    except Exception:
        pass


if __name__ == "__main__":
    main()
