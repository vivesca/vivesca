---
name: custodia
description: Reference for persistence layer decisions. Use when deciding where to save an insight or how many storage layers to use. "where should this go", "persistence"
disable-model-invocation: true
tags: [meta, reference]
---

# Custodia — Persistence Heuristics

> *Custodia: Latin "guardianship" — deciding what's worth keeping and where.*

Reference skill. Consult when deciding how to persist an insight, correction, or finding.

**Garden post:** [[Systematise Decisions, Not Actions]]

## Rules

1. **One home per insight.** Pick the place closest to where it's needed. Second layer only if genuinely different audience or trigger.
2. **Retrieval test beats capture test.** "How will I find this?" not "where should this go?" Good filename > metadata.
3. **Never point to a pointer.** If layer A says "see layer B" which says "see layer C" — collapse the chain. Put content where it fires.

## Distinctions

4. **Content for Claude (memory file) vs content for Terry (vault note) vs content for understanding (garden post).** These are different audiences. Don't duplicate across them unless justified.
5. **Time-bound triggers work. Behavioral triggers don't.** "Check in October" = reliable. "When feeling doubt, remember Y" = too fuzzy to match. Convert behavioral triggers to scheduled reviews.
6. **Writing > filing.** A garden post forces understanding. A memory file just stores. When choosing one, write.
7. **Reference skill > memory file** when: content has >5 items, needs to fire at a specific decision point, and would benefit from always-loaded access. Memory files sit hoping to be found. Skills load when consulted.

## Anti-patterns

8. **Systemising in the afterglow.** Capture impulse peaks when the insight feels most important. Save content now, sleep on architecture.
9. **Maintenance cost denial.** Every layer has review cost. The stack must earn its maintenance budget.
10. **Filing as substitute for acting.** Did you change a behaviour, or file a note about changing one?

## Scaling

11. **Persistence depth scales with reuse frequency:** daily → skill (always loaded). Weekly → MEMORY.md (loaded per session). Monthly → vault note (searchable). Once → daily log (append-only).
12. **The stack should shrink over time.** Growing = hoarding. Maturity = culling confidently.

## The Gate

Before persisting anything, answer:
1. How many layers am I creating for this insight? (If >1, justify each)
2. Is any layer just pointing to another layer? (If yes, collapse)
3. Will I actually find this when I need it? (If not, move it closer to the decision point)
