---
name: opencode-delegate
description: Delegate coding tasks to OpenCode (GLM-4.7) for background execution on cheaper model.
user_invocable: false
---

# OpenCode Delegate

Delegate coding tasks to OpenCode (Gemini/GLM-powered) for background execution.

## When to Use

- **Cost optimization**: Gemini is ~6x cheaper than Opus
- **Parallel work**: Run tasks in background while continuing conversation
- **Well-defined tasks**: Refactoring phases, code extraction, file reorganization
- **Self-recoverable errors**: Tasks where OpenCode can debug its own mistakes

## When NOT to Use

- Tasks requiring user decisions mid-execution
- Errors needing external context (API keys, environment issues)
- Exploratory work where direction is unclear
- Tasks with heavy dependencies on conversation context

## Commands

### Run headless task (default: GLM-4.7 — unlimited quota)
```bash
# Use lean config (no MCPs) for fast ~15s startup
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-4.7 --title "Task Name" "Detailed prompt" &
```

> **⚠️ Provider Matters:** Use `zhipuai-coding-plan/glm-4.7` (BigModel direct) NOT `opencode/glm-4.7` (OpenCode proxy with separate billing).

> **⚠️ Use Lean Config:** `OPENCODE_HOME=~/.opencode-lean` skips MCP servers (gmail, search, browser, etc.) — cuts startup from ~60s to ~15s. Coding tasks don't need MCPs.

**Best practice**: Always append `&` when running from Claude Code. This backgrounds the task so you can continue working or dispatch more tasks in parallel.

### Run with Gemini 3 Flash (fallback for speed)
```bash
OPENCODE_HOME=~/.opencode-lean opencode run -m opencode/gemini-3-flash --variant high --title "Task Name" "Detailed prompt"
```

### Resume a session
```bash
opencode -s <session-id>
# Or continue last session:
opencode -c
```

> **Note:** Resume uses full `opencode` (not lean) since sessions may need MCP access.

### Terminal alias
For quick interactive use from terminal: `ol` (defined in .zshrc) is equivalent to lean config.

### Find session IDs
```bash
/bin/ls -lt ~/.local/share/opencode/storage/session/
# Then read the session JSON:
cat ~/.local/share/opencode/storage/session/<project-hash>/*.json
```

## PII Masking

When delegating prompts that contain personal information, mask first:

```bash
# Mask sensitive info before delegation
cd /Users/terry/skills/pii-mask
masked=$(uv run mask.py "Prompt with terry@email.com and 6187 2354")

# Then delegate the masked version
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-4.7 --title "Task" "$masked"
```

**Preview what gets masked:**
```bash
uv run mask.py --dry-run "Contact Terry at +852 6187 2354"
```

See `/Users/terry/skills/pii-mask/SKILL.md` for details on what gets detected.

## Prompt Engineering for Delegation

Good delegation prompts include:

1. **Clear scope**: "Execute Phase 2 from docs/plans/X.md"
2. **Specific deliverables**: "Create these files: A, B, C"
3. **Verification command**: "Verify by running: python -c '...'"
4. **Constraints**: "Keep existing patterns", "Don't modify X"

### Example Prompt
```
Execute Phase 2 from docs/plans/refactor-plan.md.

Your task: Extract routes into backend/routes/*.py

Create these files:
1. backend/routes/__init__.py - router exports
2. backend/routes/documents.py - /upload, /documents endpoints
3. backend/routes/system.py - /healthz, /stats endpoints

Then update main.py to import and include the routers.

Verify by running: python -c 'from backend.routes import documents_router'
```

## Session Storage

Sessions are persisted at:
```
~/.local/share/opencode/storage/session/
├── <project-hash>/
│   └── ses_<id>.json  # Contains title, summary, timestamps
└── global/
```

Session JSON includes:
- `id`: Session ID for resume
- `title`: Task name
- `summary`: {additions, deletions, files}
- `time`: {created, updated}

## Model Selection

Use `-m <model>` and optionally `--variant <level>`.

| Model | Use Case |
|-------|----------|
| `zhipuai-coding-plan/glm-4.7` ⭐ | **Default** — unlimited via BigModel Coding Max (valid to 2027-01-28) |
| `opencode/gemini-3-flash` | Speed-critical — 3x faster, higher hallucination rate |
| `opencode/gemini-3-pro` | More capable, slower |
| `opencode/claude-sonnet-4-5` | When you need Claude quality |
| `opencode/glm-4.7` | ❌ Avoid — separate OpenCode billing |

> **⚠️ MUST use `zhipuai-coding-plan/` prefix** for GLM-4.7 — `opencode/glm-4.7` depletes.

Variant levels: `--variant high` (recommended) | `max` (slower) | `minimal` (fastest)

## Monitoring Background Tasks

When launched via Claude Code's Bash with `run_in_background`:
```bash
# Check progress
tail -f /private/tmp/claude-501/-Users-terry/tasks/<task-id>.output

# Or use TaskOutput tool with the task ID
```

**⚠️ Output files are often empty** — OpenCode doesn't reliably capture stdout to the task output file. If the file is empty, check the session JSON instead:
```bash
# Find recent sessions for the project
/bin/ls -lt ~/.local/share/opencode/storage/session/<project-hash>/

# Read session summary (shows additions, deletions, files changed)
cat ~/.local/share/opencode/storage/session/<project-hash>/ses_<id>.json
```

The session JSON's `summary` field tells you if OpenCode actually made changes, even when output is empty.

## Error Handling

OpenCode often self-recovers from errors by:
1. Reading error output
2. Editing the problematic code
3. Retrying

If it fails repeatedly on the same error, take over interactively.

## CE Integration

See `delegation-reference` skill for the full Claude-plans/OpenCode-executes workflow. Key pattern:

```bash
# Execute plan phases (sequential or parallel)
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-4.7 \
  --title "Phase 1" "Execute Phase 1 from docs/plans/YYYY-MM-DD-plan.md." &
```

**Plans are prompts** — include exact file paths, code snippets, verification commands, and constraints.
