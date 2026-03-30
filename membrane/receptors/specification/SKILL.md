---
name: specification
description: Write spec, dispatch to goose/sortase, review output. The dispatch lifecycle.
user_invocable: true
context: fork
epistemics: [plan, delegate, build]
---

# specification -- Dispatch Lifecycle

The single entry point for all coding work that isn't a quick edit. Pre-flight → spec → dispatch → review → coaching.

## When to Use

- When user says "build", "implement", "spec this", "dispatch", "add a feature"
- After `/transcription` when the design is approved
- When requirements are clear and no design exploration is needed
- Proactively when user asks to build, port, fix, refactor, or add a feature
- **Not needed for:** single-file changes, obvious bug fixes, config tweaks (do those directly)

## Pre-flight (absorbed from nucleation)

Before speccing, answer these:

### Should we build at all?

**Default: yes.** If a task will recur even twice, build a proper tool. Build cost is low (delegated), purge cost is near-zero.

| Signal | Action |
|--------|--------|
| Will run this logic >1 time | Build a proper CLI or skill |
| Ad-hoc data wrangling, truly once | Inline Python/bash is fine |
| Unsure | Default to building |

### Pre-flight checks

- **Data governance:** can this code leave the machine? No `.env`, secrets, proprietary code.
- **Parallel sessions?** → `lucus new <branch>` first.
- **Naming?** → name before code. Check registry availability (PyPI/crates.io).
- **Solutions KB:** `receptor-scan "<topic>"` — catches gotchas the spec may miss.

### Weight class

| Task size | Route |
|-----------|-------|
| **Trivial** (<=20 lines, single file) | Build directly in-session, skip spec |
| **Unclear requirements** | `/transcription` first, then return here |
| **Spec already exists** | Skip to Dispatch below |
| **Everything else** | Full pipeline (below) |

## Inputs

Accept any of:
- A requirements doc path (from `/transcription`)
- A verbal feature description
- A GitHub issue or bug report

If a requirements doc exists in `~/epigenome/chromatin/brainstorms/` matching the topic, read it and use it as the origin. Don't re-ask questions the transcription already answered.

If inputs are too vague to spec, say so. Either ask targeted questions (one at a time) or suggest `/transcription` first.

## Pre-Spec Quality Gate

Before writing the spec, score the input. Predict whether each requirement can fold into executable tasks.

### Foldability (per section)

| Score | Meaning | Action |
|-------|---------|--------|
| **5** | Fully specified -- exact behavior, clear inputs/outputs | Spec directly |
| **4** | Minor gaps -- reasonable defaults exist | Spec with stated assumptions |
| **3** | Ambiguous -- multiple valid interpretations | Flag, ask one targeted question |
| **2** | Underspecified -- cannot produce executable tasks | Block this section, state what's missing |
| **1** | Contradictory or incoherent | Reject, explain why |

All 4-5: proceed. Mixed: spec the foldable sections, flag the rest. Any 2 or below: resolve before speccing.

### Disordered Region Detection

Sections that can't fold have specific signatures:
- **No verb** -- describes a state, not a behavior
- **Unbounded scope** -- "handle all edge cases", "support any format"
- **Missing actor** -- who/what triggers this?
- **Circular reference** -- requirement depends on another that depends on it
- **Taste without criteria** -- "make it clean" without measurable definition

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

## Passing Criteria

Every spec must define what "done" looks like. Goose will accept its own failures if criteria are vague.

\```markdown
## Passing Criteria

- [ ] All tests pass (0 failures) -- paste output
- [ ] <specific verify command> shows expected output
- [ ] Files X, Y, Z exist/modified as specified
\```

Be explicit. "Verify it works" is not a criterion. "Run `X` and output contains `Y`" is.

## Constraints

Always include:
- MANDATORY: Write tests BEFORE implementation. Run pytest twice (TDD red then green). Paste BOTH outputs.
- Spec file location: `~/germline/loci/plans/`, not `/tmp/`
- nociceptor: scripts must be Python, not bash
- Keep under <N> lines
```

## Checklist (verify before dispatching)

1. **Protected paths** -- genome.md and epigenome/marks/ are CC-only. NEVER dispatch goose to edit these. If the spec touches memory/genome, CC does it directly.
2. **Foldability** -- all sections score 4+ (or disordered regions resolved)
3. **Frontmatter** -- `status: ready`, `depends_on` if blocked
4. **Context** -- what exists, not what we want (agent reads current state, not aspirational)
5. **Tasks are atomic** -- one task = one change
5. **Code snippets** -- for files >200 lines, provide exact before/after
6. **Test file specified** -- exact path, exact test names, what each tests
7. **Constraints include coaching** -- TDD red/green, no /tmp, Python not bash
8. **No ambiguity** -- if the agent could interpret it two ways, it will pick wrong

## Proven Spec Patterns (from overnight dispatch data)

### Ambitious specs work — use them
GLM-5.1 reliably delivers multi-file features when the spec names every file and test. Pattern:
```
1. New module: metabolon/sortase/<name>.py — list functions
2. CLI: add command in cli.py — describe behavior
3. Tests: assays/test_<name>.py — list test names
Verification: pytest command
```
Success rate: 5/5 on this pattern (overnight, coaching, lint, diff, worktree).

### Spec signals that predict success
- "YOUR ONLY JOB: write one file" — highest success for content tasks
- "EXACTLY 1 tool call: write_file" — prevents turn exhaustion
- "Do NOT read any files" — for generative tasks, goose knows enough
- Explicit output path with absolute path
- `--timeout 600` for ambitious tasks (default 300 is too short)
- `--worktree` for parallel code tasks in same repo

### Spec signals that predict failure
- "Read these 3 source files then produce X" — goose exhausts turns reading
- Specs for unfamiliar repos (~/code/*) as project dir — goose exits in 1.5s
- Append to large existing file (>200 lines) — unreliable past ~56 items
- No explicit output path — goose doesn't know where to write

### Route everything through germline
Always use `-p ~/germline` even for tasks touching other repos. Use absolute paths in the spec to read/write elsewhere. Goose has coaching + context in germline, nowhere else.

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
| Read implementation files ad-hoc | Route through this skill first |

## Dispatch

```bash
sortase exec -b goose -p ~/germline ~/germline/loci/plans/<name>.md \
  --verbose --test-command "cd ~/germline && python -m pytest assays/test_<name>.py -v"
```

Backend selection: `-b goose` (default, fastest, free), `-b gemini` (boilerplate), `-b codex` (Rust, hard bugs). One task per delegation. Independent tasks dispatch in parallel.

### Parallel dispatches

When dispatching multiple specs to the same repo, use worktrees to prevent conflicts:
```bash
sortase exec -b goose -p ~/germline <spec>.md --worktree --verbose
```
Each dispatch gets an isolated copy. Merge results after review.

### Atomic commits

Each dispatch should produce exactly one commit with a clear message. Use `--commit` flag or commit immediately after review. Don't accumulate uncommitted changes across multiple dispatches — they conflict and make review harder.

## Review (after goose returns)

Goose output is a claim, not evidence. CC must verify before approving.

### Steps

1. **Test results** -- grep output for PASS/FAIL/passed/failed. Check counts match expectations.
2. **Read modified files** -- open the actual files goose changed. Read the sections to verify they match the spec. Grepping is sampling, not reviewing.
3. **Smoke test** (code changes only) -- run the actual binary/hook/command with real input. Markdown-only changes skip this.
4. **Approve or redispatch** -- if changes are correct, commit. If not, write a follow-up spec targeting the specific gap.

### Coaching check

After review, check: did goose exhibit a new failure pattern or repeat a known one?
- New pattern → append to `~/epigenome/marks/feedback_glm_coaching.md` (format: pattern name → what GLM does wrong → fix instruction)
- Known pattern that didn't fire → no action (need systematic eval to retire)
- Clean pass → no entry needed

This is how the organism's skill transfer compounds. Every review is a coaching opportunity.

### Review anti-patterns

| Don't | Do |
|---|---|
| Grep for keywords and call it reviewed | Read the modified sections |
| Trust goose's summary of what it did | Read the files |
| Approve based on test pass alone | Tests + file read + smoke test (if code) |
| Fix goose mistakes in-session | Write a follow-up spec and redispatch |
| Skip coaching check after review | Always ask: new pattern? |
