---
name: translation
description: Turn a design into an implementation plan with TDD steps, exact paths, code.
user_invocable: true
epistemics: [plan, delegate]
---

# /translation — Implementation Plan

Turn a validated design into a plan that an executing agent (or future you) can follow with zero additional context. The plan is the complete instruction set.

## When to Use

- After `/transcription` when the design is approved
- When requirements are already clear and no design exploration is needed
- When the user says "plan this", "how do we build this", "break this down"
- **Not needed for:** single-file changes, obvious bug fixes, config tweaks

## Inputs

Accept any of:
- A requirements doc path (from `/transcription`)
- A verbal feature description
- A GitHub issue or bug report

If a requirements doc exists in `~/epigenome/chromatin/brainstorms/` matching the topic, read it and use it as the origin. Reference it with `origin:` in frontmatter. Don't re-ask questions the transcription already answered.

If inputs are too vague to plan, say so. Either ask targeted questions (one at a time) or suggest `/transcription` first.

## Context Scan

Before planning, scan what exists. Match depth to scope:

- **Light:** Search for relevant files, check for prior art. 30 seconds.
- **Standard/Deep:** Read relevant source files, check `~/germline/loci/antisera/` for learnings, note patterns to follow. Check for system-wide impacts: what callbacks, middleware, or observers fire when this code runs? What breaks if this fails halfway?

If local context is sufficient, skip external research. If the domain is unfamiliar or high-risk (security, payments, external APIs), do targeted web research before planning.

## Foldability Assessment

Before writing the plan, score the input. This is the AlphaFold pass — predict whether each requirement can fold into executable steps before spending tokens on a full plan.

### Per-Section Confidence (pLDDT)

Score each requirement or section of the input on foldability:

| Score | Meaning | Action |
|-------|---------|--------|
| **5** | Fully specified — exact behavior, clear inputs/outputs | Plan directly |
| **4** | Minor gaps — reasonable defaults exist | Plan with stated assumptions |
| **3** | Ambiguous — multiple valid interpretations | Flag, ask one targeted question |
| **2** | Underspecified — cannot produce executable steps | Flag as disordered, block planning for this section |
| **1** | Contradictory or incoherent | Reject, explain why |

Present the scores as a table before the plan. If any section scores 2 or below, do not plan that section — state what's missing and ask. A spec with all 4-5 scores proceeds directly. Mixed scores: plan the foldable sections, flag the disordered ones.

### Disordered Region Detection

Sections that cannot fold have specific signatures:

- **No verb** — describes a state, not a behavior ("the system should be fast")
- **Unbounded scope** — "handle all edge cases", "support any format"
- **Missing actor** — who/what triggers this? If unstated, it's disordered
- **Circular reference** — requirement depends on another requirement that depends on it
- **Taste without criteria** — "make it clean", "good UX" without measurable definition

When detected, name the disorder type explicitly. Don't silently interpret vague requirements — that's how bad plans get written.

### Implicit Constraint Inference

Mine prior builds to surface constraints the spec omits:

1. **Search `~/germline/loci/antisera/`** for entries matching the domain — prior learnings encode constraints that were discovered the hard way
2. **Search `~/epigenome/chromatin/plans/`** for similar past plans — what did they require that this spec doesn't mention?
3. **Check patterns in target codebase** — if modifying existing code, what conventions/middleware/callbacks/observers will fire? What breaks if this fails halfway?

Present inferred constraints as a list: "Not stated, but implied by prior work: [constraint]". The user confirms or rejects before planning proceeds.

### Assessment Output

```markdown
## Foldability

| Section | Score | Notes |
|---------|-------|-------|
| Auth flow | 5 | Fully specified |
| Data model | 4 | Assumed UUID PKs |
| Error handling | 2 | DISORDERED — no failure modes defined |

**Disordered regions:** Error handling — no verb, unbounded scope ("handle errors gracefully")

**Inferred constraints:**
- Prior: `~/germline/loci/antisera/auth-token-rotation.md` — token refresh needs retry logic (not in spec)
- Codebase: `middleware/audit.py` fires on all writes — plan must account for audit log entries
```

If all sections score 4+, state "Fully foldable" and proceed to planning. If disordered regions exist, resolve them before writing the plan. Don't plan around ambiguity — surface it.

## The Plan

### Structure

Scale the plan to the work. A 3-step task gets a compact plan. A cross-cutting feature gets full treatment.

**Every plan starts with:**

```markdown
---
date: YYYY-MM-DD
topic: <kebab-case>
origin: ~/epigenome/chromatin/brainstorms/YYYY-MM-DD-<topic>.md  # if one exists
---

# <Feature Name>

**Goal:** [One sentence — what this builds and why]

**Approach:** [2-3 sentences — how, and key technical choices]
```

### File Map

Before defining tasks, map every file that will be created or modified:

```markdown
## Files

- Create: `exact/path/to/new_file.py` — [what it does]
- Modify: `exact/path/to/existing.py` — [what changes]
- Test: `tests/exact/path/to/test_file.py` — [what it covers]
```

This is where decomposition decisions get locked in. Each file should have one clear job. Files that change together should live together.

### Tasks

Each task is a self-contained unit that produces a working, testable increment. A task that leaves things broken is too big or wrongly scoped.

````markdown
### Task N: [Component Name]

**Files:** `path/to/file.py`, `tests/path/to/test.py`

- [ ] Write failing test

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] Verify it fails — `pytest tests/path/test.py::test_name -v` → FAIL

- [ ] Implement

```python
def function(input):
    return expected
```

- [ ] Verify it passes — `pytest tests/path/test.py::test_name -v` → PASS

- [ ] Commit — `git commit -m "feat: add specific behavior"`
````

**The standard is TDD.** Write the test first, watch it fail, implement minimally, watch it pass, commit. Every task follows this rhythm unless testing genuinely doesn't apply (pure config, documentation, CI changes).

### Task Granularity

Each step is one action, 2-5 minutes:
- "Write the failing test" — one step
- "Run it to verify failure" — one step
- "Implement minimal code" — one step
- "Verify pass" — one step
- "Commit" — one step

If a step takes more than 5 minutes to describe or execute, it's multiple steps.

### What Goes in the Plan

- **Exact file paths.** Always.
- **Complete code.** Not "add validation" — the actual code.
- **Exact commands with expected output.** Not "run the tests" — the specific command and what success looks like.
- **Why, not just what.** When a choice isn't obvious, explain the reasoning in a sentence.

### What Stays Out

- Alternative approaches already rejected in transcription (link to origin doc)
- Future considerations and extensibility (YAGNI)
- Resource estimates and timelines
- Issue tracker integration

## Save

Write the plan to `~/epigenome/chromatin/plans/YYYY-MM-DD-<topic>-plan.md`. Confirm the path.

## Handoff

- **Completeness check:** "Could `/folding` execute this plan without asking a single question?" If not, the plan is incomplete — fill the gaps before handing off.
- State the plan path and recommend `/folding` for execution. Don't start implementing — the user decides when.
- If the plan is small enough that full delegation is overkill (2-3 tasks, all straightforward), say so: "This is small enough to just execute directly."

## Principles

- **Zero-context execution.** An agent reading only this plan should be able to execute it without asking questions. If they'd need to ask, the plan is incomplete.
- **TDD by default.** Tests first. Exceptions must be justified.
- **Complete code, not descriptions.** "Add error handling for X" is not a plan step. The actual error handling code is.
- **One working increment per task.** Never leave the system broken between tasks.
- **Scale ceremony to scope.** Don't write a 50-step plan for a 3-step job.
