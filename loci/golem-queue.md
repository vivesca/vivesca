# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.
**NOTE: ZhiPu broken as golem provider. Use Infini/Volcano only.**

## Pending

### Retries (split [!] failures into smaller tasks)

#### Sortase executor (33K — needs solo golem)
- [ ] `golem --provider infini --max-turns 50 "Write tests for metabolon/sortase/executor.py (33K — large module). Write assays/test_sortase_executor.py. Focus on pure functions. Mock subprocess/external. Run pytest. Fix failures."`

#### Sortase decompose + graph + logger (3 modules)
- [!] `golem --provider volcano --max-turns 50 "Write tests for 3 modules. Write assays/test_sortase_decompose.py, test_sortase_graph.py, test_sortase_logger.py. Run pytest. Fix failures. Modules: metabolon/sortase/decompose.py metabolon/sortase/graph.py metabolon/sortase/logger.py"`

#### Lysin + endosomal (4 modules)
- [ ] `golem --provider infini --max-turns 40 "Write tests: assays/test_lysin_fetch.py, test_lysin_format.py, test_endosomal_organelle.py, test_endosomal_enzyme.py. Run pytest. Fix failures. Modules: metabolon/lysin/fetch.py metabolon/lysin/format.py metabolon/organelles/endosomal.py metabolon/enzymes/endosomal.py"`

#### Morphology + codons (2 modules)
- [!] `golem --provider volcano --max-turns 30 "Write tests: assays/test_morphology_base.py, assays/test_codons_templates_unit.py. Run pytest. Fix failures. Modules: metabolon/morphology/base.py metabolon/codons/templates.py"`

#### Pinocytosis + sporulation (4 modules)
- [!] `golem --provider infini --max-turns 30 "Write tests: assays/test_pinocytosis_photoreception.py, test_pinocytosis_ultradian.py, test_pinocytosis_ecdysis.py, test_organelle_sporulation.py. Run pytest. Fix failures. Modules: metabolon/pinocytosis/photoreception.py metabolon/pinocytosis/ultradian.py metabolon/pinocytosis/ecdysis.py metabolon/organelles/sporulation.py"`

#### Remaining tiny (3 modules)
- [!] `golem --provider volcano --max-turns 20 "Write tests: assays/test_resource_glycogen.py, test_resource_chromatin_stats.py, test_resource_consolidation.py. Run pytest. Fix failures. Modules: metabolon/resources/glycogen.py metabolon/resources/chromatin_stats.py metabolon/resources/consolidation.py"`

### Fixes (mop up test failures)

#### Fix all remaining test failures
- [ ] `golem --provider infini --max-turns 40 "Run: uv run pytest -q --tb=line 2>&1 | grep FAILED. For each failing test file, read the test and source module. Fix. Run pytest on each fixed file. Iterate until all pass. Do NOT delete tests."`

### Compound infra

#### Coaching enforcement — post-golem validation gate
- [!] `golem --provider volcano --max-turns 50 "Read effectors/golem-daemon. Find check_new_test_files_and_run_pytest. Add validate_golem_output() that runs BEFORE pytest gate on all new/modified .py files (git diff --name-only --diff-filter=AM HEAD). Checks: (1) ast.parse() each .py — fail on SyntaxError. (2) grep for TODO/FIXME/stub — fail if found. (3) test_*.py must be flat in assays/ — reject assays/subdir/test_foo.py. (4) No __pycache__/.pyc. Return (passed: bool, errors: list[str]). Wire into daemon_loop after exit=0: validate first, then pytest gate. Fail = mark_failed with errors. Update assays/test_golem_daemon.py with tests. Run pytest. Fix failures."`

### Builds (features > tests)

#### ZhiPu golem diagnosis
- [ ] `golem --provider volcano --max-turns 30 "Debug why golem --provider zhipu hangs. Read effectors/golem. Run: timeout 30 bash -c 'source ~/.zshenv.local; CLAUDECODE= ANTHROPIC_API_KEY=$ZHIPU_API_KEY ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-5.1 ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-5.1 ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-air claude --print --dangerously-skip-permissions --max-turns 1 --bare -p hello 2>&1'. Compare with how the golem script invokes claude. Find the difference causing the hang. Fix it. Test with: golem --provider zhipu --max-turns 3 'Say hello'. Verify output appears."`

#### Golem auto-retry on [!]
- [!] `golem --provider infini --max-turns 40 "Read effectors/golem-daemon. Add retry logic: when a task gets mark_failed, if it was the first attempt, re-queue it once (change [!] back to [ ] and append ' (retry)' to the command). Only retry once — if the retry also fails, keep [!]. Add a 'retried' field to the log. Update assays/test_golem_daemon.py. Run pytest. Fix failures."`

#### Golem provider health check
- [ ] `golem --provider volcano --max-turns 30 "Create effectors/golem-health as Python script. For each provider (zhipu, infini, volcano): send a minimal test prompt via the golem script, check exit code and output. Report: provider, status (ok/fail), latency, model name. Usage: golem-health. Write tests in assays/test_golem_health.py. Run pytest. Fix failures."`

#### Effector: test-dashboard
- [ ] `golem --provider infini --max-turns 40 "Create effectors/test-dashboard as Python. Reads golem.jsonl log + runs uv run pytest --co -q. Outputs: total tests, pass rate, tests per provider, recent trend (last 5 entries), untested module count. Write tests. Run pytest. Fix failures."`

### Effector test blitz (24 tasks, 73 effectors)

- [ ] `golem --provider infini --max-turns 50 "Write tests for effectors/cytokinesis (40K). Write assays/test_cytokinesis.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 50 "Write tests for effectors/lacuna (30K). Write assays/test_lacuna.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider infini --max-turns 50 "Write tests for effectors/methylation (26K). Write assays/test_methylation.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 50 "Write tests for effectors/legatum (24K). Write assays/test_legatum.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider infini --max-turns 50 "Write tests for effectors/telophase (24K). Write assays/test_telophase.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 50 "Write tests for effectors/respirometry (21K). Write assays/test_respirometry.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider infini --max-turns 50 "Write tests for effectors/chat_history.py (20K). Write assays/test_chat_history.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_proteostasis.py, assays/test_overnight_gather.py, assays/test_replisome.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/proteostasis effectors/overnight-gather effectors/replisome"`
- [ ] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_inflammasome_probe.py, assays/test_photos.py, assays/test_weekly_gather.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/inflammasome-probe effectors/photos.py effectors/weekly-gather"`
- [ ] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_linkedin_monitor.py, assays/test_paracrine.py, assays/test_diapedesis.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/linkedin-monitor effectors/paracrine effectors/diapedesis"`
- [ ] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_publish.py, assays/test_vesicle.py, assays/test_council.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/publish effectors/vesicle effectors/council"`
- [ ] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_circadian_probe.py, assays/test_legatum_verify.py, assays/test_centrosome.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/circadian-probe.py effectors/legatum-verify effectors/centrosome"`
- [ ] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_poiesis.py, assays/test_chemoreception.py, assays/test_nightly.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/poiesis effectors/chemoreception.py effectors/nightly"`
- [ ] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_switch_layer.py, assays/test_test_dashboard.py, assays/test_backfill_marks.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/switch-layer effectors/test-dashboard effectors/backfill-marks"`
- [ ] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_plan_exec_deprecated.py, assays/test_test_spec_gen.py, assays/test_rename_plists.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/plan-exec.deprecated effectors/test-spec-gen effectors/rename-plists"`
- [ ] `golem --provider volcano --max-turns 40 "Write tests for 2 effectors. Write assays/test_cn_route.py, assays/test_methylation_review.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/cn-route effectors/methylation-review"`
- [ ] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_grok.py, assays/test_channel.py, assays/test_commensal.py, assays/test_chromatin_decay_report.py, assays/test_tmux_workspace.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/grok effectors/channel effectors/commensal effectors/chromatin-decay-report.py effectors/tmux-workspace.py"`
- [ ] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_autoimmune.py, assays/test_capco_prep.py, assays/test_electroreception.py, assays/test_efferens.py, assays/test_rheotaxis_local.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/autoimmune.py effectors/capco-prep effectors/electroreception effectors/efferens effectors/rheotaxis-local"`
- [ ] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_express.py, assays/test_pinocytosis.py, assays/test_generate_solutions_index.py, assays/test_taste_score.py, assays/test_importin.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/express effectors/pinocytosis effectors/generate-solutions-index.py effectors/taste-score effectors/importin"`
- [ ] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_mitosis_checkpoint.py, assays/test_launchagent_health.py, assays/test_lysis.py, assays/test_pulse_review.py, assays/test_x_feed_to_lustro.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/mitosis-checkpoint.py effectors/launchagent-health effectors/lysis effectors/pulse-review effectors/x-feed-to-lustro"`
- [ ] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_synthase.py, assays/test_safe_search.py, assays/test_wewe_rss_health.py, assays/test_rg.py, assays/test_search_guard.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/synthase effectors/safe_search.py effectors/wewe-rss-health.py effectors/rg effectors/search-guard"`
- [ ] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_grep.py, assays/test_find.py, assays/test_immunosurveillance.py, assays/test_dr_sync.py, assays/test_phagocytosis.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/grep effectors/find effectors/immunosurveillance effectors/dr-sync effectors/phagocytosis.py"`
- [ ] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_bud.py, assays/test_receptor_scan.py, assays/test_browse.py, assays/test_safe_rm.py, assays/test_rename_kindle_asins.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/bud effectors/receptor-scan effectors/browse effectors/safe_rm.py effectors/rename-kindle-asins.py"`
- [ ] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_hkicpa.py, assays/test_rotate_logs.py, assays/test_taobao.py, assays/test_sarcio.py, assays/test_sortase.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/hkicpa effectors/rotate-logs.py effectors/taobao effectors/sarcio effectors/sortase"`

## Done (2026-03-31)

- [x] Sortase fix, substrate fix, sortase tooling, respirometry, gastrulation, substrates small, golem summary cleanup
- [x] Daemon pytest gate, vasomotor_core, RSS core, substrate tests, golem_daemon tests
- [x] Prior: golem-daemon, council, browse, provider infra, case_study, anatomy batch (+505)
