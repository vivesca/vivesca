---
name: grapho
description: Manage MEMORY.md — add entries, demote over-budget entries to overflow, promote back, review overflow, scaffold solution files.
triggers: [memory, overflow, demote, promote, gotcha, grapho, budget, solutions]
user_invocable: false
---

# grapho — Memory System CLI

Write-side of the memory system. Pairs with `cerno` (read) — grapho writes, cerno searches.

## Commands

```bash
grapho status                    # line count, budget, section list (exit 1 if over budget)
grapho status --format json      # machine-readable
grapho add                       # interactive: pick section, enter entry (TTY only)
grapho hit "<search>"            # record a hit for a matching MEMORY.md entry (non-interactive)
grapho demote "<search>"         # move entry MEMORY.md → overflow (shows hit count in selection)
grapho promote "<search>"        # move entry overflow → MEMORY.md
grapho review                    # list overflow entries by age, prompt p/k/d per entry
grapho solution <name>           # scaffold ~/docs/solutions/<name>.md (dedup check)
```

## Files

```
MEMORY.md     ~/.claude/projects/-home-terry-germline/memory/MEMORY.md
overflow      ~/docs/solutions/memory-overflow.md
solutions     ~/docs/solutions/
budget        150 lines
```

## When to Use

- **Over budget** (`grapho status` exits 1) → `grapho demote` infrequent entries (hit count shown in selection)
- **Entry just prevented a mistake** → `grapho hit "<search>"` to record it
- **New gotcha to capture** → `grapho add` (TTY) or edit MEMORY.md directly
- **Weekly review** → `grapho review` to triage overflow (promote 2+ repeat hits); `grapho status` shows top hits
- **New solutions doc** → `grapho solution <name>` (checks dedup before creating)

## Hit Counter

`grapho hit` records when an entry actually fires — the empirical answer to "what to demote."

```bash
# After a correction or close call:
grapho hit "anam default"        # found match, incremented to 2
grapho status                    # Top hits section shows frequency ranking
grapho demote "..."              # selection shows [0 hits] / [3 hits] per entry
```

Hit data: `~/.grapho/hits.json`. Key = first 60 chars of entry text (bullet/markdown stripped, lowercased). Resets naturally if entry text is substantially reworded — acceptable, a reworded rule is effectively a new rule.

**Workflow integration:** After any correction noted in daily log, run `grapho hit "<distinctive substring>"`. Low-hit entries are demotion candidates; high-hit entries should stay regardless of age.

## Gotchas

- **Search terms must match entry text exactly (substring).** Use short, unique substrings — `"@import"` not `"@import syntax"`. If too specific, no match.
- **Disambiguation requires TTY.** If >1 match, grapho prompts interactively. Run from a real terminal, not via Bash tool.
- **`add`, `promote`, `review` require TTY.** `status`, `demote`, `solution`, `hit` work piped.
- **Demoting duplicates:** if an entry already exists in overflow, demote adds it again. Check overflow first with `grep` if unsure.
- **CLAUDE.md dedup:** Before adding to MEMORY.md, check if the same rule already exists in CLAUDE.md. CLAUDE.md = rules (loads in full), MEMORY.md = gotchas (200-line limit). If a rule is in both, delete it from MEMORY.md — CLAUDE.md is the canonical source. The nightly `memory-hygiene` legatus job checks for this, but catch it manually too.
- **Empty sections stay.** Demoting all entries from a section leaves the `## Header` in MEMORY.md. Not a bug — add new entries to it later or ignore.

## Budget Workflow

```bash
grapho status          # check current count
# if over budget:
grapho demote "<low-frequency entry>"   # repeat until under 150
grapho status          # confirm exit 0
```

## Reference

- crates.io: `cargo install grapho`
