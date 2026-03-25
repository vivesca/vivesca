# Abandoned Approaches — Search Guide

Negative knowledge: things we tried and deliberately dropped. Prevents re-litigating settled decisions.

## How to find

Daily notes use a consistent `**Abandoned:**` marker. Search with:

```bash
grep -r "Abandoned:" ~/epigenome/chromatin/Daily/ | head -20
```

Or via Grep tool: pattern `Abandoned:`, path `/Users/terry/epigenome/chromatin/Daily`.

## Convention

When abandoning an approach, always log in the daily note as:

```
**Abandoned:** X because Y
```

Include the *why* — that's the negative knowledge. "Abandoned CrewAI rebuild — framework overhead, no value add" is searchable and prevents re-proposing.

## When to check

Before starting work on something that feels familiar, grep for `Abandoned:` + keywords. If a prior session already tried and dropped it, read the rationale before re-attempting.
