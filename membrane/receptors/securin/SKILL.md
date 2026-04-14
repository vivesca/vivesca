---
name: securin
description: "Quality gate for mtor dispatch tasks — monitor, triage, salvage, re-dispatch"
triggers:
  - "monitor mtor"
  - "check mtor"
  - "securin"
  - "keep watching"
  - "review mtor runs"
  - "what's running"
  - "vigilia"
---

# Securin — mtor task checkpoint

Quality gate for mtor dispatch tasks. Monitors execution, triages results, salvages partial work, fixes specs, re-dispatches. Named for the checkpoint protein that prevents chromosome separation until all attachments are verified — holds back progression until quality conditions are met.

## Mechanism

Self-ping loop via CC background tasks:

```
Bash(command="sleep 900 && cd ~/code/mtor && mtor riboseq --count 50", run_in_background=true)
```

When the task notification fires (~15 min), CC wakes up, reads the output, triages, acts, then sets the next timer. The loop continues as long as the session lives (Blink stays connected). No user interaction needed after initial `/vigilia` — CC operates autonomously.

**Critical:** Always set the next timer BEFORE doing triage work. If triage takes long and the session dies mid-work, at least the timer is set.

## Cycle (every 15 min)

### 1. Poll
```bash
mtor riboseq --count 50
```

Also check active logs on ganglion — this is the real execution signal:
```bash
ssh ganglion 'ls -lt ~/code/mtor/logs/*.log 2>/dev/null | head -5'
```
Files modified within last 5 min = actively executing. No recent modification = queued or stuck in preflight. `mtor riboseq` RUNNING status alone doesn't distinguish.

### 2. Triage completed tasks

**NEVER archive without investigation.** Every completed task gets the full checklist — no exceptions, no shortcuts. Tasks may come from other CC sessions, cron dispatches, or manual queuing. Treat ALL tasks as intentional work worth reviewing.

**Investigation checklist (mandatory before archive):**
1. `mtor status <workflow_id>` — read failure_reason, exit_code, task_preview
2. `ssh ganglion 'cat ~/code/mtor/logs/<workflow_id>.log | tail -30'` — read output
3. `ssh ganglion 'cd ~/code/mtor && git log --oneline -5'` — check for commits
4. `ssh ganglion 'cd ~/code/mtor && git diff --stat'` — check for uncommitted work
5. If work exists (committed or uncommitted) → review the diff for correctness
6. Only THEN decide: salvage, re-dispatch, or archive

**Do NOT dismiss tasks targeting other repos/projects.** They were dispatched intentionally. If a task targets germline, epsin, or any other repo — investigate it in that repo's context, not just mtor.

For each COMPLETED task:

| Verdict | Action |
|---------|--------|
| `activity_failed` | Check `git log` on ganglion for commits by this task. If commits exist → false positive, archive. If no commits → investigate worker log, re-dispatch with more explicit prompt. Max 2 retries per original task. |
| `rejected` (chaperone) | Check if code landed on main despite rejection (verdict false positive pattern). If landed → archive with override. If not → read failure reason. If task is worth retrying → write tighter spec and re-dispatch. Else archive with reason noted. |
| `accepted` / `merged` | **Review the actual diff** (`git diff <pre>..<post>` or `git show <commit>`). Verify the change matches the prompt intent and is correct. Then archive. Don't trust verdicts — review everything until the system is proven. |

### 3. Investigate failures and auto-fix infra

For failed tasks with no commits, classify the failure and act:

**Step 1: Read the log to classify.**
```bash
ssh ganglion 'cat ~/code/mtor/logs/<workflow_id>.log | tail -40'
```

**Step 2: Match failure pattern → auto-fix.**

| Log pattern | Diagnosis | Auto-fix |
|-------------|-----------|----------|
| `API key not valid` (Gemini) | Transient API rejection or stale key | Test: `ssh ganglion 'source ~/.env.bootstrap && op run --env-file ~/germline/loci/env.op -- bash -c "curl -s \"https://generativelanguage.googleapis.com/v1beta/models?key=\$GOOGLE_API_KEY\" \| head -c50"'`. If OK → transient, re-dispatch on zhipu/volcano instead. If fails → key expired, flag to user. |
| `401 Unauthorized.*wss://api.openai.com` (Codex) | Codex CLI uses OAuth, not API key. No login session on ganglion. | **Not auto-fixable** (requires interactive `codex login`). Remove codex from fallback: re-dispatch on zhipu/volcano. Don't retry on codex. |
| `FATAL: claude preflight probe returned empty output` | Provider API returned empty — transient rate limit or network. | Check if other tasks on same provider succeeded this cycle. If yes → transient, re-dispatch same provider. If all failed → provider is down, shift to other providers. |
| `RIBOSOME_RATE_LIMIT` / `Service concurrency exceeded` | Provider rate limit hit. | Wait — don't re-dispatch immediately. The provider's backoff will resolve. Re-dispatch on next cycle, or shift to a different provider. |
| `[wall-limit]` in log or `AccountQuotaExceeded` | Stale worker self-killed on time limit — often a false error. | Check `git log` for commits (work may have landed). If commits exist → false positive, archive. If no commits → re-dispatch. |
| `activity_failed` with no output_path | Temporal activity crashed before harness started. | Check worker health: `ssh ganglion 'pgrep -af mtor.worker'`. If dead → restart worker. If alive → re-dispatch (transient Temporal issue). |
| `exit_code=1` + `command failed with exit=1 at line NNNN` | Harness script crashed (not the LLM). | Read the line number in ribosome script to identify the stage (preflight, execution, commit). Fix the script bug if pattern repeats. |
| `IndentationError` / `SyntaxError` in committed code | GLM produced invalid Python. | Revert on ganglion, add coaching note (syntax check mandatory), re-spec with tighter constraints. |
| No log file at all | Task never started or log path is wrong. | Check `mtor status <id>` for output_path. Check worker log: `ssh ganglion 'tail -20 /tmp/mtor-worker.log'`. |

**Step 3: Provider health check (when ≥2 tasks fail on same provider).**
```bash
# Test each provider's API directly
ssh ganglion 'source ~/.env.bootstrap && op run --env-file ~/germline/loci/env.op -- bash -c "
  curl -s \"https://generativelanguage.googleapis.com/v1beta/models?key=\$GOOGLE_API_KEY\" | head -c30  # Gemini
  curl -s -H \"Authorization: Bearer \$OPENAI_API_KEY\" https://api.openai.com/v1/models | head -c30    # OpenAI
  curl -s -H \"Authorization: Bearer \$ZHIPU_API_KEY\" https://open.bigmodel.cn/api/paas/v4/models | head -c30  # ZhiPu
"'
```
If API responds but CLI fails → CLI config issue (version, auth flow change). If API fails → key expired or provider down.

**Step 4: After fixing, re-dispatch all affected tasks** on working providers. Don't wait for next cycle.

### 4. Dispatch new work
Dispatch all ready specs — Temporal queues them and drains at 2 concurrent per provider. No need to batch or throttle from CC's side. Dispatch and forget.
- Enforce: tests written before dispatch (or `--no-tests` explicit)

### 5. Set next timer
```bash
sleep 900 && cd ~/code/mtor && mtor riboseq --count 50
```
Run with `run_in_background: true`. The task notification is the ping.

## Closed-loop convergence

Securin is not a single pass. Every task must reach one of two terminal states:
1. **Landed** — committed, tested, pushed, grade B or above
2. **Parked** — explicitly parked with a reason (too complex for GLM, needs human taste, blocked on external dep)

**Re-dispatch rules (the loop):**
- **Infra failure** (auth, preflight, rate limit) → troubleshoot per §3, re-dispatch on a working provider. Same prompt is fine.
- **Grade D or below** (syntax errors, scope creep, regressions) → revert bad code, write a tighter spec (exact files, line constraints, "do NOT touch X"), re-dispatch. Max 2 re-specs per original task — after that, park it.
- **No commit** (GLM forgot `git add + commit`) → check if uncommitted work exists on ganglion. If good code → salvage (commit manually, push). If no work → re-dispatch with coaching emphasis on commit discipline.
- **Partial work** (some sub-tasks done, others not) → commit what's good, write a new spec for the remaining sub-tasks only, dispatch.

**Escalation ladder (per original task):**
1. First failure → re-dispatch same provider (might be transient)
2. Second failure → re-dispatch different provider + tighter spec
3. Third failure → **decompose** the task into smaller pieces and dispatch each separately
4. Park ONLY if the task fundamentally requires judgment/taste that GLM can't provide (architectural decisions, multi-file coordination, design choices). Infra failures and spec failures are never reasons to park — keep fixing and retrying.

**Track retry count mentally per original task intent.** After 2 failures with the same prompt, the problem is the spec — rewrite it, don't just retry.

## Stop conditions

- **All tasks landed or explicitly parked** — this is the primary stop condition
- 3 consecutive cycles with zero progress (same git log, same task count)
- User says stop

**Do NOT stop for budget red or metabolic state.** The whole point of securin is autonomous overnight monitoring. Poll until morning or until all tasks converge — whichever comes first. The session lives in tmux; Blink disconnects don't kill it.

**Do NOT stop just because the queue is empty after one pass.** Check: are there failed tasks that should be re-dispatched? Parked tasks that infra fixes unblocked? Only stop when every original task intent has converged.

## Pre-flight checks (first cycle)

1. Worker alive: `ssh ganglion 'pgrep -af mtor.worker'`
2. OP bootstrap: `ssh ganglion 'source ~/.env.bootstrap && op run --env-file ~/germline/loci/env.op -- printenv ZHIPU_API_KEY | head -c5'`
3. Coaching file size: `ssh ganglion 'wc -c ~/epigenome/marks/feedback_ribosome_coaching.md'` — must be <10KB
4. Germline sync: `ssh ganglion 'cd ~/germline && git log --oneline -1'` — matches origin?

If any fail → fix before dispatching.

5. Provider liveness (quick smoke test):
```bash
ssh ganglion 'source ~/.env.bootstrap && op run --env-file ~/germline/loci/env.op -- bash -c "
  printf \"gemini: \"; curl -sf \"https://generativelanguage.googleapis.com/v1beta/models?key=\$GOOGLE_API_KEY\" | head -c5 && echo \" OK\" || echo \" FAIL\"
  printf \"zhipu: \"; curl -sf -H \"Authorization: Bearer \$ZHIPU_API_KEY\" https://open.bigmodel.cn/api/paas/v4/models | head -c5 && echo \" OK\" || echo \" FAIL\"
"'
```
If a provider fails → don't dispatch to it. Shift load to working providers. Codex needs interactive OAuth (`codex login` on ganglion) — if 401 errors appear, flag to user for re-login.

### 6. Update coaching notes
When reviewing diffs, spot GLM mistakes and add entries to `~/epigenome/marks/feedback_ribosome_coaching.md`. This is the skill transfer loop: review → spot pattern → coaching entry → next dispatch avoids it. Keep file under 10KB (ribosome refuses to start above that).

### 7. Review ALL completed tasks (trust-building phase)
Until the system is proven, review every completed task's actual diff — not just failures. Successful verdicts could be false positives (wrong code landed), and rejected ones might have good code. `git log` + `git show` on ganglion is the truth, not mtor verdicts.

**Quality review checklist per commit (mandatory):**
- Did GLM delete existing logic it shouldn't have? (regression check — diff deletions > additions is a red flag)
- Does the implementation match the spec's intent, or just the literal words? (cosmetic vs functional)
- Are new functions actually wired into callers, or just dead code?
- `test_test_*` double-prefix → GLM coaching issue, add to coaching file
- Defensive type conversions (str→list, etc.) that mask upstream bugs → flag, don't merge blindly

**Grade each commit A-F.** Anything below B: re-spec with explicit constraints on what NOT to delete/change. Don't let throughput pressure skip review — 3 quality commits > 6 mediocre ones.

### 8. Re-spec and re-dispatch (mandatory for all non-landed tasks)

**Do not just note failures — fix the spec and re-dispatch in the same cycle.**

**For grade C or below (bad code):**
1. Revert if it deleted important logic (`git revert` on ganglion)
2. Diagnose WHY GLM failed — too many files? Ambiguous scope? Large file corruption?
3. Write a tighter spec:
   - Constrain to ONE file per task
   - Include exact function signatures to preserve
   - Add "DO NOT touch lines X-Y" / "DO NOT delete any existing functions"
   - Name expected test functions explicitly
   - For files >500 lines: include the relevant code block in the spec so GLM doesn't misread it
4. Re-dispatch immediately on a working provider

**For infra failures (no work done):**
1. Troubleshoot per §3 (provider health, auth, preflight)
2. Re-dispatch the SAME prompt on a different working provider
3. No spec change needed — the prompt was fine, the infra wasn't

**For no-commit (GLM forgot to commit):**
1. Check ganglion for uncommitted work (`git diff --stat`)
2. If good code exists → salvage: run tests, commit, push
3. If no work exists → re-dispatch with same prompt (coaching file already emphasizes commit discipline)

**For scope creep / multi-file mess:**
1. Decompose the original task into single-file tasks
2. Dispatch each as a separate mtor task
3. Example: "refactor _streamlit_app.py into modules" → 4 tasks: "extract search functions to _st_search.py", "extract chart functions to _st_charts.py", etc.

**For complex tasks that failed 2x:**
1. Read the original spec and the failure logs
2. Identify the smallest subtask that would still be useful
3. Dispatch that subtask alone — accumulate progress incrementally
4. After it lands, dispatch the next piece

## Daytime mode (autonomous)

User is working on other things (Capco). CC runs fully autonomously — same self-ping loop as overnight. No asking permission, no "want me to continue?", no waiting for user input. Act on reversible actions (commit, push personal repos, fix specs, re-dispatch, kill orphans) and report at milestones (task completed, commit pushed, spec rewritten). Only pause for: destructive ops on shared repos, or genuine ambiguity requiring taste.

**Entry:** Pre-flight checks (same as overnight §Pre-flight). Then start self-ping loop at 10-min intervals:
```bash
sleep 600 && mtor riboseq && ssh ganglion 'cd ~/code/mtor && git log --oneline -5 && git diff --stat && git status --short && ps aux | grep ribosome | grep -v grep | wc -l'
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
- Max 2 concurrent tasks per provider (zhipu: 2, volcano: 2, infini: 2)
- Dispatch across all 3 providers to maximize throughput (6 concurrent total)
- When `mtor --harness` flag is available, use it to route: `mtor --harness goose --spec X` for variety
- Never dispatch 2 tasks targeting the same file
- `git stash` dirty work before another task touches the same file
- Worker must restart (`kill + nohup`) after code changes land

**Provider dispatch strategy:**
- Spread specs evenly across zhipu, volcano, infini
- If one provider is flaky (preflight failures), shift load to the others
- ZhiPu most reliable 22:00-06:00 HKT; volcano/infini untested — learn their patterns overnight

## Anti-patterns

- **Don't archive without investigating** — run the full checklist first. "No logs" is a finding, not an excuse to skip.
- **Don't dismiss tasks from other sessions** — every task in the queue was dispatched intentionally. Different repo ≠ irrelevant.
- Don't re-dispatch the same failing prompt 3+ times — investigate root cause
- Don't dispatch without checking ganglion git log first (commits may have landed despite failed verdicts)
- Don't dispatch complex multi-file tasks — break into single-function edits
- Don't skip the pre-flight on first cycle
- Don't poll background tasks in a tight loop — set `sleep 300-600` with `run_in_background: true` and wait for notification
- Don't dispatch tasks targeting the same file concurrently — they will conflict
