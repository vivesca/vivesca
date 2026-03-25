---
name: vault-pathfinding
description: Reference for Obsidian vault paths and linking conventions. Consult when reading/writing vault notes.
user_invocable: false
---

# Vault Pathfinding

Standard paths and conventions for Terry's Obsidian vault at `~/notes/`.

## Core Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `CLAUDE.md` | Personal context about Terry | Always at session start |
| `Active Pipeline.md` | Live job pipeline (offers, interviews) | Job evaluation, morning briefing |
| `Job Hunting.md` | Archive (CV, comp, market signals, passed roles) | Job evaluation, pattern recognition |
| `Job Hunting - Passed Roles.md` | 90+ passed roles with reasons | Duplicate check, anti-signal detection |
| `Job Hunting - Applied Archive.md` | Full application history | Duplicate check |

## Job-Related Note Conventions

| Note Type | Filename Pattern | Example |
|-----------|------------------|---------|
| Role evaluation | `Role Title - Company.md` | `Senior Data Scientist - Fano Labs.md` |
| Company research | `Company Name.md` | `Capco.md` |
| Interviewer profile | `Person Name.md` or link in daily | `[[Tobin - HSBC]]` |
| Daily note | `YYYY-MM-DD.md` | `2026-01-31.md` |

## Wikilink Conventions

```markdown
[[Role Title - Company]]           # Job evaluation note
[[Job Hunting]]                    # Main tracking file
[[Active Pipeline]]                # Live pipeline
[[Core Story Bank]]                # Interview stories
[[Interview Preparation]]          # Prep materials
```

## Reading Patterns

### Before Job Evaluation
```
1. Read Job Hunting - Passed Roles.md (check duplicates)
2. Read Job Hunting.md → Anti-Signals section
3. Read Active Pipeline.md (pipeline health)
```

### Before Interview Prep
```
1. Read CLAUDE.md (background)
2. Read Core Story Bank.md (stories to use)
3. Read Interview Preparation.md (frameworks)
4. Search for existing Company.md note
```

### After Debrief
```
1. Update Job Hunting.md → Market Signals
2. Update or create Interviewer profile
3. Update Active Pipeline.md if status changed
```

## Error Handling

If a file doesn't exist:
- Note it and continue — don't fail the workflow
- Create the note if the workflow requires it
- Use vault search (`grep`) to find alternatives

## Vault Search Patterns

```bash
# Find all evaluations for a company
grep -l "Company Name" ~/notes/*.md

# Find all roles with a specific anti-signal
grep -l "too junior" ~/notes/Job\ Hunting\ -\ Passed\ Roles.md

# Find recent daily notes
ls -t ~/notes/2026-*.md | head -5
```

## Related Skills

- `evaluate-job` — Uses vault for duplicate check, tracking updates
- `interview-prep` — Reads Core Story Bank, Interview Preparation
- `debrief` — Updates Market Signals
- `counter-intel` — Manages interviewer profiles
