### Pending (deduped 2026-04-02)
- [x] `golem [t-6443f1] --provider zhipu --max-turns 40 "Modify ~/germline/effectors/golem-daemon to add SSH-based remote worker overflow to ganglion. READ the full file first. Changes: (1) Add REMOTE_WORKERS config near top: [{"host": "ganglion", "user": "ubuntu", "max_concurrent": 2}]. (2) Add remote_exec() that runs via ssh -o ConnectTimeout=5 ubuntu@ganglion docker run --rm gemmule:latest bash -c ... with same stdout/stderr/exit capture as local. On SSH fail, re-mark pending. (3) In task pickup loop: if local_running >= MAX_LOCAL and remote has capacity, route there. Track in golem-running.json with node field. (4) Append [ganglion] or [soma] to completion lines. (5) Add ssh health check before remote dispatch — skip worker if unreachable. (6) Add --dry-run flag that logs routing decisions without executing. Do NOT change queue format or locking. No new files. No new deps."`

































































































































































































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
- [x] `golem [t-2e2dd5] --provider codex --max-turns 50 "assays/test_golem_reviewer.py: 2 fail / 10 pass. test_all_expected_functions_present expects a 'run' function. Read effectors/golem-reviewer, list all def/function names, update the expected list in the test. Also fix test_golem_review.py (4 fail / 46 pass) — same approach. Commit both."`

#### Fix — replisome (4 failures)

#### Fix operon — consulting tools (regulatory_scan + capco_brief + card_search)
- [x] `golem [t-f47173] --provider volcano --max-turns 30 "Three consulting effector tests have failures: (1) assays/test_regulatory_scan.py — 1 fail + 3 errors. (2) assays/test_capco_brief.py — 1 fail + 5 errors. (3) assays/test_card_search.py — 2 fail. For each: run pytest -v --tb=short, read test + source, fix. Commit. (retry)"`

#### Fix — pulse_review (1 fail + 10 errors)
- [x] `golem [t-76a037] --provider codex --max-turns 30 "assays/test_pulse_review.py: 1 fail + 10 errors / 5 pass. Run uv run pytest assays/test_pulse_review.py -v --tb=short. Read test + effectors/pulse-review. The 10 errors suggest import or fixture issues. Fix. Commit."`

#### Fix — test_fixer errors





### Auto-requeue (2 tasks @ 09:27)
- [x] `golem [t-8f861f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`



### Mitogen batch — System hardening + Capco readiness (2026-04-02 09:30)

#### Fix operon — Critical failures
- [!] `golem [t-f40380] --provider codex --max-turns 30 "Run uv run pytest --co -q 2>&1 | grep ERROR | head -20. Count total collection errors. For the first 10 unique files with errors: read the file, diagnose (usually bad import, syntax, or hardcoded path), fix. Run --co again. Target: reduce collection errors by 50%+. Commit. (retry)"`
- [!] `golem [t-8bb69e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on just that file, read the traceback, fix the root cause. Iterate until each file is green. Commit. (retry)"`

#### Build operon — New capabilities
- [x] `golem [t-6352e9] --provider infini --max-turns 50 "Create effectors/consulting-card as a Python CLI script with uv inline metadata. Features: (1) --topic 'AI incident response' --output path/to/card.md, (2) reads a YAML template from stdin or uses a default structure: problem (2 sentences), why-it-matters (3 bullets), approach (numbered steps), considerations, Capco angle, (3) generates the markdown skeleton with TODO placeholders for each section, (4) --list to search existing cards in ~/epigenome/chromatin/euchromatin/consulting/cards/. Write tests in assays/test_consulting_card.py. Run uv run pytest assays/test_consulting_card.py. Commit."`
- [x] `golem [t-d0938f] --provider codex --max-turns 40 "Create effectors/soma-status as a Python CLI script. It combines: (1) supervisorctl status output (parse each program's state), (2) python3 effectors/golem-daemon stats (parse provider lines), (3) df -h / (disk usage), (4) uptime, (5) free -h (memory). Output a clean single-screen summary with sections. Add --json flag for machine-readable output. Write tests in assays/test_soma_status.py. Run pytest. Commit."`
- [x] `golem [t-674c15] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a --export-stats flag that outputs the stats as JSON to stdout (provider name, total, passed, failed, rate_limited, real_fail, capability_pct). This makes it parseable by other tools. Write tests for the new flag in assays/test_golem_daemon.py (append, don't overwrite). Run pytest on the file. Commit."`
- [x] `golem [t-779d0e] --provider infini --max-turns 30 "Read effectors/nightly. Add --json flag that outputs the health check results as JSON array of objects with fields: component, status, details. Currently it outputs a table — add JSON as alternative format. Write tests for the new flag. Run pytest assays/test_nightly.py. Commit."`

#### Fix operon — Code quality
- [!] `golem [t-5683af] --provider codex --max-turns 25 "Run: for f in effectors/*; do timeout 5 python3 \$f --help >/dev/null 2>&1 || echo CRASH: \$f; done 2>/dev/null. For each crasher that is a Python script: read it, fix the --help crash (usually missing argparse or bad import). Skip shell scripts and non-executable files. Commit. (retry)"`
- [x] `golem [t-7f465e] --provider zhipu --max-turns 25 "Search assays/ for hardcoded '/Users/' paths: grep -rn '/Users/' assays/. Replace each occurrence with Path.home() or a platform-independent equivalent. Also check for '/home/terry' hardcoded paths in test expectations (not in tmp_path usage). Commit."`
- [x] `golem [t-3eed3b] --provider infini --max-turns 25 "Run: python3 -c 'import ast, sys, glob; [print(f) for f in sorted(glob.glob(\"metabolon/*.py\")) if not f.endswith(\"__init__.py\") for node in ast.walk(ast.parse(open(f).read())) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom) for alias in (node.names if isinstance(node, ast.Import) else [type(\"obj\",(),{\"name\":node.module})]()) if alias.name and not __import__(\"importlib\").util.find_spec(alias.name.split(\".\")[0])]' 2>&1 | head -20. Find dead/broken imports in metabolon/. Fix or remove them. Commit."`

#### Test operon — Critical gaps
- [x] `golem [t-f43054] --provider zhipu --max-turns 40 "Write tests for effectors/temporal-golem/dispatch.py. Read the source first to understand what it does (polls golem-queue.md, dispatches tasks). Test the parsing, task extraction, and dispatch logic with mocked subprocess calls. Write to assays/test_temporal_dispatch.py. Run uv run pytest assays/test_temporal_dispatch.py -v --tb=short. Fix failures. Commit."`
- [x] `golem [t-98b934] --provider infini --max-turns 30 "Write tests for effectors/coverage-map. Read the source first. Test CLI args, output format, and edge cases. Write to assays/test_coverage_map.py. Run uv run pytest assays/test_coverage_map.py -v --tb=short. Fix failures. Commit."`
- [x] `golem [t-0969d8] --provider codex --max-turns 30 "Write tests for effectors/golem-dash. Read the source first. Test CLI args, output parsing, and display logic. Write to assays/test_golem_dash.py. Run uv run pytest assays/test_golem_dash.py -v --tb=short. Fix failures. Commit. (retry)"`

### Auto-requeue (2 tasks @ 09:29)
- [x] `golem [t-209a59] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-df5429] --provider volcano --max-turns 30 "Health check: vesicle, nightly, chromatin-backup.sh, coaching-stats, queue-balance, conftest-gen, centrosome, oura-weekly-digest.py, oci-arm-retry, oci-region-subscribe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 09:30)
- [x] `golem [t-4b8c52] --provider zhipu --max-turns 30 "Health check: perplexity.sh, immunosurveillance, golem, client-brief, publish, chromatin-backup.py, golem-reviewer, find, safe_rm.py, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 09:30)
- [x] `golem [t-cae9e3] --provider volcano --max-turns 30 "Health check: linkedin-monitor, efferens, backfill-marks, importin, inflammasome-probe, golem-health, channel, mitosis-checkpoint.py, soma-activate, poiesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
















### Build — temporal-golem feature parity with golem-daemon (2026-04-02 09:50)

#### Build — add QueueLock and rate-limit cooldowns to temporal-dispatch
- [x] `golem [t-a0c377] --provider zhipu --max-turns 50 "Upgrade effectors/temporal-golem/dispatch.py to match golem-daemon's operational features. Read effectors/golem-daemon lines 166-180 (QueueLock class using fcntl.flock on ~/.local/share/vivesca/golem-queue.lock) and lines 180-200 (TASK_ID_RE, rate limit patterns). Then read the current dispatch.py. Add these features: (1) Use QueueLock (same lock file) around ALL queue file reads and writes — import fcntl, copy the QueueLock class from golem-daemon. (2) Add per-provider concurrency tracking — match golem-daemon's PROVIDER_LIMITS dict. (3) Add rate-limit cooldown tracking — when a task fails with rate-limit error, set a cooldown timer for that provider and skip dispatching to it until cooldown expires. (4) Generate task IDs for entries that lack them (same t-XXXXXX format as golem-daemon). Run uv run pytest assays/test_temporal_golem.py if it exists. Commit. (retry)"`

### Auto-requeue (10 tasks @ 09:50)
- [x] `golem [t-4961ae] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit. (retry)"`
- [x] `golem [t-6bb74c] --provider infini --max-turns 40 "Run git log --oneline --since='24 hours ago' --author=golem | head -10. For each commit: git show <hash> --stat. Pick the 3 largest diffs. For each: read the changed file, check for assert True stubs, empty functions, broken logic, missing error handling. Fix issues. Run uv run pytest on affected files. Commit."`
- [x] `golem [t-220771] --provider volcano --max-turns 30 "Run uv run ruff check metabolon/ --select E,W,F --output-format=concise 2>&1 | head -30. Fix the first 15 issues. Run ruff check again to verify. Commit."`
- [x] `golem [t-f74b5d] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_templates.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_templates.py -v --tb=short. Commit."`
- [x] `golem [t-8ae11b] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_chromatin_stats.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_chromatin_stats.py -v --tb=short. Commit."`
- [x] `golem [t-3428b1] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_parsers_hsbc.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_hsbc.py -v --tb=short. Commit."`
- [x] `golem [t-5a31d5] --provider volcano --max-turns 35 "Read /home/terry/germline/metabolon/organelles/telegram_auth.py carefully first. Write assays/test_organelles_telegram_auth.py with tests for every public function. No assert True placeholders — test real behavior. Run uv run pytest assays/test_organelles_telegram_auth.py -v --tb=short. Commit."`
- [x] `golem [t-2574a2] --provider zhipu --max-turns 25 "Run uv run ruff check metabolon/ --select F401,F841 --output-format=concise 2>&1 | head -20. These are unused imports (F401) and unused variables (F841). Fix all of them. Run ruff check again. Commit."`

### Auto-requeue (5 tasks @ 09:56)
- [x] `golem [t-3ef112] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_substrates_memory.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_memory.py -v --tb=short. Commit."`
- [x] `golem [t-48ddcf] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_ecdysis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ecdysis.py -v --tb=short. Commit."`
- [x] `golem [t-addd89] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_emit.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_emit.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 09:57)
- [x] `golem [t-47d553] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7c2b51] --provider zhipu --max-turns 30 "Health check: browser, wacli-ro, hkicpa, replisome, golem-daemon, poiesis, golem-orchestrator, channel, start-chrome-debug.sh, rename-kindle-asins.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-e6b054] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test___init__.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test___init__.py -v --tb=short. Commit."`
- [x] `golem [t-ca9c48] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_substrates_vasomotor.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_vasomotor.py -v --tb=short. Commit."`

### Reliability — pre-Capco hardening (2026-04-02)

#### Fix — calendar CLI on soma
- [x] `golem [t-f95e10] --provider zhipu --max-turns 40 "The fasti CLI (effectors/fasti) wraps gog for Google Calendar. On soma (Fly.io), gog only has the gmail subcommand — calendar is missing. Read effectors/fasti to understand what gog calendar commands it uses. Read effectors/gog to understand why calendar subcommand is missing on soma. Either: (a) fix gog to include calendar on soma, or (b) make fasti use the Google Calendar API directly via the existing OAuth creds. Test that 'fasti today' works. Commit. (retry)"`

#### Fix — stale epigenome marks batch cleanup
- [x] `golem [t-00a18c] --provider zhipu --max-turns 50 "In ~/epigenome/marks/, there are ~86 memory files with stale path references pointing to moved or deleted files. Run: grep -rl 'germline/scripts\|~/scripts\|~/bin/' ~/epigenome/marks/ to find them. For each: read the file, check if the referenced path exists, update to the correct current path (likely ~/germline/effectors/ or ~/germline/metabolon/). If the entire memory is obsolete (references something that no longer exists and has no other value), move it to ~/epigenome/marks/Archive/. Commit changes to both repos."`

#### Fix — soma disk: clean golem output history
- [x] `golem [t-cea629] --provider zhipu --max-turns 25 "Free disk space on soma. Run df -h / to confirm current usage. Then: (1) Clean completed golem outputs older than 7 days: find ~/germline/loci/golem-output/ -name '*.md' -mtime +7 -delete 2>/dev/null. (2) Clean old pytest cache: find ~/germline -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null. (3) Run git gc --aggressive in ~/germline. (4) Clean pip/uv cache: uv cache clean. Report df -h / before and after. Commit if any code changed."`


### Auto-requeue (4 tasks @ 09:58)
- [x] `golem [t-efd999] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bc4a5e] --provider infini --max-turns 30 "Health check: express, golem-dash, cookie-sync, golem-daemon-wrapper.sh, soma-snapshot, perplexity.sh, assay, replisome, tm, porta. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-0e5038] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_consolidation.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_consolidation.py -v --tb=short. Commit."`
- [x] `golem [t-e907ea] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_parsers_boc.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_boc.py -v --tb=short. Commit."`

### Reliability fixes — system check findings (2026-04-02)

#### Fix — golem-tools doubled function name
- [x] `golem [t-a2d61c] --provider zhipu --max-turns 20 "In effectors/golem-tools, line 388 has a function named report_report_load_jsonl (doubled prefix). Rename it to report_load_jsonl. Also check line 543 for the internal call. Fix both. Run uv run pytest assays/test_golem_report.py. Commit."`

#### Fix — delete duplicate test file
- [!] `golem [t-cc9b32] --provider zhipu --max-turns 10 "Delete ~/germline/assays/test_backup_due.sh.py (keep test_backup_due_sh.py). Run uv run pytest --co -q 2>&1 | grep ERROR | head -5 to verify no collection errors from this. Commit. (retry)"`

#### Fix — integrin PermissionError on docker-data
- [x] `golem [t-c38f8c] --provider zhipu --max-turns 30 "Read effectors/integrin. It crashes with PermissionError on /home/terry/.docker-data/settings.json during MCP dispatch. The _KNOWN_PLATFORM_DIRS skip at line 125 should catch .docker-data but the error surfaces through membrane.py MCP layer before that guard. Add a broader try/except PermissionError around the scan path. Test by running: python3 effectors/integrin --help. Commit."`

#### Build — install missing Rust CLIs on soma
- [x] `golem [t-cfc57b] --provider zhipu --max-turns 40 "Install these Rust CLI tools on soma via cargo install: deltos, defuddle, sopor, amicus, praeco. For each: check if the crate exists in ~/germline/ or ~/code/ first (cargo install --path), otherwise try crates.io. Verify each works with --help after install. Report which succeeded and which failed."`


### Auto-requeue (4 tasks @ 09:59)
- [x] `golem [t-c7abe8] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ab4054] --provider infini --max-turns 30 "Health check: bud, engram, rename-kindle-asins.py, test-spec-gen, tmux-url-select.sh, golem-validate, methylation-review, telophase, exocytosis.py, proteostasis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-cc73a2] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_constitution.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_constitution.py -v --tb=short. Commit."`
- [x] `golem [t-bc59be] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_endocytosis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_endocytosis.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 09:59)
- [x] `golem [t-c9379b] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-5b06d7] --provider zhipu --max-turns 30 "Health check: weekly-gather, lacuna, cibus.py, perplexity.sh, client-brief, soma-bootstrap, soma-activate, commensal, exocytosis.py, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-d178fc] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_telegram_receptor.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_telegram_receptor.py -v --tb=short. Commit."`
- [x] `golem [t-05a2f6] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_proprioception.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_proprioception.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:00)
- [x] `golem [t-af6045] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1feb7b] --provider infini --max-turns 30 "Health check: rename-kindle-asins.py, soma-clean, queue-balance, vesicle, tmux-osc52.sh, demethylase, test-spec-gen, photos.py, capco-prep, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a8648c] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_auscultation.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_auscultation.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:01)
- [x] `golem [t-a872ca] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-24cf58] --provider infini --max-turns 30 "Health check: efferens, soma-watchdog, start-chrome-debug.sh, queue-gen, effector-usage, immunosurveillance.py, soma-clean, soma-wake, lacuna, git-activity. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-110bdc] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_noesis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_noesis.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:01)
- [x] `golem [t-2098e2] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a955f4] --provider infini --max-turns 30 "Health check: fix-symlinks, sortase, cn-route, update-compound-engineering, med-tracker, rename-kindle-asins.py, engram, importin, replisome, compound-engineering-test. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8a50a6] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_ultradian.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ultradian.py -v --tb=short. Commit."`
- [x] `golem [t-3cbf93] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_parsers_mox.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_mox.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:03)
- [x] `golem [t-34bd19] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-70bdc4] --provider infini --max-turns 30 "Health check: engram, soma-wake, rotate-logs.py, golem-dash, pharos-health.sh, regulatory-capture, council, golem-daemon-wrapper.sh, skill-search, plan-exec. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-12c6a4] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_telegram_auth.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_telegram_auth.py -v --tb=short. Commit."`
- [x] `golem [t-5db0e3] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_overnight.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_overnight.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:06)
- [x] `golem [t-768a8e] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4f386c] --provider volcano --max-turns 30 "Health check: chemoreception.py, centrosome, lacuna, orphan-scan, backfill-marks, cg, tmux-osc52.sh, importin, test-spec-gen, taste-score. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-603bfe] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_format.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_format.py -v --tb=short. Commit."`
- [x] `golem [t-ee8356] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_rss_config.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_rss_config.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:09)
- [x] `golem [t-db7bf2] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-cf58ef] --provider volcano --max-turns 30 "Health check: git-activity, golem-report, golem-dash, cytokinesis, plan-exec, compound-engineering-test, wacli-ro, soma-activate, consulting-card, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-2ac011] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_rss_cli.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_rss_cli.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:11)
- [x] `golem [t-68344f] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-580967] --provider volcano --max-turns 30 "Health check: circadian-probe.py, lacuna.py, soma-bootstrap, grep, golem-orchestrator, methylation-review, tmux-url-select.sh, plan-exec, git-activity, proteostasis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9ebedc] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_mismatch_repair.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_mismatch_repair.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 10:14)
- [x] `golem [t-9d9d8b] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1cef26] --provider zhipu --max-turns 30 "Health check: legatum-verify, legatum, pharos-env.sh, methylation-review, gemmation-env, golem-daemon, compound-engineering-test, pinocytosis, lacuna.py, agent-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 10:17)
- [x] `golem [t-16ff57] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fa0810] --provider zhipu --max-turns 30 "Health check: health-check, med-tracker, lacuna, search-guard, golem, soma-bootstrap, immunosurveillance, client-brief, golem-review, launchagent-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-39ebcc] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_check.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_check.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:21)
- [x] `golem [t-d2ca20] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3d084f] --provider zhipu --max-turns 30 "Health check: linkedin-monitor, respirometry, poiesis, synthase, immunosurveillance.py, soma-snapshot, auto-update-compound-engineering.sh, safe_rm.py, pulse-review, quorum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-284859] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_fetch.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_fetch.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:32)
- [x] `golem [t-9db678] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-170b91] --provider volcano --max-turns 30 "Health check: cookie-sync, browser, oura-weekly-digest.py, update-coding-tools.sh, overnight-gather, pulse-review, receptor-health, find, safe_search.py, assay. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a808fd] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_spending.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_spending.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:34)
- [x] `golem [t-682492] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-763d39] --provider infini --max-turns 30 "Health check: find, coaching-stats, golem-report, complement, golem, pharos-env.sh, safe_search.py, med-tracker, chromatin-backup.py, lacuna.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b9ce67] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_substrates_operon_monitor.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_operon_monitor.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:37)
- [x] `golem [t-c6fbe5] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-68bba5] --provider zhipu --max-turns 30 "Health check: launchagent-health, council, health-check, cibus.py, rheotaxis, backfill-marks, soma-health, engram, queue-gen, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-d50c1f] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_polarization.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_polarization.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:41)
- [x] `golem [t-e3c6b0] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-dfeb08] --provider volcano --max-turns 30 "Health check: oura-weekly-digest.py, complement, channel, cibus.py, gog, lustro-analyze, safe_search.py, chemoreception.py, chromatin-backup.py, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9c7bee] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_browser.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_browser.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:42)
- [x] `golem [t-f4d82a] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6a982b] --provider volcano --max-turns 30 "Health check: effector-usage, importin, legatum-verify, queue-gen, pinocytosis, golem, switch-layer, diapedesis, vesicle, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b57b23] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test___main__.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test___main__.py -v --tb=short. Commit. (retry)"`
- [x] `golem [t-24f9e1] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_catabolism.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_catabolism.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:43)
- [x] `golem [t-21b282] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1d2721] --provider infini --max-turns 30 "Health check: demethylase, transduction-daily-run, oura-weekly-digest.py, cleanup-stuck, bud, cg, ck, rotate-logs.py, soma-snapshot, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-2a4a1f] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_browser_stealth.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_browser_stealth.py -v --tb=short. Commit."`
- [x] `golem [t-c031d6] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_parsers_ccba.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_ccba.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:45)
- [x] `golem [t-e5b984] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1e26ef] --provider volcano --max-turns 30 "Health check: lacuna, tmux-workspace.py, rheotaxis, overnight-gather, orphan-scan, test-spec-gen, golem-review, exocytosis.py, translocon, paracrine. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-2cfe11] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_ecphory.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ecphory.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:48)
- [x] `golem [t-e576d4] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-ff5299] --provider zhipu --max-turns 30 "Health check: rename-kindle-asins.py, legatum-verify, med-tracker, goose-worker, respirometry, capco-prep, disk-audit, gog, oci-region-subscribe, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-7c6fca] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_substrates_operons.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_operons.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 10:49)
- [x] `golem [t-2ff2fb] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f2e8b9] --provider zhipu --max-turns 30 "Health check: effector-usage, photos.py, golem-report, goose-worker, express, council, bud, git-activity, wacli-ro, hkicpa. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-fa6bc9] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_substrates_constitution.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_constitution.py -v --tb=short. Commit."`
- [x] `golem [t-8b8c5b] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_base.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_base.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:50)
- [x] `golem [t-c445ab] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-677980] --provider infini --max-turns 30 "Health check: telophase, golem-validate, safe_search.py, pinocytosis, photos.py, gog, electroreception, phagocytosis.py, pharos-sync.sh, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-671634] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_epigenome.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_epigenome.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 10:52)
- [x] `golem [t-1e51dc] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2a42b4] --provider infini --max-turns 30 "Health check: express, efferens, plan-exec, regulatory-capture, git-activity, pharos-sync.sh, immunosurveillance, search-guard, queue-balance, commensal. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (3 tasks @ 10:53)
- [x] `golem [t-77ef0f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-fc1a79] --provider infini --max-turns 30 "Health check: complement, regulatory-scrape, coverage-map, inflammasome-probe, update-compound-engineering, circadian-probe.py, transduction-daily-run, electroreception, cg, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b54247] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_add.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_add.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 10:54)
- [x] `golem [t-f74f04] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bd7814] --provider infini --max-turns 30 "Health check: porta, skill-sync, conftest-gen, complement, importin, consulting-card.py, queue-balance, cn-route, dr-sync, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8b5615] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_init.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_init.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 10:56)
- [x] `golem [t-c9b33c] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-084978] --provider zhipu --max-turns 30 "Health check: golem-daemon, linkedin-monitor, bud, pulse-review, commensal, skill-sync, autoimmune.py, regulatory-scrape, soma-pull, judge. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-bfa9d4] --provider zhipu --max-turns 20 "Add m3's SSH key to GitHub so m3 can git clone vivesca/vivesca. From soma: (1) Run: gh ssh-key list — check if key already exists. (2) If not, the key is: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH1+4UQWEfVOPVfyoEVjGVDW3q93zJukRK4WP656qUU5 terry@mac. You may need to unset GITHUB_TOKEN first, then gh auth refresh -h github.com -s admin:public_key, then gh ssh-key add with --title m3-mac. (3) Once key is on GitHub, SSH to m3 and clone: ssh terry@m3 'git clone git@github.com:vivesca/vivesca.git ~/germline'. (4) Verify: ssh terry@m3 'ls ~/germline/effectors/cn-route && git -C ~/germline remote -v'."`
- [!] `golem [t-fce6ba] --provider zhipu --max-turns 10 "Rename the cn-route LaunchDaemon on mac (iMac) to match m3 naming. SSH to mac with -t for sudo: ssh -t terry@mac. (1) sudo launchctl bootout system /Library/LaunchDaemons/com.vivesca.zhipu-route.plist. (2) sudo mv /Library/LaunchDaemons/com.vivesca.zhipu-route.plist /Library/LaunchDaemons/com.vivesca.cn-route.plist. (3) Use python3 to edit the plist: change Label value from com.vivesca.zhipu-route to com.vivesca.cn-route. (4) sudo launchctl bootstrap system /Library/LaunchDaemons/com.vivesca.cn-route.plist. (5) Verify: sudo launchctl print system/com.vivesca.cn-route. (retry)"`

### Auto-requeue (2 tasks @ 10:59)
- [x] `golem [t-6a5d23] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-cc5dee] --provider zhipu --max-turns 30 "Health check: cn-route, publish, queue-gen, chemoreception.py, disk-audit, weekly-gather, agent-sync.sh, taste-score, rg, rotate-logs.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:00)
- [x] `golem [t-b7e9b9] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-af7e1b] --provider volcano --max-turns 30 "Health check: consulting-card, auto-update-compound-engineering.sh, goose-worker, compound-engineering-test, find, autoimmune.py, gog, rg, fasti, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:01)
- [x] `golem [t-73c08d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-94288e] --provider zhipu --max-turns 30 "Health check: health-check, chat_history.py, update-coding-tools.sh, backup-due.sh, safe_rm.py, circadian-probe.py, commensal, tmux-url-select.sh, launchagent-health, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 11:02)
- [x] `golem [t-71c3bd] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4da0f6] --provider volcano --max-turns 30 "Health check: update-coding-tools.sh, transduction-daily-run, plan-exec, cytokinesis, council, start-chrome-debug.sh, safe_rm.py, immunosurveillance.py, pinocytosis, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-98ae6c] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_photoreception.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_photoreception.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 11:04)
- [x] `golem [t-628580] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ac6d5f] --provider infini --max-turns 30 "Health check: commensal, telophase, grok, demethylase, complement, weekly-gather, ck, diapedesis, golem, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:06)
- [x] `golem [t-9b3c23] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-996cf5] --provider infini --max-turns 30 "Health check: engram, rg, diapedesis, immunosurveillance, agent-sync.sh, consulting-card, channel, legatum-verify, capco-brief, soma-snapshot. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:08)
- [x] `golem [t-cebd22] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-97f4f4] --provider volcano --max-turns 30 "Health check: provider-bench, mitosis-checkpoint.py, lysis, golem-daemon-wrapper.sh, search-guard, rheotaxis, poiesis, lacuna.py, conftest-gen, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:08)
- [x] `golem [t-972b19] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2b730c] --provider zhipu --max-turns 30 "Health check: golem-review, diapedesis, update-compound-engineering, hetzner-bootstrap.sh, goose-worker, git-activity, soma-health, start-chrome-debug.sh, compound-engineering-status, immunosurveillance.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:11)
- [x] `golem [t-e3ce4d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-31d92e] --provider volcano --max-turns 30 "Health check: plan-exec, porta, queue-gen, soma-scale, conftest-gen, fasti, provider-bench, complement, bud, phagocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:12)
- [x] `golem [t-bdf637] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9944ba] --provider infini --max-turns 30 "Health check: grep, engram, rename-plists, pharos-env.sh, cg, x-feed-to-lustro, assay, golem-daemon, soma-pull, golem. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:13)
- [x] `golem [t-7ac6cf] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a50205] --provider infini --max-turns 30 "Health check: pharos-sync.sh, rotate-logs.py, qmd-reindex.sh, rename-kindle-asins.py, diapedesis, oura-weekly-digest.py, provider-bench, synthase, regulatory-capture, orphan-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:15)
- [x] `golem [t-03c104] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-de2c76] --provider volcano --max-turns 30 "Health check: sortase, lacuna, taste-score, telophase, photos.py, queue-balance, coverage-map, hetzner-bootstrap.sh, orphan-scan, gog. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:15)
- [x] `golem [t-59db87] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2adfb4] --provider infini --max-turns 30 "Health check: log-summary, exocytosis.py, overnight-gather, linkedin-monitor, git-activity, commensal, gog, backup-due.sh, update-coding-tools.sh, hkicpa. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 11:16)
- [x] `golem [t-77a958] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-91b186] --provider zhipu --max-turns 30 "Health check: immunosurveillance, judge, soma-watchdog, engram, diapedesis, fasti, rheotaxis, immunosurveillance.py, coverage-map, sortase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:18)
- [x] `golem [t-8deb1a] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-78125f] --provider volcano --max-turns 30 "Health check: cn-route, electroreception, tmux-osc52.sh, legatum-verify, cleanup-stuck, gog, rename-kindle-asins.py, client-brief, golem-dash, gemmation-env. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:18)
- [x] `golem [t-ca597e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-095971] --provider infini --max-turns 30 "Health check: assay, autoimmune.py, consulting-card, rename-kindle-asins.py, find, mitosis-checkpoint.py, golem-orchestrator, chromatin-backup.py, chemoreception.py, disk-audit. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:20)
- [x] `golem [t-7705af] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-859807] --provider zhipu --max-turns 30 "Health check: compound-engineering-test, dr-sync, quorum, pharos-health.sh, safe_search.py, photos.py, client-brief, skill-search, assay, lysis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:23)
- [x] `golem [t-7ec688] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2e010e] --provider zhipu --max-turns 30 "Health check: mitosis-checkpoint.py, legatum-verify, browser, lysis, poiesis, weekly-gather, cg, grok, cn-route, x-feed-to-lustro. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:23)
- [x] `golem [t-193942] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-41c6ac] --provider zhipu --max-turns 30 "Health check: rheotaxis, effector-usage, inflammasome-probe, vesicle, cleanup-stuck, disk-audit, golem-dash, orphan-scan, golem-validate, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:24)
- [x] `golem [t-4f23a4] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-569c34] --provider volcano --max-turns 30 "Health check: centrosome, phagocytosis.py, vesicle, inflammasome-probe, immunosurveillance.py, grok, golem-orchestrator, pharos-health.sh, log-summary, hetzner-bootstrap.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:25)
- [x] `golem [t-424f08] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-75c40f] --provider zhipu --max-turns 30 "Health check: evident-brief, lacuna, consulting-card.py, immunosurveillance, regulatory-capture, safe_rm.py, regulatory-scrape, telophase, receptor-health, golem-reviewer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:26)
- [x] `golem [t-8a69f3] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7ce873] --provider volcano --max-turns 30 "Health check: card-search, vesicle, backfill-marks, golem-reviewer, weekly-gather, golem-report, conftest-gen, complement, quorum, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:27)
- [x] `golem [t-55f179] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-052842] --provider infini --max-turns 30 "Health check: backfill-marks, proteostasis, disk-audit, centrosome, channel, exocytosis.py, hkicpa, respirometry, update-compound-engineering, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:31)
- [x] `golem [t-7f4f8e] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-68716e] --provider volcano --max-turns 30 "Health check: log-summary, fasti, express, safe_rm.py, commensal, generate-solutions-index.py, browser, card-search, soma-bootstrap, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:32)
- [x] `golem [t-d833a7] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-b648db] --provider volcano --max-turns 30 "Health check: backup-due.sh, consulting-card, soma-snapshot, hkicpa, golem-reviewer, start-chrome-debug.sh, electroreception, channel, weekly-gather, translocon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:33)
- [x] `golem [t-bee342] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-063944] --provider zhipu --max-turns 30 "Health check: search-guard, mitosis-checkpoint.py, queue-gen, receptor-health, gemmule-sync, pharos-sync.sh, rename-plists, update-coding-tools.sh, lacuna, fix-symlinks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:35)
- [x] `golem [t-7c3437] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-48df8a] --provider volcano --max-turns 30 "Health check: immunosurveillance, auto-update-compound-engineering.sh, golem-daemon, backup-due.sh, backfill-marks, gemmation-env, gap_junction_sync, perplexity.sh, soma-scale, switch-layer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:37)
- [x] `golem [t-294aa8] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d449ad] --provider zhipu --max-turns 30 "Health check: legatum, sortase, soma-activate, oura-weekly-digest.py, dr-sync, soma-bootstrap, electroreception, safe_search.py, browse, synthase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:38)
- [x] `golem [t-8c53e8] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-5a4969] --provider volcano --max-turns 30 "Health check: wewe-rss-health.py, telophase, safe_rm.py, centrosome, proteostasis, tmux-osc52.sh, goose-worker, auto-update-compound-engineering.sh, channel, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:40)
- [x] `golem [t-a0d432] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e4f4a8] --provider volcano --max-turns 30 "Health check: oci-arm-retry, soma-clean, electroreception, proteostasis, council, soma-scale, chemoreception.py, auto-update-compound-engineering.sh, orphan-scan, dr-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:42)
- [x] `golem [t-1703dd] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-83a017] --provider infini --max-turns 30 "Health check: cibus.py, coverage-map, soma-bootstrap, cytokinesis, skill-lint, qmd-reindex.sh, porta, update-coding-tools.sh, capco-prep, transduction-daily-run. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:45)
- [x] `golem [t-87fe2e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-266e39] --provider infini --max-turns 30 "Health check: taste-score, gemmule-sync, update-compound-engineering, golem-health, golem-dash, weekly-gather, phagocytosis.py, provider-bench, health-check, oci-arm-retry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:47)
- [x] `golem [t-35bf19] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ec5147] --provider volcano --max-turns 30 "Health check: backfill-marks, oura-weekly-digest.py, cg, perplexity.sh, diapedesis, receptor-health, log-summary, golem-validate, soma-status, wacli-ro. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:48)
- [x] `golem [t-f14959] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bd57cf] --provider zhipu --max-turns 30 "Health check: nightly, oci-arm-retry, immunosurveillance.py, agent-sync.sh, weekly-gather, tmux-osc52.sh, rheotaxis-local, capco-brief, soma-snapshot, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:52)
- [x] `golem [t-6c198d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-446a24] --provider volcano --max-turns 30 "Health check: orphan-scan, proteostasis, golem-validate, tmux-url-select.sh, golem-reviewer, publish, find, regulatory-scrape, capco-brief, express. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:53)
- [x] `golem [t-4448ac] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a618ac] --provider zhipu --max-turns 30 "Health check: respirometry, demethylase, lacuna, quorum, test-spec-gen, tmux-url-select.sh, pharos-sync.sh, sortase, complement, lacuna.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:54)
- [x] `golem [t-a3dce0] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-45cfd1] --provider zhipu --max-turns 30 "Health check: publish, pulse-review, electroreception, hetzner-bootstrap.sh, nightly, oci-arm-retry, start-chrome-debug.sh, tmux-url-select.sh, mismatch-repair, health-check. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:55)
- [x] `golem [t-16720f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fb9559] --provider infini --max-turns 30 "Health check: gap_junction_sync, commensal, golem-report, engram, immunosurveillance, update-compound-engineering, cg, chromatin-decay-report.py, phagocytosis.py, skill-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:56)
- [x] `golem [t-0e5e7d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f4f875] --provider infini --max-turns 30 "Health check: perplexity.sh, golem, find, phagocytosis.py, immunosurveillance, rheotaxis-local, consulting-card, compound-engineering-test, provider-bench, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:57)
- [x] `golem [t-8a2368] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f50443] --provider volcano --max-turns 30 "Health check: porta, tmux-url-select.sh, grep, golem-daemon-wrapper.sh, queue-stats, perplexity.sh, phagocytosis.py, lysis, safe_rm.py, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 11:59)
- [x] `golem [t-57d482] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a756af] --provider volcano --max-turns 30 "Health check: rename-plists, cg, wewe-rss-health.py, tmux-workspace.py, update-compound-engineering, overnight-gather, soma-clean, phagocytosis.py, test-fixer, golem-top. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:01)
- [x] `golem [t-d0dbdd] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-66d7ae] --provider volcano --max-turns 30 "Health check: x-feed-to-lustro, golem, update-coding-tools.sh, chromatin-backup.sh, gemmule-sync, start-chrome-debug.sh, grep, golem-reviewer, golem-daemon-wrapper.sh, search-guard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:01)
- [x] `golem [t-f50843] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-d03877] --provider volcano --max-turns 30 "Health check: agent-sync.sh, council, poiesis, cn-route, browse, cg, wewe-rss-health.py, goose-worker, rheotaxis, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:03)
- [x] `golem [t-c526f6] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a9c154] --provider zhipu --max-turns 30 "Health check: golem, pinocytosis, golem-validate, gemmule-sync, rheotaxis-local, hkicpa, coverage-map, golem-dash, soma-health, update-compound-engineering-skills.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:06)
- [x] `golem [t-783576] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-97f886] --provider zhipu --max-turns 30 "Health check: taste-score, methylation, compound-engineering-test, translocon, exocytosis.py, launchagent-health, med-tracker, lysis, goose-worker, mismatch-repair. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:06)
- [x] `golem [t-446f52] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-efb27e] --provider infini --max-turns 30 "Health check: consulting-card.py, safe_rm.py, test-dashboard, golem-cost, log-summary, effector-usage, golem-report, perplexity.sh, chromatin-decay-report.py, golem-dash. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:07)
- [x] `golem [t-4011c0] --provider volcano --max-turns 30 "Health check: judge, regulatory-scrape, porta, demethylase, nightly, tmux-workspace.py, coverage-map, centrosome, skill-search, golem-report. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:08)
- [x] `golem [t-79fd58] --provider zhipu --max-turns 30 "Health check: receptor-health, log-summary, methylation, exocytosis.py, cytokinesis, tmux-osc52.sh, safe_search.py, golem-dash, chromatin-backup.sh, porta. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:09)
- [x] `golem [t-f59605] --provider infini --max-turns 30 "Health check: gog, council, regulatory-scrape, diapedesis, receptor-health, lustro-analyze, circadian-probe.py, soma-pull, med-tracker, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:09)
- [x] `golem [t-af9a14] --provider infini --max-turns 30 "Health check: importin, photos.py, fasti, complement, ck, queue-gen, card-search, golem-tools, judge, centrosome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:11)
- [x] `golem [t-87f6d3] --provider volcano --max-turns 30 "Health check: phagocytosis.py, queue-balance, launchagent-health, tmux-workspace.py, golem, golem-review, safe_search.py, electroreception, tmux-osc52.sh, immunosurveillance.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:12)
- [x] `golem [t-4be15a] --provider zhipu --max-turns 30 "Health check: mitosis-checkpoint.py, soma-watchdog, soma-health, fasti, generate-solutions-index.py, capco-brief, coverage-map, rheotaxis-local, lacuna.py, browser. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:14)
- [x] `golem [t-2dd1e9] --provider infini --max-turns 30 "Health check: chromatin-decay-report.py, methylation, backfill-marks, golem-validate, soma-snapshot, golem, oci-arm-retry, linkedin-monitor, skill-lint, fix-symlinks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:15)
- [x] `golem [t-4647e6] --provider infini --max-turns 30 "Health check: regulatory-scrape, soma-pull, channel, hetzner-bootstrap.sh, conftest-gen, soma-activate, chat_history.py, skill-lint, wacli-ro, skill-search. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:17)
- [x] `golem [t-fbd4cd] --provider infini --max-turns 30 "Health check: pulse-review, hkicpa, rename-kindle-asins.py, queue-stats, start-chrome-debug.sh, efferens, lacuna.py, methylation-review, importin, chromatin-backup.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:18)
- [x] `golem [t-aed1d5] --provider infini --max-turns 30 "Health check: pharos-health.sh, complement, safe_rm.py, queue-stats, receptor-scan, golem-daemon-wrapper.sh, golem-reviewer, circadian-probe.py, test-fixer, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:20)
- [x] `golem [t-7eebe6] --provider volcano --max-turns 30 "Health check: centrosome, client-brief, circadian-probe.py, compound-engineering-status, legatum-verify, linkedin-monitor, cn-route, exocytosis.py, agent-sync.sh, orphan-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:22)
- [x] `golem [t-937794] --provider zhipu --max-turns 30 "Health check: soma-pull, vesicle, hetzner-bootstrap.sh, legatum, telophase, soma-snapshot, transduction-daily-run, capco-brief, rename-kindle-asins.py, card-search. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:23)
- [x] `golem [t-7fc917] --provider volcano --max-turns 30 "Health check: gog, importin, soma-watchdog, lacuna.py, oci-region-subscribe, soma-activate, engram, chemoreception.py, update-compound-engineering-skills.sh, compound-engineering-test. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:24)
- [x] `golem [t-326b66] --provider infini --max-turns 30 "Health check: poiesis, coverage-map, skill-lint, soma-pull, rotate-logs.py, golem-validate, gemmule-sync, health-check, capco-brief, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:26)
- [x] `golem [t-94a2c2] --provider volcano --max-turns 30 "Health check: chemoreception.py, card-search, chromatin-decay-report.py, porta, golem-tools, judge, golem-cost, golem-validate, auto-update-compound-engineering.sh, publish. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:28)
- [x] `golem [t-67f4de] --provider zhipu --max-turns 30 "Health check: soma-status, disk-audit, compound-engineering-status, test-spec-gen, cookie-sync, coaching-stats, consulting-card.py, pharos-sync.sh, lacuna, proteostasis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:29)
- [x] `golem [t-60352a] --provider infini --max-turns 30 "Health check: commensal, golem-dash, chat_history.py, goose-worker, evident-brief, regulatory-capture, demethylase, soma-clean, tm, paracrine. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:29)
- [x] `golem [t-8d6870] --provider infini --max-turns 30 "Health check: rename-plists, chromatin-decay-report.py, test-dashboard, grep, rheotaxis-local, methylation, browser, hkicpa, skill-lint, tmux-osc52.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-31b8a9] [t-stats01] --provider zhipu --max-turns 40 "Enhance golem-daemon stats command in ~/germline/effectors/golem-daemon. READ the full file first — especially _write_jsonl_record, cmd_stats, cmd_export_stats, and the JSONLFILE constant. Changes: (1) Make 'stats' default to last-8h window: filter golem.jsonl records where ts >= now-8h. Parse both ts formats ('2026-04-02 12:29:05' and ISO '2026-04-02T04:29:07Z') into epoch for comparison. (2) Add --today flag: filter ts >= midnight local. (3) Add --all flag: current lifetime behavior (no filter). (4) Add --since=DURATION flag (e.g. --since=2h, --since=30m) for custom windows. (5) First line of stats output: check queue file for daemon status (pidfile) and count pending [ ] tasks — print 'Daemon: running|stopped — N tasks pending, M running' as header. Count running by [>] markers. (6) Add 'Currently running' section listing task IDs and elapsed time from started_at in queue entries. (7) Add 'Permanently failed' section listing task IDs that hit max retries. (8) Update --export-stats to accept same time filters. (9) Keep --all backward compatible — exact same output as current stats when --all is passed. Do NOT change queue format, locking, JSONL schema, or dispatch logic. Tests: update test_golem_daemon.py and test_golem_daemon_stats.py — add tests for time-windowed filtering, --today, --since, daemon status header, running tasks display. Run tests with: cd ~/germline && uv run pytest assays/test_golem_daemon.py -x -q && uv run pytest assays/test_golem_daemon_stats.py -x -q. Commit with clear message. (retry)"`

### Auto-requeue (2 tasks @ 12:30)
- [x] `golem [t-de5a80] --provider volcano --max-turns 30 "Health check: compound-engineering-status, oci-arm-retry, med-tracker, cn-route, soma-snapshot, circadian-probe.py, centrosome, maintenance-cron, oci-region-subscribe, golem-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:31)
- [x] `golem [t-1310c4] --provider volcano --max-turns 30 "Health check: synthase, test-fixer, pharos-env.sh, browser, pharos-health.sh, tm, council, compound-engineering-test, golem-report, med-tracker. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c0b44d] [t-alwayson] --provider zhipu --max-turns 40 "Make golem-daemon always-on in ~/germline/effectors/golem-daemon. READ the full file first — especially the main loop, queue polling, and cooldown logic. Changes: (1) When queue is empty or all pending tasks are on cooled-down providers, sleep 60s then re-poll instead of exiting. (2) When all providers are cooled down AND tasks are pending, sleep 300s (5min backoff) then re-poll. (3) Add SIGTERM handler that sets a shutdown flag — on next loop iteration, drain running tasks and exit cleanly. (4) Log 'Idle: queue empty, sleeping 60s' and 'Backoff: all providers cooled, sleeping 300s' so the log shows why it's quiet. (5) On wake from sleep, re-read the queue file fresh (it may have new entries added by CC or cron). (6) Do NOT change start/stop/status commands — stop should still work via pidfile+SIGTERM. Do NOT change queue format, locking, dispatch logic, or JSONL schema. Tests: update test_golem_daemon.py — add tests for idle-sleep behavior, backoff-sleep, SIGTERM graceful shutdown, re-read on wake. Run: cd ~/germline && uv run pytest assays/test_golem_daemon.py -x -q. Commit with clear message. (retry)"`

### Auto-requeue (2 tasks @ 12:34)
- [x] `golem [t-0441ae] --provider volcano --max-turns 30 "Health check: taste-score, rotate-logs.py, golem-dash, backfill-marks, regulatory-scrape, update-coding-tools.sh, switch-layer, golem-validate, ck, receptor-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:36)
- [x] `golem [t-97c7e7] --provider zhipu --max-turns 30 "Health check: rheotaxis-local, soma-bootstrap, overnight-gather, soma-clean, ck, med-tracker, golem-orchestrator, wewe-rss-health.py, coaching-stats, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:37)
- [x] `golem [t-534419] --provider volcano --max-turns 30 "Health check: coaching-stats, centrosome, synthase, methylation-review, cibus.py, receptor-scan, agent-sync.sh, golem-tools, update-compound-engineering-skills.sh, test-fixer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:38)
- [x] `golem [t-93f450] --provider zhipu --max-turns 30 "Health check: grok, rename-kindle-asins.py, gemmation-env, soma-pull, soma-health, exocytosis.py, browse, coverage-map, sortase, commensal. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:38)
- [x] `golem [t-07ed2d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-83233f] --provider volcano --max-turns 30 "Health check: paracrine, circadian-probe.py, methylation-review, update-compound-engineering-skills.sh, regulatory-capture, pulse-review, soma-pull, importin, regulatory-scrape, launchagent-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:39)
- [x] `golem [t-3949d7] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-99cec1] --provider volcano --max-turns 30 "Health check: paracrine, golem-report, consulting-card.py, golem-daemon, centrosome, pinocytosis, oci-arm-retry, porta, fix-symlinks, golem-reviewer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:39)
- [!] `golem [t-7552ff] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-7a9d53] --provider volcano --max-turns 30 "Health check: council, rg, capco-prep, importin, compound-engineering-test, card-search, soma-status, gemmule-sync, lacuna.py, search-guard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:40)
- [x] `golem [t-bb401a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-65285d] --provider infini --max-turns 30 "Health check: golem-review, fasti, launchagent-health, card-search, porta, gap_junction_sync, lysis, start-chrome-debug.sh, legatum, disk-audit. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:40)
- [x] `golem [t-cadd56] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-5b388c] --provider infini --max-turns 30 "Health check: oci-region-subscribe, gog, test-fixer, soma-health, gemmation-env, mismatch-repair, proteostasis, coverage-map, pulse-review, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:41)
- [x] `golem [t-b4b855] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1ef028] --provider volcano --max-turns 30 "Health check: respirometry, tmux-workspace.py, weekly-gather, transduction-daily-run, replisome, log-summary, poiesis, regulatory-capture, mismatch-repair, immunosurveillance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:41)
- [x] `golem [t-4fb2b6] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-512dd8] --provider volcano --max-turns 30 "Health check: regulatory-scan, test-spec-gen, lacuna, synthase, oci-arm-retry, skill-search, weekly-gather, switch-layer, capco-prep, qmd-reindex.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:42)
- [x] `golem [t-6fb82a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-6253fa] --provider infini --max-turns 30 "Health check: capco-prep, lacuna, methylation-review, legatum-verify, provider-bench, pinocytosis, browser, pharos-health.sh, backup-due.sh, compound-engineering-test. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:43)
- [x] `golem [t-abfc13] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-c9151b] --provider volcano --max-turns 30 "Health check: queue-gen, secrets-sync, centrosome, test-dashboard, golem, wewe-rss-health.py, tmux-url-select.sh, overnight-gather, proteostasis, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:43)
- [x] `golem [t-ecadba] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e5406c] --provider volcano --max-turns 30 "Health check: soma-wake, synthase, engram, soma-pull, methylation-review, capco-brief, tm, hkicpa, pharos-health.sh, photos.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-01c09d] [t-reroute] --provider zhipu --max-turns 40 "Fix fallback routing bug in ~/germline/effectors/golem-daemon. READ the full file first. Bug: when infini/volcano are cooled down, their tasks should reroute to codex first (per PROVIDER_FALLBACK chains at line 205-211), but in practice nearly all go to zhipu instead. Codex sits at 1/4 slots while zhipu fills to 7-8/8. Investigate _pick_dispatch_provider (line 259), _dispatch_candidates (line 244), and the main dispatch loop (~line 1550). Likely cause: provider_running count for codex is over-counted or stale during the dispatch loop iteration — if the loop optimistically increments running counts as it queues tasks within a single cycle, one slow codex task makes codex look full for the rest of the cycle. Or: the loop iterates pending tasks in queue order and zhipu-affinity tasks get dispatched first, incrementing global running count, leaving fewer slots by the time infini/volcano tasks try to fallback to codex. Fix: ensure fallback routing actually fills codex to its cap (4) before overflowing to zhipu. Add debug logging when a fallback candidate is skipped and why (at capacity, cooled down, etc). Tests: add test cases in test_golem_daemon.py for fallback routing — mock 3 providers cooled down, verify tasks route to the 2 healthy ones proportionally to their caps. Run: cd ~/germline && uv run pytest assays/test_golem_daemon.py -x -q. Commit with clear message."`

### Auto-requeue (2 tasks @ 12:44)
- [x] `golem [t-612284] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2bc267] --provider zhipu --max-turns 30 "Health check: golem-health, methylation-review, pulse-review, soma-clean, soma-status, grok, regulatory-scrape, assay, auto-update-compound-engineering.sh, gog. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:44)
- [x] `golem [t-62a321] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-eed1e8] --provider infini --max-turns 30 "Health check: gemmule-sync, capco-brief, golem-cost, tm, find, linkedin-monitor, golem-top, chromatin-decay-report.py, golem-health, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:45)
- [x] `golem [t-5bd9cb] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-b0c07d] --provider infini --max-turns 30 "Health check: gemmule-sync, test-fixer, cg, queue-stats, gemmation-env, capco-prep, wacli-ro, porta, skill-search, cleanup-stuck. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:45)
- [x] `golem [t-9b8263] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9d8d9f] --provider volcano --max-turns 30 "Health check: paracrine, gemmation-env, commensal, oci-arm-retry, queue-gen, circadian-probe.py, skill-search, lysis, inflammasome-probe, capco-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:46)
- [x] `golem [t-c34ad1] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ac496f] --provider infini --max-turns 30 "Health check: pharos-env.sh, exocytosis.py, golem-review, backfill-marks, search-guard, gap_junction_sync, overnight-gather, circadian-probe.py, chromatin-decay-report.py, electroreception. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:46)
- [!] `golem [t-f670ce] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-c5197a] --provider volcano --max-turns 30 "Health check: chromatin-backup.sh, golem-reviewer, update-compound-engineering, receptor-scan, perplexity.sh, oura-weekly-digest.py, importin, channel, fix-symlinks, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:47)
- [!] `golem [t-037762] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-a03558] --provider volcano --max-turns 30 "Health check: test-spec-gen, sortase, lacuna, agent-sync.sh, queue-balance, pharos-env.sh, qmd-reindex.sh, oci-arm-retry, rename-plists, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:49)
- [!] `golem [t-a42204] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-6713e1] --provider zhipu --max-turns 30 "Health check: methylation-review, lacuna, pulse-review, engram, golem-cost, replisome, pharos-health.sh, golem-health, transduction-daily-run, methylation. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:50)
- [x] `golem [t-c282d8] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-c00369] --provider infini --max-turns 30 "Health check: launchagent-health, plan-exec, generate-solutions-index.py, gemmule-sync, council, regulatory-capture, legatum, test-dashboard, quorum, translocon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:50)
- [x] `golem [t-39ed3c] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-a35cc3] --provider zhipu --max-turns 30 "Health check: pinocytosis, receptor-scan, backup-due.sh, cibus.py, ck, tmux-workspace.py, proteostasis, queue-balance, med-tracker, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:51)
- [!] `golem [t-805747] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-7b81dd] --provider zhipu --max-turns 30 "Health check: express, overnight-gather, soma-bootstrap, provider-bench, compound-engineering-status, fix-symlinks, methylation, golem, grep, dr-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:51)
- [!] `golem [t-c6f7f8] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-c4d8ec] --provider zhipu --max-turns 30 "Health check: launchagent-health, telophase, client-brief, weekly-gather, golem-tools, health-check, electroreception, replisome, pulse-review, phagocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:53)
- [x] `golem [t-14bf62] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-753a9e] --provider infini --max-turns 30 "Health check: update-coding-tools.sh, golem, commensal, tm, golem-daemon, card-search, lacuna, translocon, queue-gen, log-summary. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:54)
- [x] `golem [t-b5a113] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-417fcf] --provider zhipu --max-turns 30 "Health check: regulatory-scrape, gog, commensal, inflammasome-probe, start-chrome-debug.sh, rheotaxis, fix-symlinks, golem-report, poiesis, generate-solutions-index.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:54)
- [x] `golem [t-2f11f8] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-39a066] --provider infini --max-turns 30 "Health check: respirometry, oci-arm-retry, regulatory-scrape, pharos-sync.sh, exocytosis.py, poiesis, goose-worker, fix-symlinks, compound-engineering-test, test-fixer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:56)
- [x] `golem [t-56d689] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f92f03] --provider volcano --max-turns 30 "Health check: gog, transduction-daily-run, launchagent-health, synthase, health-check, test-spec-gen, mismatch-repair, rg, skill-sync, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 12:57)
- [x] `golem [t-c99d9a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-82c444] --provider infini --max-turns 30 "Health check: dr-sync, launchagent-health, oura-weekly-digest.py, centrosome, browse, tmux-workspace.py, capco-prep, skill-sync, regulatory-capture, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:02)
- [x] `golem [t-23c8f9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a2802d] --provider infini --max-turns 30 "Health check: soma-clean, golem-dash, dr-sync, pinocytosis, replisome, secrets-sync, rename-kindle-asins.py, diapedesis, oura-weekly-digest.py, oci-arm-retry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:04)
- [x] `golem [t-24a2cb] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ac4954] --provider zhipu --max-turns 30 "Health check: wewe-rss-health.py, phagocytosis.py, browse, update-compound-engineering, oura-weekly-digest.py, pharos-sync.sh, council, health-check, grok, cn-route. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:07)
- [!] `golem [t-1ecc57] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-2830f4] --provider volcano --max-turns 30 "Health check: provider-bench, med-tracker, electroreception, skill-search, phagocytosis.py, bud, rg, pulse-review, chromatin-backup.sh, paracrine. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 13:08)
- [!] `golem [t-9b7cc2] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-5c4772] --provider infini --max-turns 30 "Health check: receptor-scan, fasti, coaching-stats, queue-stats, respirometry, compound-engineering-test, telophase, council, queue-balance, chemoreception.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:10)
- [!] `golem [t-3c4da4] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-a448c0] --provider volcano --max-turns 30 "Health check: switch-layer, pulse-review, importin, gemmation-env, rheotaxis, receptor-scan, exocytosis.py, queue-gen, rheotaxis-local, maintenance-cron. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:11)
- [!] `golem [t-97e297] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-ac887d] --provider zhipu --max-turns 30 "Health check: regulatory-scrape, nightly, oci-arm-retry, generate-solutions-index.py, consulting-card.py, cookie-sync, methylation-review, test-dashboard, agent-sync.sh, respirometry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:13)
- [!] `golem [t-50067b] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-839a49] --provider zhipu --max-turns 30 "Health check: soma-activate, lysis, linkedin-monitor, gemmation-env, maintenance-cron, assay, cleanup-stuck, complement, update-coding-tools.sh, coaching-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:18)
- [!] `golem [t-ed5b32] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-f99284] --provider zhipu --max-turns 30 "Health check: soma-scale, launchagent-health, golem-top, oci-arm-retry, effector-usage, regulatory-capture, rotate-logs.py, centrosome, pharos-env.sh, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:18)
- [!] `golem [t-faafef] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-e79942] --provider volcano --max-turns 30 "Health check: chromatin-backup.py, golem, grep, channel, plan-exec, golem-validate, legatum, lustro-analyze, med-tracker, agent-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:19)
- [!] `golem [t-41687c] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-aaa232] --provider infini --max-turns 30 "Health check: grep, golem-dash, replisome, find, rheotaxis-local, compound-engineering-test, fix-symlinks, ck, overnight-gather, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:21)
- [!] `golem [t-76c881] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-ab84ce] --provider zhipu --max-turns 30 "Health check: methylation-review, commensal, coverage-map, diapedesis, consulting-card, switch-layer, pharos-sync.sh, proteostasis, oci-arm-retry, queue-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:22)
- [x] `golem [t-75e4f1] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-42939c] --provider volcano --max-turns 30 "Health check: mitosis-checkpoint.py, fix-symlinks, pharos-health.sh, find, generate-solutions-index.py, gap_junction_sync, perplexity.sh, cg, health-check, chromatin-backup.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:24)
- [x] `golem [t-ffcf91] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-98e501] --provider volcano --max-turns 30 "Health check: med-tracker, effector-usage, safe_search.py, rename-kindle-asins.py, soma-status, circadian-probe.py, consulting-card.py, golem-report, paracrine, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:28)
- [x] `golem [t-786ae4] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f32194] --provider zhipu --max-turns 30 "Health check: proteostasis, rename-plists, mismatch-repair, goose-worker, golem-health, git-activity, autoimmune.py, vesicle, capco-prep, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:29)
- [!] `golem [t-dcfe76] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-7b48a3] --provider volcano --max-turns 30 "Health check: coaching-stats, gog, importin, consulting-card.py, soma-status, capco-brief, express, backup-due.sh, replisome, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:32)
- [!] `golem [t-cd5c34] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-7dcde2] --provider zhipu --max-turns 30 "Health check: centrosome, backup-due.sh, tmux-workspace.py, respirometry, med-tracker, pulse-review, safe_rm.py, weekly-gather, golem-top, regulatory-capture. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:36)
- [!] `golem [t-2e2381] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-dd6eb1] --provider zhipu --max-turns 30 "Health check: golem-report, chemoreception.py, golem-review, centrosome, browse, receptor-health, golem-dash, wewe-rss-health.py, pharos-env.sh, gog. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:37)
- [!] `golem [t-793835] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-95eb34] --provider zhipu --max-turns 30 "Health check: soma-snapshot, update-compound-engineering-skills.sh, auto-update-compound-engineering.sh, council, soma-scale, pharos-health.sh, soma-wake, med-tracker, generate-solutions-index.py, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:48)
- [!] `golem [t-f6790b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-b6bb88] --provider infini --max-turns 30 "Health check: receptor-health, hetzner-bootstrap.sh, exocytosis.py, cibus.py, qmd-reindex.sh, secrets-sync, rheotaxis-local, chromatin-decay-report.py, capco-brief, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b08088] [t-hardlimit] --provider zhipu --max-turns 40 "Fix billing-cycle rate limit detection in ~/germline/effectors/golem-daemon. READ the full file first — especially the rate-limit detection in the main loop (~line 1500-1550) and _log_cooldown. Bug: when Codex returns 'You've hit your usage limit... try again at Apr 8th, 2026 4:01 PM', the daemon treats it as a normal short cooldown (hours). It should detect billing-cycle exhaustion and set a long cooldown. Changes: (1) In the exit-code/stderr parsing section, detect patterns like 'usage limit', 'hit your.*limit', 'try again at <date>' where date is >24h away. (2) Parse the reset date from stderr (formats: 'Apr 8th, 2026 4:01 PM', ISO, etc). (3) If reset date is >24h away, set cooldown_until to that date and log as 'billing-exhausted' not 'burnout'. (4) Add a PROVIDER_DISABLED dict separate from cooldown — disabled providers are never probed. (5) In status output, show 'codex (billing limit, resets Apr 8)' instead of 'codex (resets 18:36)'. (6) golem-daemon clear-cooldown should still be able to override this. Tests: add tests for billing-limit detection, date parsing from stderr, long vs short cooldown classification. Run: cd ~/germline && uv run pytest assays/test_golem_daemon.py -x -q. Commit with clear message. (retry)"`

### Auto-requeue (2 tasks @ 13:50)
- [!] `golem [t-eb8bc3] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-0102d7] --provider infini --max-turns 30 "Health check: receptor-health, soma-scale, switch-layer, soma-wake, telophase, commensal, demethylase, consulting-card, provider-bench, rheotaxis-local. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 13:52)
- [!] `golem [t-7def6f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-361209] --provider zhipu --max-turns 30 "Health check: consulting-card, plan-exec, diapedesis, soma-activate, respirometry, synthase, coaching-stats, cg, assay, fix-symlinks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 13:54)
- [x] `golem [t-aa8b6c] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-3d44f2] --provider infini --max-turns 30 "Health check: golem-report, regulatory-scrape, hkicpa, update-compound-engineering-skills.sh, rheotaxis, grok, queue-balance, oci-region-subscribe, translocon, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 13:57)
- [!] `golem [t-913bc1] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [!] `golem [t-611c21] --provider infini --max-turns 30 "Health check: rheotaxis-local, tmux-osc52.sh, secrets-sync, weekly-gather, circadian-probe.py, overnight-gather, sortase, client-brief, oci-region-subscribe, diapedesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 13:59)
- [!] `golem [t-5b6d98] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-1f67e9] --provider volcano --max-turns 30 "Health check: soma-bootstrap, council, gog, golem-daemon, lacuna, grep, commensal, skill-sync, safe_rm.py, coaching-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:02)
- [!] `golem [t-6c93c0] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [!] `golem [t-47679f] --provider zhipu --max-turns 30 "Health check: circadian-probe.py, pharos-sync.sh, engram, golem-tools, phagocytosis.py, skill-search, judge, transduction-daily-run, demethylase, consulting-card. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:03)
- [!] `golem [t-370af5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-ef8a9b] --provider infini --max-turns 30 "Health check: paracrine, perplexity.sh, pulse-review, electroreception, lysis, disk-audit, gemmule-sync, plan-exec, cibus.py, soma-clean. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:04)
- [!] `golem [t-9a4784] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [!] `golem [t-b70299] --provider volcano --max-turns 30 "Health check: browse, chromatin-backup.py, client-brief, launchagent-health, phagocytosis.py, safe_rm.py, judge, publish, golem-dash, rename-kindle-asins.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:08)
- [!] `golem [t-36864e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-9bd3be] --provider infini --max-turns 30 "Health check: publish, electroreception, disk-audit, soma-wake, replisome, tmux-osc52.sh, golem, safe_search.py, conftest-gen, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:11)
- [!] `golem [t-29234c] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-22a00a] --provider zhipu --max-turns 30 "Health check: evident-brief, soma-status, provider-bench, orphan-scan, commensal, autoimmune.py, lustro-analyze, pinocytosis, golem-dash, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:14)
- [!] `golem [t-015a87] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-485415] --provider infini --max-turns 30 "Health check: plan-exec, soma-bootstrap, golem-review, skill-lint, exocytosis.py, commensal, publish, channel, soma-clean, overnight-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:16)
- [x] `golem [t-b15766] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [!] `golem [t-7c03ae] --provider infini --max-turns 30 "Health check: oci-arm-retry, soma-scale, autoimmune.py, golem-review, grep, test-spec-gen, transduction-daily-run, gemmation-env, pharos-env.sh, golem-validate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 14:20)
- [!] `golem [t-65807f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-b07b11] --provider infini --max-turns 30 "Health check: demethylase, oci-arm-retry, skill-search, test-spec-gen, assay, commensal, auto-update-compound-engineering.sh, oura-weekly-digest.py, telophase, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:20)
- [x] `golem [t-06f273] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-7556c5] --provider zhipu --max-turns 30 "Health check: soma-wake, rotate-logs.py, importin, golem-validate, gog, search-guard, golem-top, evident-brief, rename-plists, launchagent-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:21)
- [x] `golem [t-29cb0d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2472bd] --provider zhipu --max-turns 30 "Health check: soma-scale, git-activity, overnight-gather, med-tracker, pharos-sync.sh, centrosome, soma-pull, diapedesis, publish, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:24)
- [!] `golem [t-49eed7] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-d6bebc] --provider infini --max-turns 30 "Health check: oci-arm-retry, electroreception, replisome, queue-stats, immunosurveillance.py, golem-report, log-summary, commensal, backfill-marks, golem. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:29)
- [x] `golem [t-6fbf17] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-de64bc] --provider volcano --max-turns 30 "Health check: auto-update-compound-engineering.sh, translocon, coverage-map, assay, fix-symlinks, chemoreception.py, golem, complement, golem-daemon, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:29)
- [!] `golem [t-5c6eb5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-b01632] --provider infini --max-turns 30 "Health check: engram, coverage-map, golem-cost, disk-audit, chromatin-backup.py, replisome, soma-scale, golem-dash, tm, switch-layer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:31)
- [x] `golem [t-4135da] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ee6887] --provider volcano --max-turns 30 "Health check: quorum, golem-report, overnight-gather, effector-usage, skill-lint, soma-activate, assay, council, safe_search.py, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:33)
- [ ] `golem [t-9a91b6] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-ff9038] --provider zhipu --max-turns 30 "Health check: pharos-env.sh, golem-orchestrator, consulting-card, golem-report, inflammasome-probe, card-search, respirometry, backfill-marks, cn-route, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:35)
- [x] `golem [t-5cc0f8] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d2e150] --provider volcano --max-turns 30 "Health check: test-spec-gen, backup-due.sh, test-fixer, plan-exec, electroreception, golem-daemon, cg, poiesis, qmd-reindex.sh, browser. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:37)
- [ ] `golem [t-930635] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit. (retry)"`
- [x] `golem [t-5fd339] --provider zhipu --max-turns 30 "Health check: golem-daemon, regulatory-capture, consulting-card, chemoreception.py, test-spec-gen, soma-scale, soma-health, capco-prep, complement, lustro-analyze. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:40)
- [x] `golem [t-a97d6d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f0edea] --provider volcano --max-turns 30 "Health check: lacuna, quorum, soma-bootstrap, consulting-card, rename-kindle-asins.py, autoimmune.py, legatum, rheotaxis-local, client-brief, safe_search.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:47)
- [ ] `golem [t-ea50bf] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4030c4] --provider infini --max-turns 30 "Health check: gap_junction_sync, overnight-gather, oura-weekly-digest.py, centrosome, queue-stats, transduction-daily-run, engram, paracrine, taste-score, evident-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:49)
- [x] `golem [t-4be929] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-07aba8] --provider infini --max-turns 30 "Health check: chromatin-backup.py, mitosis-checkpoint.py, launchagent-health, electroreception, agent-sync.sh, linkedin-monitor, golem, browser, council, golem-daemon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 14:51)
- [ ] `golem [t-5a7786] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-437632] --provider infini --max-turns 30 "Health check: immunosurveillance.py, evident-brief, transduction-daily-run, safe_search.py, soma-snapshot, rheotaxis-local, auto-update-compound-engineering.sh, golem-daemon-wrapper.sh, judge, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:00)
- [ ] `golem [t-e9cb7f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-38af71] --provider zhipu --max-turns 30 "Health check: wacli-ro, queue-stats, mitosis-checkpoint.py, sortase, goose-worker, coaching-stats, golem-reviewer, pulse-review, gemmule-sync, methylation. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:05)
- [ ] `golem [t-f876a9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-c94102] --provider infini --max-turns 30 "Health check: hetzner-bootstrap.sh, queue-stats, tm, wacli-ro, golem-top, lacuna.py, mitosis-checkpoint.py, express, start-chrome-debug.sh, generate-solutions-index.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:06)
- [ ] `golem [t-63eb8e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-61d199] --provider infini --max-turns 30 "Health check: receptor-health, test-dashboard, council, transduction-daily-run, methylation-review, x-feed-to-lustro, agent-sync.sh, engram, soma-bootstrap, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:07)
- [ ] `golem [t-70ae76] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-e99ea5] --provider volcano --max-turns 30 "Health check: coverage-map, disk-audit, safe_rm.py, update-compound-engineering-skills.sh, golem-tools, capco-prep, rheotaxis-local, client-brief, golem-daemon-wrapper.sh, golem. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:13)
- [ ] `golem [t-991a07] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-0102e4] --provider zhipu --max-turns 30 "Health check: rg, search-guard, soma-health, launchagent-health, legatum-verify, soma-snapshot, pharos-env.sh, demethylase, soma-pull, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:14)
- [ ] `golem [t-f897c2] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-c8ff48] --provider zhipu --max-turns 30 "Health check: cn-route, channel, cytokinesis, gog, health-check, pinocytosis, client-brief, taste-score, switch-layer, cibus.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:16)
- [ ] `golem [t-b3a999] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-1c184a] --provider infini --max-turns 30 "Health check: golem-report, perplexity.sh, pulse-review, capco-brief, rheotaxis-local, vesicle, card-search, electroreception, maintenance-cron, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:18)
- [ ] `golem [t-0ba71f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-1e29ba] --provider zhipu --max-turns 30 "Health check: rename-kindle-asins.py, rotate-logs.py, conftest-gen, rename-plists, phagocytosis.py, plan-exec, pharos-sync.sh, golem-report, search-guard, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:24)
- [ ] `golem [t-9d5dce] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-9f79a3] --provider zhipu --max-turns 30 "Health check: rename-kindle-asins.py, sortase, methylation-review, auto-update-compound-engineering.sh, test-fixer, quorum, pharos-env.sh, transduction-daily-run, qmd-reindex.sh, capco-prep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:26)
- [ ] `golem [t-aae875] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-5db512] --provider zhipu --max-turns 30 "Health check: complement, coaching-stats, hkicpa, gog, taste-score, secrets-sync, maintenance-cron, browser, council, pharos-env.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:32)
- [ ] `golem [t-594440] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-f39593] --provider infini --max-turns 30 "Health check: hkicpa, consulting-card.py, golem-validate, regulatory-scrape, lacuna.py, rename-plists, soma-health, med-tracker, evident-brief, chromatin-decay-report.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:33)
- [ ] `golem [t-ec0945] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-976228] --provider volcano --max-turns 30 "Health check: golem-dash, council, immunosurveillance.py, engram, inflammasome-probe, health-check, proteostasis, golem-daemon, dr-sync, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:39)
- [ ] `golem [t-ffdece] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-bb39bf] --provider volcano --max-turns 30 "Health check: browse, cytokinesis, gemmation-env, channel, soma-scale, pinocytosis, auto-update-compound-engineering.sh, circadian-probe.py, soma-clean, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:45)
- [ ] `golem [t-8274be] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-e893b1] --provider zhipu --max-turns 30 "Health check: receptor-scan, queue-balance, cleanup-stuck, git-activity, channel, goose-worker, nightly, golem-dash, importin, pharos-env.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:49)
- [ ] `golem [t-db44a5] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-22b336] --provider zhipu --max-turns 30 "Health check: log-summary, golem-orchestrator, telophase, soma-health, evident-brief, oci-region-subscribe, exocytosis.py, golem-dash, channel, soma-scale. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:54)
- [ ] `golem [t-78f4a1] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-fd4fd8] --provider infini --max-turns 30 "Health check: grok, git-activity, skill-search, complement, exocytosis.py, switch-layer, dr-sync, phagocytosis.py, conftest-gen, autoimmune.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 15:55)
- [ ] `golem [t-8b4fb3] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-d3b3e7] --provider zhipu --max-turns 30 "Health check: golem-daemon, soma-health, lacuna.py, med-tracker, skill-lint, poiesis, commensal, orphan-scan, agent-sync.sh, rotate-logs.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:06)
- [ ] `golem [t-58c32c] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-9ff79c] --provider zhipu --max-turns 30 "Health check: cibus.py, express, card-search, tmux-url-select.sh, rheotaxis, test-fixer, publish, update-coding-tools.sh, find, golem-reviewer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:07)
- [ ] `golem [t-2e3345] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-f694dd] --provider infini --max-turns 30 "Health check: golem-dash, replisome, generate-solutions-index.py, golem-tools, exocytosis.py, update-coding-tools.sh, compound-engineering-status, soma-clean, consulting-card.py, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:08)
- [ ] `golem [t-1ac536] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-66018b] --provider zhipu --max-turns 30 "Health check: chromatin-backup.sh, gemmation-env, commensal, electroreception, consulting-card, maintenance-cron, launchagent-health, fasti, golem-validate, regulatory-capture. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:13)
- [ ] `golem [t-1a18fc] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-979598] --provider infini --max-turns 30 "Health check: telophase, perplexity.sh, immunosurveillance, start-chrome-debug.sh, cleanup-stuck, update-compound-engineering-skills.sh, nightly, chromatin-backup.sh, dr-sync, photos.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:17)
- [ ] `golem [t-cf0a21] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-abbb7b] --provider volcano --max-turns 30 "Health check: effector-usage, legatum-verify, soma-watchdog, update-compound-engineering, soma-wake, paracrine, cg, regulatory-scrape, update-compound-engineering-skills.sh, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 16:22)
- [ ] `golem [t-f8987a] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-b76304] --provider volcano --max-turns 30 "Health check: regulatory-capture, golem-reviewer, log-summary, publish, bud, rg, test-spec-gen, taste-score, rotate-logs.py, chromatin-decay-report.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-246f7e] [t-cookiefix] --provider zhipu --max-turns 40 "Fix cookie bridge on Mac at ~/bin/cookie-bridge. READ the full file first. Bug: Chrome v10 cookies decrypt with garbled first 16 bytes — the first AES-CBC block produces garbage while remaining blocks are correct. This means the derived key or IV is slightly wrong for the first block. The script uses PBKDF2(chrome_safe_storage_key, b'saltysalt', 1003, 16) with AES-128-CBC and iv=b' '*16. Chrome may have changed to include a per-cookie nonce in the first 3 bytes after the v10 prefix, or the IV derivation changed. Research current Chrome v10 cookie encryption (2025-2026) and fix. Also add: (1) /health endpoint that returns 200 OK. (2) Bind to 0.0.0.0 not just Tailscale IP so localhost works too. (3) Add /cookies endpoint that returns Playwright-compatible JSON format (name, value, domain, path, expires, httpOnly, secure, sameSite). (4) Fix the LaunchAgent plist at ~/Library/LaunchAgents/com.vivesca.cookie-bridge.plist if it exists, or create one. Test: curl http://localhost:9742/health returns 200; curl http://localhost:9742/cookies?domain=google.com returns valid decrypted cookies. Commit."`
