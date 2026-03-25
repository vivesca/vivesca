---
name: mitosis
description: Monthly review — parallel auditors (financial, health, system, peer) + maintenance, then cross-domain synthesis into prioritized monthly plan. "monthly", "monthly review", "run monthly"
model: opus
disable-model-invocation: true
context: fork
---

# Monthly Review

You are the hypothalamus — integrating signals from multiple body systems into one coordinated response.

## Phase 1: Parallel audit (dispatch all at once)

Launch ALL FOUR agents simultaneously using the Agent tool in a single message. Each runs on sonnet:

1. **hepatocyte** — "Run your full metabolic audit for the month."
2. **osteocyte** — "Run your full structural health and capacity assessment."
3. **microglia** — "Run your full neural maintenance audit."
4. **dendritic-cell** — "Run your full boundary patrol and peer scan."

While agents run, proceed to Phase 2 (maintenance) in parallel.

## Phase 2: Maintenance (inline, while auditors run)

Run these sequentially — they're fast, deterministic, and don't need agents:

### Content & AI digests
```bash
digest --dry-run && digest
~/.local/bin/lustro digest --dry-run && ~/.local/bin/lustro digest
```
If either fails, mark as skipped and continue.

### Source health
```bash
lustro check 2>&1 | grep "<-\|(stale)\|x0)"
```
Fix URL-rotted sources in `~/.config/lustro/sources.yaml`. Remove dead sources.

### Vault hygiene
- `python3 ~/scripts/generate-solutions-index.py` — regenerate solutions KB index
- `uv run ~/scripts/vault-decay-report.py` — orphans/cold notes
- Verify `[[wikilinks]]` in CLAUDE.md still resolve

### Oghma hygiene
```bash
oghma stats
```
Flag sources with >100 entries that aren't `claude_code`/`opencode`/`codex`.

### Housekeeping
- `/usr/bin/find ~/.claude/todos -name "*.json" -mtime +7 -delete`
- Check `wc -l` on MEMORY.md — flag if >150
- CLAUDE.md tightening pass: remove stale, demote mechanical rules to skills

## Phase 3: Cross-domain synthesis (the real output)

Once all four auditor reports are back, synthesize. This is the value — no single auditor can see across domains.

Cross-reference questions:
- **Financial stress + health capacity**: Can Terry sustain current commitments? Defer anything?
- **System gaps + peer patterns**: Are peers solving problems Terry still does manually?
- **Health trends + workload**: Is the capacity score compatible with planned workload?
- **Financial deadlines + career positioning**: Do financial pressures change priorities?

## Phase 4: Monthly priority plan

Write to `~/epigenome/chromatin/Monthly Review - YYYY-MM.md`:

```markdown
## Monthly Review — [Month Year]

### Capacity Assessment
[One paragraph: health + financial = what's realistic this month]

### Top 3 Priorities
1. [What] — [Why it's #1, which domain signals point here]
2. [What] — [Why]
3. [What] — [Why]

### Defer
- [What to explicitly NOT do this month and why]

### Signals to Watch
- [What would change priorities if it shifts]

### Maintenance Summary
| Section | Status | Notes |
|---------|--------|-------|
| Content Digest | ... | ... |
| Source Health | ... | ... |
| Vault Hygiene | ... | ... |
| Oghma | ... | ... |
| Housekeeping | ... | ... |

### Raw Auditor Reports
[Summary of each auditor's key findings]
```

## Phase 5: Update Praxis.md

Add/update items based on priority plan. Remove or defer items the review says to drop.

## Principles

- The synthesis is the product, not the individual reports.
- Priorities should CONFLICT — if everything aligns, you're not looking hard enough.
- "Defer" is as important as "do" — saying no is the real output.
- One review that changes one priority beats four audits confirming status quo.

## See also
- `/ecdysis` — Sunday planning (runs first)
- `/meiosis` — direction, career, investments (quarterly)
