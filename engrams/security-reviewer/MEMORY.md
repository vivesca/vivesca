# Security Reviewer Memory

## Terry's Codebase — Key Patterns

### Architecture
- Hooks in `~/.claude/hooks/` are PreToolUse/PostToolUse/Stop/UserPromptSubmit lifecycle hooks for Claude Code.
- Hook deny mechanism: `permissionDecision: "deny"` via JSON to stdout + `process.exit(0)`. Exit 2 = crash.
- `~/officina/` is a git repo with auto-push. Anything committed here goes to GitHub.
- `~/skills/` is a separate git repo (also auto-committed by skill-autocommit.py hook).
- LaunchAgents in `~/officina/launchd/` run automation as the user. All plists use absolute paths (good).
- 1Password service account token injects API keys via `~/.zshenv.tpl`. This is the intended pattern.
- `~/officina/bin/keychain-env` maps 20+ env vars to Keychain service names — reference this before flagging any hardcoded credential; check if the script bypasses this correctly-existing mechanism.

### Known Vulnerabilities (audited 2026-03-05; re-audited 2026-03-20)
- ~~**CRIT**: `~/scripts/tg-notify.sh`, `~/scripts/tg-clip.sh`, `~/scripts/job-heartbeat.py` — hardcoded Telegram bot tokens.~~ **FIXED 2026-03-20** — now use `${TELEGRAM_BOT_TOKEN}` env var injected via 1Password. Commit: `12c92e0`.
- ~~**CRIT**: `~/officina/bin/cg` — hardcoded ZhipuAI API key committed to git repo.~~ **FIXED 2026-03-20** — now uses `${ZHIPU_API_KEY:?}` env var; key rotated; git history scrubbed. Commit: `383bd0c`.
- ~~**CRIT**: `~/.claude/hooks/notification-telegram.sh` — unquoted `$MSG` in `curl -d text=`.~~ **FIXED 2026-03-20** — `$MSG` is double-quoted; curl invocation reviewed and accepted as low-risk for notification payloads.
- **MED**: `~/scripts/imessage.sh` — `$MESSAGE` interpolated into Python source string. Use `sys.argv[1]` instead.
- **MED**: `~/scripts/opencode-queue.py` — executes tasks from `~/epigenome/chromatin/agent-queue.yaml` without validating `backend` or `working_dir`. YAML file is in the Obsidian vault (synced, pull-on-session).
- **LOW**: `~/.claude/hooks/glob-guard.js` — unscoped `**` glob passes through when `path` param is empty.
- **LOW**: `~/officina/bin/cg` — `--dangerously-skip-permissions` bypasses all PreToolUse hooks.
- **LOW**: `~/officina/launchd/com.terry.theoros.plist` — empty ANTHROPIC_API_KEY placeholder; remove it.

### What's Well-Secured
- All `subprocess.run()` calls in Python hooks use list form (no shell=True).
- write-guard and read-guard both block `.secrets`, `.env`, `credentials.json`.
- Most `officina/bin/` tools correctly use `os.environ.get()` or `_keychain()` helpers.
- bash-guard has 22 rules covering exfil, destructive git ops, WhatsApp/email sends, pipe-to-shell.
- Hook fire events are logged to `~/logs/hook-fire-log.jsonl` (append-only).

### Common Vulnerability Patterns in This Codebase
1. **Convenience scripts bypass the keychain architecture** — tg-notify, tg-clip, job-heartbeat were written before keychain-env existed. When reviewing new scripts, check if they hardcode creds that keychain-env already manages.
2. **Shell variable interpolation into Python `-c` strings** — seen in imessage.sh. Pattern: `python3 -c "...${VAR}..."` — always use `sys.argv`.
3. **Unquoted variables in curl `-d`** — seen in notification-telegram.sh. `-d text="$VAR"` does not properly URL-encode; use `--data-urlencode`.
4. **YAML/config files in synced vault as untrusted input to command execution** — agent-queue.yaml is in `~/epigenome/chromatin/` which is Obsidian-synced and git-pulled on every session. Validate fields from this source.

### Framework-Specific Notes
- Claude Code hooks receive tool input as JSON on stdin. Always parse with JSON.parse/json.load — never eval.
- Hook exit codes: 0 = allow (or deny via JSON), 2 = crash the session. Use 0 for graceful deny.
- PostToolUse hooks that do `console.log(input)` pass-through the tool result — important for format hooks.
- `repo-autocommit.py` auto-commits `~/officina/` on every Write/Edit. Credential leaks committed there push automatically.
