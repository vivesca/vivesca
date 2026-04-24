---
name: sporulation
description: Save session checkpoint with codename for instant resume later. "checkpoint", "save session", "sporulate"
user_invocable: true
context: inline
triggers:
  - sporulation
model: sonnet
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Sporulation — Cross-Session Resume

> A bacterium sporulates when conditions turn hostile: it compresses its essential DNA into a compact, resistant spore. When conditions improve, the spore germinates and resumes full activity. Same thing here — compress live context into a checkpoint, germinate in a fresh session.

## When to sporulate

- MCP session drops mid-conversation
- Switching to a different task but need to come back
- Session is getting long and context is at risk
- User says "warp", "checkpoint", "save where we are"

## Sporulate (save)

1. Run **full cytokinesis inline** first (see pre-sporulation section below)
2. Call `sporulation(action="save")` MCP tool with:
   - `context`: what we were doing (2-3 sentences)
   - `where_we_left_off`: last actions, pending items
   - `action_needed`: numbered steps to resume (include tool names, file paths)
   - `summary`: one-line summary
3. Report the codename to the user

## Germinate (resume)

When a user says an adjective-noun codename (e.g., "happy-cat") in a new session:

1. Search for `~/.claude/projects/-home-terry-germline/memory/checkpoint_<codename>.md`
2. Read it
3. Execute the "Action needed" steps
4. Delete the checkpoint file after successful resume (spore consumed)

**Detection:** If user's message is a short adjective-noun phrase matching `checkpoint_*.md`, treat it as a resume request. Don't ask "what do you mean by happy-cat?" — just load it.

## Cleanup

Checkpoints older than 7 days are stale. On any sporulation, delete checkpoints older than 7 days:

```bash
find ~/.claude/projects/-home-terry-germline/memory/ -name "checkpoint_*.md" -mtime +7 -delete
```

## Pre-sporulation: full cytokinesis

Before saving the spore, run **full cytokinesis** (consolidation + housekeeping + daily note):
1. Scan session for unfiled corrections, findings, user facts — file them
2. Commit dirty repos
3. Update Tonus.md (`~/epigenome/chromatin/Tonus.md` — canonical path)
4. Write daily note arc
5. Then sporulate

If context is dying, everything should be captured — not just the checkpoint. Full cytokinesis is fast when there's nothing to capture (filed=0). Don't optimize for the rare mid-session park case.

## Boundaries

- Not a replacement for Praxis (commitments). If there's a todo, it goes in Praxis, not a checkpoint.
- Checkpoints are ephemeral. They exist to be consumed, not archived.
