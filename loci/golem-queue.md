# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.
**ZhiPu fixed (stdin redirect). All 3 providers active: ZhiPu(4) + Infini(6) + Volcano(8) = 18 concurrent.**

## Pending

### IMPORTANT (perishable / high-impact — dispatch first)

#### Capco onboarding research
- [!] `golem --provider zhipu --full --max-turns 50 "Research Capco consulting firm. Use rheotaxis_search to find: (1) recent Capco projects in APAC banking/AI, (2) their methodology and delivery approach, (3) key competitors in HK finserv consulting. Write findings to ~/epigenome/chromatin/euchromatin/consulting/capco-research.md as structured reference. Include actionable prep items for a new joiner." (retry)`

#### AI in banking regulatory briefing
- [!] `golem --provider infini --full --max-turns 50 "Use rheotaxis_search to find latest HKMA, SFC, and MAS guidance on AI in banking (2025-2026). Focus on: model risk management, AI governance, GenAI usage policies. Write a consulting-ready briefing to ~/epigenome/chromatin/euchromatin/regulatory/ai-banking-briefing-2026.md. Structure as: key themes, regulatory expectations, gaps banks typically have, consulting opportunities." (retry)`

#### Fix effector test coaching (prevents broken golem output)
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/golem. After the _run_golem function, find the BATCH mode section. Update the batch prompt template to include: 'NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {\"__name__\": \"test_module\"}) or test via subprocess.run. NEVER use import <effector_name>.' Do the same for the TEST mode prompt. This coaching prevents broken test files."`

#### Integrin health check (is the organism healthy?)
- [!] `golem --provider infini --full --max-turns 40 "Run the integrin skill: scan all CLI binaries in ~/germline/effectors/ for breakage. For each Python effector, run python3 -c 'import ast; ast.parse(open(path).read())' to check syntax. For each with --help, run it. Report: total effectors, healthy, broken, missing shebangs. Write report to ~/epigenome/chromatin/euchromatin/system/integrin-report.md." (retry)`

### Retries (split [!] failures into smaller tasks)

#### Sortase executor (33K — needs solo golem)
- [x] `golem --provider zhipu --max-turns 50 "Write tests for metabolon/sortase/executor.py (33K — large module). Write assays/test_sortase_executor.py. Focus on pure functions. Mock subprocess/external. Run pytest. Fix failures."`

#### Sortase decompose + graph + logger (3 modules)
- [!] `golem --provider volcano --max-turns 50 "Write tests for 3 modules. Write assays/test_sortase_decompose.py, test_sortase_graph.py, test_sortase_logger.py. Run pytest. Fix failures. Modules: metabolon/sortase/decompose.py metabolon/sortase/graph.py metabolon/sortase/logger.py"`

#### Lysin + endosomal (4 modules)
- [!] `golem --provider infini --max-turns 40 "Write tests: assays/test_lysin_fetch.py, test_lysin_format.py, test_endosomal_organelle.py, test_endosomal_enzyme.py. Run pytest. Fix failures. Modules: metabolon/lysin/fetch.py metabolon/lysin/format.py metabolon/organelles/endosomal.py metabolon/enzymes/endosomal.py" (retry)`

#### Morphology + codons (2 modules)
- [!] `golem --provider volcano --max-turns 30 "Write tests: assays/test_morphology_base.py, assays/test_codons_templates_unit.py. Run pytest. Fix failures. Modules: metabolon/morphology/base.py metabolon/codons/templates.py"`

#### Pinocytosis + sporulation (4 modules)
- [!] `golem --provider infini --max-turns 30 "Write tests: assays/test_pinocytosis_photoreception.py, test_pinocytosis_ultradian.py, test_pinocytosis_ecdysis.py, test_organelle_sporulation.py. Run pytest. Fix failures. Modules: metabolon/pinocytosis/photoreception.py metabolon/pinocytosis/ultradian.py metabolon/pinocytosis/ecdysis.py metabolon/organelles/sporulation.py"`

#### Remaining tiny (3 modules)
- [!] `golem --provider volcano --max-turns 20 "Write tests: assays/test_resource_glycogen.py, test_resource_chromatin_stats.py, test_resource_consolidation.py. Run pytest. Fix failures. Modules: metabolon/resources/glycogen.py metabolon/resources/chromatin_stats.py metabolon/resources/consolidation.py"`

### Fixes (mop up test failures)

#### Fix all remaining test failures
- [!] `golem --provider volcano --max-turns 40 "Run: uv run pytest -q --tb=line 2>&1 | grep FAILED. For each failing test file, read the test and source module. Fix. Run pytest on each fixed file. Iterate until all pass. Do NOT delete tests." (retry)`

### Compound infra

#### Coaching enforcement — post-golem validation gate
- [!] `golem --provider volcano --max-turns 50 "Read effectors/golem-daemon. Find check_new_test_files_and_run_pytest. Add validate_golem_output() that runs BEFORE pytest gate on all new/modified .py files (git diff --name-only --diff-filter=AM HEAD). Checks: (1) ast.parse() each .py — fail on SyntaxError. (2) grep for TODO/FIXME/stub — fail if found. (3) test_*.py must be flat in assays/ — reject assays/subdir/test_foo.py. (4) No __pycache__/.pyc. Return (passed: bool, errors: list[str]). Wire into daemon_loop after exit=0: validate first, then pytest gate. Fail = mark_failed with errors. Update assays/test_golem_daemon.py with tests. Run pytest. Fix failures."`

### Builds (features > tests)

#### ZhiPu golem diagnosis
- [x] `golem --provider zhipu --max-turns 30 "Debug why golem --provider zhipu hangs. Read effectors/golem. Run: timeout 30 bash -c 'source ~/.zshenv.local; CLAUDECODE= ANTHROPIC_API_KEY=$ZHIPU_API_KEY ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-5.1 ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-5.1 ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-air claude --print --dangerously-skip-permissions --max-turns 1 --bare -p hello 2>&1'. Compare with how the golem script invokes claude. Find the difference causing the hang. Fix it. Test with: golem --provider zhipu --max-turns 3 'Say hello'. Verify output appears."`

#### Golem auto-retry on [!]
- [!] `golem --provider infini --max-turns 40 "Read effectors/golem-daemon. Add retry logic: when a task gets mark_failed, if it was the first attempt, re-queue it once (change [!] back to [ ] and append ' (retry)' to the command). Only retry once — if the retry also fails, keep [!]. Add a 'retried' field to the log. Update assays/test_golem_daemon.py. Run pytest. Fix failures."`

#### Golem provider health check
- [!] `golem --provider infini --max-turns 30 "Create effectors/golem-health as Python script. For each provider (zhipu, infini, volcano): send a minimal test prompt via the golem script, check exit code and output. Report: provider, status (ok/fail), latency, model name. Usage: golem-health. Write tests in assays/test_golem_health.py. Run pytest. Fix failures." (retry)`

#### Effector: test-dashboard
- [!] `golem --provider volcano --max-turns 40 "Create effectors/test-dashboard as Python. Reads golem.jsonl log + runs uv run pytest --co -q. Outputs: total tests, pass rate, tests per provider, recent trend (last 5 entries), untested module count. Write tests. Run pytest. Fix failures." (retry)`

### Effector test blitz (24 tasks, 73 effectors)

- [x] `golem --provider zhipu --max-turns 50 "Write tests for effectors/cytokinesis (40K). Write assays/test_cytokinesis.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [!] `golem --provider infini --max-turns 50 "Write tests for effectors/lacuna (30K). Write assays/test_lacuna.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures." (retry)`
- [!] `golem --provider volcano --max-turns 50 "Write tests for effectors/methylation (26K). Write assays/test_methylation.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures." (retry)`
- [!] `golem --provider zhipu --max-turns 50 "Write tests for effectors/legatum (24K). Write assays/test_legatum.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures."`
- [!] `golem --provider infini --max-turns 50 "Write tests for effectors/telophase (24K). Write assays/test_telophase.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures." (retry)`
- [!] `golem --provider volcano --max-turns 50 "Write tests for effectors/respirometry (21K). Write assays/test_respirometry.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures." (retry)`
- [!] `golem --provider zhipu --max-turns 50 "Write tests for effectors/chat_history.py (20K). Write assays/test_chat_history.py. Mock external calls, subprocess, file I/O. Run pytest. Fix failures." (retry)`
- [!] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_proteostasis.py, assays/test_overnight_gather.py, assays/test_replisome.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/proteostasis effectors/overnight-gather effectors/replisome" (retry)`
- [!] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_inflammasome_probe.py, assays/test_photos.py, assays/test_weekly_gather.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/inflammasome-probe effectors/photos.py effectors/weekly-gather" (retry)`
- [x] `golem --provider zhipu --max-turns 40 "Write tests for 3 effectors. Write assays/test_linkedin_monitor.py, assays/test_paracrine.py, assays/test_diapedesis.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/linkedin-monitor effectors/paracrine effectors/diapedesis"`
- [!] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_publish.py, assays/test_vesicle.py, assays/test_council.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/publish effectors/vesicle effectors/council" (retry)`
- [!] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_circadian_probe.py, assays/test_legatum_verify.py, assays/test_centrosome.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/circadian-probe.py effectors/legatum-verify effectors/centrosome" (retry)`
- [x] `golem --provider zhipu --max-turns 40 "Write tests for 3 effectors. Write assays/test_poiesis.py, assays/test_chemoreception.py, assays/test_nightly.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/poiesis effectors/chemoreception.py effectors/nightly"`
- [!] `golem --provider infini --max-turns 40 "Write tests for 3 effectors. Write assays/test_switch_layer.py, assays/test_test_dashboard.py, assays/test_backfill_marks.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/switch-layer effectors/test-dashboard effectors/backfill-marks" (retry)`
- [!] `golem --provider volcano --max-turns 40 "Write tests for 3 effectors. Write assays/test_plan_exec_deprecated.py, assays/test_test_spec_gen.py, assays/test_rename_plists.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/plan-exec.deprecated effectors/test-spec-gen effectors/rename-plists" (retry)`
- [x] `golem --provider zhipu --max-turns 40 "Write tests for 2 effectors. Write assays/test_cn_route.py, assays/test_methylation_review.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/cn-route effectors/methylation-review"`
- [!] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_grok.py, assays/test_channel.py, assays/test_commensal.py, assays/test_chromatin_decay_report.py, assays/test_tmux_workspace.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/grok effectors/channel effectors/commensal effectors/chromatin-decay-report.py effectors/tmux-workspace.py" (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_autoimmune.py, assays/test_capco_prep.py, assays/test_electroreception.py, assays/test_efferens.py, assays/test_rheotaxis_local.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/autoimmune.py effectors/capco-prep effectors/electroreception effectors/efferens effectors/rheotaxis-local" (retry)`
- [x] `golem --provider zhipu --max-turns 30 "Write tests for 5 effectors. Write assays/test_express.py, assays/test_pinocytosis.py, assays/test_generate_solutions_index.py, assays/test_taste_score.py, assays/test_importin.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/express effectors/pinocytosis effectors/generate-solutions-index.py effectors/taste-score effectors/importin"`
- [!] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_mitosis_checkpoint.py, assays/test_launchagent_health.py, assays/test_lysis.py, assays/test_pulse_review.py, assays/test_x_feed_to_lustro.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/mitosis-checkpoint.py effectors/launchagent-health effectors/lysis effectors/pulse-review effectors/x-feed-to-lustro" (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_synthase.py, assays/test_safe_search.py, assays/test_wewe_rss_health.py, assays/test_rg.py, assays/test_search_guard.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/synthase effectors/safe_search.py effectors/wewe-rss-health.py effectors/rg effectors/search-guard" (retry)`
- [ ] `golem --provider zhipu --max-turns 30 "Write tests for 5 effectors. Write assays/test_grep.py, assays/test_find.py, assays/test_immunosurveillance.py, assays/test_dr_sync.py, assays/test_phagocytosis.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/grep effectors/find effectors/immunosurveillance effectors/dr-sync effectors/phagocytosis.py"`
- [!] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_bud.py, assays/test_receptor_scan.py, assays/test_browse.py, assays/test_safe_rm.py, assays/test_rename_kindle_asins.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/bud effectors/receptor-scan effectors/browse effectors/safe_rm.py effectors/rename-kindle-asins.py" (retry)`
- [x] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_hkicpa.py, assays/test_rotate_logs.py, assays/test_taobao.py, assays/test_sarcio.py, assays/test_sortase.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/hkicpa effectors/rotate-logs.py effectors/taobao effectors/sarcio effectors/sortase"`

### Builds + consulting prep (20 tasks)

- [x] `golem --provider zhipu --full --max-turns 50 "Research AI consulting market in Hong Kong 2026. Use rheotaxis_search. Focus on: Big 4 vs boutique positioning, AI transformation demand in banking, skills gaps. Write to ~/epigenome/chromatin/euchromatin/consulting/hk-ai-consulting-market.md"`
- [x] `golem --provider infini --full --max-turns 50 "Research model risk management frameworks for banks. Use rheotaxis_search. Find: SR 11-7, SS2/16, HKMA circulars on model risk. Write a consulting-ready summary to ~/epigenome/chromatin/euchromatin/regulatory/model-risk-frameworks.md"`
- [!] `golem --provider volcano --full --max-turns 50 "Research GenAI use cases in banking operations. Use rheotaxis_search. Focus on: document processing, compliance monitoring, customer service, risk assessment. Write to ~/epigenome/chromatin/euchromatin/consulting/genai-banking-usecases.md" (retry)`
- [x] `golem --provider zhipu --full --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/ directory. List all files. Identify gaps in consulting knowledge base. Write a readiness assessment to ~/epigenome/chromatin/euchromatin/consulting/readiness-assessment.md"`
- [!] `golem --provider infini --max-turns 40 "Create effectors/client-brief as Python. Takes a company name, uses rheotaxis to research it, outputs a 1-page client brief (industry, size, recent news, AI posture, risks). Test it. Run pytest. Fix failures." (retry)`
- [x] `golem --provider volcano --max-turns 40 "Create effectors/regulatory-scan as Python. Scans ~/epigenome/chromatin/euchromatin/regulatory/ for stale documents (>90 days). For each stale doc, uses rheotaxis to check for updates. Outputs freshness report. Test it."`
- [ ] `golem --provider zhipu --max-turns 40 "Create effectors/consulting-card as Python. Takes a topic, generates a structured consulting insight card (problem, impact, approach, evidence, so-what). Writes to ~/epigenome/chromatin/euchromatin/consulting/cards/. Test it."`
- [!] `golem --provider infini --max-turns 40 "Read effectors/nightly. Add a section that checks golem-daemon status and includes golem summary stats in the nightly report. Test the new section. Run pytest on test_nightly.py if it exists, or create it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/express. Verify it works for weekly consulting IP production. Run it with --dry-run if available. If broken, fix it. Write tests if none exist."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/enzymes/histone.py AND the histone MCP tool. Verify memory save/recall works end-to-end. Write an integration test that saves a mark, recalls it, verifies content. assays/test_histone_integration.py."`
- [!] `golem --provider infini --max-turns 40 "Create effectors/meeting-prep as Python. Takes a meeting topic + attendees. Searches chromatin for relevant context, generates talking points and questions. Outputs markdown. Test it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/circadian-probe.py. Check if it works — run python3 effectors/circadian-probe.py --help. If broken, fix. Write assays/test_circadian_probe.py. Run pytest."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/efferens. Check if it works — run it with --help or --dry-run. If broken, fix. Write assays/test_efferens.py. Run pytest."`
- [!] `golem --provider infini --max-turns 40 "Create effectors/skill-index as Python. Scans ~/.claude/skills/*/SKILL.md, extracts name+description+triggers, outputs a searchable index. Useful for skill discovery. Test it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/respirometry. Check if cost tracking works. Run with --help. If broken, fix. Write assays/test_respirometry_effector.py. Run pytest."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/immunosurveillance. Verify LaunchAgent health checking works. Run --help. Fix if broken. Write assays/test_immunosurveillance.py."`
- [!] `golem --provider infini --max-turns 30 "Read effectors/proteostasis. Verify session cleanup works. Run --help. Fix if broken. Write assays/test_proteostasis.py." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/overnight-gather. Verify overnight content gathering works. Run --help. Fix if broken. Write assays/test_overnight_gather.py."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/weekly-gather. Verify weekly summary works. Run --help. Fix if broken. Write assays/test_weekly_gather.py."`
- [x] `golem --provider infini --max-turns 30 "Read effectors/diapedesis. Verify data migration/export works. Run --help. Fix if broken. Write assays/test_diapedesis.py."`

### Effector tests with coaching (25 tasks)

- [ ] `golem --provider zhipu --max-turns 50 "Write tests for effectors/cytokinesis (40K). Write assays/test_cytokinesis.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 50 "Write tests for effectors/telophase (24K). Write assays/test_telophase.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [x] `golem --provider volcano --max-turns 50 "Write tests for effectors/respirometry (21K). Write assays/test_respirometry.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [ ] `golem --provider zhipu --max-turns 50 "Write tests for effectors/chat_history.py (20K). Write assays/test_chat_history.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [x] `golem --provider infini --max-turns 50 "Write tests for effectors/replisome (13K). Write assays/test_replisome.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [x] `golem --provider volcano --max-turns 50 "Write tests for effectors/inflammasome-probe (13K). Write assays/test_inflammasome_probe.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [ ] `golem --provider zhipu --max-turns 50 "Write tests for effectors/photos.py (12K). Write assays/test_photos.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [x] `golem --provider infini --max-turns 40 "Write tests for effectors/linkedin-monitor (10K). Write assays/test_linkedin_monitor.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [x] `golem --provider volcano --max-turns 40 "Write tests for effectors/paracrine (10K). Write assays/test_paracrine.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Write tests for effectors/publish (9K) and effectors/vesicle (9K). Write assays/test_publish.py, assays/test_vesicle.py. NOTE: Effectors are scripts, not importable modules. Load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [x] `golem --provider infini --max-turns 40 "Write tests for effectors/council (9K) and effectors/circadian-probe.py (8K). Write assays/test_council.py, assays/test_circadian_probe.py. NOTE: Effectors are scripts, not importable modules. Load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [x] `golem --provider volcano --max-turns 40 "Write tests for effectors/legatum-verify (7K) and effectors/poiesis (7K). Write assays/test_legatum_verify.py, assays/test_poiesis.py. NOTE: Effectors are scripts, not importable modules. Load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Write tests for effectors/chemoreception.py (7K) and effectors/nightly (7K). Write assays/test_chemoreception.py, assays/test_nightly.py. NOTE: Effectors are scripts, not importable modules. Load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [x] `golem --provider infini --max-turns 40 "Write tests for effectors/switch-layer (6K) and effectors/backfill-marks (6K). Write assays/test_switch_layer.py, assays/test_backfill_marks.py. NOTE: Effectors are scripts, not importable modules. Load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/grok, effectors/channel, effectors/commensal. Write assays/test_grok.py, test_channel.py, test_commensal.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures." (retry)`
- [ ] `golem --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-decay-report.py, effectors/autoimmune.py, effectors/capco-prep. Write assays/test_chromatin_decay_report.py, test_autoimmune.py, test_capco_prep.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [!] `golem --provider infini --max-turns 30 "Write tests for effectors/express, effectors/pinocytosis, effectors/generate-solutions-index.py. Write assays/test_express.py, test_pinocytosis.py, test_generate_solutions_index.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/taste-score, effectors/importin, effectors/mitosis-checkpoint.py. Write assays/test_taste_score.py, test_importin.py, test_mitosis_checkpoint.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures." (retry)`
- [ ] `golem --provider zhipu --max-turns 30 "Write tests for effectors/lysis, effectors/pulse-review, effectors/x-feed-to-lustro, effectors/synthase. Write assays/test_lysis.py, test_pulse_review.py, test_x_feed_to_lustro.py, test_synthase.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [ ] `golem --provider volcano --max-turns 30 "Write tests for effectors/safe_search.py, effectors/rg, effectors/search-guard, effectors/grep. Write assays/test_safe_search.py, test_rg.py, test_search_guard.py, test_grep.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [x] `golem --provider volcano --max-turns 30 "Write tests for effectors/find, effectors/dr-sync, effectors/phagocytosis.py, effectors/bud. Write assays/test_find.py, test_dr_sync.py, test_phagocytosis.py, test_bud.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [ ] `golem --provider zhipu --max-turns 30 "Write tests for effectors/receptor-scan, effectors/browse, effectors/safe_rm.py, effectors/rename-kindle-asins.py. Write assays/test_receptor_scan.py, test_browse.py, test_safe_rm.py, test_rename_kindle_asins.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [!] `golem --provider infini --max-turns 30 "Write tests for effectors/hkicpa, effectors/rotate-logs.py, effectors/taobao, effectors/sarcio, effectors/sortase. Write assays/test_hkicpa.py, test_rotate_logs.py, test_taobao.py, test_sarcio.py, test_sortase.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/rename-plists, effectors/cn-route, effectors/methylation-review, effectors/plan-exec.deprecated. Write assays/test_rename_plists.py, test_cn_route.py, test_methylation_review.py, test_plan_exec_deprecated.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures." (retry)`
- [ ] `golem --provider zhipu --max-turns 30 "Write tests for effectors/test-spec-gen, effectors/tmux-workspace.py, effectors/launchagent-health, effectors/wewe-rss-health.py. Write assays/test_test_spec_gen.py, test_tmux_workspace.py, test_launchagent_health.py, test_wewe_rss_health.py. NOTE: Effectors are scripts — load via exec or subprocess.run. NEVER import. Run pytest. Fix failures."`


### Robustness wave — Fly/Vivesca/Golem (2026-03-31 evening)

#### Fix operon — top 5 failing test files (201 failures → target <50)
- [ ] `golem --provider zhipu --max-turns 40 "Read assays/test_legatum.py (29 failures). Run uv run pytest assays/test_legatum.py -q --tb=short. Read the source it tests (effectors/legatum). Fix all test failures — likely path issues (/Users/terry vs /home/terry) or mock mismatches. Use Path.home() everywhere. Run pytest until green. NEVER hardcode /Users/terry/."`
- [ ] `golem --provider volcano --max-turns 40 "Read assays/test_grok.py (25 failures). Run uv run pytest assays/test_grok.py -q --tb=short. Read the source it tests. Fix all failures. Use Path.home() for paths. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 40 "Read assays/test_commensal.py (23 failures). Run uv run pytest assays/test_commensal.py -q --tb=short. Read the source it tests. Fix all failures. Run pytest until green."`
- [!] `golem --provider infini --max-turns 40 "Read assays/test_channel.py (22 failures). Run uv run pytest assays/test_channel.py -q --tb=short. Read the source it tests. Fix all failures. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 40 "Read assays/test_sortase_actions.py (14 failures). Run uv run pytest assays/test_sortase_actions.py -q --tb=short. Read metabolon/sortase/actions.py. Fix all failures. Run pytest until green."`

#### Fix operon — next 5 failing test files
- [ ] `golem --provider volcano --max-turns 30 "Read assays/test_tmux_workspace.py (12 failures). Run uv run pytest assays/test_tmux_workspace.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 30 "Read assays/test_pinocytosis.py (12 failures). Run uv run pytest assays/test_pinocytosis.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`
- [ ] `golem --provider volcano --max-turns 30 "Read assays/test_golem_summary.py (11 failures). Run uv run pytest assays/test_golem_summary.py -q --tb=short. Read effectors/golem. Fix failures. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 30 "Read assays/test_generate_solutions_index.py (11 failures). Run uv run pytest assays/test_generate_solutions_index.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`
- [ ] `golem --provider infini --max-turns 30 "Read assays/test_chromatin_decay_report.py (7 failures). Run uv run pytest assays/test_chromatin_decay_report.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`

#### Fix operon — remaining failures (batch smaller files)
- [ ] `golem --provider zhipu --max-turns 30 "Fix test failures in: assays/test_search_guard.py (5), assays/test_scaffold_epigenome.py (4), assays/test_phagocytosis.py (4). For each: run pytest on the file, read source, fix, rerun. Use Path.home() for all paths."`
- [ ] `golem --provider infini --max-turns 30 "Fix test failures in: assays/test_methylation.py (4), assays/test_circadian_probe.py (4), assays/test_safe_search.py (3), assays/test_wewe_rss_health.py (4). For each: run pytest, read source, fix, rerun."`
- [ ] `golem --provider zhipu --max-turns 30 "Fix test failures in: assays/test_respirometry_effector.py (2), assays/test_importin.py (2), assays/test_rg.py (1). For each: run pytest, read source, fix, rerun."`

#### Fix — collection errors
- [ ] `golem --provider zhipu --max-turns 20 "Run: uv run pytest --co -q 2>&1 | grep ERROR. For each collection error: read the test file, fix the import/path/syntax issue. Common fix: replace /Users/terry/ with Path.home(). Replace import <effector> with exec(open(path).read()). Run pytest --co again to verify 0 errors."`

#### Build — golem-health effector (provider liveness check)
- [ ] `golem --provider infini --max-turns 40 "Create effectors/golem-health as a Python script. For each provider (zhipu, infini, volcano): source ~/.env.fly, then run a minimal golem invocation (golem --provider X --max-turns 1 'Say hello'). Measure: exit code, output presence, latency. Print a table: provider | status | latency | model. Usage: golem-health [--provider X]. Write assays/test_golem_health.py with mocked subprocess tests. Run pytest. Fix failures."`

#### Build — daemon log rotation
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a rotate_logs() function called at daemon start. If golem-daemon.log > 5MB, rename to golem-daemon.log.1 (overwrite old .1). Also rotate golem.jsonl the same way. Add to existing daemon start sequence. Write tests in assays/test_golem_daemon.py (append to existing). Run pytest on the file. Fix failures."`

#### Build — daemon disk space check
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem-daemon. Add a check_disk_space() function called every 10 poll cycles in daemon_loop. Use shutil.disk_usage(Path.home()). If free space < 1GB, log a WARNING and pause task dispatch (skip the 'Fill available slots' section for this cycle). Resume when space recovered. Add tests. Run pytest. Fix failures."`

#### Build — daemon auto-commit
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add auto_commit() called after every 5 successful task completions. Runs: git -C ~/germline add assays/ effectors/ metabolon/ && git commit -m 'golem: daemon auto-commit' --allow-empty-message. Only commit if there are staged changes. Log the commit hash. Add tests (mock subprocess). Run pytest. Fix failures."`

#### Build — golem stdin safety
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem. Verify that all subprocess.run / os.system calls redirect stdin from /dev/null (stdin=subprocess.DEVNULL or < /dev/null). This prevents hangs when a child process tries to read stdin. Add stdin=subprocess.DEVNULL to any subprocess.run call that lacks it. Add a test that verifies no subprocess.run call in golem is missing stdin redirect. Run pytest."`

#### Build — golem output validator
- [ ] `golem --provider zhipu --max-turns 40 "Create effectors/golem-validate as a Python script. Takes a list of .py files as args. For each: (1) ast.parse — catch SyntaxError, (2) check for /Users/terry/ hardcoded paths, (3) check for TODO/FIXME/stub, (4) if test file: check it can be collected by pytest --co. Print: file | status | issues. Exit 0 if all pass, 1 if any fail. Write assays/test_golem_validate.py. Run pytest. Fix failures."`

#### Enhance — golem summary improvements
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem. Find the summary subcommand. Enhance it to also show: (1) retry count vs first-attempt success rate, (2) average duration per provider, (3) tasks that timed out. Read ~/.local/share/vivesca/golem.jsonl for the data. Write/update assays/test_golem_summary.py. Run pytest. Fix failures."`


### Infra wave 2 — Gemmule/Golem/Daemon hardening (2026-03-31 late)

#### Daemon — log rotation (prevents disk fill)
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add rotate_logs() called once at daemon start. If ~/.local/share/vivesca/golem-daemon.log > 5MB: rename to .log.1 (overwrite). Same for golem.jsonl. Use pathlib, no external deps. Add 2 tests to assays/test_golem_daemon.py (create tmp files, verify rotation). Run uv run pytest assays/test_golem_daemon.py. Fix failures."`

#### Daemon — periodic git commit (don't lose golem output)
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem-daemon. Add auto_commit() function. Call it after every 5 successful mark_done calls (add a counter). It runs: git -C ~/germline add assays/ effectors/ metabolon/ && git diff --cached --quiet || git commit -m 'golem: daemon auto-commit'. Log the commit hash or 'nothing to commit'. Add 2 tests (mock subprocess). Run uv run pytest assays/test_golem_daemon.py. Fix failures."`

#### Daemon — dead task cleanup (purge old [!] entries)
- [ ] `golem --provider zhipu --max-turns 25 "Read effectors/golem-daemon. Add cmd_clean() invoked by 'golem-daemon clean'. It reads the queue, removes all lines matching '- [!]' and '- [x]', preserves headers and '- [ ]' lines. Rewrites the file. Prints count of removed entries. Add to main() dispatch. Add tests. Run uv run pytest assays/test_golem_daemon.py."`

#### Golem — structured JSONL logging (better analytics)
- [ ] `golem --provider infini --max-turns 30 "Read effectors/golem. Find the JSONL logging section near the end of _run_golem. Add fields: 'coaching_injected': true/false, 'model': the model name from provider config, 'mode': bare/full/batch/test. These help track which provider+model combinations succeed. Run golem --provider zhipu --max-turns 1 'Say hi' and verify the JSONL has new fields. Add tests to assays/test_golem_summary.py."`

#### Golem — provider fallback (auto-retry on different provider)
- [ ] `golem --provider zhipu --max-turns 40 "Read effectors/golem. Add --fallback flag. When set AND the primary provider fails (exit != 0), automatically retry once on a different provider: zhipu->infini, infini->zhipu, volcano->infini. Log the fallback attempt. Usage: golem --provider zhipu --fallback 'task'. Add tests that mock subprocess to verify fallback triggers. Run uv run pytest."`

#### Gemmule — startup validation script
- [ ] `golem --provider infini --max-turns 30 "Create effectors/gemmule-validate as Python. Checks: (1) disk free > 2GB, (2) supervisorctl status shows vivesca+golem-daemon running, (3) git -C ~/germline status is clean or only has expected untracked, (4) ~/.env.fly has ZHIPU/INFINI/VOLCANO keys set, (5) uv run pytest --co -q exits 0. Print pass/fail for each. Exit 0 if all pass, 1 otherwise. Write assays/test_gemmule_validate.py. Run uv run pytest."`

#### Gemmule — ephemeral file cleanup
- [ ] `golem --provider zhipu --max-turns 25 "Create effectors/gemmule-clean as Python. Removes: /tmp/claude-*/ older than 24h, ~/.cache/uv/archive-v0/ entries older than 7d, __pycache__ dirs in ~/germline/. Reports bytes freed. Safe: never touches germline source or epigenome. Write assays/test_gemmule_clean.py with mocked paths. Run uv run pytest."`

#### MCP server — health endpoint
- [ ] `golem --provider infini --max-turns 30 "Read metabolon/server.py. Add a /health HTTP endpoint that returns JSON: {status: 'ok', uptime_s: int, tools_count: int, pid: int}. Use the existing HTTP server setup. Write assays/test_server_health.py that starts the server and hits /health. Run uv run pytest."`

#### Test infra — conftest for platform-aware paths
- [ ] `golem --provider zhipu --max-turns 25 "Create assays/conftest.py (or append to existing). Add a fixture 'home_dir' that returns Path.home(). Add a fixture 'germline_dir' that returns Path.home() / 'germline'. Add a fixture 'effectors_dir'. This ensures no test hardcodes /Users/terry or /home/terry. Write 3 tests in assays/test_conftest.py to verify fixtures work. Run uv run pytest assays/test_conftest.py."`

#### Test infra — ast-check all test files pre-commit hook
- [ ] `golem --provider infini --max-turns 25 "Create effectors/check-test-syntax as Python. Runs ast.parse() on every assays/test_*.py file. Reports broken files. Exit 0 if all pass, 1 if any fail. Intended as a pre-commit or CI check. Write assays/test_check_test_syntax.py. Run uv run pytest."`

#### Monitoring — golem dashboard CLI
- [ ] `golem --provider zhipu --max-turns 40 "Create effectors/golem-dash as Python. Reads golem.jsonl + golem-daemon.log + golem-queue.md. Prints a dashboard: (1) Provider stats table (pass/fail/rate/avg_dur), (2) Queue status (pending/done/failed counts), (3) Last 5 completed tasks with result, (4) Disk free. Colorize pass=green fail=red. Usage: golem-dash. Write assays/test_golem_dash.py. Run uv run pytest."`

## Done (2026-03-31)

- [x] Sortase fix, substrate fix, sortase tooling, respirometry, gastrulation, substrates small, golem summary cleanup
- [x] Daemon pytest gate, vasomotor_core, RSS core, substrate tests, golem_daemon tests
- [x] Prior: golem-daemon, council, browse, provider infra, case_study, anatomy batch (+505)
