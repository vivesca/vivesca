### Test queue (project namespace isolation)
- [x] `golem [t-8a716f] [t-test-zh] --provider zhipu --max-turns 5 "Create /tmp/golem-test-zhipu.txt with 'ZHIPU_OK' and timestamp. Verify with cat. (retry)"`
- [x] `golem [t-0430ed] [t-test-vc] --provider volcano --max-turns 5 "Create /tmp/golem-test-volcano.txt with 'VOLCANO_OK' and timestamp. Verify with cat. (retry)"`
- [x] `golem [t-43d180] [t-test-in] --provider infini --max-turns 5 "Create /tmp/golem-test-infini.txt with 'INFINI_OK' and timestamp. Verify with cat."`

### Auto-requeue (7 tasks @ 21:32)
- [x] `golem [t-b9c778] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit. (retry)"`
- [ ] `golem [t-cd95a2] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-341bb6] --provider infini --max-turns 40 "Run git log --oneline --since='24 hours ago' --author=golem | head -10. For each commit: git show <hash> --stat. Pick the 3 largest diffs. For each: read the changed file, check for assert True stubs, empty functions, broken logic, missing error handling. Fix issues. Run uv run pytest on affected files. Commit."`
- [ ] `golem [t-af9bda] --provider volcano --max-turns 30 "Run uv run ruff check metabolon/ --select E,W,F --output-format=concise 2>&1 | head -30. Fix the first 15 issues. Run ruff check again to verify. Commit. (retry)"`
- [x] `golem [t-4c8388] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-940412] --provider infini --max-turns 30 "Health check: regulatory-capture, golem-cost, soma-status, ck, pulse-review, provider-bench, judge, rheotaxis, methylation-review, soma-snapshot. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-2ad8ff] --provider volcano --max-turns 25 "Run uv run ruff check metabolon/ --select F401,F841 --output-format=concise 2>&1 | head -20. These are unused imports (F401) and unused variables (F841). Fix all of them. Run ruff check again. Commit. (retry)"`

### Auto-requeue (2 tasks @ 21:32)
- [ ] `golem [t-4b410c] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-bdb072] --provider volcano --max-turns 30 "Health check: effector-usage, launchagent-health, chemoreception.py, skill-search, replisome, golem-report, golem-daemon-wrapper.sh, coaching-stats, switch-layer, cibus.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit. (retry)"`

### Auto-requeue (2 tasks @ 21:33)
- [ ] `golem [t-12ef22] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-5c9616] --provider volcano --max-turns 30 "Health check: pharos-health.sh, receptor-health, chat_history.py, rename-plists, switch-layer, dr-sync, golem-top, golem-daemon, golem-dash, soma-scale. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:33)
- [ ] `golem [t-ab98e1] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-27d0d7] --provider volcano --max-turns 30 "Health check: replisome, golem-report, generate-solutions-index.py, switch-layer, lacuna, mismatch-repair, rename-kindle-asins.py, backup-due.sh, secrets-sync, golem-cost. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:34)
- [ ] `golem [t-e75769] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-30107a] --provider infini --max-turns 30 "Health check: skill-lint, secrets-sync, express, demethylase, channel, chromatin-decay-report.py, receptor-health, rename-kindle-asins.py, switch-layer, mismatch-repair. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:34)
- [ ] `golem [t-3a01c0] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-cfddf6] --provider zhipu --max-turns 30 "Health check: effector-usage, soma-watchdog, tm, hetzner-bootstrap.sh, electroreception, mismatch-repair, transduction-daily-run, telophase, goose-worker, soma-bootstrap. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:35)
- [ ] `golem [t-587ed7] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-2b31ab] --provider zhipu --max-turns 30 "Health check: mismatch-repair, chemoreception.py, plan-exec, soma-wake, cn-route, skill-sync, rheotaxis-local, assay, evident-brief, pharos-env.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:35)
- [ ] `golem [t-ecd4b9] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-e43e7c] --provider volcano --max-turns 30 "Health check: lacuna, update-compound-engineering-skills.sh, chromatin-backup.py, compound-engineering-test, soma-pull, update-coding-tools.sh, coaching-stats, mismatch-repair, golem-dash, golem-validate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:36)
- [ ] `golem [t-9637f3] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-b72134] --provider infini --max-turns 30 "Health check: tm, wacli-ro, sortase, soma-health, paracrine, regulatory-scan, queue-balance, golem-cost, exocytosis.py, regulatory-scrape. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:36)
- [ ] `golem [t-3571a5] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-66424d] --provider zhipu --max-turns 30 "Health check: porta, qmd-reindex.sh, browse, soma-health, tmux-workspace.py, rheotaxis, tmux-osc52.sh, search-guard, poiesis, mitosis-checkpoint.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:37)
- [ ] `golem [t-1fbdbe] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-f58922] --provider volcano --max-turns 30 "Health check: golem-health, golem-dash, soma-activate, compound-engineering-status, golem-report, golem-daemon-wrapper.sh, secrets-sync, plan-exec, weekly-gather, golem-validate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:37)
- [ ] `golem [t-69ea51] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-a7f858] --provider zhipu --max-turns 30 "Health check: channel, soma-health, client-brief, express, pinocytosis, soma-scale, browse, rotate-logs.py, golem-daemon, golem. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:38)
- [ ] `golem [t-339628] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-22ee62] --provider volcano --max-turns 30 "Health check: grok, evident-brief, transduction-daily-run, safe_rm.py, safe_search.py, methylation-review, browse, golem-top, conftest-gen, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:39)
- [ ] `golem [t-036c2f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-1de730] --provider zhipu --max-turns 30 "Health check: cleanup-stuck, x-feed-to-lustro, consulting-card.py, browse, generate-solutions-index.py, oci-arm-retry, golem-health, golem-reviewer, conftest-gen, agent-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:39)
- [ ] `golem [t-9c5a9d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-50a877] --provider infini --max-turns 30 "Health check: inflammasome-probe, golem-dash, mitosis-checkpoint.py, browse, grok, golem-health, chemoreception.py, soma-clean, cn-route, soma-activate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:40)
- [ ] `golem [t-08bc58] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-f8191d] --provider zhipu --max-turns 30 "Health check: photos.py, assay, secrets-sync, golem-validate, golem-report, golem, capco-brief, chat_history.py, nightly, regulatory-scrape. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:40)
- [ ] `golem [t-a33720] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-3b09a4] --provider zhipu --max-turns 30 "Health check: client-brief, paracrine, soma-watchdog, gemmation-env, mitosis-checkpoint.py, find, card-search, golem-report, demethylase, maintenance-cron. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:41)
- [ ] `golem [t-27669d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-fc9558] --provider volcano --max-turns 30 "Health check: capco-prep, skill-sync, telophase, provider-bench, perplexity.sh, lysis, rheotaxis-local, poiesis, capco-brief, rename-kindle-asins.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:41)
- [ ] `golem [t-3162b9] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-a60c07] --provider volcano --max-turns 30 "Health check: soma-clean, nightly, coaching-stats, demethylase, maintenance-cron, queue-stats, autoimmune.py, tmux-workspace.py, golem-tools, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:42)
- [ ] `golem [t-c265d9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-6464c6] --provider infini --max-turns 30 "Health check: soma-watchdog, med-tracker, gog, bud, rheotaxis-local, transduction-daily-run, synthase, find, rheotaxis, cn-route. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:43)
- [ ] `golem [t-2ca23a] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-c69d23] --provider zhipu --max-turns 30 "Health check: regulatory-capture, paracrine, pharos-env.sh, lustro-analyze, golem, vesicle, goose-worker, chromatin-backup.py, regulatory-scrape, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:43)
- [ ] `golem [t-6442a3] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-1ee943] --provider infini --max-turns 30 "Health check: soma-wake, med-tracker, regulatory-scrape, photos.py, telophase, cleanup-stuck, consulting-card, centrosome, express, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:44)
- [ ] `golem [t-f17336] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-2750f1] --provider volcano --max-turns 30 "Health check: bud, lysis, assay, browse, exocytosis.py, pulse-review, sortase, judge, pharos-env.sh, evident-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:44)
- [ ] `golem [t-3ee92d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-14152c] --provider infini --max-turns 30 "Health check: oci-region-subscribe, grok, efferens, quorum, test-fixer, autoimmune.py, test-spec-gen, switch-layer, update-compound-engineering, pharos-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 21:45)
- [ ] `golem [t-de9a4a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-4efe8e] --provider infini --max-turns 30 "Health check: centrosome, update-compound-engineering, cg, dr-sync, efferens, evident-brief, pharos-health.sh, wewe-rss-health.py, poiesis, immunosurveillance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
