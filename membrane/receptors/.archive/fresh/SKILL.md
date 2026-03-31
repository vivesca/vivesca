---
name: fresh
description: Re-sync with external state before resuming work. Grounds AI in reality, not stale memory.
user_invocable: true
---

# Fresh — Ground in Reality

Re-sync with external state before resuming work. Prevents the AI from reasoning based on stale chat memory.

## When to Use

- Resuming after a break
- Switching between different tasks/domains
- After `/clear` to rebuild context
- Whenever things feel "off" or confused
- Starting a session after being away

## Instructions

Run these checks and present a concise status summary:

### 1. Current Task (always)

```bash
cat ~/epigenome/chromatin/WORKING.md 2>/dev/null || echo "No WORKING.md found"
```

### 2. Pending Items (always)

```bash
cat ~/epigenome/chromatin/Praxis.md 2>/dev/null | head -30
```

### 3. Git Status (if in a git repo)

```bash
if git rev-parse --git-dir > /dev/null 2>&1; then
  echo "=== Git Status ==="
  git status --short
  echo ""
  echo "=== Recent Changes ==="
  git diff --stat HEAD~3..HEAD 2>/dev/null || git diff --stat
fi
```

### 4. Job Hunting Context (if relevant)

If the conversation involves job hunting, also glance at:
```bash
head -50 "~/epigenome/chromatin/Active Pipeline.md"
```

## Output Format

Present a brief, scannable summary:

```
## Current State

**Working on:** [from WORKING.md or "nothing tracked"]

**Pending:** [top 3-5 items from Praxis.md]

**Git:** [clean / X files modified / not a repo]

**Ready to:** [infer next action from context]
```

Keep it tight. The goal is grounding, not a full report.

## Future: Auto-Hook (Optional)

If manual /fresh proves valuable and you want it automatic, add to `~/.claude/hooks.json`:

```json
{
  "hooks": {
    "session-start": {
      "command": "claude --skill fresh --quiet"
    }
  }
}
```

Only add this after validating the habit manually.
