# Hook Pattern: Auto-Commit on Write

## Problem
Agent writes to config repos (agent-config, skills) don't get committed atomically — changes accumulate until wrap or manual action.

## Solution
`PostToolUse` hook on `Write`/`Edit` → git add + commit for targeted repos.

## Implementation
- `~/.claude/hooks/repo-autocommit.py` — handles `~/agent-config/` (commit + push)
- `~/.claude/hooks/skill-autocommit.py` — handles `~/skills/` (commit only, synaxis pushes)
- Matcher in settings.json: `(tool == 'Edit' || tool == 'Write') && tool_input.file_path matches '/agent-config/'`

## Key Design Decisions
- **Per-write commits are right for config repos** — changes are always self-contained
- **Per-write commits are wrong for vault/code repos** — breaks logical-unit commit principle, creates noise
- **`git add -A` is acceptable for agent-config** — no partial/multi-file edits in practice
- **Vault (~/notes)**: excluded from auto-commit. `dirty-repos.js` Stop hook warns at session end instead.

## Vault Sync Separate Problem
Cron backup pushes to remote overnight → pull conflict on session start.
Fix: `vault-pull.py` UserPromptSubmit hook pulls on first prompt with `-X ours`.
See: `~/.claude/hooks/vault-pull.py`
