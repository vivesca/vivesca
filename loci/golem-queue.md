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
- [!] `golem --provider zhipu --max-turns 30 "Write tests for 5 effectors. Write assays/test_grep.py, assays/test_find.py, assays/test_immunosurveillance.py, assays/test_dr_sync.py, assays/test_phagocytosis.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/grep effectors/find effectors/immunosurveillance effectors/dr-sync effectors/phagocytosis.py" (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for 5 effectors. Write assays/test_bud.py, assays/test_receptor_scan.py, assays/test_browse.py, assays/test_safe_rm.py, assays/test_rename_kindle_asins.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/bud effectors/receptor-scan effectors/browse effectors/safe_rm.py effectors/rename-kindle-asins.py" (retry)`
- [x] `golem --provider volcano --max-turns 30 "Write tests for 5 effectors. Write assays/test_hkicpa.py, assays/test_rotate_logs.py, assays/test_taobao.py, assays/test_sarcio.py, assays/test_sortase.py. Mock external calls. Run pytest. Fix failures. Modules: effectors/hkicpa effectors/rotate-logs.py effectors/taobao effectors/sarcio effectors/sortase"`

### Builds + consulting prep (20 tasks)

- [x] `golem --provider zhipu --full --max-turns 50 "Research AI consulting market in Hong Kong 2026. Use rheotaxis_search. Focus on: Big 4 vs boutique positioning, AI transformation demand in banking, skills gaps. Write to ~/epigenome/chromatin/euchromatin/consulting/hk-ai-consulting-market.md"`
- [x] `golem --provider infini --full --max-turns 50 "Research model risk management frameworks for banks. Use rheotaxis_search. Find: SR 11-7, SS2/16, HKMA circulars on model risk. Write a consulting-ready summary to ~/epigenome/chromatin/euchromatin/regulatory/model-risk-frameworks.md"`
- [!] `golem --provider volcano --full --max-turns 50 "Research GenAI use cases in banking operations. Use rheotaxis_search. Focus on: document processing, compliance monitoring, customer service, risk assessment. Write to ~/epigenome/chromatin/euchromatin/consulting/genai-banking-usecases.md" (retry)`
- [x] `golem --provider zhipu --full --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/ directory. List all files. Identify gaps in consulting knowledge base. Write a readiness assessment to ~/epigenome/chromatin/euchromatin/consulting/readiness-assessment.md"`
- [!] `golem --provider infini --max-turns 40 "Create effectors/client-brief as Python. Takes a company name, uses rheotaxis to research it, outputs a 1-page client brief (industry, size, recent news, AI posture, risks). Test it. Run pytest. Fix failures." (retry)`
- [x] `golem --provider volcano --max-turns 40 "Create effectors/regulatory-scan as Python. Scans ~/epigenome/chromatin/euchromatin/regulatory/ for stale documents (>90 days). For each stale doc, uses rheotaxis to check for updates. Outputs freshness report. Test it."`
- [x] `golem --provider zhipu --max-turns 40 "Create effectors/consulting-card as Python. Takes a topic, generates a structured consulting insight card (problem, impact, approach, evidence, so-what). Writes to ~/epigenome/chromatin/euchromatin/consulting/cards/. Test it."`
- [!] `golem --provider infini --max-turns 40 "Read effectors/nightly. Add a section that checks golem-daemon status and includes golem summary stats in the nightly report. Test the new section. Run pytest on test_nightly.py if it exists, or create it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/express. Verify it works for weekly consulting IP production. Run it with --dry-run if available. If broken, fix it. Write tests if none exist."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/enzymes/histone.py AND the histone MCP tool. Verify memory save/recall works end-to-end. Write an integration test that saves a mark, recalls it, verifies content. assays/test_histone_integration.py."`
- [!] `golem --provider infini --max-turns 40 "Create effectors/meeting-prep as Python. Takes a meeting topic + attendees. Searches chromatin for relevant context, generates talking points and questions. Outputs markdown. Test it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/circadian-probe.py. Check if it works — run python3 effectors/circadian-probe.py --help. If broken, fix. Write assays/test_circadian_probe.py. Run pytest."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/efferens. Check if it works — run it with --help or --dry-run. If broken, fix. Write assays/test_efferens.py. Run pytest."`
- [!] `golem --provider infini --max-turns 40 "Create effectors/skill-index as Python. Scans ~/.claude/skills/*/SKILL.md, extracts name+description+triggers, outputs a searchable index. Useful for skill discovery. Test it." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/respirometry. Check if cost tracking works. Run with --help. If broken, fix. Write assays/test_respirometry_effector.py. Run pytest."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/immunosurveillance. Verify LaunchAgent health checking works. Run --help. Fix if broken. Write assays/test_immunosurveillance.py."`
- [!] `golem --provider infini --max-turns 30 "Read effectors/proteostasis. Verify session cleanup works. Run --help. Fix if broken. Write assays/test_proteostasis.py." (retry)`
- [x] `golem --provider volcano --max-turns 30 "Read effectors/overnight-gather. Verify overnight content gathering works. Run --help. Fix if broken. Write assays/test_overnight_gather.py."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/weekly-gather. Verify weekly summary works. Run --help. Fix if broken. Write assays/test_weekly_gather.py."`
- [x] `golem --provider infini --max-turns 30 "Read effectors/diapedesis. Verify data migration/export works. Run --help. Fix if broken. Write assays/test_diapedesis.py."`

### Effector tests with coaching (25 tasks)

- [ ] `golem --provider zhipu --max-turns 50 "Write tests for effectors/cytokinesis (40K). Write assays/test_cytokinesis.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
- [!] `golem --provider volcano --max-turns 50 "Write tests for effectors/telophase (24K). Write assays/test_telophase.py. NOTE: Effectors are scripts, not importable modules. Load via exec(open(path).read(), {'__name__': 'test_mod'}) or test via subprocess.run. NEVER use import <name>. Run pytest. Fix failures."`
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
- [!] `golem --provider volcano --max-turns 40 "Read assays/test_grok.py (25 failures). Run uv run pytest assays/test_grok.py -q --tb=short. Read the source it tests. Fix all failures. Use Path.home() for paths. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 40 "Read assays/test_commensal.py (23 failures). Run uv run pytest assays/test_commensal.py -q --tb=short. Read the source it tests. Fix all failures. Run pytest until green."`
- [!] `golem --provider infini --max-turns 40 "Read assays/test_channel.py (22 failures). Run uv run pytest assays/test_channel.py -q --tb=short. Read the source it tests. Fix all failures. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 40 "Read assays/test_sortase_actions.py (14 failures). Run uv run pytest assays/test_sortase_actions.py -q --tb=short. Read metabolon/sortase/actions.py. Fix all failures. Run pytest until green."`

#### Fix operon — next 5 failing test files
- [x] `golem --provider volcano --max-turns 30 "Read assays/test_tmux_workspace.py (12 failures). Run uv run pytest assays/test_tmux_workspace.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`
- [ ] `golem --provider zhipu --max-turns 30 "Read assays/test_pinocytosis.py (12 failures). Run uv run pytest assays/test_pinocytosis.py -q --tb=short. Read the source. Fix failures. Run pytest until green."`
- [x] `golem --provider volcano --max-turns 30 "Read assays/test_golem_summary.py (11 failures). Run uv run pytest assays/test_golem_summary.py -q --tb=short. Read effectors/golem. Fix failures. Run pytest until green."`
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


### Mega batch (2026-03-31 night) — fixes, health, builds, cleanup

- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_legatum.py -q --tb=short. Read the test AND source. Fix all 29 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_grok.py -q --tb=short. Read the test AND source. Fix all 25 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_commensal.py -q --tb=short. Read the test AND source. Fix all 23 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_channel.py -q --tb=short. Read the test AND source. Fix all 22 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_sortase_actions.py -q --tb=short. Read the test AND source. Fix all 14 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_tmux_workspace.py -q --tb=short. Read the test AND source. Fix all 12 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_pinocytosis.py -q --tb=short. Read the test AND source. Fix all 12 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_golem_summary.py -q --tb=short. Read the test AND source. Fix all 11 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_generate_solutions_index.py -q --tb=short. Read the test AND source. Fix all 11 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_chromatin_decay_report.py -q --tb=short. Read the test AND source. Fix all 7 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_search_guard.py -q --tb=short. Read the test AND source. Fix all 5 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_scaffold_epigenome.py -q --tb=short. Read the test AND source. Fix all 4 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_phagocytosis.py -q --tb=short. Read the test AND source. Fix all 4 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_methylation.py -q --tb=short. Read the test AND source. Fix all 4 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_circadian_probe.py -q --tb=short. Read the test AND source. Fix all 4 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_safe_search.py -q --tb=short. Read the test AND source. Fix all 3 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_wewe_rss_health.py -q --tb=short. Read the test AND source. Fix all 4 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 40 "Run uv run pytest assays/test_respirometry_effector.py -q --tb=short. Read the test AND source. Fix all 2 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider zhipu --max-turns 40 "Run uv run pytest assays/test_importin.py -q --tb=short. Read the test AND source. Fix all 2 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider infini --max-turns 40 "Run uv run pytest assays/test_rg.py -q --tb=short. Read the test AND source. Fix all 1 failures. Use Path.home(). NEVER hardcode /Users/terry/. Iterate until 0 failures."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: assay, autoimmune.py, backfill-marks, browse, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: capco-prep, centrosome, cg, channel, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: chemoreception.py, chromatin-decay-report.py, cibus.py, circadian-probe.py, ck. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: cleanup-stuck, client-brief, cn-route, commensal, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: compound-engineering-status, compound-engineering-test, consulting-card.py, council, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: demethylase, diapedesis, dr-sync, efferens, electroreception. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: engram, exocytosis.py, express, find, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: gemmation-env, generate-solutions-index.py, golem, golem-daemon, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: goose-worker, grep, grok, hkicpa, immunosurveillance. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: immunosurveillance.py, importin, inflammasome-probe, judge, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: lacuna.py, launchagent-health, legatum, legatum-verify, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: lysis, methylation, methylation-review, mismatch-repair, mitosis-checkpoint.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: nightly, oura-weekly-digest.py, overnight-gather, paracrine, phagocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: photos.py, pinocytosis, plan-exec, plan-exec.deprecated, poiesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: proteostasis, publish, pulse-review, quorum, receptor-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: regulatory-scan, rename-kindle-asins.py, rename-plists, replisome, respirometry. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: rg, rheotaxis, rheotaxis-local, rotate-logs.py, safe_rm.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: safe_search.py, search-guard, skill-sync, sortase, switch-layer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 25 "Health check: synthase, taste-score, telophase, test-dashboard, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider zhipu --max-turns 25 "Health check: tm, tmux-workspace.py, transduction-daily-run, translocon, update-compound-engineering. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider infini --max-turns 25 "Health check: vesicle, wacli-ro, weekly-gather, wewe-rss-health.py, x-feed-to-lustro. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit fixes."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: adhesion, adytum, agent-cli, agoras, amicus, analyze, anam, artifex, askesis, assay. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: auceps, auscultation, auspex, autophagy, autopoiesis, bouleusis, caelum, cardo, centrosome, certus. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: chemoreception, circadian, comes, conjugation, consilium, contract, cron, cursus, custodia, cytokinesis. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: cytometry, daily, debridement, defuddle, deleo, deltos, diagnosis, dialexis, differentiation, digest. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: docima, ecphory, elencho, endocytosis, endosomal, endosymbiosis, eow, epistula, etiology, evaluate-ai-repo. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: evaluate-job, evolvo, examen, exauro, expression, fasti, fingo, fiscus, fodina, friction. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: gist, gnome, graphis, grapho, hemostasis, heuretes, histology, hkicpa, horizo, hybridization. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: hypha, imessage, indago, infradian, integrin, involution, iris, iter, judex, judge. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: kairos, keryx, kindle, kritike, lacuna, lararium, legatum, legatus, libra, limen. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: linkedin-profile, linkedin-research, lucus, lustro, mandatum, manus, mappa, maturation, meeting-prep, meiosis. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: melete, message, metabolize, methylation, mitogen, mitosis, modification, monthly, mora, morphogenesis. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: nauta, nexis, nexum, nodus, nuntius, obsidian-cli, obsidian-markdown, oghma, ontogenesis, opifex. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: opsonization, overnight, palpation, parsimonia, peira, peirasmos, phagocytosis, photos, pinocytosis, polarization. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: pondus, poros, porta, praecepta, praeco, presentation, proliferation, prospective, python, qianli. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: qmd, quies, quorum, receptor, rector, redarguo, remote-llm, replication, rust, salus. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: sarcio, sched, scrinium, scrutor, secretion, skill-review, solutions, sopor, specification, specula. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 20 "Validate skills: speculor, splicing, sporulation, statio, stealth-browser, stilus, stips, summarize, synaxis, taobao. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider infini --max-turns 20 "Validate skills: taxis, tecton, tessera, theoria, theoros, todo, topica, transcription, transcription-factor, trutina. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider volcano --max-turns 20 "Validate skills: usage, usus, vectura, video-digest, waking-up, wechat-article, weekly. Check SKILL.md has name+description in frontmatter, description < 200 chars, no broken refs. Fix issues."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/symbiont.py metabolon/pore.py metabolon/locus.py metabolon/operons.py metabolon/cytosol.py metabolon/checkpoint.py metabolon/membrane.py metabolon/perfusion.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/respiration.py metabolon/vasomotor.py metabolon/pulse.py metabolon/enzymes/noesis.py metabolon/enzymes/mitosis.py metabolon/enzymes/synthase.py metabolon/enzymes/judge.py metabolon/enzymes/kinesin.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/enzymes/catabolism.py metabolon/enzymes/lysis.py metabolon/enzymes/histone.py metabolon/enzymes/emit.py metabolon/enzymes/cytokinesis.py metabolon/enzymes/efferens.py metabolon/enzymes/differentiation.py metabolon/enzymes/pseudopod.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/enzymes/electroreception.py metabolon/enzymes/demethylase.py metabolon/enzymes/pinocytosis.py metabolon/enzymes/sporulation.py metabolon/enzymes/navigator.py metabolon/enzymes/ingestion.py metabolon/enzymes/rheotaxis.py metabolon/enzymes/circadian.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/enzymes/tachometer.py metabolon/enzymes/gap_junction.py metabolon/enzymes/expression.py metabolon/enzymes/assay.py metabolon/enzymes/ecphory.py metabolon/enzymes/interoception.py metabolon/enzymes/endocytosis.py metabolon/enzymes/integrin.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/enzymes/turgor.py metabolon/enzymes/hemostasis.py metabolon/enzymes/sortase.py metabolon/enzymes/proprioception.py metabolon/enzymes/endosomal.py metabolon/enzymes/polarization.py metabolon/enzymes/auscultation.py metabolon/codons/templates.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/gastrulation/add.py metabolon/gastrulation/check.py metabolon/gastrulation/init.py metabolon/gastrulation/epigenome.py metabolon/morphology/base.py metabolon/pathways/overnight.py metabolon/respirometry/detect.py metabolon/respirometry/schema.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/respirometry/categories.py metabolon/respirometry/chromatin.py metabolon/respirometry/monitors.py metabolon/respirometry/payments.py metabolon/respirometry/parsers/ccba.py metabolon/respirometry/parsers/hsbc.py metabolon/respirometry/parsers/boc.py metabolon/respirometry/parsers/scb.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/respirometry/parsers/mox.py metabolon/organelles/engagement_scope.py metabolon/organelles/case_study.py metabolon/organelles/porta.py metabolon/organelles/conjugation_engine.py metabolon/organelles/pacemaker.py metabolon/organelles/secretory_vesicle.py metabolon/organelles/retrograde.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/organelles/praxis.py metabolon/organelles/mitosis.py metabolon/organelles/metabolism_loop.py metabolon/organelles/translocon_metrics.py metabolon/organelles/vasomotor_sensor.py metabolon/organelles/statolith.py metabolon/organelles/potentiation.py metabolon/organelles/receptor_sense.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/organelles/crispr.py metabolon/organelles/gemmation.py metabolon/organelles/rename.py metabolon/organelles/baroreceptor.py metabolon/organelles/polarization_loop.py metabolon/organelles/demethylase.py metabolon/organelles/circulation.py metabolon/organelles/sporulation.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/organelles/tachometer.py metabolon/organelles/gradient_sense.py metabolon/organelles/mitophagy.py metabolon/organelles/gap_junction.py metabolon/organelles/chemoreceptor.py metabolon/organelles/engram.py metabolon/organelles/glycolysis_rate.py metabolon/organelles/angiogenesis.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/organelles/golgi.py metabolon/organelles/talking_points.py metabolon/organelles/tissue_routing.py metabolon/organelles/moneo.py metabolon/organelles/rheotaxis_engine.py metabolon/organelles/inflammasome.py metabolon/organelles/phenotype_translate.py metabolon/organelles/quorum.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/organelles/effector.py metabolon/organelles/endosomal.py metabolon/organelles/entrainment.py metabolon/organelles/circadian_clock.py metabolon/organelles/translocon.py metabolon/organelles/complement.py metabolon/organelles/chromatin.py metabolon/organelles/endocytosis_rss/cargo.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/organelles/endocytosis_rss/relevance.py metabolon/organelles/endocytosis_rss/config.py metabolon/organelles/endocytosis_rss/log.py metabolon/organelles/endocytosis_rss/state.py metabolon/organelles/endocytosis_rss/fetcher.py metabolon/organelles/endocytosis_rss/cli.py metabolon/organelles/endocytosis_rss/digest.py metabolon/organelles/endocytosis_rss/migration.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/organelles/endocytosis_rss/discover.py metabolon/organelles/endocytosis_rss/breaking.py metabolon/organelles/endocytosis_rss/sorting.py metabolon/organelles/tests/test_moneo.py metabolon/pinocytosis/ultradian.py metabolon/pinocytosis/ecdysis.py metabolon/pinocytosis/interphase.py metabolon/pinocytosis/photoreception.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/pinocytosis/polarization.py metabolon/lysin/fetch.py metabolon/lysin/format.py metabolon/lysin/cli.py metabolon/metabolism/sweep.py metabolon/metabolism/setpoint.py metabolon/metabolism/dependency_check.py metabolon/metabolism/repair.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/metabolism/signals.py metabolon/metabolism/mismatch_repair.py metabolon/metabolism/preflight.py metabolon/metabolism/nociceptor.py metabolon/metabolism/fitness.py metabolon/metabolism/substrate.py metabolon/metabolism/variants.py metabolon/metabolism/infection.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/metabolism/gates.py metabolon/metabolism/substrates/memory.py metabolon/metabolism/substrates/tools.py metabolon/metabolism/substrates/spending.py metabolon/metabolism/substrates/operons.py metabolon/metabolism/substrates/constitution.py metabolon/metabolism/substrates/hygiene.py metabolon/metabolism/substrates/mismatch_repair.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/metabolism/substrates/vasomotor.py metabolon/sortase/graph.py metabolon/sortase/linter.py metabolon/sortase/overnight.py metabolon/sortase/diff_viewer.py metabolon/sortase/executor.py metabolon/sortase/history.py metabolon/sortase/cli.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Import check: metabolon/sortase/coaching_cli.py metabolon/sortase/validator.py metabolon/sortase/coaching.py metabolon/sortase/compare.py metabolon/sortase/logger.py metabolon/sortase/decompose.py metabolon/sortase/router.py metabolon/resources/reflexes.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider zhipu --max-turns 25 "Import check: metabolon/resources/oscillators.py metabolon/resources/anatomy.py metabolon/resources/circadian.py metabolon/resources/operons.py metabolon/resources/proteome.py metabolon/resources/constitution.py metabolon/resources/receptome.py metabolon/resources/vitals.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Import check: metabolon/resources/glycogen.py metabolon/resources/consolidation.py metabolon/resources/chromatin_stats.py. For each: ast.parse + try importing. Fix SyntaxError or ImportError. Commit."`
- [ ] `golem --provider volcano --max-turns 40 "Create effectors/golem-report as Python. Reads golem.jsonl. Table: pass/fail by provider, avg duration, top 5 longest, top 5 retried. Write tests."`
- [ ] `golem --provider zhipu --max-turns 30 "Create effectors/queue-stats as Python. Reads golem-queue.md. Shows: pending/done/failed, tasks per provider, estimated completion time. Write tests."`
- [ ] `golem --provider infini --max-turns 35 "Create effectors/test-health as Python. Runs pytest --co -q, counts errors. Runs pytest on random 50 tests. Reports pass rate. Write tests."`
- [ ] `golem --provider volcano --max-turns 30 "Create effectors/effector-lint as Python. Checks each effector: shebang, ast.parse, executable bit. Reports broken. Exit 1 if any. Write tests."`
- [ ] `golem --provider zhipu --max-turns 30 "Create effectors/orphan-scan as Python. Find .py in metabolon/ not imported anywhere. Report orphans. Exclude __init__.py. Write tests."`
- [ ] `golem --provider infini --max-turns 30 "Create effectors/skill-lint as Python. Check each membrane/receptors/ dir: SKILL.md exists, valid YAML frontmatter, name+description. Write tests."`
- [ ] `golem --provider volcano --max-turns 25 "Create effectors/dep-check as Python. Read pyproject.toml deps. Try importing each. Report failures. Write tests."`
- [ ] `golem --provider zhipu --max-turns 30 "Create effectors/log-summary as Python. Reads golem-daemon.log. Tasks in last 1h/6h/24h, failure rate trend, top errors. Write tests."`
- [ ] `golem --provider infini --max-turns 35 "Create effectors/conftest-gen as Python. Scans assays/ for hardcoded /Users/terry or /home/terry. Rewrites to Path.home(). --dry-run default, --fix to apply. Write tests."`
- [ ] `golem --provider volcano --max-turns 25 "Create effectors/stale-test-finder as Python. For each assays/test_*.py, check if the source module it tests still exists. Report orphan tests. Write tests."`
- [ ] `golem --provider zhipu --max-turns 25 "Scan metabolon/**/*.py for unused imports (import X where X is never used). Remove them. ast.parse after each edit. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Find duplicate effectors — pairs that do similar things. Report to loci/copia/duplicate-effectors.md."`
- [ ] `golem --provider volcano --max-turns 25 "Find all TODO/FIXME in metabolon/**/*.py. List file:line:context. Write to loci/copia/todo-audit.md."`
- [ ] `golem --provider zhipu --max-turns 25 "Find print() in metabolon/**/*.py that should be logging. Write to loci/copia/print-audit.md."`
- [ ] `golem --provider infini --max-turns 25 "Check assays/test_*.py for false-positive tests (assert True, empty bodies, over-mocked). Write to loci/copia/false-positive-tests.md."`
- [ ] `golem --provider volcano --max-turns 25 "Find .py files > 500 lines in metabolon/. For each, suggest split points. Write to loci/copia/large-module-audit.md."`
- [ ] `golem --provider zhipu --max-turns 25 "Check all effectors for hardcoded /Users/terry paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem --provider infini --max-turns 25 "Find effectors with no error handling (no try/except around subprocess calls). List them in loci/copia/error-handling-audit.md."`
- [ ] `golem --provider volcano --max-turns 25 "Check pyproject.toml for unused dependencies (declared but never imported). Report to loci/copia/unused-deps.md."`
- [ ] `golem --provider zhipu --max-turns 25 "Find circular imports in metabolon/. Try importing each top-level module and check for ImportError. Report to loci/copia/circular-imports.md."`
- [ ] `golem --provider infini --max-turns 25 "Check all assays/test_*.py use uv run pytest, not .venv/bin/python. Fix any that use old pattern. Commit."`
- [ ] `golem --provider volcano --max-turns 25 "Find effectors that shell out to other effectors (subprocess calling another effector). Map the call graph to loci/copia/effector-call-graph.md."`
- [ ] `golem --provider zhipu --max-turns 25 "Check membrane/phenotype.md references — does every path mentioned still exist? Report broken refs."`
- [ ] `golem --provider infini --max-turns 25 "Scan genome.md for rules. Check each has enforcement (test, hook, or lint). Report gaps to loci/copia/unenforced-rules.md."`
- [ ] `golem --provider volcano --max-turns 25 "Find assays/test_*.py that import from metabolon but the import path changed. Fix imports. Run pytest. Commit."`
- [ ] `golem --provider zhipu --max-turns 30 "Read effectors/golem + golem-daemon. Write operator guide: start/stop, logs, debug, tune limits. To loci/copia/golem-ops-guide.md."`
- [ ] `golem --provider infini --max-turns 25 "Generate skills index: scan all membrane/receptors/*/SKILL.md. Table: name | description | triggers. Write to loci/copia/skills-index.md."`
- [ ] `golem --provider volcano --max-turns 25 "Generate effector index: scan effectors/. Table: name | language | size | has-tests | has-help. Write to loci/copia/effector-index.md."`
- [ ] `golem --provider zhipu --max-turns 30 "Map metabolon package structure. For each subpackage: purpose, key classes, test coverage. Write to loci/copia/metabolon-map.md."`
- [ ] `golem --provider infini --max-turns 25 "Generate provider comparison from golem.jsonl: pass rate, avg speed, cost-efficiency per provider. Write to loci/copia/provider-comparison.md."`
- [ ] `golem --provider infini --max-turns 40 "Create effectors/test-fixer as Python. Takes a test file as arg. Runs pytest on it. If failures: reads test + source, applies common fixes (Path.home(), exec-based loading, mock placement). Reruns. Reports result. Write tests."`
- [ ] `golem --provider volcano --max-turns 30 "Create effectors/daemon-metrics as Python. Reads golem-daemon.log + golem.jsonl. Outputs Prometheus-style metrics: golem_tasks_total, golem_tasks_failed, golem_duration_seconds. For future monitoring. Write tests."`
- [ ] `golem --provider zhipu --max-turns 35 "Create effectors/coaching-stats as Python. Reads feedback_golem_coaching.md. Counts rules. Reads golem.jsonl for failure patterns. Reports which coaching rules are most/least effective. Write tests."`
- [ ] `golem --provider infini --max-turns 30 "Create effectors/queue-gen as Python. Takes a directory (e.g. effectors/) and generates golem-queue.md entries for all untested files. Smart batching by size. Write tests."`
- [ ] `golem --provider volcano --max-turns 30 "Create effectors/session-stats as Python. Reads ~/.local/share/vivesca/golem.jsonl. Shows: sessions today, total turns used, provider breakdown, pass rate trend over last 7 days. Write tests."`
- [ ] `golem --provider zhipu --max-turns 35 "Create effectors/provider-bench as Python. Sends identical 1-turn task to all 3 providers in parallel. Compares: latency, output quality (length, coherence). Table output. Write tests."`
- [ ] `golem --provider infini --max-turns 25 "Create effectors/disk-audit as Python. Reports: total/used/free on /, largest dirs under ~/germline, largest dirs under ~/epigenome, tmp cleanup candidates. Write tests."`
- [ ] `golem --provider volcano --max-turns 35 "Create effectors/import-graph as Python. For each .py in metabolon/, extract imports. Build dependency graph. Find circular deps, unused modules. Write DOT format to loci/copia/import-graph.dot. Write tests."`
- [ ] `golem --provider zhipu --max-turns 30 "Create effectors/receptor-health as Python. For each membrane/receptors/*/SKILL.md: validate YAML, check description length, check referenced files exist. Report broken. Write tests."`
- [ ] `golem --provider infini --max-turns 25 "Create effectors/coverage-map as Python. For each module in metabolon/, check if assays/test_<name>.py exists. Report: tested %, untested modules list. Write tests."`
- [ ] `golem --provider volcano --max-turns 15 "Fix effectors/cg: replace all /Users/terry with Path.home() or $HOME. Verify with ast.parse if Python. Run --help to confirm working. Commit."`
- [ ] `golem --provider zhipu --max-turns 15 "Fix effectors/channel: replace all /Users/terry with Path.home() or $HOME. Verify with ast.parse if Python. Run --help to confirm working. Commit."`
- [ ] `golem --provider infini --max-turns 15 "Fix effectors/ck: replace all /Users/terry with Path.home() or $HOME. Verify with ast.parse if Python. Run --help to confirm working. Commit."`
- [ ] `golem --provider volcano --max-turns 15 "Fix effectors/compound-engineering-test: replace all /Users/terry with Path.home() or $HOME. Verify with ast.parse if Python. Run --help to confirm working. Commit."`
- [ ] `golem --provider zhipu --max-turns 15 "Fix effectors/cytokinesis: replace all /Users/terry with Path.home() or $HOME. Verify with ast.parse if Python. Run --help to confirm working. Commit."`
- [ ] `golem --provider infini --max-turns 15 "Fix metabolon/enzymes/synthase.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider volcano --max-turns 15 "Fix metabolon/enzymes/judge.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider zhipu --max-turns 15 "Fix metabolon/enzymes/lysis.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider infini --max-turns 15 "Fix metabolon/enzymes/efferens.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider volcano --max-turns 15 "Fix metabolon/enzymes/assay.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider zhipu --max-turns 15 "Fix metabolon/organelles/phenotype_translate.py: replace hardcoded /Users/terry paths with Path.home(). ast.parse after. Run relevant tests. Commit."`
- [ ] `golem --provider infini --max-turns 30 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors."`
- [ ] `golem --provider volcano --max-turns 30 "Find all assays/test_*.py that use sys.path.insert to load effectors. Replace with exec(open(path).read()) pattern. Verify with pytest. Commit."`
- [ ] `golem --provider zhipu --max-turns 30 "Check all effectors/ Python files: do they handle --help gracefully? Add argparse --help to any that crash on --help. Commit."`
- [ ] `golem --provider infini --max-turns 30 "Find effectors that reference other effectors by absolute path. Replace with relative or Path-based. Commit."`
- [ ] `golem --provider volcano --max-turns 30 "Check all metabolon/__init__.py files. Verify they export the right symbols. Fix any that import deleted modules."`
- [ ] `golem --provider zhipu --max-turns 30 "Run uv run pytest -x --tb=short on the FULL suite. Note the first failure. Fix it. Run again. Fix next. Repeat for 10 failures max."`
- [ ] `golem --provider infini --max-turns 30 "Find all .py files that import from metabolon.sortase. Verify the import paths are still valid after recent refactors. Fix broken imports."`
- [ ] `golem --provider volcano --max-turns 30 "Check effectors/golem for edge cases: what if --provider is invalid? What if prompt is empty? Add input validation. Write tests."`
- [ ] `golem --provider zhipu --max-turns 30 "Check effectors/golem-daemon for edge cases: what if queue file is missing? Malformed lines? Empty file? Add guards. Write tests."`
- [ ] `golem --provider infini --max-turns 30 "Find all subprocess.run calls in effectors/ that lack timeout=. Add reasonable timeouts (60s for simple, 300s for complex). Commit."`
- [ ] `golem --provider volcano --max-turns 30 "Check all effectors for proper exit codes. 0=success, 1=error, 2=usage. Fix any that exit 0 on error. Commit."`
- [ ] `golem --provider zhipu --max-turns 30 "Find effectors that create temp files but never clean them. Add cleanup. Commit."`
- [ ] `golem --provider infini --max-turns 30 "Check genome.md for outdated references (old paths, removed tools, renamed concepts). Fix or flag. Commit."`
- [ ] `golem --provider volcano --max-turns 30 "Check membrane/phenotype.md (CLAUDE.md) for stale content. Update any references to old paths or renamed tools. Commit."`
- [ ] `golem --provider zhipu --max-turns 30 "Run uv run pytest assays/ -q --tb=no -x 2>&1 | tail -5. Record total pass/fail. Compare with last known (5369/201). Write result to loci/copia/test-baseline.md."`
- [ ] `golem --provider infini --max-turns 30 "Find all Python files using bare except: or except Exception:. Replace with specific exception types where the error is predictable. Commit."`
- [ ] `golem --provider volcano --max-turns 30 "Check assays/conftest.py exists. If not, create with home_dir, germline_dir, effectors_dir fixtures. Run pytest to verify. Commit."`
- [ ] `golem --provider zhipu --max-turns 30 "Scan for files > 1000 lines in metabolon/. For each, count functions. Report to loci/copia/complexity-audit.md."`
- [ ] `golem --provider infini --max-turns 30 "Find all .py files that use os.path instead of pathlib. In metabolon/ only: migrate to pathlib where straightforward. Commit."`
- [ ] `golem --provider volcano --max-turns 30 "Check all assays/test_*.py for proper cleanup (temp files, mock patches). Add missing cleanup. Commit."`

## Done (2026-03-31)

- [x] Sortase fix, substrate fix, sortase tooling, respirometry, gastrulation, substrates small, golem summary cleanup
- [x] Daemon pytest gate, vasomotor_core, RSS core, substrate tests, golem_daemon tests
- [x] Prior: golem-daemon, council, browse, provider infra, case_study, anatomy batch (+505)
