# PostToolUse Blocking Validators

Pattern from disler/claude-code-hooks-mastery.

## Current State

Our PostToolUse hooks are **formatters** (prettier, ruff, tsc). They fix output but never reject it.

## The Pattern

PostToolUse hooks can also **validate** tool output and return errors that block the action. Examples:

- After a file edit: run linter, reject if new errors introduced
- After a bash command: check exit code patterns, flag if destructive output detected
- After a write: validate against schema or naming conventions

The hook returns a non-zero exit code with an error message, which Claude sees as tool failure.

## When to Adopt

Wait for the pain. Adopt when:
- Same class of bad edit keeps recurring (e.g., introducing type errors)
- A PostToolUse check would catch it faster than review agents

Don't add preemptively — each hook fires on every tool call and adds latency.

## Implementation

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "command": "node ~/scripts/hooks/validate-edit.js"
      }
    ]
  }
}
```

The validator script receives the tool result via stdin and exits non-zero to block.
