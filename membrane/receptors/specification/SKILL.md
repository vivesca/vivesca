---
name: specification
description: Write a dispatch-ready spec before any goose/droid/sortase dispatch. Use BEFORE writing implementation specs -- not after.
user_invocable: true
context: fork
epistemics: [plan, delegate]
---

# specification -- Write Dispatch-Ready Specs

Write specs that goose/droid can execute via sortase without CC hand-holding.

## When to Use

- Before `sortase exec` -- every dispatch needs a spec
- When CC says "let me write the spec and dispatch"
- When user says "spec this", "write a plan", "break this down", "dispatch this"
- After `/transcription` when the design is approved
- When requirements are clear and no design exploration is needed
- **Not needed for:** single-file changes, obvious bug fixes, config tweaks

## Inputs

Accept any of:
- A requirements doc path (from `/transcription`)
- A verbal feature description
- A GitHub issue or bug report

If a requirements doc exists in `~/epigenome/chromatin/brainstorms/` matching the topic, read it and use it as the origin. Reference it with `origin:` in frontmatter. Don't re-ask questions the transcription already answered.

If inputs are too vague to spec, say so. Either ask targeted questions (one at a time) or suggest `/transcription` first.

## Pre-Spec Quality Gate

Before writing the spec, score the input. Predict whether each requirement can fold into executable tasks before spending tokens on a full spec.

### Foldability (per section)

| Score | Meaning | Action |
|-------|---------|--------|
| **5** | Fully specified -- exact behavior, clear inputs/outputs | Spec directly |
| **4** | Minor gaps -- reasonable defaults exist | Spec with stated assumptions |
| **3** | Ambiguous -- multiple valid interpretations | Flag, ask one targeted question |
| **2** | Underspecified -- cannot produce executable tasks | Block this section, state what's missing |
| **1** | Contradictory or incoherent | Reject, explain why |

Present scores as a table before the spec. All 4-5: proceed. Mixed: spec the foldable sections, flag the rest. Any 2 or below: resolve before speccing that section.

### Disordered Region Detection

Sections that can't fold have specific signatures:
- **No verb** -- describes a state, not a behavior ("the system should be fast")
- **Unbounded scope** -- "handle all edge cases", "support any format"
- **Missing actor** -- who/what triggers this? If unstated, disordered
- **Circular reference** -- requirement depends on another that depends on it
- **Taste without criteria** -- "make it clean", "good UX" without measurable definition

Name the disorder type explicitly. Don't silently interpret vague requirements.

### Implicit Constraint Inference

Mine prior builds to surface constraints the input omits:

1. Search `~/germline/loci/antisera/` for entries matching the domain
2. Search `~/epigenome/chromatin/plans/` for similar past plans
3. Check patterns in target codebase -- conventions, middleware, callbacks, observers

Present inferred constraints: "Not stated, but implied by prior work: [constraint]". User confirms or rejects before spec proceeds.

### Skip Conditions

Skip the quality gate when ALL true: scope is trivial (1-2 tasks), requirements are fully specified (score 5), no cross-cutting concerns.

## Template

Every spec follows this structure. Fill in, skip sections that don't apply.

```markdown
---
status: ready
depends_on: []
origin: ~/epigenome/chromatin/brainstorms/YYYY-MM-DD-<topic>.md  # if one exists
---

# <Name> -- <one-line description>

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

List each test with one-line description. Tests use mocks -- no real API/CLI calls.

## Constraints

Always include:
- MANDATORY: Write tests BEFORE implementation. Run pytest twice (TDD red then green). Paste BOTH outputs.
- Spec file location: `~/germline/loci/plans/`, not `/tmp/`
- nociceptor: scripts must be Python, not bash
- Keep under <N> lines
```

## Checklist (verify before dispatching)

1. **Foldability** -- all sections score 4+ (or disordered regions resolved)
2. **Frontmatter** -- `status: ready`, `depends_on` if blocked
3. **Context** -- what exists, not what we want (agent reads current state, not aspirational)
4. **Tasks are atomic** -- one task = one change. Don't combine "add feature + write tests + update config"
5. **Code snippets** -- for files >200 lines, provide exact before/after. Don't say "rewrite the file"
6. **Test file specified** -- exact path, exact test names, what each tests
7. **Constraints include coaching** -- TDD red/green, no /tmp, Python not bash
8. **No ambiguity** -- if the agent could interpret it two ways, it will pick wrong

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
| Skip foldability on complex specs | Always score when >2 tasks or cross-cutting |

## Dispatch command

After writing spec:
```bash
sortase exec -b goose -p ~/germline ~/germline/loci/plans/<name>.md \
  --verbose --test-command "cd ~/germline && python -m pytest assays/test_<name>.py -v"
```
