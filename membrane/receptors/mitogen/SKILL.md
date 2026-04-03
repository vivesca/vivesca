---
name: mitogen
description: Dispatch golem for any build task — bulk campaigns or single features. "build", "implement", "dispatch", "go build", "blitz", "batch"
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

**Philosophy: CC judges, golem implements. CC writes tests, post-gate verifies. No Opus review of passing output.**

## When to trigger

User says: "build", "implement", "dispatch", "spec this", "batch", "go build", "blitz", "keep going while I'm away", or invokes `/mitogen` directly.

**Two modes:**
- **Directed** — user specifies what to build -> skip to Phase 2
- **Autonomous** — user says "blitz" / "work on everything" -> Phase 1 audit first

## Architecture

**Temporal on ganglion is the sole dispatch path.** Local golem-daemon is stopped.

```
soma (dispatch.py --poll) -> Temporal server (ganglion:7233) -> worker.py (ganglion) -> golem script -> zhipu/GLM-5.1
```

- **Dispatch poller:** supervisor-managed `temporal-dispatch` on soma, polls `golem-queue.md` every 60s
- **Worker:** `temporal-golem/worker.py` on ganglion, executes golem subprocess
- **Workflow:** `temporal-golem/workflow.py`, retry policy (2 attempts), review activity
- **Logs:** `~/tmp/temporal-dispatch.log` on soma, `~/germline/loci/golem-outputs/` on ganglion
- **Queue:** `~/germline/loci/golem-queue.md` — single source of truth

**Provider reality (2026-04):**
- **zhipu (GLM-5.1):** Only working provider on ganglion. ~44% rate-limited on heavy days. 90% capability when not rate-limited.
- **volcano/infini:** Cheap tiers, quota-exhausted frequently. Not worth retrying.
- **codex:** Not installed on ganglion.

**Auto-generation is disabled.** Queue is manually curated by CC.

## Process

### Phase 0: Check dispatch status

```bash
# On soma
supervisorctl -s unix:///tmp/supervisor.sock status temporal-dispatch
tail -10 ~/tmp/temporal-dispatch.log
python3 ~/germline/effectors/temporal-golem/dispatch.py --status | head -20
cat ~/germline/loci/golem-queue.md
```

### Phase 1: What matters? (CC judgment — do this BEFORE queuing)

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

**Prose is not golem work.** Consulting cards, case studies, briefings — single-turn generation. Generate inline in CC.

### Phase 2: Write tasks with test gates

**CC writes tests first, golem implements to pass them.** This is the core loop:

1. CC writes `assays/test_<feature>.py` with concrete test cases
2. CC writes queue entry referencing the test file
3. Golem implements until tests pass
4. Post-gate (ast + test suite + scope check) auto-approves or rejects

**Task format:**
```markdown
- [ ] `golem [t-<id>] --provider zhipu --max-turns <N> "<prompt>"`
```

- `[t-<hex>]` — unique task ID for tracking
- `--provider zhipu` — only working provider on ganglion
- `--max-turns 30` for fixes/tests, `40-50` for features
- Prompt must include: READ the file, what to change, test gate command, COMMIT

**Task types:**
- **Fix** — read failing test, diagnose, fix, verify. `--max-turns 30`.
- **Build** — create new feature + tests. `--max-turns 50`.
- **Test** — write tests for existing module. `--max-turns 30`.

**Group related tasks into operons** when they share context.

### Phase 3: Queue writes (use fcntl lock)

```python
import fcntl
from pathlib import Path

lock_path = Path.home() / '.local' / 'share' / 'vivesca' / 'golem-queue.lock'
queue_path = Path.home() / 'germline' / 'loci' / 'golem-queue.md'

with open(lock_path, 'w') as fd:
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        content = queue_path.read_text()
        content += new_tasks
        queue_path.write_text(content)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
```

No need to trigger dispatch — temporal poller picks up within 60s.

### Phase 4: Verify

**Post-gate handles verification automatically** (once t-postgate ships):
- ast_check: all modified `.py` files parse
- test_check: full test suite passes
- scope_check: warns if files outside target modified

If all pass -> auto-approved, no review. If any fail -> `[!]`, no retry.

**Manual spot-check** (until post-gate ships):
```bash
# Check outputs on ganglion
ssh ganglion "ls -lt ~/germline/loci/golem-outputs/ | head -10"
ssh ganglion "cat ~/germline/loci/golem-outputs/<latest>.txt"

# Or via temporal
python3 ~/germline/effectors/temporal-golem/dispatch.py --status
```

### Phase 5: Report

```
## Mitogen Report
- Dispatched: N tasks
- Provider: zhipu (ganglion via Temporal)
- Tests written: [list of test files]
- Queue: N pending
```

## Timeout alignment

Three timeout layers (must be nested correctly):
1. **Golem wall-limit** (`GOLEM_WALL_LIMIT`, default 28min) — gates retries, never kills active work
2. **Worker activity timeout** (`_ACTIVITY_TIMEOUT`, 30min) — asyncio.wait_for kills subprocess
3. **Workflow start_to_close** (35min) — Temporal cancels the activity

## Gotchas

- **Only zhipu on ganglion.** Other providers exit 127 or quota-exhaust.
- **Rate-limits are billing reality.** Tasks trickle through as capacity frees up.
- **Golem may not commit.** Check `git status` on ganglion after batch.
- **Mac-only tasks can't run on ganglion** (ARM Linux). Drop or tag for local.
- **`--dangerously-skip-permissions` is in the golem script.** Never remove it.
- **Don't run full pytest from CC.** Queue a golem or check outputs.
- **Don't duplicate tasks across providers** — one task per unique job.
- **Don't pad queue with filler** — 10 high-value tasks beat 50 generic ones.

## Switching back to local daemon

```bash
# Stop temporal, start daemon
supervisorctl -s unix:///tmp/supervisor.sock stop temporal-dispatch
supervisorctl -s unix:///tmp/supervisor.sock start golem-daemon
```
