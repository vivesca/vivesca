---
name: mitogen
description: Dispatch ribosome for any build task — bulk campaigns or single features. "build", "implement", "dispatch", "go build", "blitz", "batch"
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

User says: "build", "implement", "dispatch", "spec this", "batch", "go build", "blitz", "keep going while I'm away", or invokes `/mitogen` directly.

**Two modes:**
- **Directed** — user specifies what to build -> skip to Phase 2
- **Autonomous** — user says "blitz" / "work on everything" -> Phase 1 audit first

## Architecture

**Temporal on ganglion is the sole dispatch path.** CC dispatches directly via `ribosome_dispatch` MCP tool — no markdown queue, no poller.

```
CC (soma) --ribosome_dispatch MCP--> Temporal server (ganglion:7233) --> translocase.py (ganglion) --> ribosome script --> zhipu/GLM-5.1
```

- **MCP tool:** `ribosome_dispatch` — dispatch, batch, status, list, cancel actions
- **Translocase:** `polysome/translocase.py` on ganglion (eEF2 — drives the translation cycle)
- **Workflow:** `polysome/workflow.py`, retry policy (2 attempts), review activity
- **Review:** auto-rejects no_commit_on_success, target_file_missing, destruction patterns
- **Logs:** `~/germline/loci/ribosome-outputs/` on ganglion, `~/germline/loci/ribosome-reviews.jsonl`

**Provider reality (2026-04):**
- **zhipu (GLM-5.1):** Only working provider on ganglion. ~44% rate-limited on heavy days. 90% capability when not rate-limited.
- **volcano/infini:** Cheap tiers, quota-exhausted frequently. Not worth retrying.
- **codex:** Not installed on ganglion.

## Process

### Phase 0: Pre-flight

Check dispatch health:
```bash
# MCP tool — list recent workflows
ribosome_dispatch action=list limit=5

# Or via SSH
ssh ganglion 'export PATH="$HOME/.local/bin:$PATH" && cd ~/germline/effectors/polysome && uv run python cli.py list -n 5'

# Worker status
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

- **Data governance:** can this code leave the machine? No `.env`, secrets, proprietary code.
- **Parallel sessions?** → `lucus new <branch>` first.
- **Naming?** → HARD GATE: name before code. Check registry availability (PyPI/crates.io). See `artifex`.
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

### Phase 2: Write tasks with test gates

**CC writes tests first, ribosome implements to pass them.** This is the core loop.

**Controller extracts, subagents don't read.** CC reads specs/plans once and injects exactly what the ribosome needs into its prompt. Never tell ribosome "read the plan file and do what it says" — that wastes turns and lets the ribosome misinterpret. State the action directly.

**Prompt quality matters more than prompt length.** Include:
- Exact file path to create/modify
- Pattern file to copy from (if applicable)
- Test command to verify
- Commit message

1. CC writes `assays/test_<feature>.py` with concrete test cases
2. CC dispatches via MCP tool with clear prompt
3. Ribosome implements until tests pass
4. Post-gate (ast + test suite + scope check + no_commit check) auto-approves or rejects

### Phase 3: Dispatch via MCP

**Single task:**
```
ribosome_dispatch action=dispatch prompt="<prompt>" provider=zhipu max_turns=25
```

**Batch (multiple tasks):**
```
ribosome_dispatch action=batch specs='[{"task": "...", "provider": "zhipu", "max_turns": 25}, ...]'
```

**Direct execution (debugging/urgent, bypasses Temporal):**
```bash
ribosome --provider zhipu --max-turns 15 "prompt"
```

### Phase 4: Verify

**Post-gate handles verification automatically:**
- ast_check: all modified `.py` files parse
- test_check: full test suite passes
- scope_check: warns if files outside target modified
- no_commit_on_success: rejects if ribosome exits 0 but produced no git changes
- target_file_missing: flags if named target file isn't in the diff

If all pass -> auto-approved. If any fail -> rejected.

**Check status:**
```
ribosome_dispatch action=status workflow_id=<id>
ribosome_dispatch action=list limit=10
```

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

- **Only zhipu on ganglion.** Other providers exit 127 or quota-exhaust.
- **Rate-limits are billing reality.** Tasks trickle through as capacity frees up.
- **Ribosome may not commit.** Review gate now catches this — no_commit_on_success = rejected.
- **Mac-only tasks can't run on ganglion** (ARM Linux). Drop or tag for local.
- **`--dangerously-skip-permissions` is in the ribosome script.** Never remove it.
- **Don't pad queue with filler** — 10 high-value tasks beat 50 generic ones.
- **Prior discussion is NOT a plan.** Always run solutions KB check first.
- **Never write non-trivial code in-session** without proposing delegation first.
- **One task per delegation.** 3 tasks = 3 dispatches.
- **Write tests** for any non-trivial fix or feature.
