---
name: specification
description: Write a dispatch-ready spec for sortase/goose/droid. "spec this", "write a plan", "dispatch this"
user_invocable: true
---

# specification — Write Dispatch-Ready Specs

Write specs that goose/droid can execute via sortase without CC hand-holding.

## When to Use

- Before `sortase exec` — every dispatch needs a spec
- When CC says "let me write the spec and dispatch"
- When user says "spec this", "write a plan for goose", "dispatch this"

## Template

Every spec follows this structure. Fill in, skip sections that don't apply.

```markdown
---
status: ready
depends_on: []
---

# <Name> — <one-line description>

## Context

What exists now. What's changing. Why.

## Task 1: <verb> <object>

Exact instructions. Include:
- File paths (absolute, no ~)
- Before/after code snippets for modifications >10 lines
- For new files: full content or clear structure

## Task N: Run tests

MANDATORY. Always the last task.

\```bash
cd ~/germline && python -m pytest <test_file> -v
\```

## Tests

Write `~/germline/assays/test_<name>.py`:

List each test with one-line description. Tests use mocks — no real API/CLI calls.

## Constraints

Always include:
- MANDATORY: Write tests BEFORE implementation. Run pytest twice (TDD red then green). Paste BOTH outputs.
- Spec file location: `~/germline/loci/plans/`, not `/tmp/`
- nociceptor: scripts must be Python, not bash
- Keep under <N> lines
```

## Checklist (verify before dispatching)

1. **Frontmatter** — `status: ready`, `depends_on` if blocked
2. **Context** — what exists, not what we want (the agent reads current state, not aspirational)
3. **Tasks are atomic** — one task = one change. Don't combine "add feature + write tests + update config"
4. **Code snippets** — for files >200 lines, provide exact before/after for key sections. Don't say "rewrite the file"
5. **Test file specified** — exact path, exact test names, what each tests
6. **Constraints include coaching** — TDD red/green, no /tmp, Python not bash
7. **No ambiguity** — if the agent could interpret it two ways, it will pick wrong

## Anti-patterns

| Don't | Do |
|---|---|
| "Update the code to handle X" | Exact before/after snippet |
| "Write appropriate tests" | List each test by name with one-line spec |
| "Fix any issues" | Specific issue + specific fix |
| Put spec in /tmp | `~/germline/loci/plans/<name>.md` |
| Forget test command | Always: `--test-command "cd ~/germline && python -m pytest ..."` |
| Skip frontmatter | Always: `status: ready` minimum |
| Inline full files in spec | Give paths, let agent read. Inline only the diff. |

## Dispatch command

After writing spec:
```bash
sortase exec -b goose -p ~/germline ~/germline/loci/plans/<name>.md \
  --verbose --test-command "cd ~/germline && python -m pytest assays/test_<name>.py -v"
```
