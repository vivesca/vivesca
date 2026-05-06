---
name: mitogen
description: Dispatch ribosome for a specific build task — directed campaigns or single features. "build", "implement", "dispatch", "go build", "batch". For autonomous work discovery, use /blitz.
effort: high
model: opus
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
context: inline
epistemics: [audit, delegate, verify]
---

# /mitogen — Autonomous Bulk Dispatch Campaign

Biology: a mitogen is a signal that triggers rapid cell proliferation. `/mitogen` is the signal that tells the organism to mass-produce improvements autonomously.

**Philosophy: CC judges, ribosome implements. CC writes tests, post-gate verifies. No Opus review of passing output.**

## When to trigger

User says: "build", "implement", "dispatch", "spec this", "batch", "go build", or invokes `/mitogen` directly. User specifies WHAT to build.

For "what should I build?" / "find work" / "work on everything" → use `/blitz` instead.

## Architecture

**Temporal on ganglion is the sole dispatch path.** CC dispatches via `mtor` CLI (translation controller) — no MCP, no markdown queue, no poller.

```
CC (soma) --mtor CLI--> Temporal server (ganglion:7233) --> translocase.py (ganglion, polysome/) --> ribosome --provider {zhipu|infini|volcano|goose|droid|gemini|codex}
```

- **CLI:** `mtor` — dispatch, list, status, logs, cancel, doctor, schema (agent-first JSON envelope)
- **Translocase:** `polysome/translocase.py` on ganglion (eEF2 — drives the translation cycle)
- **Workflow:** `polysome/workflow.py`, retry policy (2 attempts), review activity
- **Review:** auto-rejects no_commit_on_success, target_file_missing, destruction patterns
- **Logs:** `~/germline/loci/ribosome-outputs/` on ganglion, `~/germline/loci/ribosome-reviews.jsonl`
- **COMPLETED status is unreliable** — verify against reviews.jsonl (`finding_temporal_completed_is_a_lie.md`)

**Provider reality (2026-04):**
- **zhipu (GLM-5.1 via CC):** Primary. ~44% rate-limited on heavy days. 90% capability when not.
- **infini (minimax-m2.7 via CC):** Coding plan, SWE-Pro 56.2% (near Opus 4.6). Use `--provider infini`.
- **goose (GLM-5.1 via Goose):** Alternative harness. Streaming bug on long output — experimental.
- **droid (GLM-5.1 via Factory Droid):** Alternative harness. Rich context (genome+skills+coaching). Tested 20/21 on hard tasks.
- **volcano (doubao):** Cheap tier, quota-exhausted frequently. Viable for builds — earlier "hallucination" diagnosis was wrong (model correctly identified pre-existing code).
- **gemini/codex:** Available but less tested on ganglion.

## Process

### Phase 0: Pre-flight

Check dispatch health:
```bash
# CLI — list recent workflows
mtor riboseq --count 5

# Health check (Temporal reachable, worker alive)
mtor doctor

# Worker status (fallback if CLI not yet installed)
ssh ganglion "sudo systemctl status temporal-worker --no-pager"
```

### Phase 0.5: Complexity routing

Before planning, classify the task:

| Size | Signal | Action |
|------|--------|--------|
| Trivial | Single file, <20 lines, obvious fix | CC does it directly — no dispatch |
| Small | 1-3 files, clear scope | Single ribosome dispatch, skip Phase 1 audit |
| Large | Multi-file, ambiguity, dependencies | Full Phase 1 audit + multi-task batch |

Don't build a 5-task campaign for a one-liner fix.

### Phase 0.75: Pre-flight (from rector)

- **Already-shipped check (mandatory).** Before any `mtor --spec` or `ribosome` dispatch, verify the target feature has not already shipped. Recency-window git log (`git log -N`) is the wrong form — an active parallel session can push relevant commits below the visible window. Right form: `git log --all --grep="<feature_name>"` AND grep the target file directly for the named function. Both must come back empty before dispatch. If either has hits, READ the prior implementation and decide whether the dispatch is incremental change or no-op redundant. Codifies `finding_dispatch_self_context_blindness.md` (2026-05-06): A and B Layer-1 dispatches duplicated already-shipped Slot 47 commits because `git log -8` was too shallow.
- **Data governance:** can this code leave the machine? No `.env`, secrets, proprietary code.
- **Parallel sessions?** → `lucus new <branch>` first.
- **Naming?** → HARD GATE: name before code. Check registry availability (PyPI/crates.io). See `organogenesis`.
- **Solutions KB:** `cerno "<topic>"` before starting.

### Phase 1: What matters? (CC judgment — do this BEFORE dispatch)

**Stop and think:** what is the most impactful work right now? Check:
- **Tonus.md** — what's active, what's perishable, what deadline is next?
- **Calendar** — what's coming in 1-7 days that needs prep?
- **Broken things** — what's failing that blocks real usage?
- **User's last request** — did they ask for something specific?

Then prioritize:
1. **Perishable** — deadlines, prep work, things that lose value if delayed
2. **Fixes** — broken tests, regressions, bugs
3. **Compound infra** — improvements to dispatch system itself
4. **Features** — new capabilities, effectors
5. **Tests** — coverage for untested modules (filler, not main course)

**Prose is not ribosome work.** Consulting cards, case studies, briefings — single-turn generation. Generate inline in CC.

### Phase 2: Write specs + tests (primase)

**CC writes specs and tests, ribosome implements to pass them.** This is the core loop.

**Spec file:** `~/epigenome/chromatin/loci/plans/spec-<slug>.md` with YAML frontmatter. Only mtor-validated fields go in frontmatter; aspirational fields (`pipeline_stage`, `wave`, `parent_spec`) belong in body prose until mtor's validator accepts them. Get the current schema with `mtor schema` if unsure.

```yaml
---
title: "One-line description"
status: ready
repo: ~/code/<repo>
depends_on: []
scope:
  - path/to/file.py
tests:
  run: "uv run pytest assays/test_foo.py -x"
---
```

If you need pipeline-stage tracking, wave grouping, or parent-spec linking, write them as prose paragraphs after the frontmatter (`**Wave:** 1 (parallel-safe with spec-bar.md)`, `**Parent spec:** ../foo.md`). The validator rejects unknown frontmatter fields and aborts dispatch — `2026-05-06` had a 2-min friction loop because /mitogen documented `pipeline_stage` / `wave` / `parent_spec` that mtor didn't honour.

**Spec body:** Problem (2-3 sentences) → Solution (concrete: name the function, the approach) → Location (exact file, line numbers, paste current code if >200 lines) → Constraints (only modify X, do NOT modify Y) → Tests (exact function names + assertions + STOP condition).

**Spec rules:**
1. **One function per spec.** Split broad changes into multiple specs with `depends_on`.
2. **Paste current code.** GLM corrupts files >500 lines when working blind.
3. **Explicit file constraint.** "Only modify `translocase.py` lines 200-250" — not "only modify mtor".
4. **Name the insertion point.** "Add after `_merge_lock` helper" not "add near the top".
5. **Tests with explicit stop conditions.** "Add test_foo, test_bar. Stop after these 2 — do not add more." Without this, GLM loops (22 commits in 2hr observed 2026-04-10).
6. **Frontmatter matches rptor fields.** `depends_on` not `blocked_by`.

**Pre-spec checklist:** Read target file → identify exact function/line → check naming patterns → check `git log` on ganglion for conflicts with running tasks.

**Dispatch flow:**
1. CC writes spec file with all above
2. CC writes `assays/test_<name>.py` with test scaffolds
3. CC pushes both to origin
4. CC dispatches: `mtor --spec <spec.md> "Implement X per spec"`
5. Post-gate auto-approves or rejects

### Phase 2.5: Wave grouping (wave concept adapted from `compound-engineering/ce-work` Phase 1 Step 4 parallel-safety check; `wave:` frontmatter field is vivesca-original)

Before dispatching a multi-task batch, group specs into **waves** by dependency:

- **Same wave** = independent specs (no shared `depends_on` chain, no overlapping `scope:` paths). Fire in parallel.
- **Next wave** = waits for previous wave's review verdicts (approved/rejected via reviews.jsonl) before starting.
- **Sequential within wave** when two specs touch the same file — file conflicts force serialisation.

**Wave-assignment procedure (3 steps):**
1. **Map `scope:` paths per spec.** Build `{spec_id → set(scope_paths)}` from frontmatter.
2. **Check pairwise intersection.** For every pair in the candidate wave, if `scope_a ∩ scope_b ≠ ∅` → conflict. Either move one to a later wave, or serialise within the wave.
3. **Honour `depends_on` chains.** Spec B with `depends_on: [A]` must be in a later wave than A regardless of scope.

Vertical slices (one feature end-to-end per spec) parallelise; horizontal layers (all models, then all APIs) serialise unnecessarily.

**Wave-boundary simplification checkpoint** (adapted from `compound-engineering/ce-work` Phase 2.5 "Simplify as you go"). After a wave's reviews.jsonl verdicts land and BEFORE dispatching the next wave, scan cross-spec diff for: (a) duplicated helpers extractable to shared module, (b) inconsistent naming/conventions across specs, (c) accumulating coupling that should be refactored before more specs land on it. For 3+ wave campaigns, the cluster review catches drift the per-spec post-gate cannot. Skip for ≤2 specs.

Single-spec campaigns: skip this phase.

### Phase 3: Dispatch via CLI

**Single task:**
```bash
mtor "prompt"
mtor --provider infini "prompt"              # use minimax-m2.7
mtor --spec ~/path/to/spec.md "prompt"       # attach spec (auto-updates status)
```

**Check status:**
```bash
mtor riboseq --count 10
mtor status <workflow_id>
```

**Cancel a stuck workflow:**
```bash
mtor cancel <workflow_id>
```

### Phase 4: Verify

**Post-gate handles verification automatically:**
- ast_check: all modified `.py` files parse
- test_check: full test suite passes
- scope_check: warns if files outside target modified
- no_commit_on_success: rejects if ribosome exits 0 but produced no git changes
- target_file_missing: flags if named target file isn't in the diff

If all pass -> auto-approved. If any fail -> rejected.
**IMPORTANT:** Temporal COMPLETED status does not mean the task succeeded — always check reviews.jsonl verdict (`finding_temporal_completed_is_a_lie.md`).

### Phase 5: Report

```
## Mitogen Report
- Dispatched: N tasks
- Provider: zhipu (ganglion via Temporal)
- Tests written: [list of test files]
- Status: N approved, N rejected, N running
```

## Timeout alignment

Three timeout layers (must be nested correctly):
1. **Ribosome wall-limit** (`RIBOSOME_WALL_LIMIT`, default 28min) — gates retries, never kills active work
2. **Worker activity timeout** (`_ACTIVITY_TIMEOUT`, 30min) — asyncio.wait_for kills subprocess
3. **Workflow start_to_close** (35min) — Temporal cancels the activity

## Gotchas

- **zhipu + infini on ganglion.** Infini uses minimax-m2.7 (SWE-Pro 56.2%). Use `--provider infini` for alternative.
- **Rate-limits are billing reality.** Tasks trickle through as capacity frees up.
- **Ribosome may not commit.** Review gate now catches this — no_commit_on_success = rejected.
- **"Already done" detection.** If a task is rejected with empty diff BUT stdout says "done/pass/complete", check ganglion first: `ssh ganglion 'cd ~/code/mtor && grep -l "feature_name" mtor/*.py'`. The feature may already exist from a prior task. Don't re-dispatch — pull instead.
- **Mac-only tasks can't run on ganglion** (ARM Linux). Drop or tag for local.
- **`--dangerously-skip-permissions` is in the ribosome script.** Never remove it.
- **Don't pad queue with filler** — 10 high-value tasks beat 50 generic ones.
- **Prior discussion is NOT a plan.** Always run solutions KB check first.
- **Never write non-trivial code in-session** without proposing delegation first.
- **One task per delegation.** 3 tasks = 3 dispatches.
- **Write tests** for any non-trivial fix or feature.

## Motifs
- [audit-first](../motifs/audit-first.md)
- [verify-gate](../motifs/verify-gate.md)
- [state-branch](../motifs/state-branch.md)
