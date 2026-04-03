---
name: solutions
description: Search docs/solutions/ for past learnings before starting work. Use proactively before implementing fixes, filling forms, or handling admin tasks — not just coding.
user_invocable: false
triggers:
  - solutions
  - gotcha
  - past learning
  - operational
  - before starting
---

# Solutions Lookup

Reference skill. Consult `~/docs/solutions/` before starting non-trivial work — both coding AND operational tasks.

## When to Check

**Before coding:** Already covered by CLAUDE.md "Read before write" rule.

**Before operational/admin tasks (the gap this skill fills):**
- Filing insurance claims → check `operational/manulife-simpleclaim-gotchas.md`
- Medical appointments → check `operational/qhms-process.md`, etc.
- HR/resignation processes → check `operational/resignation-exit-tactics.md`
- Financial admin → check `operational/` for relevant entries
- Any task where Terry or Claude previously hit friction

## How to Search

Quick keyword search — no agents needed:

```bash
# By filename
ls ~/docs/solutions/ ~/docs/solutions/operational/ | grep -i "<keyword>"

# By content (scoped, fast)
rg -il "<keyword>" ~/docs/solutions/ --max-depth 2
```

## Directory Structure

```
~/docs/solutions/
├── operational/          # Day-to-day life/admin (insurance, medical, banking, HR)
│   ├── manulife-simpleclaim-gotchas.md
│   ├── qhms-process.md
│   ├── orso-termination-mechanics.md
│   ├── hk-rates-pps-payment.md
│   ├── cisa-reinstatement-process.md
│   └── resignation-exit-tactics.md
├── patterns/             # Reusable workflow patterns
├── best-practices/       # External best practices
├── browser-automation/   # Browser-specific patterns
├── claude-config/        # Claude Code configuration
└── *.md                  # Everything else (flat)
```

## Routing New Learnings Here

| Type | Subdirectory |
|------|-------------|
| Insurance, medical, banking, HR, government | `operational/` |
| Coding tool gotcha | Root (`~/docs/solutions/`) |
| Reusable workflow pattern | `patterns/` |
| Browser automation | `browser-automation/` |

## File Naming Convention

All files must use **kebab-case**: `word-word-word.md`. No spaces, no camelCase, no underscores.

Examples: `claude-code-kimi-k2-setup.md`, `office-noise-focus-music.md`

## Integration with Other Tools

- **cerno** searches QMD (vault) → Oghma (conversations) but does NOT cover docs/solutions/
- **learnings-researcher** (compound-engineering) does search here but is heavy
- **This skill** = lightweight first-pass before either of those

## Key Rule

The "Read before write" principle applies to operational work too. Before handling an insurance claim, medical appointment, or HR process — check if we've already documented the gotchas.
