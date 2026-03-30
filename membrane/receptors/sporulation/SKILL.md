---
name: sporulation
description: Save session checkpoint with codename for instant resume in a new session.
user_invocable: true
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

### 1. Generate codename

Random `adjective-noun` pair. Must be memorable and distinct from existing checkpoints.

```bash
# Check existing checkpoints to avoid collision
ls ~/.claude/projects/-Users-terry/memory/checkpoint_*.md 2>/dev/null
```

Generate with Python:

```bash
python3 -c "
import random
adj = ['happy', 'calm', 'bold', 'warm', 'keen', 'swift', 'bright', 'quiet', 'wild', 'crisp',
       'pale', 'dark', 'soft', 'sharp', 'cool', 'odd', 'rare', 'slim', 'tall', 'deep',
       'gold', 'iron', 'blue', 'red', 'green', 'silver', 'amber', 'coral', 'jade', 'onyx']
noun = ['cat', 'fox', 'owl', 'elk', 'bee', 'ant', 'bat', 'cod', 'eel', 'yak',
        'oak', 'elm', 'fig', 'ash', 'bay', 'gem', 'orb', 'arc', 'key', 'bell',
        'star', 'moon', 'rain', 'leaf', 'wave', 'fern', 'moss', 'pine', 'crow', 'hawk']
print(f'{random.choice(adj)}-{random.choice(noun)}')
"
```

### 2. Write checkpoint

Write to `~/.claude/projects/-Users-terry/memory/checkpoint_<codename>.md`:

```markdown
---
name: <codename> checkpoint
description: Resume point for <one-line summary> (<date> ~<time> HKT)
type: project
---

## Context
<What we were doing — 2-3 sentences max>

## Where we left off
<Bullet list: last actions taken, last messages exchanged, pending items>

## Action needed
<Numbered list: exact steps to resume, including tool calls if relevant>

## Passcode: <codename>
```

Rules:
- **Compress.** Only what's needed to resume. Not a transcript.
- **Be specific.** Include tool names, file paths, message content — not "we were chatting."
- **Pending items first.** The whole point is unfinished business.

### 3. Report

Tell the user the codename. That's it.

```
Passcode: **<codename>**
```

## Germinate (resume)

When a user says an adjective-noun codename (e.g., "happy-cat") in a new session:

1. Search for `~/.claude/projects/-Users-terry/memory/checkpoint_<codename>.md`
2. Read it
3. Execute the "Action needed" steps
4. Delete the checkpoint file after successful resume (spore consumed)

**Detection:** If user's message is a short adjective-noun phrase matching `checkpoint_*.md`, treat it as a resume request. Don't ask "what do you mean by happy-cat?" — just load it.

## Cleanup

Checkpoints older than 7 days are stale. On any sporulation, delete checkpoints older than 7 days:

```bash
find ~/.claude/projects/-Users-terry/memory/ -name "checkpoint_*.md" -mtime +7 -delete
```

## Pre-sporulation: full cytokinesis

Before saving the spore, run **full cytokinesis** (consolidation + housekeeping + daily note):
1. Scan session for unfiled corrections, findings, user facts — file them
2. Commit dirty repos
3. Update Tonus.md
4. Write daily note arc
5. Then sporulate

If context is dying, everything should be captured — not just the checkpoint. Full cytokinesis is fast when there's nothing to capture (filed=0). Don't optimize for the rare mid-session park case.

## Boundaries

- Not a replacement for Praxis (commitments). If there's a todo, it goes in Praxis, not a checkpoint.
- Checkpoints are ephemeral. They exist to be consumed, not archived.
