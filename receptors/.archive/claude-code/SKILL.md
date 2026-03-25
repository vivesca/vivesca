---
name: claude-code
description: "Run Claude Code with model selection. Use from OpenClaw or when specifying opus/sonnet/haiku."
user_invocable: true
---

# Claude Code Delegation

Run a task in Claude Code with explicit model selection. Primarily useful from OpenClaw or other tools that need to invoke Claude Code as a subprocess.

## Usage

```
/claude-code <model> <task>
```

Where `<model>` is one of:
- **opus** — Deep reasoning, judgment, architecture (default)
- **sonnet** — Analysis, code review, multi-step research
- **haiku** — Quick lookups, file searches, simple summarisation

If no model specified, defaults to opus.

## Examples

```
/claude-code haiku check if oura daemon is running
/claude-code sonnet review the PR at #123 for security issues
/claude-code opus design the authentication architecture for reg-atlas
/claude-code update WORKING.md with current task status
```

## Implementation

Parse the first argument. If it matches a model name, use it; otherwise treat the entire input as the task and default to opus.

```bash
MODEL="opus"
TASK="$*"

case "$1" in
  opus|sonnet|haiku)
    MODEL="$1"
    shift
    TASK="$*"
    ;;
esac

claude --model "claude-$MODEL" --dangerously-skip-permissions -p "$TASK"
```

## Model Routing Guide

| Task Type | Model | Cost | Examples |
|-----------|-------|------|---------|
| Quick lookup | haiku | Lowest | File search, simple grep, status check |
| Analysis | sonnet | Medium | Code review, research, summarisation |
| Deep reasoning | opus | Highest | Architecture, judgment calls, complex debugging |

**Rule of thumb:** Start with haiku. If the task needs multi-step reasoning, use sonnet. Reserve opus for tasks where being wrong is expensive.
