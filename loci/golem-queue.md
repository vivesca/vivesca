### Pending (deduped 2026-04-02)

- [ ] `golem [t-A1B2] -b zhipu Scan metabolon/ for duplicated path/config resolution patterns beyond -Users-terry. Extract shared utilities into morphology.base (or new module). Scope: grep for Path.home() patterns, hardcoded dirs, repeated env lookups. Deliverable: PR with shared helpers + callsite migrations + passing tests.`































































































































































































### Architecture audit P2 (2026-04-02)
































































### Mitogen batch — golem monitoring suite repair (2026-04-02 08:00)

#### Fix operon — golem-tools @dataclass collection crash (dash, report, top)
Three test files crash at collection because `exec(golem-tools-source, ns)` fails on `@dataclass` decorators — `HealthResult` class at line ~144 of effectors/golem-tools. The exec namespace doesn't resolve dataclass field annotations properly (NoneType.__dict__ error). Fix the loader pattern in all three test files. The fix is: add `ns["__builtins__"] = __builtins__` before exec, OR restructure `_load_golem_*()` to handle the @dataclass. Verify all three pass.

#### Fix operon — golem-health tests (15 failures)

#### Fix operon — golem-validate tests (10 failures)

#### Fix — golem-review tests (4 failures)

#### Fix — golem-reviewer tests (2 failures — missing `run` function)

#### Sweep — find remaining broken test files






### Mitogen batch — golem monitoring suite repair (2026-04-02 08:05)

#### Fix operon — golem-tools @dataclass collection crash

#### Fix operon — golem-health tests (15 failures)

#### Fix operon — golem-validate tests (10 failures)

#### Fix — golem-review tests (4 failures)

#### Fix — golem-reviewer tests (2 failures)

#### Sweep — find remaining broken test files




























































### Mitogen batch 2 — core module fixes (2026-04-02 08:15)

#### Fix operon — translocon + hemostasis (dispatch pipeline)

#### Fix operon — monitoring (interoception + phenotype_translate)

#### Fix — methylation_review (3 failures)

#### Fix — pinocytosis + queue_gen + golem_daemon (1 failure each)



































### Mitogen batch 3 — broader fixes + monitoring re-attempt (2026-04-02 08:30)

#### Fix operon — golem monitoring suite (retry with max-turns 50)
Previous golems attempted fixes but tests still fail. Giving more turns and clearer diagnosis context.

#### Fix — replisome (4 failures)

#### Fix operon — consulting tools (regulatory_scan + capco_brief + card_search)

#### Fix — pulse_review (1 fail + 10 errors)

#### Fix — test_fixer errors





### Auto-requeue (2 tasks @ 09:27)



### Mitogen batch — System hardening + Capco readiness (2026-04-02 09:30)

#### Fix operon — Critical failures

#### Build operon — New capabilities

#### Fix operon — Code quality

#### Test operon — Critical gaps

### Auto-requeue (2 tasks @ 09:29)

### Auto-requeue (2 tasks @ 09:30)

### Auto-requeue (2 tasks @ 09:30)
















### Build — temporal-golem feature parity with golem-daemon (2026-04-02 09:50)

#### Build — add QueueLock and rate-limit cooldowns to temporal-dispatch

### Auto-requeue (10 tasks @ 09:50)

### Auto-requeue (5 tasks @ 09:56)

### Auto-requeue (4 tasks @ 09:57)

### Reliability — pre-Capco hardening (2026-04-02)

#### Fix — calendar CLI on soma

#### Fix — stale epigenome marks batch cleanup

#### Fix — soma disk: clean golem output history


### Auto-requeue (4 tasks @ 09:58)

### Reliability fixes — system check findings (2026-04-02)

#### Fix — golem-tools doubled function name

#### Fix — delete duplicate test file

#### Fix — integrin PermissionError on docker-data

#### Build — install missing Rust CLIs on soma


### Auto-requeue (4 tasks @ 09:59)

### Auto-requeue (4 tasks @ 09:59)

### Auto-requeue (3 tasks @ 10:00)

### Auto-requeue (3 tasks @ 10:01)

### Auto-requeue (4 tasks @ 10:01)

### Auto-requeue (4 tasks @ 10:03)

### Auto-requeue (4 tasks @ 10:06)

### Auto-requeue (3 tasks @ 10:09)

### Auto-requeue (3 tasks @ 10:11)

### Auto-requeue (2 tasks @ 10:14)

### Auto-requeue (3 tasks @ 10:17)

### Auto-requeue (3 tasks @ 10:21)

### Auto-requeue (3 tasks @ 10:32)

### Auto-requeue (3 tasks @ 10:34)

### Auto-requeue (3 tasks @ 10:37)

### Auto-requeue (3 tasks @ 10:41)

### Auto-requeue (4 tasks @ 10:42)

### Auto-requeue (4 tasks @ 10:43)

### Auto-requeue (3 tasks @ 10:45)

### Auto-requeue (3 tasks @ 10:48)

### Auto-requeue (4 tasks @ 10:49)

### Auto-requeue (3 tasks @ 10:50)

### Auto-requeue (2 tasks @ 10:52)

### Auto-requeue (3 tasks @ 10:53)

### Auto-requeue (3 tasks @ 10:54)

### Auto-requeue (2 tasks @ 10:56)

### Auto-requeue (2 tasks @ 10:59)

### Auto-requeue (2 tasks @ 11:00)

### Auto-requeue (2 tasks @ 11:01)

### Auto-requeue (3 tasks @ 11:02)

### Auto-requeue (2 tasks @ 11:04)

### Auto-requeue (2 tasks @ 11:06)

### Auto-requeue (2 tasks @ 11:08)

### Auto-requeue (2 tasks @ 11:08)

### Auto-requeue (2 tasks @ 11:11)

### Auto-requeue (2 tasks @ 11:12)

### Auto-requeue (2 tasks @ 11:13)

### Auto-requeue (2 tasks @ 11:15)

### Auto-requeue (2 tasks @ 11:15)

### Auto-requeue (2 tasks @ 11:16)

### Auto-requeue (2 tasks @ 11:18)

### Auto-requeue (2 tasks @ 11:18)

### Auto-requeue (2 tasks @ 11:20)

### Auto-requeue (2 tasks @ 11:23)

### Auto-requeue (2 tasks @ 11:23)

### Auto-requeue (2 tasks @ 11:24)

### Auto-requeue (2 tasks @ 11:25)

### Auto-requeue (2 tasks @ 11:26)

### Auto-requeue (2 tasks @ 11:27)

### Auto-requeue (2 tasks @ 11:31)

### Auto-requeue (2 tasks @ 11:32)

### Auto-requeue (2 tasks @ 11:33)

### Auto-requeue (2 tasks @ 11:35)

### Auto-requeue (2 tasks @ 11:37)

### Auto-requeue (2 tasks @ 11:38)

### Auto-requeue (2 tasks @ 11:40)

### Auto-requeue (2 tasks @ 11:42)

### Auto-requeue (2 tasks @ 11:45)

### Auto-requeue (2 tasks @ 11:47)

### Auto-requeue (2 tasks @ 11:48)

### Auto-requeue (2 tasks @ 11:52)

### Auto-requeue (2 tasks @ 11:53)

### Auto-requeue (2 tasks @ 11:54)

### Auto-requeue (2 tasks @ 11:55)

### Auto-requeue (2 tasks @ 11:56)

### Auto-requeue (2 tasks @ 11:57)

### Auto-requeue (2 tasks @ 11:59)

### Auto-requeue (2 tasks @ 12:01)

### Auto-requeue (2 tasks @ 12:01)

### Auto-requeue (2 tasks @ 12:03)

### Auto-requeue (2 tasks @ 12:06)

### Auto-requeue (2 tasks @ 12:06)

### Auto-requeue (2 tasks @ 12:07)

### Auto-requeue (2 tasks @ 12:08)

### Auto-requeue (2 tasks @ 12:09)

### Auto-requeue (2 tasks @ 12:09)

### Auto-requeue (2 tasks @ 12:11)

### Auto-requeue (2 tasks @ 12:12)

### Auto-requeue (2 tasks @ 12:14)

### Auto-requeue (2 tasks @ 12:15)

### Auto-requeue (2 tasks @ 12:17)

### Auto-requeue (2 tasks @ 12:18)

### Auto-requeue (2 tasks @ 12:20)

### Auto-requeue (2 tasks @ 12:22)

### Auto-requeue (2 tasks @ 12:23)

### Auto-requeue (2 tasks @ 12:24)

### Auto-requeue (2 tasks @ 12:26)

### Auto-requeue (2 tasks @ 12:28)

### Auto-requeue (2 tasks @ 12:29)

### Auto-requeue (2 tasks @ 12:29)

### Auto-requeue (2 tasks @ 12:30)

### Auto-requeue (2 tasks @ 12:31)

### Auto-requeue (2 tasks @ 12:34)

### Auto-requeue (2 tasks @ 12:36)

### Auto-requeue (2 tasks @ 12:37)

### Auto-requeue (2 tasks @ 12:38)

### Auto-requeue (2 tasks @ 12:38)

### Auto-requeue (2 tasks @ 12:39)

### Auto-requeue (2 tasks @ 12:39)

### Auto-requeue (2 tasks @ 12:40)

### Auto-requeue (2 tasks @ 12:40)

### Auto-requeue (2 tasks @ 12:41)

### Auto-requeue (2 tasks @ 12:41)

### Auto-requeue (2 tasks @ 12:42)

### Auto-requeue (2 tasks @ 12:43)

### Auto-requeue (2 tasks @ 12:43)

### Auto-requeue (2 tasks @ 12:44)

### Auto-requeue (2 tasks @ 12:44)

### Auto-requeue (2 tasks @ 12:45)

### Auto-requeue (2 tasks @ 12:45)

### Auto-requeue (2 tasks @ 12:46)

### Auto-requeue (2 tasks @ 12:46)

### Auto-requeue (2 tasks @ 12:47)

### Auto-requeue (2 tasks @ 12:49)

### Auto-requeue (2 tasks @ 12:50)

### Auto-requeue (2 tasks @ 12:50)

### Auto-requeue (2 tasks @ 12:51)

### Auto-requeue (2 tasks @ 12:51)

### Auto-requeue (2 tasks @ 12:53)

### Auto-requeue (2 tasks @ 12:54)

### Auto-requeue (2 tasks @ 12:54)

### Auto-requeue (2 tasks @ 12:56)

### Auto-requeue (2 tasks @ 12:57)

### Auto-requeue (2 tasks @ 13:02)

### Auto-requeue (2 tasks @ 13:04)

### Auto-requeue (2 tasks @ 13:07)

### Auto-requeue (2 tasks @ 13:08)

### Auto-requeue (2 tasks @ 13:10)

### Auto-requeue (2 tasks @ 13:11)

### Auto-requeue (2 tasks @ 13:13)

### Auto-requeue (2 tasks @ 13:18)

### Auto-requeue (2 tasks @ 13:18)

### Auto-requeue (2 tasks @ 13:19)

### Auto-requeue (2 tasks @ 13:21)

### Auto-requeue (2 tasks @ 13:22)

### Auto-requeue (2 tasks @ 13:24)

### Auto-requeue (2 tasks @ 13:28)

### Auto-requeue (2 tasks @ 13:29)

### Auto-requeue (2 tasks @ 13:32)

### Auto-requeue (2 tasks @ 13:36)

### Auto-requeue (2 tasks @ 13:37)

### Auto-requeue (2 tasks @ 13:48)

### Auto-requeue (2 tasks @ 13:50)

### Auto-requeue (2 tasks @ 13:52)

### Auto-requeue (2 tasks @ 13:54)

### Auto-requeue (2 tasks @ 13:57)

### Auto-requeue (2 tasks @ 13:59)

### Auto-requeue (2 tasks @ 14:02)

### Auto-requeue (2 tasks @ 14:03)

### Auto-requeue (2 tasks @ 14:04)

### Auto-requeue (2 tasks @ 14:08)

### Auto-requeue (2 tasks @ 14:11)

### Auto-requeue (2 tasks @ 14:14)

### Auto-requeue (2 tasks @ 14:16)

### Auto-requeue (2 tasks @ 14:20)

### Auto-requeue (2 tasks @ 14:20)

### Auto-requeue (2 tasks @ 14:21)

### Auto-requeue (2 tasks @ 14:24)

### Auto-requeue (2 tasks @ 14:29)

### Auto-requeue (2 tasks @ 14:29)

### Auto-requeue (2 tasks @ 14:31)

### Auto-requeue (2 tasks @ 14:33)

### Auto-requeue (2 tasks @ 14:35)

### Auto-requeue (2 tasks @ 14:37)

### Auto-requeue (2 tasks @ 14:40)

### Auto-requeue (2 tasks @ 14:47)

### Auto-requeue (2 tasks @ 14:49)

### Auto-requeue (2 tasks @ 14:51)

### Auto-requeue (2 tasks @ 15:00)

### Auto-requeue (2 tasks @ 15:05)

### Auto-requeue (2 tasks @ 15:06)

### Auto-requeue (2 tasks @ 15:07)

### Auto-requeue (2 tasks @ 15:13)

### Auto-requeue (2 tasks @ 15:14)

### Auto-requeue (2 tasks @ 15:16)

### Auto-requeue (2 tasks @ 15:18)

### Auto-requeue (2 tasks @ 15:24)

### Auto-requeue (2 tasks @ 15:26)

### Auto-requeue (2 tasks @ 15:32)

### Auto-requeue (2 tasks @ 15:33)

### Auto-requeue (2 tasks @ 15:39)

### Auto-requeue (2 tasks @ 15:45)

### Auto-requeue (2 tasks @ 15:49)

### Auto-requeue (2 tasks @ 15:54)

### Auto-requeue (2 tasks @ 15:55)

### Auto-requeue (2 tasks @ 16:06)

### Auto-requeue (2 tasks @ 16:07)

### Auto-requeue (2 tasks @ 16:08)

### Auto-requeue (2 tasks @ 16:13)

### Auto-requeue (2 tasks @ 16:17)

### Auto-requeue (2 tasks @ 16:22)


### Auto-requeue (2 tasks @ 16:30)

### Auto-requeue (2 tasks @ 16:30)

### Auto-requeue (2 tasks @ 16:31)

### Auto-requeue (2 tasks @ 16:32)

### Auto-requeue (2 tasks @ 16:32)

### Auto-requeue (2 tasks @ 16:33)

### Auto-requeue (2 tasks @ 16:33)

### Auto-requeue (2 tasks @ 16:34)

### Auto-requeue (2 tasks @ 16:34)

### Auto-requeue (2 tasks @ 16:35)

### Auto-requeue (2 tasks @ 16:35)

### Auto-requeue (2 tasks @ 16:36)

### Auto-requeue (2 tasks @ 16:36)

### Auto-requeue (2 tasks @ 16:37)

### Auto-requeue (2 tasks @ 16:38)

### Auto-requeue (2 tasks @ 16:38)

### Auto-requeue (2 tasks @ 16:39)

### Auto-requeue (2 tasks @ 16:39)

### Auto-requeue (2 tasks @ 16:40)

### Auto-requeue (2 tasks @ 16:40)

### Auto-requeue (2 tasks @ 16:41)

### Auto-requeue (2 tasks @ 16:41)

### Auto-requeue (2 tasks @ 16:42)

### Auto-requeue (2 tasks @ 16:42)

### Auto-requeue (2 tasks @ 16:43)

### Auto-requeue (2 tasks @ 16:43)

### Auto-requeue (2 tasks @ 16:44)

### Auto-requeue (2 tasks @ 16:44)

### Auto-requeue (2 tasks @ 16:50)

### Auto-requeue (2 tasks @ 16:52)

### Auto-requeue (2 tasks @ 16:55)

### Auto-requeue (2 tasks @ 17:00)

### Auto-requeue (2 tasks @ 17:02)

### Auto-requeue (2 tasks @ 17:06)

### Auto-requeue (2 tasks @ 17:06)

### Auto-requeue (2 tasks @ 17:10)

### Auto-requeue (2 tasks @ 17:17)

### Auto-requeue (2 tasks @ 17:20)

### Auto-requeue (2 tasks @ 17:21)

### Auto-requeue (2 tasks @ 17:26)

### Auto-requeue (2 tasks @ 17:27)

### Auto-requeue (2 tasks @ 17:36)

### Auto-requeue (2 tasks @ 17:37)

### Auto-requeue (2 tasks @ 17:47)

### Auto-requeue (2 tasks @ 17:51)

### Auto-requeue (2 tasks @ 17:52)

### Auto-requeue (2 tasks @ 17:55)

### Auto-requeue (2 tasks @ 17:55)

### Auto-requeue (2 tasks @ 17:57)

### Auto-requeue (2 tasks @ 18:00)

### Auto-requeue (2 tasks @ 18:01)

### Auto-requeue (2 tasks @ 18:03)

### Auto-requeue (2 tasks @ 18:06)

### Auto-requeue (2 tasks @ 18:12)

### Auto-requeue (2 tasks @ 18:15)

### Auto-requeue (2 tasks @ 18:16)

### Auto-requeue (2 tasks @ 18:22)

### Auto-requeue (2 tasks @ 18:22)

### Auto-requeue (2 tasks @ 18:25)

### Auto-requeue (2 tasks @ 18:27)

### Auto-requeue (2 tasks @ 18:27)

### Auto-requeue (2 tasks @ 18:31)

### Auto-requeue (2 tasks @ 18:39)

### Auto-requeue (2 tasks @ 18:41)

### Auto-requeue (2 tasks @ 18:43)

### Auto-requeue (2 tasks @ 18:43)

### Auto-requeue (2 tasks @ 18:44)

### Auto-requeue (2 tasks @ 18:46)

### Auto-requeue (2 tasks @ 18:48)

### Auto-requeue (2 tasks @ 18:51)

### Auto-requeue (2 tasks @ 18:55)

### Auto-requeue (2 tasks @ 18:57)

### Auto-requeue (2 tasks @ 18:59)

### Auto-requeue (2 tasks @ 19:05)

### Auto-requeue (2 tasks @ 19:06)

### Auto-requeue (2 tasks @ 19:07)

### Auto-requeue (2 tasks @ 19:08)

### Auto-requeue (2 tasks @ 19:10)

### Auto-requeue (2 tasks @ 19:14)

### Auto-requeue (2 tasks @ 19:16)

### Auto-requeue (2 tasks @ 19:16)

### Auto-requeue (2 tasks @ 19:17)

### Auto-requeue (2 tasks @ 19:20)

### Auto-requeue (2 tasks @ 19:21)

### Auto-requeue (2 tasks @ 19:24)

### Auto-requeue (2 tasks @ 19:25)

### Auto-requeue (2 tasks @ 19:29)

### Auto-requeue (2 tasks @ 19:34)

### Auto-requeue (2 tasks @ 19:36)

### Auto-requeue (2 tasks @ 19:37)

### Auto-requeue (2 tasks @ 19:39)

### Auto-requeue (2 tasks @ 19:40)

### Auto-requeue (2 tasks @ 19:44)

### Auto-requeue (2 tasks @ 19:47)

### Auto-requeue (2 tasks @ 19:50)

#### Refactor judge → CC headless

### Auto-requeue (2 tasks @ 19:56)

### Auto-requeue (2 tasks @ 19:57)

### Auto-requeue (2 tasks @ 20:03)

### Auto-requeue (2 tasks @ 20:06)
- [ ] `golem --max-turns 30 "Enhance golem analytics. Three changes to ~/germline/effectors/golem and ~/germline/effectors/golem-daemon:

1. REPLACE golem summary (lines 44-125 of ~/germline/effectors/golem) with a call to golem-daemon stats. The current inline Python is redundant — golem-daemon already has richer analytics (rate-limit vs real-fail, build/maint breakdown, capability %). Replace _run_summary() body to just exec golem-daemon stats with the same args forwarded. Delete the inline Python.

2. ADD 'golem summary --failed' flag. In golem-daemon cmd_stats(), when --failed is in args: after printing the permanently failed task IDs, also print each one's prompt snippet (first 100 chars of cmd field from JSONL) and last error (tail field, last 100 chars). Data source: match perma_failed_ids against records by task_id.

3. ADD 'golem summary --trend [Nd]' flag. In golem-daemon cmd_stats(), when --trend is in args: group records by date (from ts field), show daily table: date | total | passed | rate-limited | real-fail | capability%. Default 7d. Simple ASCII table.

Test: run golem summary, golem summary --failed, golem summary --trend after changes. All must produce output without errors."`

### Auto-requeue (2 tasks @ 20:17)
- [ ] `golem --max-turns 30 "Add a productivity metric to golem-daemon stats. In ~/germline/effectors/golem-daemon cmd_stats() (around line 2250), after loading records from JSONL:

1. For each passed task (exit==0), check if it produced a commit by looking for a git commit hash pattern (7+ hex chars) in the tail field, OR check if files_created > 0. Count these as 'productive'. Passed tasks with no commit hash in tail AND files_created==0 are 'no-op passes'.

2. Add to the stats output after the total line: 'Productive passes: N/M (X%) — no-op passes: Y'. This tells us what fraction of passes actually shipped something.

3. In the per-provider table, add a 'productive' column showing productive count per provider.

Test: run golem-daemon stats and verify the new fields appear. The numbers should be plausible (productive < passed, no-ops > 0)."`

### Auto-requeue (2 tasks @ 20:18)

### Auto-requeue (2 tasks @ 20:20)

### Auto-requeue (2 tasks @ 20:20)

### Auto-requeue (2 tasks @ 20:21)

### Auto-requeue (2 tasks @ 20:21)

### Auto-requeue (2 tasks @ 20:22)

### Auto-requeue (2 tasks @ 20:23)

### Auto-requeue (2 tasks @ 20:23)

### Auto-requeue (2 tasks @ 20:24)

### Auto-requeue (2 tasks @ 20:25)

### Auto-requeue (2 tasks @ 20:25)

### Auto-requeue (2 tasks @ 20:26)

### Auto-requeue (2 tasks @ 20:26)

### Auto-requeue (2 tasks @ 20:27)

### Auto-requeue (2 tasks @ 20:27)

### Auto-requeue (2 tasks @ 20:28)

### Auto-requeue (2 tasks @ 20:29)

### Auto-requeue (2 tasks @ 20:29)

### Auto-requeue (2 tasks @ 20:30)

### Auto-requeue (2 tasks @ 20:30)

### Auto-requeue (2 tasks @ 20:31)

### Auto-requeue (2 tasks @ 20:31)

### Auto-requeue (2 tasks @ 20:32)

### Auto-requeue (2 tasks @ 20:32)

### Auto-requeue (2 tasks @ 20:33)

### Auto-requeue (2 tasks @ 20:34)

### Auto-requeue (2 tasks @ 20:42)

### Auto-requeue (2 tasks @ 20:43)

### Auto-requeue (2 tasks @ 20:43)

### Auto-requeue (2 tasks @ 20:44)

### Auto-requeue (2 tasks @ 20:45)

### Auto-requeue (2 tasks @ 20:45)

### Auto-requeue (2 tasks @ 20:48)

### Auto-requeue (2 tasks @ 20:49)

### Auto-requeue (2 tasks @ 20:51)

### Auto-requeue (2 tasks @ 20:54)

### Auto-requeue (2 tasks @ 20:55)

### Auto-requeue (2 tasks @ 20:56)

### Auto-requeue (2 tasks @ 20:57)

### Auto-requeue (2 tasks @ 21:02)

### Auto-requeue (2 tasks @ 21:05)

### Auto-requeue (2 tasks @ 21:06)

### Auto-requeue (2 tasks @ 21:09)

### Auto-requeue (2 tasks @ 21:09)

### Auto-requeue (2 tasks @ 21:11)

### Auto-requeue (2 tasks @ 21:11)

### Auto-requeue (2 tasks @ 21:13)

### Auto-requeue (2 tasks @ 21:14)

### Auto-requeue (2 tasks @ 21:14)

### Auto-requeue (2 tasks @ 21:22)

### Auto-requeue (2 tasks @ 21:23)

### Auto-requeue (2 tasks @ 21:24)

### Auto-requeue (2 tasks @ 21:24)

### Auto-requeue (2 tasks @ 21:25)

### Auto-requeue (2 tasks @ 21:26)

### Auto-requeue (2 tasks @ 21:27)

### Auto-requeue (2 tasks @ 21:28)

### Auto-requeue (2 tasks @ 21:28)

### Auto-requeue (2 tasks @ 21:29)

### Auto-requeue (2 tasks @ 21:30)

### Auto-requeue (2 tasks @ 21:31)

### Auto-requeue (2 tasks @ 21:56)

### Auto-requeue (2 tasks @ 21:57)

### Auto-requeue (2 tasks @ 21:59)
