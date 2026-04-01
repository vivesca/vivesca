### Pending (deduped 2026-04-02)
- [x] `golem [t-ce29a0] --provider zhipu --max-turns 30 "Health check: log-summary, rheotaxis, engram, lacuna.py, med-tracker, golem-report, provider-bench, secrets-sync, immunosurveillance, golem-dash. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8a1025] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5276a3] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-03ff8b] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b605e1] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8238e6] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a79a5f] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-096d86] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-c7d8f6] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-27bf7b] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-c5d1cf] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-e40dc4] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-6d6ceb] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-23a102] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-eb3cb4] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-594c73] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-1d6f31] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-89dc69] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-3db579] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-527d0f] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-70f801] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-c41543] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-7e3459] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-fc04dc] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-137116] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:20)
- [x] `golem [t-236f77] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-6bf5b7] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-f760ed] --provider zhipu --max-turns 30 "Health check: cn-route, gemmule-sync, agent-sync.sh, rotate-logs.py, log-summary, circadian-probe.py, weekly-gather, complement, compound-engineering-status, test-fixer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a9ac00] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-9f3e8c] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-53c0b2] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0cf0f1] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3e0942] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-688619] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-46e4d0] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-09cc92] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-f80870] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-ef4c64] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-64ff10] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:21)
- [x] `golem [t-a47dd5] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-3c595d] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-035481] --provider volcano --max-turns 30 "Health check: tmux-osc52.sh, client-brief, safe_rm.py, test-fixer, legatum, browser, channel, update-compound-engineering, auto-update-compound-engineering.sh, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-339e04] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cb9ff6] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-719531] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-044ab3] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f4e788] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bfe359] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-9a3a16] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-372c3e] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-fc6a56] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9fbc55] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-71305b] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:22)
- [x] `golem [t-b6dcb0] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-8fc7ab] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-8c1ee5] --provider volcano --max-turns 30 "Health check: channel, methylation-review, update-compound-engineering, centrosome, pulse-review, exocytosis.py, photos.py, lysis, perplexity.sh, fix-symlinks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b100ca] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d44adb] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-26ba31] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-702620] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a6647f] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-759293] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-f5540f] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-8428d2] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-062e5d] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-7e4a48] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-600d27] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-e2417e] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-3b32c5] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-49308b] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-2fbf9e] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-2d9873] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-54ba58] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-42e0a8] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-9fcc7f] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-62f49c] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-bbdd0c] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-375037] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:23)
- [x] `golem [t-21a92d] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-c05265] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-ccd823] --provider zhipu --max-turns 30 "Health check: pharos-sync.sh, synthase, cleanup-stuck, perplexity.sh, grep, pharos-env.sh, gog, mitosis-checkpoint.py, update-coding-tools.sh, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-743825] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-198b87] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-55cadb] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-00ac22] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-aea471] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-14f839] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-9ebcfb] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-5e1231] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-beb8b7] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-695022] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-1669ae] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-8fddbe] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-6047c5] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-c924b2] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-aacc85] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-30b01e] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-539ad5] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-75f3fa] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-a459f5] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-1dc327] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-0e0728] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-8600b8] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-8f52cc] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-0ab054] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-d1373c] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-01e65c] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-a7321e] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-25e9be] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-ccc15c] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-6e6249] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-bd62ff] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-013b92] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-ca353b] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:23)
- [x] `golem [t-09d5a5] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-5f2f81] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-b685bb] --provider infini --max-turns 30 "Health check: golem-orchestrator, pulse-review, auto-update-compound-engineering.sh, phagocytosis.py, rename-plists, telophase, x-feed-to-lustro, soma-activate, judge, log-summary. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-2ac196] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8b3dba] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cfbc3e] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-49fc09] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7f01d9] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3ef059] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-ba0928] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-7a5ea0] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-e775e4] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-f85cc6] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-321cae] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:24)
- [x] `golem [t-a5640a] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-0eef00] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-6dbdef] --provider infini --max-turns 30 "Health check: secrets-sync, coaching-stats, demethylase, regulatory-scrape, oura-weekly-digest.py, golem-dash, methylation-review, golem-orchestrator, importin, auto-update-compound-engineering.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-94ddf7] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c1a6fe] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-17bbd5] --provider infini --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-48feed] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ca716d] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e34241] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-2e7450] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-987104] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-3d87b0] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-bd76df] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-4e95ac] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-0185d8] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-5d4fcd] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-a8a995] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-dcc360] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-cf3df9] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-e37101] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-c3f941] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-a5c0cd] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-3ab1f1] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-308513] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-9fb925] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:25)
- [x] `golem [t-e915dc] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-64cba9] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-fedf3d] --provider infini --max-turns 30 "Health check: cleanup-stuck, golem-cost, soma-snapshot, complement, queue-gen, launchagent-health, update-compound-engineering, coverage-map, golem, vesicle. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-cf0276] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5a534e] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-909412] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-dfb291] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ef1c7e] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bf7f24] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-50a2cf] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-dadf31] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-e7ff2e] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-1f576b] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-928c1b] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-8a7c6d] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-0b39a0] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-0dd296] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-033e57] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-cb2ebf] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-f99c3a] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-a67cf0] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-b497ea] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-874e8e] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-cb03fe] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-2aae61] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-5b3cd5] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-c809d1] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-331fe9] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-246c5e] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-2bfa59] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-b20eab] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-3169fb] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-4e5703] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-b44fd1] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-dfe0f2] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-b12c6b] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:25)
- [x] `golem [t-f8b5c4] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-0bb77b] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-d2a4b0] --provider zhipu --max-turns 30 "Health check: commensal, health-check, regulatory-capture, proteostasis, pulse-review, log-summary, test-spec-gen, respirometry, methylation, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b53ea0] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a94d42] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f5dd05] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-44cc29] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-65d004] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-1a6548] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-cdc9e2] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-e3b0dd] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-eb4b49] --provider zhipu --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-898d5a] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b6d33c] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:26)
- [x] `golem [t-67688e] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-474092] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-42e389] --provider zhipu --max-turns 30 "Health check: complement, golem-report, cg, cookie-sync, importin, tmux-url-select.sh, update-compound-engineering-skills.sh, rg, cn-route, skill-lint. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b752c8] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-1f415e] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-41040f] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-45c01a] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3e16bd] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-953f14] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-15d0b0] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-b01370] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-a567d0] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9151cd] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-67531e] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`
- [x] `golem [t-ba9cd8] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-870f31] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-47a1b5] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-275dd4] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-af9c6f] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-050745] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-d696c1] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-55b2f9] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-628a95] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-94b963] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-94f17c] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-bfb9f1] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-f53811] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-4a102a] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-9d9def] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-b88f75] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-224f31] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-7b4968] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-4e2e3b] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-ea7d2d] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-af73fa] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-db4f57] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-077ce0] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-9fa064] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-8d0385] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-0f33df] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-7362ee] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-5be24f] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-78c8a6] --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem [t-0b43bd] --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-782106] --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-5fe899] --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem [t-c6feee] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (14 tasks @ 05:27)
- [x] `golem [t-e6d4aa] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-f8eac5] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-b86c1a] --provider volcano --max-turns 30 "Health check: rg, conftest-gen, git-activity, perplexity.sh, chromatin-decay-report.py, find, soma-bootstrap, regulatory-scan, fasti, compound-engineering-status. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-249cb7] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4bcc94] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a89591] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ddf7d9] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ad6b2e] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-eab3ac] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-fa92b9] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-ad4ddf] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-bafc79] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-dadd1c] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9c3ffb] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:27)
- [x] `golem [t-3dc811] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-b02100] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-d43042] --provider infini --max-turns 30 "Health check: cookie-sync, hetzner-bootstrap.sh, client-brief, soma-pull, golem-health, coverage-map, chat_history.py, find, quorum, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-03dfa8] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-34a425] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-65db49] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-745ec4] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7cc1d0] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7ade89] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-818c9b] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-57e949] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-a178a1] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-555a41] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-315505] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:28)
- [x] `golem [t-d927b5] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-0cbdf0] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-90640e] --provider zhipu --max-turns 30 "Health check: pulse-review, nightly, tmux-url-select.sh, lustro-analyze, quorum, coaching-stats, phagocytosis.py, soma-health, exocytosis.py, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-330c17] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-69152b] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-df5da7] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-91de76] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5f8a84] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-39838f] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-7aa242] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-e835f3] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-e03a24] --provider zhipu --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-e24bf5] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-7da1be] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:28)
- [x] `golem [t-781656] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-a90f8c] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-586ce5] --provider zhipu --max-turns 30 "Health check: golem-orchestrator, git-activity, start-chrome-debug.sh, cn-route, backfill-marks, grep, test-dashboard, rg, cg, generate-solutions-index.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9e57b5] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ae10ee] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a060e3] --provider zhipu --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e33c41] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f489de] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cdcad3] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-f8253d] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-6985a1] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-8282e1] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-ced59a] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2c3a65] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:29)
- [x] `golem [t-19be7f] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-ce6969] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-831b3b] --provider infini --max-turns 30 "Health check: qmd-reindex.sh, soma-bootstrap, x-feed-to-lustro, golem-report, efferens, capco-brief, update-coding-tools.sh, backfill-marks, grok, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-11994c] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-9a72bf] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-995148] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7f6f96] --provider volcano --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-033c13] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a69f02] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-119c26] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-bcdb40] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-442330] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-c2c120] --provider volcano --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-81fb54] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:29)
- [x] `golem [t-09e683] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-1b5ad1] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-59d4c2] --provider zhipu --max-turns 30 "Health check: card-search, golem-health, golem-validate, hetzner-bootstrap.sh, update-coding-tools.sh, update-compound-engineering-skills.sh, log-summary, update-compound-engineering, synthase, respirometry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-f5d518] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ed03e5] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-411e8f] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7d2fb8] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2c1ae0] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a0ac6b] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-a7dec4] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-557288] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f1db37] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-0d2b45] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-d64412] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:30)
- [x] `golem [t-17308d] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-7fb8a8] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-100d82] --provider zhipu --max-turns 30 "Health check: legatum-verify, coverage-map, porta, golem-reviewer, soma-activate, centrosome, perplexity.sh, golem-top, importin, capco-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-c9d9ef] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c50d2f] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6380da] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-35d45f] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f80068] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ce8c5d] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-97d5e4] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-259736] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-b37465] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-3003f0] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-147a66] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:31)
- [x] `golem [t-89f31f] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-54de9e] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-44fa73] --provider volcano --max-turns 30 "Health check: med-tracker, find, lacuna.py, lacuna, auto-update-compound-engineering.sh, linkedin-monitor, sortase, oci-arm-retry, golem-dash, vesicle. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-1f65f2] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0ea322] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8f387b] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4d2806] --provider zhipu --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-545d43] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-300d98] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-4e917a] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-61eae3] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-f766ff] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-43cb68] --provider zhipu --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-6685dc] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:31)
- [x] `golem [t-8f1224] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-42f41a] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-8e38a2] --provider volcano --max-turns 30 "Health check: queue-balance, cookie-sync, goose-worker, x-feed-to-lustro, chemoreception.py, med-tracker, synthase, golem-cost, soma-watchdog, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-805300] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-00b164] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ef5775] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e3f839] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-919fb6] --provider infini --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-399d0b] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-a7ff43] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-63a677] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-5f58c4] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-349629] --provider zhipu --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-69b803] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:32)
- [x] `golem [t-a2573d] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-1435c1] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-aca3d4] --provider infini --max-turns 30 "Health check: rheotaxis, soma-scale, dr-sync, phagocytosis.py, regulatory-scrape, golem-health, backfill-marks, oura-weekly-digest.py, chat_history.py, rg. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-99cbab] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fa11c7] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d7d852] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4d4504] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-46492f] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b64a36] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-5e7f5f] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f80fa5] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-7f0bc4] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2110d7] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-d37f90] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:32)
- [x] `golem [t-e3118b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-1ad942] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-51e197] --provider volcano --max-turns 30 "Health check: oci-region-subscribe, soma-scale, wewe-rss-health.py, paracrine, grok, translocon, queue-gen, engram, regulatory-scrape, queue-balance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8302c7] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e27110] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-998dc9] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e70077] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-55e5fb] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-33a8ba] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-32184d] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-17d7ca] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-9edb04] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-c33b58] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-1e1fe0] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:33)
- [x] `golem [t-8a282f] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-8bbdb7] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-4c66b2] --provider volcano --max-turns 30 "Health check: photos.py, tmux-osc52.sh, health-check, centrosome, lacuna, rheotaxis, find, poiesis, secrets-sync, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a92953] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-145fae] --provider infini --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bfa5a3] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b2550f] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3c15ac] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-744091] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-acd89e] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-c6d326] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-38b7fd] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-120f8b] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-4a6596] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:34)
- [x] `golem [t-212bc1] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-555239] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-ca1017] --provider volcano --max-turns 30 "Health check: sortase, judge, demethylase, goose-worker, orphan-scan, photos.py, exocytosis.py, chat_history.py, health-check, client-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-aea747] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8a9a35] --provider infini --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-933089] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5adffc] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-dd8d03] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f9086e] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-6c0e00] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-aef3f7] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-a944f2] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-7bd0da] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-e61324] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:35)
- [x] `golem [t-89d0a0] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-d2e6a3] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-3e2ff5] --provider infini --max-turns 30 "Health check: compound-engineering-status, effector-usage, pharos-health.sh, taste-score, phagocytosis.py, sortase, lysis, express, methylation-review, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-09e5f5] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ec14e9] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bb5914] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-93285f] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-1de936] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-16abe0] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-101e27] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-fdba12] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-ab01f5] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-ba16dc] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-0ad911] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:35)
- [x] `golem [t-11a4e8] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-6a23e3] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-1db684] --provider volcano --max-turns 30 "Health check: skill-search, taste-score, skill-lint, assay, rg, phagocytosis.py, pharos-health.sh, backfill-marks, perplexity.sh, soma-clean. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-97ab9b] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-03a80d] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bd69eb] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2f5c39] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-10430a] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6934f5] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-545298] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-aaf22f] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-d20995] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-70f0fb] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-95e6dd] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:36)
- [x] `golem [t-83ee50] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-72dee3] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-e0384b] --provider zhipu --max-turns 30 "Health check: find, mitosis-checkpoint.py, skill-lint, effector-usage, compound-engineering-test, sortase, cookie-sync, golem-daemon, taste-score, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b95599] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c81618] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e228c1] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-da86f1] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c383d7] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-381e4b] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-80dcc5] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-c45ab7] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-b0725f] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-7dd87e] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-669b4f] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:37)
- [x] `golem [t-0dc23a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-d1d0ab] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-91c946] --provider volcano --max-turns 30 "Health check: rheotaxis-local, golem-report, regulatory-scrape, queue-stats, complement, secrets-sync, commensal, chromatin-backup.sh, soma-pull, capco-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-10c374] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8c1391] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-08bc37] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a77a21] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5220c6] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f7460f] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-b0ee75] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-ffaea4] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-9f0e6f] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2d8aaa] --provider zhipu --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9ebd95] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:37)
- [x] `golem [t-c9d744] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-80e1a6] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-dfd5ef] --provider infini --max-turns 30 "Health check: switch-layer, circadian-probe.py, golem-report, autoimmune.py, safe_search.py, publish, soma-scale, soma-clean, replisome, fasti. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-879158] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-643ca5] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7fc8ce] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e8e6e0] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-277e62] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-9f9fc5] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-c1cda0] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-e01b48] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-b09e53] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-38273c] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b1c026] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:38)
- [x] `golem [t-f39e4b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-1b1639] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-cd534c] --provider volcano --max-turns 30 "Health check: golem-review, capco-prep, cg, pulse-review, orphan-scan, regulatory-capture, soma-wake, lacuna.py, lustro-analyze, coaching-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a99ba6] --provider zhipu --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-46bda1] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-05f56a] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-305df8] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fa3f72] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-464795] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-c57e2d] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-32387b] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-1d18d3] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b3e32f] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-8344cf] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:38)
- [x] `golem [t-be9f79] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-9ae78f] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-5e4be5] --provider zhipu --max-turns 30 "Health check: soma-scale, quorum, rotate-logs.py, med-tracker, soma-health, tmux-osc52.sh, card-search, bud, nightly, soma-wake. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-91472f] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cec20b] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-be6f70] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b0a446] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b25ff1] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7fe6fc] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-75ea4f] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-cb8bac] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-4f55a2] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2aa7f6] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b17b5b] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:39)
- [x] `golem [t-388a9c] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-a9a932] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-e605e7] --provider zhipu --max-turns 30 "Health check: med-tracker, linkedin-monitor, effector-usage, generate-solutions-index.py, agent-sync.sh, methylation, legatum-verify, find, fix-symlinks, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-f354c5] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7cde2c] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8dc4bd] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0885b9] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-e4ff0c] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5a8d8f] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-a27ec0] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-d9da82] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-f8462e] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-17d825] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-486e0a] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:39)
- [x] `golem [t-4034ab] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-b81f46] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-f5a588] --provider infini --max-turns 30 "Health check: chromatin-decay-report.py, git-activity, grok, autoimmune.py, golem-dash, gog, queue-gen, tmux-workspace.py, mitosis-checkpoint.py, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-298597] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4d1e4a] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a6a8d2] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0b9557] --provider volcano --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5bfd73] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-1708ca] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-1cd694] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-a11f3e] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-551d89] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2b4608] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-f05609] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:40)
- [x] `golem [t-519454] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-99aa47] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-86c543] --provider infini --max-turns 30 "Health check: cibus.py, centrosome, legatum-verify, disk-audit, plan-exec, perplexity.sh, test-fixer, update-coding-tools.sh, git-activity, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-118341] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fa833d] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f8df8a] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a5b50a] --provider volcano --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8f132a] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6cafb0] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-2165d6] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-7e1788] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-b7eb80] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-15b5d5] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-38c730] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:41)
- [x] `golem [t-ad9033] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-405587] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-fc7716] --provider infini --max-turns 30 "Health check: grep, skill-search, respirometry, proteostasis, electroreception, rheotaxis, pulse-review, circadian-probe.py, pharos-env.sh, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-684661] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b64f1f] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-286bd8] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-975a34] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a5b654] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-12687d] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-2cf7d4] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-c3fb3e] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-d911a2] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-e90834] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-8c77ad] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:41)
- [x] `golem [t-3b4c27] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-d588fc] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-065951] --provider volcano --max-turns 30 "Health check: transduction-daily-run, bud, disk-audit, publish, coaching-stats, rg, pulse-review, taste-score, hetzner-bootstrap.sh, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9e65a8] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-99d794] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cd3e2c] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-711cef] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5acf92] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-66ac13] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-853d42] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-a5da89] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-cc6307] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-85ed6d] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-48e7c5] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:42)
- [x] `golem [t-c4fce0] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-8d063e] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-e5c86a] --provider zhipu --max-turns 30 "Health check: chat_history.py, exocytosis.py, golem-orchestrator, safe_search.py, poiesis, express, legatum-verify, golem, pharos-env.sh, capco-prep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-ab3c55] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3ae911] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-38dea6] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-02e9e9] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fc8226] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8aad83] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-b557d5] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-31258a] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-a06864] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-18fea9] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-81e9ec] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:42)
- [x] `golem [t-b6f107] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-8aeb0f] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-57ea7d] --provider volcano --max-turns 30 "Health check: assay, judge, weekly-gather, provider-bench, golem-cost, skill-lint, photos.py, plan-exec, oura-weekly-digest.py, fasti. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-399152] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-761234] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bf9a2c] --provider volcano --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a968e1] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-411185] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2cfd5c] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-498688] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-3ca96f] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-98749f] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-2c20f0] --provider zhipu --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-72885d] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:43)
- [x] `golem [t-20289b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-6aa614] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-b349e9] --provider volcano --max-turns 30 "Health check: poiesis, overnight-gather, skill-sync, soma-watchdog, golem-top, skill-search, golem-review, oci-arm-retry, immunosurveillance.py, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-01720f] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f49fd1] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-79c354] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a68b23] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5ec8fa] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-61c093] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-6b2aa1] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-4d1e16] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-801d9b] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-aa9643] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-a2d35e] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:43)
- [x] `golem [t-c68f6e] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-6b60cf] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-c9ae0d] --provider zhipu --max-turns 30 "Health check: lustro-analyze, ck, search-guard, channel, golem-validate, quorum, perplexity.sh, switch-layer, inflammasome-probe, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-59f783] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-84b9ac] --provider volcano --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5c4f1a] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7b8ed2] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0759fa] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-52955a] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-e0ff3e] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-3ec5a1] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-96e7a4] --provider zhipu --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-6c87d2] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-db51df] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:44)
- [x] `golem [t-b790b6] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-8576a0] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-601ea7] --provider volcano --max-turns 30 "Health check: gog, coverage-map, weekly-gather, update-coding-tools.sh, legatum-verify, autoimmune.py, oci-arm-retry, queue-gen, vesicle, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-25b858] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-82b23b] --provider infini --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cc0f1c] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-badfb5] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8df81b] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6a8620] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-05b7ec] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-cf0696] --provider infini --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-4588c8] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-34802f] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b41fb7] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 05:44)
- [x] `golem [t-f30a4b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-293ec1] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-0dbcf5] --provider volcano --max-turns 30 "Health check: rg, soma-scale, update-compound-engineering, cibus.py, gemmation-env, transduction-daily-run, pharos-health.sh, secrets-sync, log-summary, qmd-reindex.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9926bc] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fce1da] --provider infini --max-turns 30 "Write tests for effectors/fasti. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cd08da] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6d5e1e] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-459793] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-952a21] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-895ef4] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-230994] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-339fe4] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-278991] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9e1039] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_hetzner_bootstrap.sh.py for effectors/hetzner-bootstrap.sh. Run uv run pytest assays/test_hetzner_bootstrap.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-7acaea] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-f18988] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-5f7045] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-6f365e] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-6b5f0d] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-68a949] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-e8edf2] --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-058321] --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-bcd7a7] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-42c34c] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-cde740] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-9f7b08] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-c8237a] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-f312c6] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-6cdb11] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-f89a52] --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-320060] --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-394987] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-26a563] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-8b9265] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-1e0daf] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-dbf24b] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-0a6c6c] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-b6b6ba] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-12f3a3] --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-056526] --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-e7911b] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-f4f324] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-ca9a4d] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-665f1e] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-522f21] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-6e7191] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-d0dd31] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-2451d0] --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-db0c49] --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-c4ce98] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [x] `golem [t-5871aa] --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [x] `golem [t-447a4d] --provider zhipu --max-turns 50 "Write assays/test_backup_due.sh.py for effectors/backup-due.sh. Run uv run pytest assays/test_backup_due.sh.py -v --tb=short."`
- [x] `golem [t-bc627f] --provider volcano --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [x] `golem [t-5f3653] --provider infini --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [x] `golem [t-db3fc8] --provider zhipu --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [x] `golem [t-13a896] --provider infini --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [x] `golem [t-a190b8] --provider zhipu --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [x] `golem [t-51f7db] --provider volcano --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [x] `golem [t-adbb42] --provider infini --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`

### Auto-requeue (8 tasks @ 06:00)
- [x] `golem [t-ab8e37] --provider volcano --max-turns 40 "Run git log --oneline --since='24 hours ago' --author=golem | head -10. For each commit: git show <hash> --stat. Pick the 3 largest diffs. For each: read the changed file, check for assert True stubs, empty functions, broken logic, missing error handling. Fix issues. Run uv run pytest on affected files. Commit."`
- [x] `golem [t-0377ef] --provider zhipu --max-turns 30 "Run uv run ruff check metabolon/ --select E,W,F --output-format=concise 2>&1 | head -30. Fix the first 15 issues. Run ruff check again to verify. Commit."`
- [x] `golem [t-64105b] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-462f74] --provider volcano --max-turns 30 "Health check: centrosome, gemmation-env, provider-bench, browse, soma-watchdog, compound-engineering-test, efferens, golem-reviewer, coaching-stats, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8c0aea] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_add.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_add.py -v --tb=short. Commit."`
- [x] `golem [t-624d99] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_init.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_init.py -v --tb=short. Commit."`
- [x] `golem [t-2a68b3] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test___init__.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test___init__.py -v --tb=short. Commit."`
- [x] `golem [t-512275] --provider zhipu --max-turns 25 "Run uv run ruff check metabolon/ --select F401,F841 --output-format=concise 2>&1 | head -20. These are unused imports (F401) and unused variables (F841). Fix all of them. Run ruff check again. Commit."`

### Auto-requeue (5 tasks @ 06:00)
- [x] `golem [t-540b3a] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-67fdac] --provider zhipu --max-turns 30 "Health check: cookie-sync, soma-clean, tmux-url-select.sh, replisome, cibus.py, queue-gen, golem-daemon, porta, cn-route, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-987663] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_emit.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_emit.py -v --tb=short. Commit."`
- [x] `golem [t-4f49e2] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_fetch.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_fetch.py -v --tb=short. Commit."`
- [x] `golem [t-1662a0] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_auscultation.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_auscultation.py -v --tb=short. Commit."`

### Auto-requeue (5 tasks @ 06:01)
- [x] `golem [t-b0b701] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9decb9] --provider volcano --max-turns 30 "Health check: test-dashboard, immunosurveillance, soma-activate, demethylase, circadian-probe.py, translocon, browse, inflammasome-probe, gap_junction_sync, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-264c45] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_mismatch_repair.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_mismatch_repair.py -v --tb=short. Commit."`
- [x] `golem [t-04704e] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_photoreception.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_photoreception.py -v --tb=short. Commit."`
- [x] `golem [t-d4c494] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_base.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_base.py -v --tb=short. Commit."`

### Auto-requeue (5 tasks @ 06:01)
- [x] `golem [t-f9c8c9] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fd06ac] --provider zhipu --max-turns 30 "Health check: capco-brief, health-check, pharos-sync.sh, wacli-ro, skill-sync, test-fixer, linkedin-monitor, launchagent-health, pharos-env.sh, queue-balance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-e967a5] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_parsers_scb.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_scb.py -v --tb=short. Commit."`
- [x] `golem [t-2ccbe4] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_glycogen.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_glycogen.py -v --tb=short. Commit."`
- [x] `golem [t-b5b80e] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_memory.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_memory.py -v --tb=short. Commit."`

### Auto-requeue (5 tasks @ 06:02)
- [x] `golem [t-423e5c] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d98a12] --provider volcano --max-turns 30 "Health check: phagocytosis.py, hkicpa, chromatin-decay-report.py, start-chrome-debug.sh, importin, golem-validate, chemoreception.py, launchagent-health, test-spec-gen, chromatin-backup.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-af34a8] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_browser_stealth.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_browser_stealth.py -v --tb=short. Commit."`
- [x] `golem [t-0f4b91] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_proprioception.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_proprioception.py -v --tb=short. Commit."`
- [x] `golem [t-d239f5] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_catabolism.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_catabolism.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:02)
- [x] `golem [t-c00bae] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-34823b] --provider volcano --max-turns 30 "Health check: golem-cost, nightly, quorum, golem-orchestrator, cleanup-stuck, test-dashboard, weekly-gather, plan-exec, lacuna.py, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-46cde8] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_ultradian.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ultradian.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:03)
- [x] `golem [t-93c56b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7c81ca] --provider infini --max-turns 30 "Health check: client-brief, regulatory-capture, respirometry, browse, coverage-map, engram, coaching-stats, translocon, pharos-sync.sh, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-3d7b3b] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_epigenome.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_epigenome.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 06:03)
- [x] `golem [t-2c4c20] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-92188e] --provider infini --max-turns 30 "Health check: replisome, telophase, find, oci-arm-retry, queue-balance, rename-kindle-asins.py, importin, card-search, efferens, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-7633d1] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_rss_cli.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_rss_cli.py -v --tb=short. Commit."`
- [x] `golem [t-5a068e] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_constitution.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_constitution.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 06:04)
- [x] `golem [t-96f46b] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-b5f55c] --provider volcano --max-turns 30 "Health check: rheotaxis-local, soma-scale, electroreception, soma-snapshot, skill-search, golem-daemon, launchagent-health, oura-weekly-digest.py, chemoreception.py, rg. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9fa7ba] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_operons.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_operons.py -v --tb=short. Commit."`
- [x] `golem [t-a1a866] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_ecphory.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ecphory.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 06:05)
- [x] `golem [t-52be5b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-324704] --provider infini --max-turns 30 "Health check: legatum, rename-plists, rename-kindle-asins.py, taste-score, cibus.py, soma-wake, tmux-url-select.sh, rheotaxis-local, chromatin-decay-report.py, golem-validate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-816f4b] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_parsers_ccba.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_ccba.py -v --tb=short. Commit."`
- [x] `golem [t-18904c] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_overnight.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_overnight.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:05)
- [x] `golem [t-b5c881] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-77e778] --provider infini --max-turns 30 "Health check: cibus.py, porta, gap_junction_sync, autoimmune.py, regulatory-capture, respirometry, med-tracker, telophase, wacli-ro, legatum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-05d4ff] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_substrates_constitution.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_constitution.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:06)
- [x] `golem [t-ce4db7] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6ff24f] --provider infini --max-turns 30 "Health check: translocon, vesicle, publish, skill-search, wacli-ro, grok, commensal, mitosis-checkpoint.py, log-summary, backfill-marks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-30dcc1] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_format.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_format.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:06)
- [x] `golem [t-d66736] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e8e691] --provider zhipu --max-turns 30 "Health check: pharos-sync.sh, fix-symlinks, skill-search, golem-daemon, search-guard, queue-stats, poiesis, safe_rm.py, wacli-ro, council. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-1bd6aa] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test___main__.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test___main__.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 06:07)
- [x] `golem [t-b39350] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-be26b3] --provider zhipu --max-turns 30 "Health check: pulse-review, browse, hkicpa, cibus.py, inflammasome-probe, golem-cost, update-compound-engineering-skills.sh, mitosis-checkpoint.py, paracrine, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b9bf44] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_parsers_hsbc.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_hsbc.py -v --tb=short. Commit."`
- [x] `golem [t-19ac89] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_substrates_spending.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_spending.py -v --tb=short. Commit."`

### Auto-requeue (4 tasks @ 06:07)
- [x] `golem [t-0fa5bc] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-355fd8] --provider volcano --max-turns 30 "Health check: phagocytosis.py, immunosurveillance.py, soma-watchdog, oura-weekly-digest.py, poiesis, mismatch-repair, commensal, electroreception, launchagent-health, soma-bootstrap. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-39868b] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_templates.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_templates.py -v --tb=short. Commit."`
- [x] `golem [t-9b7acc] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_polarization.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_polarization.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:08)
- [x] `golem [t-f0790b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3d0e10] --provider infini --max-turns 30 "Health check: cn-route, client-brief, paracrine, sortase, regulatory-capture, soma-snapshot, cytokinesis, oci-region-subscribe, methylation-review, hetzner-bootstrap.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-7a0ad6] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_ecdysis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_ecdysis.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:08)
- [x] `golem [t-f07acf] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6c0f98] --provider volcano --max-turns 30 "Health check: git-activity, golem-validate, grok, paracrine, client-brief, update-coding-tools.sh, capco-brief, compound-engineering-status, immunosurveillance, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-fb3d50] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_check.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_check.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:09)
- [x] `golem [t-6c62f9] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fe17d3] --provider volcano --max-turns 30 "Health check: bud, lustro-analyze, chromatin-backup.sh, find, plan-exec, complement, translocon, qmd-reindex.sh, efferens, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:09)
- [x] `golem [t-25c95e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fb2c13] --provider infini --max-turns 30 "Health check: search-guard, phagocytosis.py, electroreception, regulatory-scan, grok, lustro-analyze, fasti, test-dashboard, importin, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:10)
- [x] `golem [t-7a7f24] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-590b94] --provider infini --max-turns 30 "Health check: gap_junction_sync, start-chrome-debug.sh, lacuna, cleanup-stuck, autoimmune.py, test-dashboard, rename-plists, generate-solutions-index.py, test-spec-gen, golem-orchestrator. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:11)
- [x] `golem [t-bcf547] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-92cc0f] --provider zhipu --max-turns 30 "Health check: taste-score, tmux-osc52.sh, qmd-reindex.sh, legatum-verify, update-compound-engineering, diapedesis, council, start-chrome-debug.sh, queue-balance, update-coding-tools.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:11)
- [x] `golem [t-37a0ed] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-000413] --provider volcano --max-turns 30 "Health check: exocytosis.py, taste-score, golem, perplexity.sh, hkicpa, chromatin-decay-report.py, capco-prep, safe_rm.py, methylation, legatum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:12)
- [x] `golem [t-50e1f9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-8ea69f] --provider infini --max-turns 30 "Health check: regulatory-scan, orphan-scan, compound-engineering-test, receptor-health, immunosurveillance, soma-health, tm, golem-health, test-fixer, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:12)
- [x] `golem [t-27d078] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-94f063] --provider infini --max-turns 30 "Health check: pinocytosis, soma-health, porta, consulting-card.py, golem-top, provider-bench, transduction-daily-run, soma-pull, fasti, capco-prep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:13)
- [x] `golem [t-6004e6] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6b5a97] --provider zhipu --max-turns 30 "Health check: capco-prep, skill-lint, start-chrome-debug.sh, lacuna, soma-snapshot, weekly-gather, transduction-daily-run, soma-clean, golem-review, grep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-48f237] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_consolidation.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_consolidation.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:13)
- [x] `golem [t-e708bc] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a6a234] --provider zhipu --max-turns 30 "Health check: capco-brief, commensal, regulatory-scan, importin, replisome, agent-sync.sh, oura-weekly-digest.py, update-compound-engineering-skills.sh, cn-route, mitosis-checkpoint.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:14)
- [x] `golem [t-992b84] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2e2e58] --provider zhipu --max-turns 30 "Health check: golem-dash, express, replisome, regulatory-scan, circadian-probe.py, goose-worker, gog, capco-prep, chemoreception.py, generate-solutions-index.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:14)
- [x] `golem [t-df02c7] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-971384] --provider infini --max-turns 30 "Health check: skill-sync, coverage-map, legatum, log-summary, lacuna, pulse-review, perplexity.sh, golem-cost, proteostasis, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:15)
- [x] `golem [t-ebe6fc] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1ad947] --provider infini --max-turns 30 "Health check: legatum, update-compound-engineering, rg, rename-plists, chromatin-decay-report.py, wewe-rss-health.py, gemmation-env, queue-balance, capco-prep, dr-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:15)
- [x] `golem [t-446ac2] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-29c091] --provider infini --max-turns 30 "Health check: goose-worker, complement, compound-engineering-test, transduction-daily-run, soma-bootstrap, pharos-env.sh, translocon, golem-validate, golem-reviewer, judge. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-dcfe53] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_endocytosis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_endocytosis.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:16)
- [x] `golem [t-3a933e] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a1c575] --provider volcano --max-turns 30 "Health check: express, legatum-verify, cibus.py, lacuna.py, conftest-gen, respirometry, soma-activate, skill-search, lysis, efferens. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:16)
- [x] `golem [t-844c3d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-be3c06] --provider zhipu --max-turns 30 "Health check: browser, immunosurveillance.py, hkicpa, wewe-rss-health.py, fasti, soma-activate, coaching-stats, grep, commensal, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:17)
- [x] `golem [t-45e5d8] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6f3f67] --provider infini --max-turns 30 "Health check: porta, paracrine, circadian-probe.py, gemmation-env, importin, update-coding-tools.sh, pulse-review, soma-bootstrap, soma-watchdog, cg. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-d00626] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_browser.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_browser.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:18)
- [x] `golem [t-28b30f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-812251] --provider infini --max-turns 30 "Health check: regulatory-scrape, backup-due.sh, rotate-logs.py, browser, regulatory-capture, legatum, safe_search.py, log-summary, client-brief, capco-prep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:18)
- [x] `golem [t-655332] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6811ba] --provider infini --max-turns 30 "Health check: express, tmux-workspace.py, med-tracker, diapedesis, lacuna, tmux-osc52.sh, soma-wake, lysis, lustro-analyze, card-search. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:19)
- [x] `golem [t-4dd694] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-16b23c] --provider infini --max-turns 30 "Health check: exocytosis.py, capco-brief, legatum-verify, chromatin-backup.sh, oci-region-subscribe, test-fixer, respirometry, synthase, golem-reviewer, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:19)
- [x] `golem [t-788656] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d24c2a] --provider volcano --max-turns 30 "Health check: golem-daemon-wrapper.sh, capco-prep, cg, rheotaxis, rheotaxis-local, diapedesis, compound-engineering-status, channel, regulatory-scan, immunosurveillance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:20)
- [x] `golem [t-b97049] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c0ea6a] --provider zhipu --max-turns 30 "Health check: rg, soma-snapshot, capco-brief, chromatin-backup.sh, test-dashboard, receptor-scan, mismatch-repair, engram, cookie-sync, soma-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:20)
- [x] `golem [t-2c264a] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bf0b89] --provider zhipu --max-turns 30 "Health check: evident-brief, health-check, golem-report, orphan-scan, lysis, coverage-map, search-guard, med-tracker, switch-layer, queue-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:21)
- [x] `golem [t-0aa98c] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9044a6] --provider infini --max-turns 30 "Health check: browse, gemmule-sync, soma-health, qmd-reindex.sh, golem-report, methylation, regulatory-capture, chemoreception.py, gap_junction_sync, chromatin-decay-report.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:21)
- [x] `golem [t-28f657] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-89b42e] --provider zhipu --max-turns 30 "Health check: lacuna, x-feed-to-lustro, mismatch-repair, pharos-env.sh, soma-wake, queue-balance, exocytosis.py, tmux-url-select.sh, receptor-scan, git-activity. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-deee06] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_chromatin_stats.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_chromatin_stats.py -v --tb=short. Commit."`

### Auto-requeue (3 tasks @ 06:22)
- [x] `golem [t-908f99] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a51abb] --provider zhipu --max-turns 30 "Health check: transduction-daily-run, channel, goose-worker, respirometry, wacli-ro, legatum-verify, cibus.py, dr-sync, safe_search.py, oci-region-subscribe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-9060e7] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_noesis.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_noesis.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:22)
- [x] `golem [t-889717] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e07be7] --provider zhipu --max-turns 30 "Health check: orphan-scan, legatum, pinocytosis, skill-search, qmd-reindex.sh, complement, photos.py, importin, git-activity, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:23)
- [x] `golem [t-0af168] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-646a4c] --provider volcano --max-turns 30 "Health check: engram, pharos-health.sh, commensal, golem-daemon, dr-sync, tmux-workspace.py, golem-report, x-feed-to-lustro, phagocytosis.py, soma-clean. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:24)
- [x] `golem [t-f50685] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-01cae8] --provider zhipu --max-turns 30 "Health check: immunosurveillance.py, golem-dash, consulting-card.py, generate-solutions-index.py, chromatin-backup.py, lysis, agent-sync.sh, chat_history.py, chemoreception.py, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (4 tasks @ 06:24)
- [x] `golem [t-5fd329] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-dd897b] --provider infini --max-turns 30 "Health check: express, golem-orchestrator, regulatory-capture, orphan-scan, perplexity.sh, plan-exec, update-compound-engineering, methylation, porta, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-cfc338] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_parsers_boc.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_boc.py -v --tb=short. Commit."`
- [x] `golem [t-6f828b] --provider zhipu --max-turns 35 "Read /home/terry/germline/assays/test_substrates_vasomotor.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_substrates_vasomotor.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:25)
- [x] `golem [t-5be1b0] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-611c12] --provider volcano --max-turns 30 "Health check: card-search, gemmule-sync, lysis, golem-report, methylation, find, agent-sync.sh, soma-wake, capco-brief, queue-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:25)
- [x] `golem [t-e5f8a9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-08f819] --provider infini --max-turns 30 "Health check: importin, start-chrome-debug.sh, log-summary, complement, porta, generate-solutions-index.py, tmux-workspace.py, med-tracker, consulting-card.py, agent-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:26)
- [x] `golem [t-af5449] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-186670] --provider infini --max-turns 30 "Health check: consulting-card.py, cg, soma-bootstrap, legatum-verify, launchagent-health, mitosis-checkpoint.py, vesicle, synthase, exocytosis.py, mismatch-repair. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:26)
- [x] `golem [t-c834b6] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a1722f] --provider zhipu --max-turns 30 "Health check: translocon, card-search, diapedesis, update-compound-engineering, soma-clean, test-spec-gen, rename-kindle-asins.py, soma-pull, council, pharos-health.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:27)
- [x] `golem [t-12892e] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-b3a489] --provider infini --max-turns 30 "Health check: bud, electroreception, x-feed-to-lustro, chemoreception.py, auto-update-compound-engineering.sh, consulting-card.py, efferens, porta, hetzner-bootstrap.sh, oci-region-subscribe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-385ce9] --provider volcano --max-turns 35 "Read /home/terry/germline/assays/test_rss_config.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_rss_config.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:27)
- [x] `golem [t-7e41c9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-cbf8ad] --provider infini --max-turns 30 "Health check: orphan-scan, agent-sync.sh, proteostasis, evident-brief, publish, legatum-verify, grep, judge, ck, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:28)
- [x] `golem [t-12ee0f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a36476] --provider infini --max-turns 30 "Health check: gemmule-sync, methylation-review, oura-weekly-digest.py, diapedesis, compound-engineering-status, chat_history.py, switch-layer, golem-health, legatum, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:28)
- [x] `golem [t-67def8] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fea16c] --provider infini --max-turns 30 "Health check: provider-bench, soma-activate, soma-wake, agent-sync.sh, coverage-map, orphan-scan, golem-report, backfill-marks, launchagent-health, pharos-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:29)
- [x] `golem [t-3d43b0] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1ca46e] --provider zhipu --max-turns 30 "Health check: golem-report, test-fixer, update-coding-tools.sh, backfill-marks, lysis, cg, express, replisome, quorum, tmux-osc52.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:30)
- [x] `golem [t-0c1568] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-8880d0] --provider infini --max-turns 30 "Health check: proteostasis, update-coding-tools.sh, auto-update-compound-engineering.sh, tmux-osc52.sh, taste-score, circadian-probe.py, transduction-daily-run, tmux-url-select.sh, translocon, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 06:30)
- [x] `golem [t-d13160] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a41dd5] --provider zhipu --max-turns 30 "Health check: nightly, chromatin-backup.py, photos.py, provider-bench, lysis, paracrine, taste-score, search-guard, soma-pull, x-feed-to-lustro. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-076f29] --provider infini --max-turns 35 "Read /home/terry/germline/assays/test_parsers_mox.py. It's a placeholder with only assert True. Find the source module it should test. Replace the placeholder with 5+ real tests covering actual functionality. Run uv run pytest /home/terry/germline/assays/test_parsers_mox.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 06:31)
- [x] `golem [t-b12153] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4a4453] --provider volcano --max-turns 30 "Health check: regulatory-capture, weekly-gather, sortase, golem-dash, golem-top, goose-worker, vesicle, express, quorum, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:31)
- [x] `golem [t-292846] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-11900b] --provider zhipu --max-turns 30 "Health check: council, gemmation-env, vesicle, skill-lint, x-feed-to-lustro, circadian-probe.py, test-fixer, autoimmune.py, chromatin-backup.py, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:32)
- [x] `golem [t-c56c4c] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2c5a75] --provider volcano --max-turns 30 "Health check: orphan-scan, med-tracker, efferens, lustro-analyze, safe_search.py, fasti, pulse-review, oura-weekly-digest.py, transduction-daily-run, overnight-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:32)
- [x] `golem [t-2992ee] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-608d49] --provider infini --max-turns 30 "Health check: start-chrome-debug.sh, queue-gen, tmux-url-select.sh, cytokinesis, ck, pulse-review, generate-solutions-index.py, test-spec-gen, goose-worker, health-check. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:33)
- [x] `golem [t-6012ea] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-638d17] --provider volcano --max-turns 30 "Health check: linkedin-monitor, tm, queue-stats, channel, update-coding-tools.sh, golem, paracrine, rheotaxis, golem-top, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:34)
- [x] `golem [t-d1110e] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e32c23] --provider volcano --max-turns 30 "Health check: auto-update-compound-engineering.sh, weekly-gather, lustro-analyze, safe_rm.py, agent-sync.sh, orphan-scan, cn-route, health-check, cg, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:34)
- [x] `golem [t-a5df56] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-04ce0c] --provider zhipu --max-turns 30 "Health check: chat_history.py, coverage-map, switch-layer, bud, vesicle, chemoreception.py, lustro-analyze, grep, lysis, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:35)
- [x] `golem [t-b854eb] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-427a90] --provider zhipu --max-turns 30 "Health check: browse, photos.py, centrosome, gog, queue-gen, commensal, chromatin-decay-report.py, efferens, hetzner-bootstrap.sh, gemmation-env. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:35)
- [x] `golem [t-29f616] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-58a7aa] --provider volcano --max-turns 30 "Health check: replisome, rename-plists, lysis, lacuna, pharos-sync.sh, immunosurveillance.py, receptor-health, soma-wake, hkicpa, methylation-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:36)
- [x] `golem [t-a251cd] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fddfe5] --provider infini --max-turns 30 "Health check: find, legatum-verify, dr-sync, cookie-sync, methylation-review, launchagent-health, autoimmune.py, phagocytosis.py, lustro-analyze, sortase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:36)
- [x] `golem [t-6114fc] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-843470] --provider zhipu --max-turns 30 "Health check: wacli-ro, circadian-probe.py, nightly, card-search, quorum, gemmation-env, compound-engineering-test, browse, launchagent-health, methylation. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:37)
- [x] `golem [t-a15c90] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-915195] --provider volcano --max-turns 30 "Health check: browser, porta, immunosurveillance.py, pulse-review, grok, test-dashboard, compound-engineering-test, demethylase, disk-audit, judge. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:37)
- [x] `golem [t-015434] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-931bba] --provider zhipu --max-turns 30 "Health check: demethylase, coaching-stats, evident-brief, compound-engineering-status, cytokinesis, rheotaxis, chat_history.py, consulting-card.py, find, regulatory-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:38)
- [x] `golem [t-8cec8a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-173c7e] --provider infini --max-turns 30 "Health check: auto-update-compound-engineering.sh, synthase, disk-audit, launchagent-health, golem-dash, conftest-gen, transduction-daily-run, respirometry, hkicpa, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:38)
- [x] `golem [t-3d0dda] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1679ca] --provider zhipu --max-turns 30 "Health check: linkedin-monitor, conftest-gen, legatum-verify, rotate-logs.py, rheotaxis, golem-top, coverage-map, immunosurveillance, receptor-health, med-tracker. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:39)
- [x] `golem [t-8fab03] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1ae31a] --provider infini --max-turns 30 "Health check: receptor-scan, tmux-osc52.sh, soma-watchdog, compound-engineering-test, test-dashboard, circadian-probe.py, goose-worker, browse, grep, hkicpa. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:40)
- [x] `golem [t-76a0c5] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-648dff] --provider zhipu --max-turns 30 "Health check: qmd-reindex.sh, golem-health, cookie-sync, oci-arm-retry, inflammasome-probe, consulting-card.py, gemmation-env, sortase, diapedesis, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:40)
- [x] `golem [t-198030] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c44850] --provider volcano --max-turns 30 "Health check: conftest-gen, telophase, lysis, cn-route, sortase, provider-bench, golem, proteostasis, translocon, quorum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:41)
- [x] `golem [t-ed294a] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-aed79a] --provider volcano --max-turns 30 "Health check: disk-audit, soma-watchdog, wewe-rss-health.py, photos.py, grok, tm, update-compound-engineering-skills.sh, soma-pull, cleanup-stuck, immunosurveillance.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:41)
- [x] `golem [t-5068b5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-8910a4] --provider infini --max-turns 30 "Health check: capco-prep, exocytosis.py, tm, tmux-workspace.py, med-tracker, bud, backfill-marks, judge, golem-cost, taste-score. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:42)
- [x] `golem [t-2b8d08] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-242967] --provider zhipu --max-turns 30 "Health check: pharos-health.sh, soma-snapshot, golem-top, tmux-workspace.py, quorum, log-summary, golem-daemon-wrapper.sh, tmux-url-select.sh, golem-review, gog. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:42)
- [x] `golem [t-71f8f1] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2341f9] --provider volcano --max-turns 30 "Health check: rename-kindle-asins.py, receptor-health, complement, gemmation-env, med-tracker, rotate-logs.py, hkicpa, centrosome, lacuna.py, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:43)
- [x] `golem [t-5e932e] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e3c9f1] --provider volcano --max-turns 30 "Health check: backup-due.sh, bud, hetzner-bootstrap.sh, goose-worker, pharos-sync.sh, telophase, assay, effector-usage, perplexity.sh, express. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:43)
- [x] `golem [t-da3c23] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-b21185] --provider infini --max-turns 30 "Health check: browser, soma-health, regulatory-scrape, rheotaxis, safe_search.py, search-guard, tmux-workspace.py, card-search, skill-search, start-chrome-debug.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:44)
- [x] `golem [t-5c24d7] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-219436] --provider volcano --max-turns 30 "Health check: receptor-health, rg, replisome, circadian-probe.py, coverage-map, oura-weekly-digest.py, golem-cost, compound-engineering-status, golem, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:44)
- [x] `golem [t-25f01d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-131c77] --provider zhipu --max-turns 30 "Health check: cookie-sync, x-feed-to-lustro, start-chrome-debug.sh, capco-prep, browser, paracrine, synthase, mismatch-repair, transduction-daily-run, autoimmune.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:45)
- [x] `golem [t-23c621] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4e5122] --provider infini --max-turns 30 "Health check: safe_rm.py, gog, express, lacuna.py, quorum, autoimmune.py, respirometry, engram, channel, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:46)
- [x] `golem [t-908a8c] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-298a0f] --provider infini --max-turns 30 "Health check: queue-stats, launchagent-health, gemmation-env, weekly-gather, evident-brief, consulting-card.py, test-fixer, regulatory-capture, golem-dash, legatum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:46)
- [x] `golem [t-4f9ce1] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-5842f7] --provider zhipu --max-turns 30 "Health check: legatum-verify, queue-gen, publish, sortase, pharos-sync.sh, test-dashboard, soma-bootstrap, oci-arm-retry, inflammasome-probe, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:47)
- [x] `golem [t-b8cbc6] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7a317f] --provider infini --max-turns 30 "Health check: paracrine, wacli-ro, circadian-probe.py, receptor-scan, soma-wake, express, golem-dash, generate-solutions-index.py, lustro-analyze, golem-orchestrator. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:47)
- [x] `golem [t-ff6c4b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7d0352] --provider infini --max-turns 30 "Health check: rheotaxis-local, golem-cost, queue-stats, git-activity, tmux-url-select.sh, soma-scale, overnight-gather, inflammasome-probe, methylation, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:48)
- [x] `golem [t-f62b53] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-90a618] --provider infini --max-turns 30 "Health check: pulse-review, pinocytosis, transduction-daily-run, regulatory-capture, legatum, soma-scale, secrets-sync, lustro-analyze, update-compound-engineering, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:48)
- [x] `golem [t-07ba21] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1c648c] --provider infini --max-turns 30 "Health check: test-dashboard, cibus.py, replisome, methylation, taste-score, chat_history.py, health-check, capco-brief, pulse-review, tmux-url-select.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:49)
- [x] `golem [t-49e095] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c7f052] --provider infini --max-turns 30 "Health check: photos.py, exocytosis.py, grep, council, golem-daemon, compound-engineering-status, taste-score, gemmule-sync, chromatin-backup.py, regulatory-capture. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:49)
- [x] `golem [t-9bfe09] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-83c710] --provider zhipu --max-turns 30 "Health check: regulatory-scrape, git-activity, gemmule-sync, rheotaxis, electroreception, replisome, pulse-review, med-tracker, receptor-health, oci-arm-retry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:50)
- [x] `golem [t-6db948] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-11e07d] --provider zhipu --max-turns 30 "Health check: regulatory-capture, soma-scale, council, rheotaxis-local, linkedin-monitor, mitosis-checkpoint.py, wacli-ro, consulting-card.py, soma-clean, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:50)
- [x] `golem [t-60e300] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-397707] --provider zhipu --max-turns 30 "Health check: mismatch-repair, golem-dash, conftest-gen, skill-search, cytokinesis, methylation, golem-daemon-wrapper.sh, tm, golem, test-dashboard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:51)
- [x] `golem [t-e11309] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f4c5ab] --provider infini --max-turns 30 "Health check: capco-prep, orphan-scan, hetzner-bootstrap.sh, regulatory-scrape, fix-symlinks, auto-update-compound-engineering.sh, dr-sync, soma-health, poiesis, oci-region-subscribe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:51)
- [x] `golem [t-f20d57] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-79f60d] --provider infini --max-turns 30 "Health check: soma-health, immunosurveillance, receptor-health, bud, compound-engineering-test, publish, browser, paracrine, auto-update-compound-engineering.sh, regulatory-capture. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:52)
- [x] `golem [t-d7f4db] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-e04a0e] --provider infini --max-turns 30 "Health check: grep, log-summary, soma-scale, soma-health, plan-exec, launchagent-health, rheotaxis, council, golem-dash, transduction-daily-run. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:52)
- [x] `golem [t-2c2b2b] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f5b477] --provider zhipu --max-turns 30 "Health check: golem-health, disk-audit, browser, cleanup-stuck, capco-prep, cytokinesis, provider-bench, methylation-review, client-brief, pinocytosis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:53)
- [x] `golem [t-341c75] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9fe8fe] --provider infini --max-turns 30 "Health check: golem-cost, legatum-verify, med-tracker, cytokinesis, skill-search, pulse-review, card-search, chemoreception.py, translocon, fasti. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:54)
- [x] `golem [t-1f3875] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-6be00b] --provider volcano --max-turns 30 "Health check: oura-weekly-digest.py, pharos-env.sh, tm, mismatch-repair, soma-scale, vesicle, cg, rheotaxis-local, sortase, nightly. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:54)
- [x] `golem [t-02459a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4e24cc] --provider infini --max-turns 30 "Health check: disk-audit, soma-snapshot, coverage-map, demethylase, test-dashboard, methylation-review, mismatch-repair, card-search, linkedin-monitor, mitosis-checkpoint.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:55)
- [x] `golem [t-e3a634] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3baad5] --provider zhipu --max-turns 30 "Health check: inflammasome-probe, grep, soma-snapshot, safe_rm.py, rheotaxis, immunosurveillance.py, soma-pull, launchagent-health, rotate-logs.py, fasti. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:55)
- [x] `golem [t-e7f7f1] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c8f4cc] --provider zhipu --max-turns 30 "Health check: golem-report, bud, cookie-sync, judge, taste-score, pulse-review, oci-region-subscribe, compound-engineering-status, poiesis, evident-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:56)
- [x] `golem [t-759fbc] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a23a51] --provider zhipu --max-turns 30 "Health check: chromatin-decay-report.py, wacli-ro, grok, tmux-osc52.sh, test-dashboard, health-check, soma-activate, gemmule-sync, council, agent-sync.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:56)
- [x] `golem [t-15d9b1] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7d493f] --provider zhipu --max-turns 30 "Health check: queue-stats, electroreception, circadian-probe.py, taste-score, poiesis, backfill-marks, cibus.py, grep, bud, x-feed-to-lustro. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:57)
- [x] `golem [t-54ff93] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-53f85e] --provider infini --max-turns 30 "Health check: phagocytosis.py, golem-cost, chromatin-decay-report.py, wacli-ro, efferens, rotate-logs.py, rheotaxis, exocytosis.py, test-spec-gen, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:57)
- [x] `golem [t-d640ae] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ed5054] --provider volcano --max-turns 30 "Health check: gog, golem-daemon, vesicle, proteostasis, regulatory-scan, launchagent-health, qmd-reindex.sh, phagocytosis.py, bud, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:58)
- [x] `golem [t-6d7da5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-97a14c] --provider infini --max-turns 30 "Health check: council, soma-bootstrap, autoimmune.py, golem, agent-sync.sh, pharos-env.sh, cn-route, backfill-marks, replisome, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:59)
- [x] `golem [t-7c7af5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-019944] --provider infini --max-turns 30 "Health check: lacuna.py, mitosis-checkpoint.py, pharos-env.sh, soma-scale, fix-symlinks, importin, complement, goose-worker, start-chrome-debug.sh, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 06:59)
- [x] `golem [t-5fe511] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-a19e1b] --provider infini --max-turns 30 "Health check: hkicpa, telophase, centrosome, switch-layer, tmux-url-select.sh, diapedesis, soma-clean, replisome, receptor-scan, electroreception. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:00)
- [x] `golem [t-bdf059] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-62521f] --provider infini --max-turns 30 "Health check: autoimmune.py, receptor-scan, qmd-reindex.sh, x-feed-to-lustro, compound-engineering-test, linkedin-monitor, poiesis, phagocytosis.py, tmux-osc52.sh, skill-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:00)
- [x] `golem [t-b3de02] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1d2f7d] --provider volcano --max-turns 30 "Health check: rheotaxis, oci-arm-retry, skill-lint, update-compound-engineering-skills.sh, lysis, test-spec-gen, electroreception, importin, backfill-marks, hetzner-bootstrap.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:01)
- [x] `golem [t-d354f6] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-dde878] --provider infini --max-turns 30 "Health check: cibus.py, queue-gen, card-search, launchagent-health, soma-pull, gemmation-env, tmux-workspace.py, mismatch-repair, council, rg. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:01)
- [x] `golem [t-9f6062] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3d8dba] --provider volcano --max-turns 30 "Health check: browse, weekly-gather, complement, immunosurveillance, soma-activate, coaching-stats, provider-bench, telophase, hetzner-bootstrap.sh, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:02)
- [x] `golem [t-167834] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c5dcde] --provider infini --max-turns 30 "Health check: soma-clean, methylation-review, disk-audit, paracrine, cytokinesis, perplexity.sh, dr-sync, regulatory-scan, circadian-probe.py, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:02)
- [x] `golem [t-70b2f4] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-de7791] --provider infini --max-turns 30 "Health check: goose-worker, launchagent-health, golem-review, importin, search-guard, golem-health, rename-plists, safe_rm.py, golem, methylation. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:03)
- [x] `golem [t-4e7639] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-080719] --provider infini --max-turns 30 "Health check: fasti, soma-snapshot, rename-plists, auto-update-compound-engineering.sh, immunosurveillance, soma-scale, soma-clean, soma-watchdog, goose-worker, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:04)
- [x] `golem [t-f0c497] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-16eede] --provider volcano --max-turns 30 "Health check: update-compound-engineering, start-chrome-debug.sh, rename-kindle-asins.py, fix-symlinks, qmd-reindex.sh, methylation, med-tracker, skill-sync, inflammasome-probe, soma-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:04)
- [x] `golem [t-69a40f] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-399d3c] --provider zhipu --max-turns 30 "Health check: cytokinesis, x-feed-to-lustro, health-check, skill-sync, chromatin-backup.sh, methylation, immunosurveillance.py, cg, test-spec-gen, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:05)
- [x] `golem [t-454a0c] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-89224f] --provider zhipu --max-turns 30 "Health check: poiesis, goose-worker, golem, judge, git-activity, chromatin-backup.sh, update-compound-engineering-skills.sh, receptor-scan, efferens, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:05)
- [x] `golem [t-bc6cdf] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d1f742] --provider infini --max-turns 30 "Health check: importin, gap_junction_sync, chromatin-backup.sh, med-tracker, synthase, agent-sync.sh, receptor-health, exocytosis.py, cleanup-stuck, lacuna.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:06)
- [x] `golem [t-82b8cb] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1550c0] --provider volcano --max-turns 30 "Health check: commensal, paracrine, diapedesis, cleanup-stuck, respirometry, wewe-rss-health.py, golem-review, log-summary, grep, golem-cost. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:07)
- [x] `golem [t-aa2d3f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4fe024] --provider infini --max-turns 30 "Health check: photos.py, rheotaxis-local, linkedin-monitor, council, test-spec-gen, tm, pharos-env.sh, compound-engineering-status, golem-daemon-wrapper.sh, qmd-reindex.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:07)
- [x] `golem [t-27e7ab] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-10f72d] --provider infini --max-turns 30 "Health check: lustro-analyze, lacuna, golem-dash, card-search, dr-sync, golem-report, cleanup-stuck, cg, capco-brief, translocon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:08)
- [x] `golem [t-221a4b] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-37e33e] --provider infini --max-turns 30 "Health check: pharos-sync.sh, cytokinesis, gap_junction_sync, sortase, agent-sync.sh, express, soma-snapshot, commensal, weekly-gather, queue-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:08)
- [x] `golem [t-5b3bc4] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-00c87e] --provider volcano --max-turns 30 "Health check: grep, soma-pull, lacuna.py, methylation-review, cleanup-stuck, rg, publish, generate-solutions-index.py, diapedesis, skill-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:09)
- [x] `golem [t-a6280f] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ef96af] --provider infini --max-turns 30 "Health check: rheotaxis, coaching-stats, exocytosis.py, secrets-sync, gemmation-env, backfill-marks, legatum-verify, orphan-scan, wewe-rss-health.py, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:09)
- [x] `golem [t-662c94] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-90fd9f] --provider volcano --max-turns 30 "Health check: tmux-workspace.py, pinocytosis, rheotaxis-local, evident-brief, hetzner-bootstrap.sh, find, soma-activate, importin, skill-lint, soma-bootstrap. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:10)
- [x] `golem [t-0c3b3a] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bec5ea] --provider zhipu --max-turns 30 "Health check: capco-brief, centrosome, importin, grep, methylation-review, rg, lysis, soma-snapshot, client-brief, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:10)
- [x] `golem [t-a91402] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-dc5e00] --provider infini --max-turns 30 "Health check: oura-weekly-digest.py, update-coding-tools.sh, sortase, x-feed-to-lustro, chromatin-decay-report.py, soma-snapshot, regulatory-scan, med-tracker, oci-region-subscribe, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:11)
- [x] `golem [t-ca946a] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fab096] --provider infini --max-turns 30 "Health check: oci-region-subscribe, qmd-reindex.sh, dr-sync, demethylase, wewe-rss-health.py, rheotaxis, effector-usage, receptor-health, importin, cn-route. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:11)
- [x] `golem [t-5c3ed1] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-34f641] --provider volcano --max-turns 30 "Health check: cytokinesis, update-compound-engineering, exocytosis.py, consulting-card.py, gap_junction_sync, commensal, receptor-scan, oci-arm-retry, soma-scale, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:12)
- [x] `golem [t-9b0070] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3866dc] --provider volcano --max-turns 30 "Health check: golem-daemon, mismatch-repair, rename-kindle-asins.py, regulatory-capture, safe_search.py, quorum, methylation, effector-usage, pharos-env.sh, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:12)
- [x] `golem [t-c17cba] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-c83467] --provider volcano --max-turns 30 "Health check: vesicle, card-search, autoimmune.py, dr-sync, nightly, x-feed-to-lustro, complement, transduction-daily-run, hetzner-bootstrap.sh, soma-activate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:13)
- [x] `golem [t-30e3ce] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-652d03] --provider volcano --max-turns 30 "Health check: lacuna, x-feed-to-lustro, tmux-workspace.py, demethylase, rg, taste-score, sortase, soma-scale, cibus.py, immunosurveillance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:13)
- [x] `golem [t-5eb3d5] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f56dc0] --provider zhipu --max-turns 30 "Health check: golem-dash, transduction-daily-run, oci-region-subscribe, vesicle, golem-cost, oura-weekly-digest.py, coaching-stats, golem-health, cookie-sync, regulatory-scrape. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:14)
- [x] `golem [t-60004d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d95f95] --provider zhipu --max-turns 30 "Health check: demethylase, immunosurveillance.py, log-summary, gemmule-sync, lacuna, pharos-health.sh, translocon, disk-audit, effector-usage, search-guard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:15)
- [x] `golem [t-f9f7e7] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-bfe42d] --provider volcano --max-turns 30 "Health check: perplexity.sh, goose-worker, soma-wake, compound-engineering-status, golem-health, engram, soma-clean, rotate-logs.py, agent-sync.sh, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:15)
- [x] `golem [t-1f9d4d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-3ba3b4] --provider infini --max-turns 30 "Health check: card-search, receptor-scan, consulting-card.py, ck, golem-report, legatum-verify, queue-stats, centrosome, grok, update-coding-tools.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:16)
- [x] `golem [t-3b9955] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fe5a8f] --provider zhipu --max-turns 30 "Health check: taste-score, oci-arm-retry, transduction-daily-run, skill-sync, backfill-marks, photos.py, regulatory-capture, test-dashboard, capco-brief, importin. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:16)
- [x] `golem [t-7d133a] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-962131] --provider zhipu --max-turns 30 "Health check: perplexity.sh, translocon, oura-weekly-digest.py, evident-brief, wewe-rss-health.py, legatum, phagocytosis.py, cleanup-stuck, rename-plists, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:17)
- [x] `golem [t-669ded] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-333bc3] --provider infini --max-turns 30 "Health check: soma-pull, consulting-card.py, soma-snapshot, linkedin-monitor, plan-exec, test-spec-gen, oci-arm-retry, rename-kindle-asins.py, methylation-review, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:17)
- [x] `golem [t-8b5c54] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-ef153b] --provider zhipu --max-turns 30 "Health check: rotate-logs.py, plan-exec, receptor-health, tm, channel, phagocytosis.py, fix-symlinks, oci-arm-retry, secrets-sync, autoimmune.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:18)
- [x] `golem [t-a2bc7a] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-2a0f37] --provider volcano --max-turns 30 "Health check: x-feed-to-lustro, agent-sync.sh, health-check, soma-activate, lustro-analyze, rename-kindle-asins.py, engram, tmux-workspace.py, conftest-gen, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:18)
- [x] `golem [t-e8c22d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fb16f5] --provider infini --max-turns 30 "Health check: gemmule-sync, golem-cost, proteostasis, cibus.py, cn-route, tmux-workspace.py, council, test-dashboard, golem-report, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:19)
- [x] `golem [t-31ee8d] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-1ec1b3] --provider infini --max-turns 30 "Health check: cytokinesis, cibus.py, importin, queue-gen, backup-due.sh, legatum-verify, evident-brief, replisome, test-fixer, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:19)
- [x] `golem [t-0785a1] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-b3bbae] --provider volcano --max-turns 30 "Health check: receptor-health, gemmule-sync, pharos-sync.sh, circadian-probe.py, wacli-ro, oci-region-subscribe, overnight-gather, express, health-check, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:20)
- [x] `golem [t-26930d] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-8d5755] --provider volcano --max-turns 30 "Health check: ck, golem-top, channel, plan-exec, soma-health, legatum, browser, backup-due.sh, regulatory-scrape, capco-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:21)
- [x] `golem [t-3d122b] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-867e36] --provider zhipu --max-turns 30 "Health check: safe_search.py, gap_junction_sync, golem-orchestrator, pharos-health.sh, skill-lint, phagocytosis.py, golem-dash, photos.py, electroreception, legatum-verify. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:21)
- [x] `golem [t-0a2554] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-4bb56b] --provider zhipu --max-turns 30 "Health check: agent-sync.sh, golem-reviewer, chromatin-backup.sh, cookie-sync, immunosurveillance.py, engram, legatum-verify, orphan-scan, golem-orchestrator, goose-worker. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (3 tasks @ 07:22)
- [x] `golem [t-5d5234] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-9d2ca8] --provider zhipu --max-turns 30 "Health check: rheotaxis-local, client-brief, publish, proteostasis, transduction-daily-run, test-dashboard, golem-daemon, rheotaxis, vesicle, evident-brief. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-3c9c55] --provider infini --max-turns 35 "Read /home/terry/germline/metabolon/metabolism/substrates/operon_monitor.py carefully first. Write assays/test_substrates_operon_monitor.py with tests for every public function. No assert True placeholders — test real behavior. Run uv run pytest assays/test_substrates_operon_monitor.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 07:22)
- [x] `golem [t-2e1684] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-48aaa2] --provider volcano --max-turns 30 "Health check: regulatory-scan, queue-balance, queue-gen, test-spec-gen, rotate-logs.py, lustro-analyze, vesicle, plan-exec, safe_rm.py, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Architecture audit P2 (2026-04-02)
- [x] `golem [t-abebcc] --provider zhipu --max-turns 50 "Consolidate golem CLI: read effectors/golem-dash, golem-health, golem-report, golem-review, golem-reviewer, golem-top, golem-validate. Merge them as subcommands into effectors/golem (add cmd_dash, cmd_health, cmd_report, cmd_review, cmd_top, cmd_validate functions dispatched by argparse). Keep effectors/golem-daemon and effectors/golem-orchestrator as separate binaries. Delete the old standalone scripts after merging. Update any tests in assays/ that import or exec the old script names. Run uv run pytest assays/test_golem*.py -v --tb=short. Commit."`
- [x] `golem [t-f352df] --provider volcano --max-turns 50 "Consolidate soma CLI: read effectors/soma-activate, soma-bootstrap, soma-clean, soma-health, soma-pull, soma-scale, soma-snapshot, soma-wake, soma-watchdog. Create effectors/soma as a single Python CLI with argparse subcommands (activate, bootstrap, clean, health, pull, scale, snapshot, wake, watchdog). Each subcommand calls the logic from the original script. Delete the old standalone scripts after merging. Update any tests. Run uv run pytest assays/test_soma*.py -v --tb=short. Commit."`

### Auto-requeue (2 tasks @ 07:23)
- [x] `golem [t-a130c8] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d5efe0] --provider volcano --max-turns 30 "Health check: backfill-marks, rename-kindle-asins.py, cibus.py, engram, legatum, poiesis, quorum, inflammasome-probe, telophase, overnight-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:23)
- [x] `golem [t-660004] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-d390a2] --provider zhipu --max-turns 30 "Health check: rg, regulatory-capture, browser, update-coding-tools.sh, inflammasome-probe, backfill-marks, methylation, translocon, capco-brief, weekly-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:24)
- [x] `golem [t-4a0477] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-02f127] --provider infini --max-turns 30 "Health check: nightly, exocytosis.py, soma-watchdog, safe_rm.py, med-tracker, test-dashboard, overnight-gather, coaching-stats, provider-bench, diapedesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:24)
- [x] `golem [t-e29d60] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-562332] --provider infini --max-turns 30 "Health check: lacuna.py, agent-sync.sh, rename-kindle-asins.py, fix-symlinks, cleanup-stuck, backup-due.sh, provider-bench, porta, orphan-scan, hetzner-bootstrap.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:25)
- [x] `golem [t-435e6d] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-7f3505] --provider zhipu --max-turns 30 "Health check: complement, quorum, commensal, diapedesis, ck, respirometry, cg, rg, centrosome, chromatin-decay-report.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:26)
- [x] `golem [t-72a2ab] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-fe9842] --provider infini --max-turns 30 "Health check: soma-activate, soma-snapshot, engram, x-feed-to-lustro, synthase, rename-plists, test-fixer, nightly, golem-dash, cibus.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:26)
- [x] `golem [t-6d52eb] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-aff08f] --provider volcano --max-turns 30 "Health check: regulatory-scrape, immunosurveillance.py, gog, provider-bench, compound-engineering-test, pharos-env.sh, hkicpa, overnight-gather, qmd-reindex.sh, auto-update-compound-engineering.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:27)
- [x] `golem [t-fa9a50] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f491ba] --provider zhipu --max-turns 30 "Health check: rheotaxis-local, golem-dash, pharos-health.sh, engram, cookie-sync, tmux-osc52.sh, test-spec-gen, golem-top, replisome, oura-weekly-digest.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:27)
- [x] `golem [t-b4106c] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-932add] --provider volcano --max-turns 30 "Health check: complement, coverage-map, vesicle, capco-prep, disk-audit, secrets-sync, grok, coaching-stats, receptor-health, chromatin-backup.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:28)
- [x] `golem [t-13abe9] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-eb7c65] --provider infini --max-turns 30 "Health check: soma-clean, rename-kindle-asins.py, taste-score, proteostasis, methylation-review, importin, golem-review, synthase, golem-reviewer, fix-symlinks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:28)
- [x] `golem [t-2dc1b5] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-842bf9] --provider infini --max-turns 30 "Health check: rotate-logs.py, find, mismatch-repair, quorum, queue-balance, weekly-gather, golem-review, test-fixer, med-tracker, plan-exec. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:29)
- [x] `golem [t-e920a9] --provider volcano --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-78be0f] --provider zhipu --max-turns 30 "Health check: cibus.py, health-check, tmux-osc52.sh, rg, log-summary, grep, vesicle, git-activity, legatum-verify, search-guard. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:29)
- [x] `golem [t-636ddf] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-509142] --provider volcano --max-turns 30 "Health check: fix-symlinks, rename-kindle-asins.py, golem-reviewer, skill-lint, golem-top, wewe-rss-health.py, rotate-logs.py, test-fixer, ck, med-tracker. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:30)
- [x] `golem [t-6f1bd2] --provider zhipu --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [x] `golem [t-f7d40f] --provider infini --max-turns 30 "Health check: update-coding-tools.sh, soma-scale, methylation, gap_junction_sync, channel, assay, fasti, auto-update-compound-engineering.sh, safe_rm.py, queue-stats. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Auto-requeue (2 tasks @ 07:31)
- [ ] `golem [t-3b8d8f] --provider infini --max-turns 30 "Run uv run pyright metabolon/ --outputjson 2>&1 | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f'{x[\\"file\\"]}:{x[\\"range\\"][\\"start\\"][\\"line\\"]} {x[\\"message\\"]}') for x in d.get('generalDiagnostics',[])[:15]]\" 2>/dev/null || echo 'pyright clean'. Fix type errors found. Commit."`
- [ ] `golem [t-cd9017] --provider volcano --max-turns 30 "Health check: diapedesis, search-guard, test-spec-gen, compound-engineering-status, gemmule-sync, golem-daemon, coverage-map, health-check, update-coding-tools.sh, cleanup-stuck. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
