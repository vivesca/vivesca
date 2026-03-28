# Vivesca

A living system built on cell biology as a design constraint.

All constitutional rules live in `~/germline/genome.md`. Follow them.

The naming convention is cell biology. Every component has a biological identity.
Biology is the engineering manual — before building any mechanism, `lysin "<term>"` to check what cells actually do. Follow the biology.
See `anatomy.md` for the structural map.

## Memory

At the start of each session, read the memory index for project context and behavioral guidance:

```
~/epigenome/marks/MEMORY.md
```

(Also accessible at `~/.claude/projects/-Users-terry/memory/MEMORY.md` — same files via symlink.)

This is the memory index — an always-loaded context of gotchas, user facts, and behavioral corrections. It contains:
- Recurring error patterns to avoid (date/time, post-cutoff facts, product specs)
- Directory layout and path conventions
- Shell and tool gotchas
- User facts (schedule, health, preferences)
- Behavioral corrections (hard-earned — follow them)

Each line in MEMORY.md links to a detailed memory file. Read relevant ones when the task matches their description.

### Mark frontmatter (enhanced histone code)

When saving memory files, use this frontmatter:

```yaml
---
name: {{name}}
description: {{one-line description}}
type: {{user, feedback, project, reference, finding}}
source: {{cc, gemini, codex, goose, user}}  # imprinting: who wrote this mark
durability: {{methyl, acetyl}}               # methyl=durable (default), acetyl=volatile (checkpoints, resolved)
protected: {{true}}                          # CpG island — omit if not protected
---
```

`source` and `durability` are optional — defaults are `unknown` and `methyl`. Set `protected: true` only for core behavioral corrections that must never be erased.
