# Securin — mtor task checkpoint

Quality gate for mtor dispatch tasks. Monitors execution, triages results, salvages partial work, fixes specs, re-dispatches. Named for the checkpoint protein that prevents chromosome separation until all attachments are verified — holds back progression until quality conditions are met.

Use when: "monitor mtor", "check mtor", "securin", "keep watching", "review mtor runs", "what's running", "vigilia"

## Mechanism

Self-ping loop via CC background tasks:

```
Bash(command="sleep 900 && cd ~/code/mtor && mtor list --count 50", run_in_background=true)
```

When the task notification fires (~15 min), CC wakes up, reads the output, triages, acts, then sets the next timer. The loop continues as long as the session lives (Blink stays connected). No user interaction needed after initial `/vigilia` — CC operates autonomously.

**Critical:** Always set the next timer BEFORE doing triage work. If triage takes long and the session dies mid-work, at least the timer is set.

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

## Daytime mode (autonomous)

User is working on other things (Capco). CC runs fully autonomously — same self-ping loop as overnight. No asking permission, no "want me to continue?", no waiting for user input. Act on reversible actions (commit, push personal repos, fix specs, re-dispatch, kill orphans) and report at milestones (task completed, commit pushed, spec rewritten). Only pause for: destructive ops on shared repos, or genuine ambiguity requiring taste.

**Entry:** Pre-flight checks (same as overnight §Pre-flight). Then start self-ping loop at 10-min intervals:
```bash
sleep 600 && mtor list && ssh ganglion 'cd ~/code/mtor && git log --oneline -5 && git diff --stat && git status --short && ps aux | grep ribosome | grep -v grep | wc -l'
```
On each ping: triage, salvage, re-dispatch, set next timer. Report a 2-line summary after each cycle.

**Salvage loop** (when tasks finish with partial work):
1. Check `git diff --stat` on ganglion — any uncommitted changes?
2. Read the diff — is it correct code?
3. Run tests on ganglion: `ssh ganglion 'export PATH="$HOME/.local/bin:$PATH" && cd ~/code/mtor && uv run pytest assays/test_<name>.py -v --tb=short'`
4. Fix lint: pre-commit catches ruff violations — fix with sed, re-stage, commit
5. Push: `git push origin main`
6. Sync soma: `cd ~/code/mtor && git pull --ff-only origin main`

**Re-spec failing tasks:**
- GLM scope drift → add exact file constraints + current code to spec
- GLM corrupts large files (>500 lines) → include line numbers + code block
- Rate limit → reduce to 1-2 concurrent tasks
- No commit → will be fixed by auto-commit ribosome enhancement

**Concurrency rules (2026-04-09 lessons):**
- Max 2 concurrent tasks to ZhiPu
- Never dispatch 2 tasks targeting the same file
- `git stash` dirty work before another task touches the same file
- Worker must restart (`kill + nohup`) after code changes land

## Anti-patterns

- Don't re-dispatch the same failing prompt 3+ times — investigate root cause
- Don't dispatch without checking ganglion git log first (commits may have landed despite failed verdicts)
- Don't dispatch complex multi-file tasks — break into single-function edits
- Don't skip the pre-flight on first cycle
- Don't poll background tasks in a tight loop — set `sleep 300-600` with `run_in_background: true` and wait for notification
- Don't dispatch tasks targeting the same file concurrently — they will conflict
