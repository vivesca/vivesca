# Vigilia — Overnight mtor Monitor

Autonomous overnight monitoring loop for mtor dispatch tasks. CC stays alive via background task self-ping, triaging results and re-dispatching failures.

Use when: "overnight", "monitor mtor", "vigilia", "keep watching", "night watch"

## Mechanism

Background `sleep N && mtor list` task fires a notification that wakes CC. CC triages, acts, sets the next timer. Loop continues as long as the session lives.

## Cycle (every 15 min)

### 1. Poll
```bash
mtor list --count 50
```

### 2. Triage completed tasks
For each COMPLETED task:

| Verdict | Action |
|---------|--------|
| `activity_failed` | Check `git log` on ganglion for commits by this task. If commits exist → false positive, archive. If no commits → investigate worker log, re-dispatch with more explicit prompt. Max 2 retries per original task. |
| `rejected` (chaperone) | Check if code landed on main despite rejection (verdict false positive pattern). If landed → archive with override. If not → read failure reason, re-dispatch with fix if prompt issue, else archive. |
| `accepted` / `merged` | **Review the actual diff** (`git diff <pre>..<post>` or `git show <commit>`). Verify the change matches the prompt intent and is correct. Then archive. Don't trust verdicts — review everything until the system is proven. |

### 3. Investigate failures
For failed tasks with no commits:
- `ssh ganglion 'tail -20 /tmp/mtor-worker.log'` — check for errors
- Common causes: coaching file bloat, wall-limit self-kill, OP bootstrap, stall detection
- If infra issue → fix infra, re-dispatch all affected
- If prompt issue → re-dispatch with more explicit, smaller-scoped prompt

### 4. Dispatch new work (optional)
If queue has < 3 running tasks and there's pending work:
- Check plans directory for `status: ready` specs
- Break large tasks into smaller scoped pieces
- Enforce: tests written before dispatch (or `--no-tests` explicit)

### 5. Set next timer
```bash
sleep 900 && cd ~/code/mtor && mtor list --count 50
```
Run with `run_in_background: true`. The task notification is the ping.

## Stop conditions

- All tasks completed and no new work to dispatch
- 3 consecutive cycles with zero progress (same git log)
- User says stop
- Budget red

## Pre-flight checks (first cycle)

1. Worker alive: `ssh ganglion 'pgrep -af mtor.worker'`
2. OP bootstrap: `ssh ganglion 'source ~/.env.bootstrap && op run --env-file ~/germline/loci/env.op -- printenv ZHIPU_API_KEY | head -c5'`
3. Coaching file size: `ssh ganglion 'wc -c ~/epigenome/marks/feedback_ribosome_coaching.md'` — must be <10KB
4. Germline sync: `ssh ganglion 'cd ~/germline && git log --oneline -1'` — matches origin?

If any fail → fix before dispatching.

### 6. Update coaching notes
When reviewing diffs, spot GLM mistakes and add entries to `~/epigenome/marks/feedback_ribosome_coaching.md`. This is the skill transfer loop: review → spot pattern → coaching entry → next dispatch avoids it. Keep file under 10KB (ribosome refuses to start above that).

### 7. Review ALL completed tasks (trust-building phase)
Until the system is proven, review every completed task's actual diff — not just failures. Successful verdicts could be false positives (wrong code landed), and rejected ones might have good code. `git log` + `git show` on ganglion is the truth, not mtor verdicts.

## Anti-patterns

- Don't re-dispatch the same failing prompt 3+ times — investigate root cause
- Don't dispatch without checking ganglion git log first (commits may have landed despite failed verdicts)
- Don't dispatch complex multi-file tasks — break into single-function edits
- Don't skip the pre-flight on first cycle
