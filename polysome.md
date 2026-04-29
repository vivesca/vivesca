---
name: polysome
description: Dispatch lifecycle contract for ribosome workers — what every dispatched task must do between mtor dispatch and COMPLETED status.
origin: openai/symphony WORKFLOW.md (Apr 2026) — concept borrowed; biology naming and procedure are vivesca-specific.
---

# Polysome

> Dispatch lifecycle for the organism. Every ribosome reads this. Constitutional peer to `genome.md` for dispatched work.

A polysome is multiple ribosomes translating one mRNA template. Here: multiple workflows reading one spec/queue ecosystem. This file is the template.

## Phases

A dispatched task moves through six phases. Each phase has an entry condition, a required action, and an exit signal. Skipping a phase is a coaching violation.

### 1. CLAIM

**Entry:** mtor dispatch creates a workflow with a spec path or inline prompt.

**Action:** Worker reads the spec in full before any tool call. If `--spec` was passed, read the spec file. If the prompt references a path, read that path. No work begins until the spec is loaded.

**Exit:** Worker writes a one-line claim to `~/epigenome/chromatin/loci/translation-queue.md` under the spec entry: `claimed by <workflow_id> at <timestamp>`.

### 2. PLAN

**Entry:** Spec read, claim recorded.

**Action:** Worker emits a 3-7 line plan to stdout: what files will change, what tests will run, what the verification will look like. This is for trace, not approval — no human gates this phase.

**Exit:** Plan emitted. If the spec is too vague to plan against, exit with FAIL and reasoning rather than guessing. Vague spec = spec defect, not worker defect.

### 3. DIFF

**Entry:** Plan emitted.

**Action:** Worker performs the work. Atomic per logical change — one commit per coherent edit, not a bundled push at the end. Each commit message ends with the workflow ID for traceability.

**Exit:** All planned changes committed. Working tree clean.

### 4. VERIFY

**Entry:** Tree clean, commits pushed.

**Action:** Worker runs the spec's `## Acceptance` checks itself before declaring done. If a check fails, fix or fail honestly — never claim PASS without running the check. Worker emits a verification log: which check, command run, output observed.

**Exit:** All acceptance checks pass and log is attached, OR worker exits with FAIL + reasoning + which check failed.

### 5. VERDICT

**Entry:** Worker exited (PASS-claimed or FAIL-claimed).

**Action:** Completion gate v2 runs (see `chromatin/loci/plans/completion-gate-v2.md`). Three layers — deterministic acceptance, coaching grep, substance pass with non-GLM model. Emits PASS / B-GRADE / FAIL.

**Exit:** Workflow status set to COMPLETED (PASS), B_GRADE (substance issue), or REJECTED (FAIL). Worker does not write its own verdict — the gate is independent.

### 6. ARCHIVE + FOLLOW-UP

**Entry:** Verdict emitted.

**Action (PASS):** Worker is permitted — and encouraged — to file follow-up tickets for out-of-scope work it noticed during the diff. Format: append to `~/epigenome/chromatin/loci/translation-queue.md` under a new heading with status `proposed`, source `worker-noticed`, parent workflow ID. Cap: 3 follow-ups per workflow. More than 3 = scope was wrong; route to a finding mark instead.

**Action (B_GRADE / REJECTED):** Worker exits without filing follow-ups. Re-dispatch with coaching update is the next loop, not noise expansion.

**Exit:** Workflow archived. translation-queue updated.

## Hard rules

- **Read spec first.** No tool call before spec is loaded into context.
- **One commit per logical change.** No bundled mega-commits.
- **Worker does not write its own verdict.** Gate v2 is independent.
- **Vague spec = exit FAIL.** Don't guess.
- **Follow-ups capped at 3 per workflow.** Above that, file a finding instead.
- **Worker writes to translation-queue.md only via the claim line and the follow-up section.** Never edits other entries.

## Coaching enforcement

Recurring violations of polysome phases get appended to `~/epigenome/marks/feedback_ribosome_coaching.md` with a phase tag (`[polysome:CLAIM]`, `[polysome:VERIFY]`, etc.). Coaching entries decay — each gets promoted to a grep gate or retired. A coaching file that only grows means polysome enforcement isn't working.

## Why this exists

Before polysome, the implicit dispatch lifecycle was scattered across `genome.md` (architect-implementer split), `feedback_ribosome_coaching.md` (failure patterns), and individual spec docs (acceptance criteria). Workers had no single contract to read. Polysome consolidates the lifecycle so a worker — or a fresh model — can be onboarded with one file.

The concept of a workflow contract for dispatched agents comes from OpenAI's Symphony spec (`WORKFLOW.md`, April 2026). Vivesca's polysome adapts the idea to the architect-implementer split, the markdown queue substrate, and the gate v2 verdict layer. We don't run Linear, we don't run Codex App Server, we don't run the Symphony orchestrator — we run mtor + ribosome. The borrowed insight: make the implicit explicit.
