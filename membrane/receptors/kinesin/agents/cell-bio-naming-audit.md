# Cell Biology Naming Audit

You are running a naming audit on the vivesca codebase at ~/germline.
Goal: rename organism-level terms to cell-biology equivalents.

Read first: ~/.claude/projects/-Users-terry/memory/project_cell_bio_naming_audit.md

## Decisions

- `histone_store` → `histone_store` (memory database = where marks are stored)
- `cortex` in metabolon/metabolism/signals.py only → `sensory_surface`
- synapse.py / axon.py / dendrite.py → **KEEP** (hooks ARE signal transduction)

## Process per rename

1. `vivesca rename <old> <new> --dry-run` — review scope
2. Exclude .venv/ and regex pattern strings
3. `vivesca rename <old> <new>` — execute
4. `python3 -m pytest assays/ -x -q` — must pass before next rename
5. Commit: "rename: <old> → <new> (cell-bio naming)"

## Order

1. `histone_store` → `histone_store`
2. `cortex` (signals.py scope only — use --scope metabolon/metabolism/)

## Hard rules

- Never rename synapse.py, axon.py, dendrite.py
- Never touch .venv/
- Never rename the string "brainstorm" (it's in a regex, not a component name)
- Tests green after each rename before proceeding
