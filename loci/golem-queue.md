# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.
**ZhiPu fixed (stdin redirect). All 3 providers active: ZhiPu(4) + Infini(6) + Volcano(8) = 18 concurrent.**

## Pending

### Capco readiness (T-7, perishable)

- [x] `golem --provider zhipu --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/regulatory/ — list all files. For each HKMA and SFC circular about AI, write a 200-word briefing card summarizing: (1) what the regulator said, (2) implications for banks, (3) what a consultant should know. Write all cards to ~/epigenome/chromatin/euchromatin/consulting/cards/regulatory-ai-briefing.md as one consolidated document. Commit."`
- [x] `golem --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/genai-risk-framework.md — a consulting insight card on GenAI risk management framework for banks. Structure: problem (2 sentences), why it matters (3 bullets), recommended approach (numbered steps), key considerations, Capco angle. 500-800 words. Commit."`
- [x] `golem --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/model-risk-ai.md — a consulting insight card on Model Risk Management for AI/ML models in banking (SR 11-7 / SS1/23 context). Cover: current regulatory expectations, gaps in most banks' MRM frameworks for AI, practical remediation steps, and how a consultant adds value. 500-800 words. Commit."`
- [x] `golem --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-use-case-tiering.md — a consulting insight card on AI use case tiering for banks. Cover: why tiering matters (proportionality), typical tier criteria (risk, materiality, customer impact), example tier matrix, governance per tier, common mistakes. 500-800 words. Commit."`

### Fix operon — test failures (diagnostic first)

- [x] `golem --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -10. For each of the top 5 failing test files: run pytest on that file alone, read the traceback, read the source it tests, diagnose the root cause, fix. Run pytest on the file again until green. Commit each fix separately."`
- [x] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn. Take failures ranked 6-10. For each: run pytest on that file alone, read traceback, fix. Iterate until green. Commit each fix."`
- [x] `golem --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors — common causes: hardcoded paths, bad imports, missing fixtures. Run --co again until 0 errors. Commit."`

### Builds — consulting IP

- [x] `golem --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-banking.md — insight card on Responsible AI in banking. Cover: ethical AI principles relevant to banking, bias testing requirements, explainability for credit decisions (ECOA/FCRA context + HK equivalent), monitoring for drift, board-level governance. 500-800 words. Commit."`
- [x] `golem --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-patterns.md — insight card on LLM deployment patterns for banks. Cover: RAG vs fine-tuning decision, data residency constraints, prompt injection risks, hallucination guardrails, human-in-the-loop patterns, cost management. Practical, not theoretical. 500-800 words. Commit."`
- [x] `golem --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/third-party-ai-risk.md — insight card on third-party AI risk management. Cover: vendor due diligence for AI services, concentration risk (everyone using same foundation models), data sharing agreements, exit strategies, regulatory expectations (HKMA OR-2, MAS TRMG). 500-800 words. Commit."`

### Infra — golem reliability

- [x] `golem --provider zhipu --max-turns 30 "Read effectors/hatchet-golem/dispatch.py. The parse_queue function returns 5-element tuples but the type hint says 4. Fix the type hint. Also fix the pyright warnings about unused 'result' parameters in mark_done and mark_failed. Run uv run pytest assays/test_dispatch* if tests exist. Commit."`



### Mitogen wave 2 — 50 tasks (2026-04-01 afternoon)

#### Consulting IP — deep cards (10 tasks)

- [!] `golem [t-041067] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-talent-strategy-banking.md — consulting insight card on AI talent strategy for banks. Cover: build vs buy vs partner for AI capabilities, upskilling existing staff, data scientist vs ML engineer roles, retention challenges, realistic timelines. 500-800 words. Commit."`
- [!] `golem [t-ddf8d2] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-operating-model.md — consulting insight card on AI operating model design for banks. Cover: centralized vs federated vs hub-and-spoke, Center of Excellence patterns, embedding AI in business lines, reporting lines, common pitfalls. 500-800 words. Commit."`
- [!] `golem [t-a4b7ef] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-data-strategy-banking.md — consulting insight card on data strategy for AI in banking. Cover: data quality as AI bottleneck, data lineage requirements, feature stores, synthetic data for testing, data mesh vs warehouse for ML, regulatory data constraints. 500-800 words. Commit."`
- [!] `golem [t-7a34d6] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/conversational-ai-banking.md — consulting insight card on conversational AI deployment in banking. Cover: chatbot maturity model, IVR modernization, agent assist vs full automation, measuring deflection and CSAT, compliance recording requirements, vendor landscape. 500-800 words. Commit."`
- [!] `golem [t-2afc07] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-in-credit-risk.md — consulting insight card on AI in credit risk. Cover: traditional scorecards vs ML models, explainability requirements (HKMA/ECOA), challenger model framework, monitoring for drift, regulatory approval process, back-testing requirements. 500-800 words. Commit."`
- [!] `golem [t-159add] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-aml-kyc.md — consulting insight card on AI for AML/KYC in banking. Cover: transaction monitoring ML, name screening NLP, network analysis for suspicious patterns, false positive reduction, regulatory expectations (HKMA 2024 AML circular), vendor landscape. 500-800 words. Commit."`
- [!] `golem [t-fef9bd] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/cloud-ai-banking.md — consulting insight card on cloud strategy for AI workloads in banking. Cover: on-prem vs cloud vs hybrid, data residency (HK PDPO, China PIPL), GPU provisioning, cost management, multi-cloud risks, regulatory stance on cloud outsourcing. 500-800 words. Commit."`
- [!] `golem [t-afa884] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-testing-validation.md — consulting insight card on AI testing and validation for banks. Cover: unit testing for ML pipelines, A/B testing in production, shadow deployment, champion-challenger, bias testing, adversarial testing, regulatory validation requirements. 500-800 words. Commit."`
- [!] `golem [t-de4aa4] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-change-management.md — consulting insight card on change management for AI initiatives in banks. Cover: stakeholder alignment, fear of job displacement, training programs, quick wins strategy, executive sponsorship, communication plan, measuring adoption. 500-800 words. Commit."`
- [!] `golem [t-a12f1a] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-ethics-board.md — consulting insight card on establishing an AI ethics board/committee in a bank. Cover: composition, charter, decision authority, escalation criteria, case study review process, integration with existing risk governance, common failures. 500-800 words. Commit."`

#### Fix operon — test failures wave 2 (5 tasks)

- [!] `golem [t-9cdd40] --provider zhipu --max-turns 50 "Run uv run pytest assays/test_sortase*.py -q --tb=short 2>&1 | head -80. Read all failures. Read the source modules they test. Fix root causes. Iterate until all sortase tests pass. Commit."`
- [!] `golem [t-6cb28f] --provider infini --max-turns 50 "Run uv run pytest assays/test_golem*.py -q --tb=short 2>&1 | head -80. Read failures and source. Fix all golem test failures. Commit."`
- [!] `golem [t-3bfa9e] --provider volcano --max-turns 40 "Run uv run pytest assays/test_effector*.py assays/test_browser*.py -q --tb=short 2>&1 | head -80. Fix all failures in effector and browser tests. Commit."`
- [!] `golem [t-d1c85f] --provider zhipu --max-turns 40 "Run uv run pytest assays/test_respirometry*.py -q --tb=short 2>&1 | head -80. Fix all respirometry test failures. Commit."`
- [!] `golem [t-a213ab] --provider infini --max-turns 40 "Run uv run pytest assays/test_circulation*.py assays/test_chromatin*.py -q --tb=short 2>&1 | head -80. Fix all circulation and chromatin test failures. Commit."`

#### Test coverage — untested metabolon modules (15 tasks)

- [!] `golem [t-d37df3] --provider zhipu --max-turns 30 "Write tests for metabolon/enzymes/hemostasis.py. Read the module first. Mock external calls (subprocess, network). Write to assays/test_enzymes_hemostasis.py. Run uv run pytest on the file. Fix failures. Commit."`
- [!] `golem [t-ed0b16] --provider infini --max-turns 30 "Write tests for metabolon/enzymes/lysis.py. Read the module first. Mock external calls. Write to assays/test_enzymes_lysis.py. Run uv run pytest on the file. Fix failures. Commit."`
- [!] `golem [t-faa758] --provider volcano --max-turns 30 "Write tests for metabolon/enzymes/sporulation.py. Read the module first. Mock external calls. Write to assays/test_enzymes_sporulation.py. Run uv run pytest on the file. Fix failures. Commit."`
- [!] `golem [t-627902] --provider zhipu --max-turns 30 "Write tests for metabolon/enzymes/pinocytosis.py. Read the module first. Mock external calls. Write to assays/test_enzymes_pinocytosis.py. Run uv run pytest on the file. Fix failures. Commit."`
- [!] `golem [t-c7b01a] --provider infini --max-turns 30 "Write tests for metabolon/enzymes/turgor.py. Read the module. Mock externals. Write assays/test_enzymes_turgor.py. Run pytest. Fix. Commit."`
- [!] `golem [t-433064] --provider volcano --max-turns 30 "Write tests for metabolon/enzymes/kinesin.py. Read the module. Mock externals. Write assays/test_enzymes_kinesin.py. Run pytest. Fix. Commit."`
- [!] `golem [t-798c72] --provider zhipu --max-turns 30 "Write tests for metabolon/enzymes/integrin.py. Read the module. Mock externals. Write assays/test_enzymes_integrin.py. Run pytest. Fix. Commit."`
- [!] `golem [t-5d2e2f] --provider infini --max-turns 30 "Write tests for metabolon/symbiont.py. Read the module. Mock network calls. Write assays/test_symbiont.py. Run pytest. Fix. Commit."`
- [!] `golem [t-d720fc] --provider volcano --max-turns 30 "Write tests for metabolon/vasomotor.py. Read the module. Mock externals. Write assays/test_vasomotor.py. Run pytest. Fix. Commit."`
- [!] `golem [t-06617c] --provider zhipu --max-turns 30 "Write tests for metabolon/respirometry/parsers/boc.py. Read the module. Mock file I/O. Write assays/test_respirometry_parsers_boc.py. Run pytest. Fix. Commit."`
- [!] `golem [t-239a24] --provider infini --max-turns 30 "Write tests for metabolon/respirometry/parsers/hsbc.py. Read the module. Mock file I/O. Write assays/test_respirometry_parsers_hsbc.py. Run pytest. Fix. Commit."`
- [!] `golem [t-6d1076] --provider volcano --max-turns 30 "Write tests for metabolon/respirometry/parsers/mox.py. Read the module. Mock file I/O. Write assays/test_respirometry_parsers_mox.py. Run pytest. Fix. Commit."`
- [!] `golem [t-21f8ff] --provider zhipu --max-turns 30 "Write tests for metabolon/respirometry/detect.py. Read the module. Mock externals. Write assays/test_respirometry_detect.py. Run pytest. Fix. Commit."`
- [!] `golem [t-1f4ade] --provider infini --max-turns 30 "Write tests for metabolon/resources/proteome.py. Read the module. Mock externals. Write assays/test_resources_proteome.py. Run pytest. Fix. Commit."`
- [!] `golem [t-a6a481] --provider volcano --max-turns 30 "Write tests for metabolon/resources/oscillators.py. Read the module. Mock externals. Write assays/test_resources_oscillators.py. Run pytest. Fix. Commit."`

#### Test coverage — untested effectors (10 tasks)

- [!] `golem [t-83a37d] --provider zhipu --max-turns 30 "Write tests for effectors/immunosurveillance.py. It is a Python script — use subprocess.run to test. Write assays/test_immunosurveillance.py. Run uv run pytest on it. Fix. Commit."`
- [!] `golem [t-5af48b] --provider infini --max-turns 30 "Write tests for effectors/phagocytosis.py. It is a Python script — use subprocess.run to test. Write assays/test_phagocytosis.py. Run uv run pytest on it. Fix. Commit."`
- [!] `golem [t-085f3f] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.py. It is a Python script — use subprocess.run to test. Write assays/test_chromatin_backup.py. Run uv run pytest on it. Fix. Commit."`
- [!] `golem [t-f4c4fa] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-decay-report.py. Python script — use subprocess.run. Write assays/test_chromatin_decay_report.py. Run pytest. Fix. Commit."`
- [!] `golem [t-9bd46a] --provider infini --max-turns 30 "Write tests for effectors/cibus.py. Python script — use subprocess.run. Write assays/test_cibus.py. Run pytest. Fix. Commit."`
- [!] `golem [t-1d847b] --provider volcano --max-turns 30 "Write tests for effectors/circadian-probe.py. Python script — use subprocess.run. Write assays/test_circadian_probe.py. Run pytest. Fix. Commit."`
- [!] `golem [t-c81383] --provider zhipu --max-turns 30 "Write tests for effectors/consulting-card.py. Python script — use subprocess.run. Write assays/test_consulting_card.py. Run pytest. Fix. Commit."`
- [!] `golem [t-978f1c] --provider infini --max-turns 30 "Write tests for effectors/rotate-logs.py. Python script — use subprocess.run. Write assays/test_rotate_logs.py. Run pytest. Fix. Commit."`
- [!] `golem [t-7096f4] --provider volcano --max-turns 30 "Write tests for effectors/wewe-rss-health.py. Python script — use subprocess.run. Write assays/test_wewe_rss_health.py. Run pytest. Fix. Commit."`
- [!] `golem [t-aae572] --provider zhipu --max-turns 30 "Write tests for effectors/mitosis-checkpoint.py. Python script — use subprocess.run. Write assays/test_mitosis_checkpoint.py. Run pytest. Fix. Commit."`

#### Builds — organism health (5 tasks)

- [!] `golem [t-43f803] --provider infini --max-turns 40 "Create effectors/queue-stats as a Python script. It should read loci/golem-queue.md and output: total pending, total done, total failed, per-provider breakdown, average estimated turns. Add --json flag. Make it executable. Write tests in assays/test_queue_stats.py. Run pytest. Commit."`
- [!] `golem [t-f074fa] --provider zhipu --max-turns 40 "Read effectors/soma-health. Enhance it to also check: (1) disk usage on /data, (2) number of running golem processes, (3) Hatchet container health via docker ps. Output a structured health report. Write tests. Run pytest. Commit."`
- [!] `golem [t-a23254] --provider volcano --max-turns 40 "Create effectors/golem-cost as a Python script. Read ~/.local/share/vivesca/golem.jsonl. Calculate: total runs per provider, success rate per provider, average duration, estimated token cost (ZhiPu=cheap, Infini=medium, Volcano=cheap). Output table. Add --json and --since flags. Write tests. Commit."`
- [!] `golem [t-a63844] --provider zhipu --max-turns 30 "Scan all assays/test_*.py files. Find any that import modules using hardcoded absolute paths like /Users/terry/ or /home/terry/. Replace with Path.home() or relative paths. Run pytest --co to verify collection. Commit."`
- [!] `golem [t-bf70fe] --provider infini --max-turns 30 "Scan effectors/ for any Python scripts missing a shebang line (#!/usr/bin/env python3). Add missing shebangs. Also check all Python effectors parse without SyntaxError using ast.parse. Fix any syntax errors. Commit."`

#### Consulting IP — case study shells (5 tasks)

- [!] `golem [t-538257] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/genai-customer-service.md — a case study shell for a GenAI-powered customer service transformation at a mid-size HK bank. Structure: situation (bank context, pain points), approach (phases, technology choices), results (metrics), lessons learned, Capco role. 600-1000 words. Commit."`
- [!] `golem [t-02875f] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ml-credit-scoring.md — a case study shell for ML-based credit scoring at a retail bank. Cover: legacy scorecard limitations, model development approach, explainability solution, regulatory approval process, production deployment, results. 600-1000 words. Commit."`
- [!] `golem [t-4702c6] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/aml-ai-transformation.md — a case study shell for AI-driven AML transformation. Cover: false positive problem (80%+ rate), ML model for transaction monitoring, alert prioritization, regulatory engagement, phased rollout, results. 600-1000 words. Commit."`
- [!] `golem [t-89b52a] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ai-operating-model.md — a case study shell for establishing an AI Center of Excellence at an APAC bank. Cover: starting from zero, talent acquisition, governance framework, first 5 use cases, scaling challenges, 18-month roadmap. 600-1000 words. Commit."`
- [!] `golem [t-fb81f2] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/data-quality-ai-readiness.md — a case study shell for data quality remediation enabling AI adoption. Cover: data assessment findings, data lineage gaps, remediation program, feature store implementation, measurable improvement in model performance. 600-1000 words. Commit."`

### Mitogen wave 3 -- 50 tasks (2026-04-01 afternoon)

#### Test coverage -- metabolon organelles (12 tasks)

- [!] `golem [t-e1adf0] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/pacemaker.py. Read the module. Mock external calls. Write assays/test_organelles_pacemaker.py. Run uv run pytest on it. Fix. Commit."`
- [!] `golem [t-fb7a92] --provider infini --max-turns 30 "Write tests for metabolon/organelles/gradient_sense.py. Read the module. Mock externals. Write assays/test_organelles_gradient_sense.py. Run pytest. Fix. Commit."`
- [!] `golem [t-9a8800] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/tachometer.py. Read the module. Mock externals. Write assays/test_organelles_tachometer.py. Run pytest. Fix. Commit."`
- [!] `golem [t-c1914f] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/statolith.py. Read the module. Mock externals. Write assays/test_organelles_statolith.py. Run pytest. Fix. Commit."`
- [!] `golem [t-8d520a] --provider infini --max-turns 30 "Write tests for metabolon/organelles/complement.py. Read the module. Mock externals. Write assays/test_organelles_complement.py. Run pytest. Fix. Commit."`
- [!] `golem [t-6dce0f] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/golgi.py. Read the module. Mock externals. Write assays/test_organelles_golgi.py. Run pytest. Fix. Commit."`
- [!] `golem [t-69c5f4] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/entrainment.py. Read the module. Mock externals. Write assays/test_organelles_entrainment.py. Run pytest. Fix. Commit."`
- [!] `golem [t-fe3f20] --provider infini --max-turns 30 "Write tests for metabolon/organelles/talking_points.py. Read the module. Mock externals. Write assays/test_organelles_talking_points.py. Run pytest. Fix. Commit."`
- [!] `golem [t-4cf89e] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/crispr.py. Read the module. Mock externals. Write assays/test_organelles_crispr.py. Run pytest. Fix. Commit."`
- [!] `golem [t-3b797a] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/moneo.py. Read the module. Mock externals. Write assays/test_organelles_moneo.py. Run pytest. Fix. Commit."`
- [!] `golem [t-c83401] --provider infini --max-turns 30 "Write tests for metabolon/organelles/phenotype_translate.py. Read the module. Mock externals. Write assays/test_organelles_phenotype_translate.py. Run pytest. Fix. Commit."`
- [!] `golem [t-d29301] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/translocon_metrics.py. Read the module. Mock externals. Write assays/test_organelles_translocon_metrics.py. Run pytest. Fix. Commit."`

#### Test coverage -- endocytosis subsystem (6 tasks)

- [!] `golem [t-45f3a0] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_cargo.py. Read the module. Mock externals. Write assays/test_endocytosis_rss_cargo.py. Run pytest. Fix. Commit."`
- [!] `golem [t-f8a2a3] --provider infini --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_fetcher.py. Read the module. Mock network calls. Write assays/test_endocytosis_rss_fetcher.py. Run pytest. Fix. Commit."`
- [!] `golem [t-6726a5] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_relevance.py. Read the module. Mock externals. Write assays/test_endocytosis_rss_relevance.py. Run pytest. Fix. Commit."`
- [!] `golem [t-ed8fff] --provider zhipu --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_sorting.py. Read the module. Mock externals. Write assays/test_endocytosis_rss_sorting.py. Run pytest. Fix. Commit."`
- [!] `golem [t-528bfe] --provider infini --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_state.py. Read the module. Mock externals. Write assays/test_endocytosis_rss_state.py. Run pytest. Fix. Commit."`
- [!] `golem [t-ab0164] --provider volcano --max-turns 30 "Write tests for metabolon/organelles/endocytosis_rss_config.py. Read the module. Mock externals. Write assays/test_endocytosis_rss_config.py. Run pytest. Fix. Commit."`

#### Test coverage -- metabolism + resources (8 tasks)

- [!] `golem [t-e77daa] --provider zhipu --max-turns 30 "Write tests for metabolon/metabolism/preflight.py. Read the module. Mock externals. Write assays/test_metabolism_preflight.py. Run pytest. Fix. Commit."`
- [!] `golem [t-4ba0f3] --provider infini --max-turns 30 "Write tests for metabolon/metabolism/repair.py. Read the module. Mock externals. Write assays/test_metabolism_repair.py. Run pytest. Fix. Commit."`
- [!] `golem [t-052655] --provider volcano --max-turns 30 "Write tests for metabolon/metabolism/substrate.py. Read the module. Mock externals. Write assays/test_metabolism_substrate.py. Run pytest. Fix. Commit."`
- [!] `golem [t-e6ff91] --provider zhipu --max-turns 30 "Write tests for metabolon/metabolism/dependency_check.py. Read the module. Mock externals. Write assays/test_metabolism_dependency_check.py. Run pytest. Fix. Commit."`
- [!] `golem [t-ebb26b] --provider infini --max-turns 30 "Write tests for metabolon/resources/consolidation.py. Read the module. Mock externals. Write assays/test_resources_consolidation.py. Run pytest. Fix. Commit."`
- [!] `golem [t-126e27] --provider volcano --max-turns 30 "Write tests for metabolon/resources/operons.py. Read the module. Mock externals. Write assays/test_resources_operons.py. Run pytest. Fix. Commit."`
- [!] `golem [t-6c0357] --provider zhipu --max-turns 30 "Write tests for metabolon/resources/chromatin_stats.py. Read the module. Mock externals. Write assays/test_resources_chromatin_stats.py. Run pytest. Fix. Commit."`
- [!] `golem [t-5e6814] --provider infini --max-turns 30 "Write tests for metabolon/respiration.py. Read the module. Mock externals. Write assays/test_respiration.py. Run pytest. Fix. Commit."`

#### Test coverage -- more effectors (8 tasks)

- [!] `golem [t-9c08af] --provider volcano --max-turns 30 "Write tests for effectors/autoimmune.py. Python script -- use subprocess.run. Write assays/test_autoimmune.py. Run pytest. Fix. Commit."`
- [!] `golem [t-e4ace3] --provider zhipu --max-turns 30 "Write tests for effectors/exocytosis.py. Python script -- use subprocess.run. Write assays/test_exocytosis.py. Run pytest. Fix. Commit."`
- [!] `golem [t-e86719] --provider infini --max-turns 30 "Write tests for effectors/chat_history.py. Python script -- use subprocess.run. Write assays/test_chat_history.py. Run pytest. Fix. Commit."`
- [!] `golem [t-282510] --provider volcano --max-turns 30 "Write tests for effectors/chemoreception.py. Python script -- use subprocess.run. Write assays/test_chemoreception.py. Run pytest. Fix. Commit."`
- [!] `golem [t-a6f499] --provider zhipu --max-turns 30 "Write tests for effectors/photos.py. Python script -- use subprocess.run. Write assays/test_photos.py. Run pytest. Fix. Commit."`
- [!] `golem [t-be01f6] --provider infini --max-turns 30 "Write tests for effectors/safe_search.py. Python script -- use subprocess.run. Write assays/test_safe_search.py. Run pytest. Fix. Commit."`
- [!] `golem [t-5ac8b4] --provider volcano --max-turns 30 "Write tests for effectors/tmux-workspace.py. Python script -- use subprocess.run. Write assays/test_tmux_workspace.py. Run pytest. Fix. Commit."`
- [!] `golem [t-2e021d] --provider zhipu --max-turns 30 "Write tests for effectors/generate-solutions-index.py. Python script -- use subprocess.run. Write assays/test_generate_solutions_index.py. Run pytest. Fix. Commit."`

#### Test coverage -- sortase + respirometry (4 tasks)

- [!] `golem [t-b5f563] --provider infini --max-turns 40 "Write tests for metabolon/sortase/__main__.py. Read the module. Mock externals. Write assays/test_sortase___main__.py. Run pytest. Fix. Commit."`
- [!] `golem [t-f3e711] --provider volcano --max-turns 30 "Write tests for metabolon/sortase/diff_viewer.py. Read the module. Mock externals. Write assays/test_sortase_diff_viewer.py. Run pytest. Fix. Commit."`
- [!] `golem [t-6cf9f5] --provider zhipu --max-turns 30 "Write tests for metabolon/respirometry/categories.py. Read the module. Mock externals. Write assays/test_respirometry_categories.py. Run pytest. Fix. Commit."`
- [!] `golem [t-ef09e1] --provider infini --max-turns 30 "Write tests for metabolon/respirometry/schema.py. Read the module. Mock externals. Write assays/test_respirometry_schema.py. Run pytest. Fix. Commit."`

#### Hardening -- codebase quality (6 tasks)

- [!] `golem [t-c11f74] --provider volcano --max-turns 30 "Scan metabolon/ for any Python files with unused imports. Remove unused imports. Run uv run pytest --co to verify nothing broke. Commit."`
- [!] `golem [t-a74a4f] --provider zhipu --max-turns 30 "Find all subprocess.run calls in metabolon/ and effectors/ that lack a timeout parameter. Add timeout=300 to each. Run pytest --co to verify. Commit."`
- [!] `golem [t-9815e4] --provider infini --max-turns 30 "Scan assays/ for test files that shell out to commands not available on Linux (e.g. macOS-only: open, pbcopy, osascript). Mock or skip those tests on Linux. Run pytest --co. Commit."`
- [!] `golem [t-3aa379] --provider volcano --max-turns 30 "Find all open() calls in metabolon/ that don't use a context manager (with statement). Refactor to use with. Run pytest --co. Commit."`
- [!] `golem [t-f8012f] --provider zhipu --max-turns 40 "Run uv run pytest -q --tb=no 2>&1 | grep FAILED | wc -l. Then run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep ERROR | wc -l. Report both counts. Fix any collection errors. Commit."`
- [!] `golem [t-5fca92] --provider infini --max-turns 30 "Check all Python files in metabolon/ have proper __all__ exports or are internal. For any public module missing __all__, add one. Run pytest --co. Commit."`

#### Builds -- organism tooling (6 tasks)

- [!] `golem [t-b4dcd3] --provider volcano --max-turns 40 "Create effectors/coverage-map as a Python script. It reads assays/ and metabolon/ to produce a coverage matrix: which modules have tests, which don't, percentage covered. Output as table. Add --json flag. Write tests. Run pytest. Commit."`
- [!] `golem [t-fa69fa] --provider zhipu --max-turns 40 "Create effectors/effector-usage as a Python script. Scan ~/.claude/ skills and hooks for references to effectors. Report which effectors are actively used by skills/hooks and which are orphaned. Add --json flag. Write tests. Commit."`
- [!] `golem [t-7a0356] --provider infini --max-turns 40 "Read effectors/golem. Add a --summary flag that shows stats from the last N runs: success rate, average duration, per-provider breakdown. Read from ~/.local/share/vivesca/golem.jsonl. Write tests. Commit."`
- [!] `golem [t-b7aa1c] --provider volcano --max-turns 40 "Create effectors/test-fixer as a Python script. It runs pytest -q --tb=line, parses failures, groups by file, and outputs a markdown report of what's broken and likely causes. Add --json flag. Write tests. Commit."`
- [!] `golem [t-1d36fa] --provider zhipu --max-turns 40 "Read effectors/queue-balance. If it doesn't exist, create it as a Python script that reads loci/golem-queue.md and reports: tasks per provider, suggested rebalancing to maximize throughput given provider concurrency limits. Write tests. Commit."`
- [!] `golem [t-d243c1] --provider infini --max-turns 40 "Read effectors/provider-bench. If it doesn't exist, create it as a Python script that dispatches a small test task to each provider (zhipu, infini, volcano) and measures TTFB and completion time. Reports in a table. Write tests. Commit."`



### Provider resilience (2026-04-01 evening)

#### Quota tracking dashboard

- [!] `golem [t-10328d] --provider zhipu --max-turns 40 "Read effectors/golem-daemon. It already tracks cooldowns in-memory but loses them on restart. Add a persistent quota state file at ~/.local/share/vivesca/provider-quota.json that records: (1) last rate-limit hit timestamp per provider, (2) estimated reset time, (3) cumulative requests today. Update it on every task completion and rate-limit detection. Read it on daemon start to restore cooldown state. Add a 'golem-daemon quota' subcommand that prints a table of provider quota status. Write tests. Commit."`
- [!] `golem [t-193f9c] --provider zhipu --max-turns 30 "Read effectors/golem. Add a --quota flag that reads ~/.local/share/vivesca/provider-quota.json and prints current quota status for all providers in a table: provider, requests today, last rate-limit, estimated reset time, status (ok/cooldown/exhausted). Exit 0. Write tests. Commit."`



#### Codex provider fix

- [!] `golem [t-2efba8] --provider zhipu --max-turns 30 "Read effectors/golem. The codex provider invokes codex exec but does not pass --dangerously-bypass-approvals-and-sandbox. Without it, codex prompts for approval and hangs. Add the flag to the codex exec command on line ~366. Also add codex and gemini to the fallback_provider mapping. Run a test: golem --provider codex --max-turns 1 'echo test'. Commit."`

#### golem-daemon provider concurrency tuning

- [!] `golem [t-3df601] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. The PROVIDER_LIMITS dict has infini=1 which is too conservative (causes 33 tasks to queue behind 1 slot). Check the Infini plan limit -- if it is 1000 req/5hr, then 4 concurrent with 5min avg task = ~48 req/hr = well within limit. Update infini to 4. Also add codex and gemini entries: codex=4, gemini=4. Commit."`

#### Add codex+gemini to golem-daemon provider tracking

- [!] `golem [t-90be4d] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Verify that codex and gemini providers are recognized by the daemon's queue parser and task runner. The golem script already handles them -- daemon just needs to not reject unknown providers. Test by adding a codex task to the queue and checking daemon status shows it. Commit."`



### Mitogen wave 5 -- Capco readiness (2026-04-01 evening)

#### HSBC + regulatory refresh (perishable)

- [!] `golem [t-476439] --provider zhipu --max-turns 40 "Search the web for HKMA circulars and announcements from March 25 to April 1, 2026. Focus on anything related to AI, GenAI, technology risk, or digital transformation. For each new circular found, write a 200-word briefing to ~/epigenome/chromatin/euchromatin/regulatory/ with filename hkma-YYYY-MM-topic.md. Include: what it says, implications for banks, what a consultant should know. Commit."`
- [!] `golem [t-0c9f24] --provider zhipu --max-turns 40 "Search the web for SFC (Hong Kong Securities and Futures Commission) announcements from March 25 to April 1, 2026 related to AI, algorithmic trading, technology risk, or digital assets. Write briefings to ~/epigenome/chromatin/euchromatin/regulatory/ with filename sfc-YYYY-MM-topic.md. Commit."`
- [!] `golem [t-227ede] --provider zhipu --max-turns 40 "Search the web for HSBC AI news, announcements, blog posts, and press releases from the last 30 days (March 2026). Look for: new AI products, leadership changes in AI/data/digital, partnerships, regulatory filings mentioning AI, earnings call AI mentions. Write findings to ~/epigenome/chromatin/euchromatin/consulting/hsbc-ai-update-apr-2026.md. Commit."`
- [!] `golem [t-ff73ac] --provider zhipu --max-turns 40 "Search the web for Evident AI Banking Brief and Evident AI Index updates from March 15 to April 1, 2026. Evident Insights publishes weekly briefings on AI in banking at evidentinsights.com. For each issue found, extract key findings and write to ~/epigenome/chromatin/Transduction/Extractions/ with appropriate filename. Commit."`
- [!] `golem [t-243c1f] --provider zhipu --max-turns 40 "Search the web for the biggest AI news and model releases from March 20 to April 1, 2026. Focus on: new foundation model releases, major product launches, regulatory actions, notable enterprise AI deployments. Write a concise briefing (top 10 developments) to ~/epigenome/chromatin/euchromatin/consulting/ai-landscape-update-apr-2026.md. Each item: what happened, why it matters for banking, talking point for a consultant. Commit."`

#### HSBC engagement prep refresh

- [!] `golem [t-4b6b22] --provider zhipu --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/HSBC AI Intelligence - Mar 2026.md. Search the web for any updates to the topics covered since that document was written. Write an addendum file ~/epigenome/chromatin/euchromatin/consulting/hsbc-ai-intelligence-addendum-apr-2026.md covering only NEW developments not in the original. Commit."`
- [!] `golem [t-a48523] --provider zhipu --max-turns 40 "Search the web for Capco recent news, blog posts, and thought leadership from the last 30 days. Focus on their AI/data practice, new client wins, published articles, conference talks. Write to ~/epigenome/chromatin/euchromatin/consulting/capco-practice-update-apr-2026.md. Commit."`
- [!] `golem [t-88d43b] --provider zhipu --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/cards/. List all existing insight card topics. Then search the web for trending AI-in-banking topics from the last 2 weeks that are NOT already covered by existing cards. Write 3 new cards on the most relevant gaps to ~/epigenome/chromatin/euchromatin/consulting/cards/. Each card 500-800 words. Commit."`

#### Week 1 conversation assets

- [!] `golem [t-9e698a] --provider zhipu --max-turns 30 "Write ~/epigenome/chromatin/euchromatin/consulting/week1-talking-points.md -- 10 sharp, specific talking points about AI in HK banking for first-week conversations at Capco. Each point: the claim (1 sentence), the evidence (specific data point or example), the contrarian angle (what most people get wrong). Draw from HKMA circulars, HSBC specifics, and recent AI developments. Not generic -- each point should demonstrate deep domain knowledge. Commit."`
- [!] `golem [t-d012c2] --provider zhipu --max-turns 30 "Write ~/epigenome/chromatin/euchromatin/consulting/60-second-intro.md -- three versions of a 60-second professional introduction for someone joining Capco's AI practice. Version 1: for peers (other consultants). Version 2: for clients (bank executives). Version 3: for leadership (Capco partners). Each emphasizes different aspects of the background: hands-on AI building, regulatory awareness, banking domain, consulting frameworks. Commit."`




### CLI setup -- Gemini + Codex parity (2026-04-01)

#### Codex config

- [!] `golem [t-0319e8] --provider zhipu --max-turns 30 "Read ~/.codex/config.toml. Add: (1) approval_policy = 'auto-edit' under [projects.'/home/terry/germline'] so codex doesn't prompt. (2) Add sandbox_permissions = ['disk-full-read-access', 'disk-write-access'] for full file access. (3) Verify the config by running: codex exec --skip-git-repo-check 'echo hello' and confirm it runs without prompting. Commit the config."`
- [!] `golem [t-097913] --provider zhipu --max-turns 30 "Read ~/germline/CLAUDE.md (the project instruction file for Claude Code). Create ~/germline/AGENTS.md with the same content adapted for Codex -- Codex reads AGENTS.md as its project instruction file. Remove CC-specific references (hooks, skills, slash commands) but keep: codebase conventions, testing patterns, bio naming, directory layout. Commit."`

#### Gemini config

- [!] `golem [t-54a938] --provider zhipu --max-turns 30 "Read ~/germline/CLAUDE.md. Create ~/germline/.gemini/GEMINI.md with equivalent instructions adapted for Gemini CLI. Gemini reads .gemini/GEMINI.md as its project instruction file. Keep: codebase conventions, testing patterns, bio naming, directory layout. Remove CC-specific hooks/skills references. Commit."`
- [!] `golem [t-691fe8] --provider zhipu --max-turns 30 "Read ~/.gemini/settings.json. Update it to enable: (1) sandbox with full disk access if available, (2) auto-approve tool use. Check gemini --help for available settings. Apply and test with: gemini -p 'list files in current directory'. Commit."`

#### Golem script fixes for non-CC providers

- [!] `golem [t-1c37bf] --provider zhipu --max-turns 40 "Read effectors/golem lines 355-375 (the codex and gemini execution paths). Fix: (1) codex exec needs --dangerously-bypass-approvals-and-sandbox flag to avoid prompting. (2) gemini -p needs to work without shell tool access -- check if gemini has a sandbox/tools config flag. (3) Test both: golem --provider codex --max-turns 1 'echo test' and golem --provider gemini --max-turns 1 'echo test'. Commit."`


### Provider quality experiment -- same prompt x 4 providers (2026-04-01)

- [!] `golem [t-43a865] --provider zhipu --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-zhipu-apr2026.md. Commit."`
- [!] `golem [t-aa1b9b] --provider gemini --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-gemini-apr2026.md. Commit."`
- [ ] `golem [t-8f95b5] --provider codex --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-codex-apr2026.md. Commit."`


### Mitogen wave 4 -- infra + orchestration (2026-04-01 evening)

#### Fix Hatchet worker (experimental)

- [!] `golem [t-460fd3] --provider zhipu --max-turns 40 "Read effectors/hatchet-golem/worker.py. The action listener subprocess dies after ~1 task. Add try/except + file logging in _run_golem to /tmp/hatchet-golem-debug.log. Check if gRPC stream closes after first response. Write findings to effectors/hatchet-golem/TROUBLESHOOTING.md. Commit."`
- [!] `golem [t-a8ed0b] --provider infini --max-turns 30 "Read effectors/hatchet-golem/worker.py. Refactor golem_zhipu (durable_task) to use _run_golem instead of duplicated inline parsing. Run uv run pytest assays/test_*hatchet* if tests exist. Commit."`
- [!] `golem [t-8db9f3] --provider volcano --max-turns 30 "Read effectors/hatchet-golem/docker-compose.yml. Add port mapping 8080:80 to the dashboard service so the SDK token reaches the REST API. Add a comment explaining why. Commit."`

#### Fix Temporal setup (experimental)

- [!] `golem [t-2a1782] --provider zhipu --max-turns 40 "Read effectors/temporal-golem/docker-compose.yml. Fix: DB=postgres12, POSTGRES_USER/POSTGRES_PWD/POSTGRES_SEEDS env vars, port 5433:5432 to avoid conflicts. Commit."`
- [!] `golem [t-2355d2] --provider infini --max-turns 40 "Read effectors/temporal-golem/workflow.py and cli.py. Fix import paths. Write smoke test in assays/test_temporal_golem.py that mocks the Temporal client. Commit."`

#### Formalize golem-daemon as primary

- [!] `golem [t-6bf518] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add --foreground flag that skips nohup/background, runs main loop in current process (for supervisor). Write tests. Commit."`
- [!] `golem [t-dfce9c] --provider infini --max-turns 30 "Write effectors/golem-daemon-supervisor.conf -- proposed supervisor config for golem-daemon. Model on hatchet-worker in /etc/supervisor/conf.d/soma.conf. Use --foreground flag. Commit."`

#### Retries -- consulting case studies + tooling

- [!] `golem [t-b1bafd] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/genai-customer-service.md -- case study shell for GenAI customer service at a HK bank. 600-1000 words. Commit."`
- [!] `golem [t-44c34b] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ml-credit-scoring.md -- case study shell for ML credit scoring. 600-1000 words. Commit."`
- [!] `golem [t-c10b08] --provider volcano --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/aml-ai-transformation.md -- case study shell for AI AML transformation. 600-1000 words. Commit."`
- [!] `golem [t-614b9c] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ai-operating-model.md -- case study shell for AI CoE at an APAC bank. 600-1000 words. Commit."`
- [!] `golem [t-5b3e7e] --provider infini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/data-quality-ai-readiness.md -- case study shell for data quality remediation. 600-1000 words. Commit."`
- [!] `golem [t-175bcf] --provider volcano --max-turns 40 "Create effectors/coverage-map as Python script. Read assays/ and metabolon/ to produce coverage matrix. Add --json flag. Write tests. Commit."`
- [!] `golem [t-fc3807] --provider zhipu --max-turns 40 "Create effectors/test-fixer as Python script. Run pytest -q --tb=line, parse failures, group by file, output markdown report. Add --json flag. Write tests. Commit."`


### Robustness wave — Fly/Vivesca/Golem (2026-03-31 evening)

#### Fix operon — top 5 failing test files (201 failures → target <50)

#### Fix operon — next 5 failing test files

#### Fix operon — remaining failures (batch smaller files)

#### Fix — collection errors

#### Build — golem-health effector (provider liveness check)

#### Build — daemon log rotation

#### Build — daemon disk space check

#### Build — daemon auto-commit

#### Build — golem stdin safety

#### Build — golem output validator

#### Enhance — golem summary improvements


### Infra wave 2 — Gemmule/Golem/Daemon hardening (2026-03-31 late)

#### Daemon — log rotation (prevents disk fill)

#### Daemon — periodic git commit (don't lose golem output)

#### Daemon — dead task cleanup (purge old [!] entries)

#### Golem — structured JSONL logging (better analytics)

#### Golem — provider fallback (auto-retry on different provider)

#### Gemmule — startup validation script

#### Gemmule — ephemeral file cleanup

#### MCP server — health endpoint

#### Test infra — conftest for platform-aware paths

#### Test infra — ast-check all test files pre-commit hook

#### Monitoring — golem dashboard CLI


### Mega batch (2026-03-31 night) — fixes, health, builds, cleanup



### Browser operon — powerful Playwright-based browser tool

#### Build — cookie sync from Mac Chrome

#### Build — core Playwright browser engine

#### Build — browser MCP tool (vivesca integration)

#### Build — stealth + anti-detection

#### Build — cookie bridge (Mac to gemmule via Tailscale)

#### Build — authenticated browsing integration test

#### Build — browser CLI effector

#### Build — LinkedIn authenticated scraper


### Regulatory circular capture — HSBC-relevant regulators

#### Build — regulatory scraper engine

#### Capture — HKMA circulars (Hong Kong Monetary Authority)

#### Capture — SFC circulars (Securities and Futures Commission HK)

#### Capture — MAS (Monetary Authority of Singapore)

#### Capture — BIS/BCBS (Basel Committee)

#### Capture — PRA/FCA (UK regulators — HSBC HQ jurisdiction)

#### Capture — Fed/OCC (US regulators — HSBC US operations)

#### Capture — ECB/EBA (European regulators)

#### Capture — FATF (anti-money laundering + AI)

#### Capture — FSB (Financial Stability Board)

#### Capture — OWASP (application security — relevant for AI system security)

#### Synthesis — HSBC regulatory landscape report


### Research — Fly.io alternatives for always-on compute




### Build — auto-scale effector + daemon integration





### Build — Oracle Cloud free tier setup

#### Research — Oracle Cloud account + instance provisioning

#### Build — gemmule migration script

#### Build — Tailscale setup automation

#### Build — env/secrets sync tool

#### Build — dual-host health check


### Overnight mega batch (2026-03-31 night)



### Overnight fill — consulting IP + hardening + enhancements



### Post-batch synthesis (run after overnight batch drains)

#### Synthesis — overnight output digest

#### Synthesis — consulting IP executive summary

#### Synthesis — regulatory landscape summary

### Lustro content analysis — process cached articles

#### Build — lustro batch analyzer

#### Process — lustro articles → consulting signals

#### Process — endocytosis content → Capco prep

#### Process — lustro financial articles

#### Process — lustro AI/tech articles

#### Synthesis — weekly intelligence brief


### Meta-golem — self-sustaining review + requeue loop

#### Build — review-and-requeue effector (runs this once, then daemon picks up the cycle)

#### Review cycle 1 (fires ~1h into batch)

#### Review cycle 2 (fires ~2h into batch)

#### Review cycle 3 (fires ~3h into batch)

#### Review cycle 4 (fires ~4h into batch)

#### Review cycle 5 — final synthesis (fires near end of batch)


### Auto-requeue (64 tasks)

### Auto-requeue (19 tasks @ 06:09)

### Auto-requeue (64 tasks)

### Auto-requeue (19 tasks @ 07:29)
- [!] `golem [t-ba2828] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:33)
- [!] `golem [t-9044f1] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:39)

### Auto-requeue (19 tasks @ 07:44)
- [!] `golem --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:49)
- [!] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/hemostasis.py. Mock external calls. Write assays/test_enzymes_hemostasis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/variants.py. Mock external calls. Write assays/test_metabolism_variants.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-be797d] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`

### Auto-requeue (19 tasks @ 07:53)
- [!] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/lysis.py. Mock external calls. Write assays/test_enzymes_lysis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider infini --max-turns 30 "Write tests for effectors/gemmule-health. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-26ae70] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-e8b985] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 07:57)
- [!] `golem [t-eae2a5] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/gates.py. Mock external calls. Write assays/test_metabolism_gates.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0fd04a] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/pacemaker.py. Mock external calls. Write assays/test_organelles_pacemaker.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon.py. Mock external calls. Write assays/test_organelles_translocon.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1b78a5] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/infection.py. Mock external calls. Write assays/test_metabolism_infection.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-bbcd2e] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-91367b] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-ca113b] --provider zhipu --max-turns 30 "Write tests for effectors/gemmule-wake. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8f649b] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [x] `golem [t-69456b] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-5e5210] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 08:02)
- [!] `golem --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-8ce0c6] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-b61fe0] --provider infini --max-turns 30 "Health check: x-feed-to-lustro, pinocytosis, complement, update-compound-engineering-skills.sh, launchagent-health, test-fixer, chromatin-backup.sh, circadian-probe.py, paracrine, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/integrin.py. Mock external calls. Write assays/test_enzymes_integrin.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-026e0c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/demethylase.py. Mock external calls. Write assays/test_organelles_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b5a8d6] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/tissue_routing.py. Mock external calls. Write assays/test_organelles_tissue_routing.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/lysis.py. Mock external calls. Write assays/test_enzymes_lysis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-fd9639] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/retrograde.py. Mock external calls. Write assays/test_organelles_retrograde.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bdcc27] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8184de] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-504602] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-0cb093] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-89ab22] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [x] `golem [t-101bf6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d1108f] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 08:14)
- [!] `golem [t-aba479] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-bfd333] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-3ff001] --provider zhipu --max-turns 30 "Health check: plan-exec.deprecated, mismatch-repair, queue-gen, golem-top, update-compound-engineering, x-feed-to-lustro, test-spec-gen, receptor-health, pharos-health.sh, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-b6972b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/quorum.py. Mock external calls. Write assays/test_organelles_quorum.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-cbccf6] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/vitals.py. Mock external calls. Write assays/test_resources_vitals.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-2c7790] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/metabolism_loop.py. Mock external calls. Write assays/test_organelles_metabolism_loop.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-f6a512] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/lysin/cli.py. Mock external calls. Write assays/test_lysin_cli.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-64383c] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/nociceptor.py. Mock external calls. Write assays/test_metabolism_nociceptor.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-106c9d] --provider zhipu --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4a7cfe] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c9abe1] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-2f2c01] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-9a450f] --provider infini --max-turns 30 "Write tests for effectors/tm. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-86c4c7] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-7af5ce] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-5c2df2] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-46c2fc] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-450d8f] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5e4a13] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 01:16)
- [!] `golem [t-218472] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-f1c201] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-c05334] --provider zhipu --max-turns 30 "Health check: synthase, grep, oura-weekly-digest.py, safe_rm.py, gemmule-wake, importin, overnight-gather, queue-gen, rotate-logs.py, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-255368] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-0b4638] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/porta.py. Mock external calls. Write assays/test_organelles_porta.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-8fe655] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/reflexes.py. Mock external calls. Write assays/test_resources_reflexes.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-88d9e2] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-103725] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-b35017] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-427595] --provider infini --max-turns 30 "Write tests for effectors/gemmule-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-80438b] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-669100] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0c426b] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-af1d4a] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-13f1ff] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-26de37] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-660d4b] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9409a7] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e8aba5] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 01:26)
- [x] `golem [t-b494d9] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-409b84] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-b0e802] --provider volcano --max-turns 30 "Health check: gemmule-wake, golem-dash, qmd-reindex.sh, lysis, complement, quorum, taste-score, backfill-marks, plan-exec, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-faeb3b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/receptome.py. Mock external calls. Write assays/test_resources_receptome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fc0302] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/differentiation.py. Mock external calls. Write assays/test_enzymes_differentiation.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-561171] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/fitness.py. Mock external calls. Write assays/test_metabolism_fitness.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-27dc20] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/integrin.py. Mock external calls. Write assays/test_enzymes_integrin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1a6297] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/pinocytosis/interphase.py. Mock external calls. Write assays/test_pinocytosis_interphase.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8588f4] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-e76e80] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6956bd] --provider infini --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-1435c9] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-ce2f80] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0fd2ab] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-66ea82] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-319968] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-514bb1] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-78fa17] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-1f5574] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:34)
- [!] `golem [t-0b726d] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c56b76] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-d7de5c] --provider volcano --max-turns 30 "Health check: provider-bench, transduction-daily-run, update-compound-engineering-skills.sh, golem-daemon, start-chrome-debug.sh, pharos-health.sh, queue-balance, lacuna, gemmule-snapshot, vesicle. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a7b546] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1caa2f] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/monitors.py. Mock external calls. Write assays/test_respirometry_monitors.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-01435a] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/hemostasis.py. Mock external calls. Write assays/test_enzymes_hemostasis.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4c08e7] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6a5771] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cb2841] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7278d9] --provider zhipu --max-turns 30 "Write tests for effectors/gemmule-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-12ac2d] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9ca91e] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c6633c] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-30c5ab] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-b8374f] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-f0b5f0] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-5dd32b] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0cd68b] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-96f1e2] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:44)
- [!] `golem [t-8ba6c5] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a62838] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-8d4065] --provider zhipu --max-turns 30 "Health check: gemmule-wake, centrosome, diapedesis, pharos-env.sh, chemoreception.py, test-spec-gen, channel, proteostasis, weekly-gather, circadian-probe.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-3cc27e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-46d6ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/categories.py. Mock external calls. Write assays/test_respirometry_categories.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6f049f] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitophagy.py. Mock external calls. Write assays/test_organelles_mitophagy.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-47bfde] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/vasomotor_sensor.py. Mock external calls. Write assays/test_organelles_vasomotor_sensor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3e2a45] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/moneo.py. Mock external calls. Write assays/test_organelles_moneo.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0518a4] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5b2e77] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8dded4] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5c5ad1] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-948003] --provider infini --max-turns 30 "Write tests for effectors/gemmule-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0799b9] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-04c730] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-41983e] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-b6be34] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f6ee5b] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0aa0c0] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:45)
- [!] `golem [t-2c460e] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-cd543b] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-39ba9f] --provider volcano --max-turns 30 "Health check: git-activity, weekly-gather, qmd-reindex.sh, methylation-review, golem-daemon, poiesis, update-coding-tools.sh, capco-prep, golem-daemon-wrapper.sh, consulting-card.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-ae21ca] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b2b335] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sortase.py. Mock external calls. Write assays/test_enzymes_sortase.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-255d63] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/payments.py. Mock external calls. Write assays/test_respirometry_payments.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e49209] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/interoception.py. Mock external calls. Write assays/test_enzymes_interoception.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-773d65] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-0fa735] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-c887a8] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-665d64] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-08da2d] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-43d345] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-6432ac] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [!] `golem [t-91e3ba] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-7ea4a1] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-4c5315] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-8515d5] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-ff9d44] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:50)
- [x] `golem [t-e2b8ac] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3cb054] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-3f98ef] --provider volcano --max-turns 30 "Health check: launchagent-health, golem-top, legatum, judge, lysis, test-fixer, skill-sync, orphan-scan, plan-exec, queue-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-f66542] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/judge.py. Mock external calls. Write assays/test_enzymes_judge.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-02cf63] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-017dec] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-747dcc] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engagement_scope.py. Mock external calls. Write assays/test_organelles_engagement_scope.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a0e9b8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-728d02] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-bae6f6] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-67a483] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-945eab] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-130f0f] --provider zhipu --max-turns 30 "Write tests for effectors/soma-activate. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-948041] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3e00f5] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-2b11d2] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-95083d] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-71bc8e] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-133735] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:52)
- [!] `golem [t-a1a8f4] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-553a58] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4fb97a] --provider infini --max-turns 30 "Health check: compound-engineering-test, gemmation-env, provider-bench, lacuna, channel, phagocytosis.py, engram, safe_search.py, replisome, compound-engineering-status. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-6a443e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-3f1618] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/variants.py. Mock external calls. Write assays/test_metabolism_variants.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e62838] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e2b1d4] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-6d21da] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/mitosis.py. Mock external calls. Write assays/test_enzymes_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-889941] --provider infini --max-turns 30 "Write tests for effectors/gemmule-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b9d23c] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-a2fcb7] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a06006] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-62ad6b] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-e89d17] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-8c5a97] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e9a281] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-7132c1] --provider zhipu --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-80e3d8] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3997be] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:01)
- [!] `golem [t-e63bf5] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-133a30] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-43e327] --provider infini --max-turns 30 "Health check: exocytosis.py, conftest-gen, skill-search, vesicle, log-summary, goose-worker, tmux-url-select.sh, provider-bench, chromatin-decay-report.py, update-compound-engineering-skills.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a38ed4] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1c3f63] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-afbec7] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/sweep.py. Mock external calls. Write assays/test_metabolism_sweep.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-dde001] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/endosomal.py. Mock external calls. Write assays/test_organelles_endosomal.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d42f07] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-359c21] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2de404] --provider volcano --max-turns 30 "Write tests for effectors/soma-activate. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ee46d2] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-95c44a] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e55b58] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-93b283] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c91c68] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e235e1] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-3a45a8] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-8110e1] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cd6401] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:03)
- [!] `golem [t-c869bc] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-1d2ce7] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-d55220] --provider volcano --max-turns 30 "Health check: pharos-sync.sh, gemmule-clean, respirometry, chat_history.py, search-guard, switch-layer, browser, capco-prep, golem-reviewer, rename-plists. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-0f4113] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser.py. Mock external calls. Write assays/test_organelles_browser.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-191fc4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/tachometer.py. Mock external calls. Write assays/test_enzymes_tachometer.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-48ab2f] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engagement_scope.py. Mock external calls. Write assays/test_organelles_engagement_scope.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-b52b3e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sortase.py. Mock external calls. Write assays/test_enzymes_sortase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-853d7d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-73e134] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-ccaed8] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-063dd3] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-21fa0f] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-2c8d90] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6ba816] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-b25a25] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [x] `golem [t-9dad86] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fb19d4] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-94b1e4] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-181317] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:14)
- [x] `golem [t-4b5b95] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c36713] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-6e62de] --provider volcano --max-turns 30 "Health check: test-fixer, overnight-gather, safe_rm.py, chromatin-decay-report.py, wewe-rss-health.py, express, golem-health, vesicle, soma-bootstrap, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-84e9dc] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/navigator.py. Mock external calls. Write assays/test_enzymes_navigator.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e8e135] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/rheotaxis.py. Mock external calls. Write assays/test_enzymes_rheotaxis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-804e09] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-6f98ae] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-888313] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ab2078] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-01b309] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-201d1e] --provider infini --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e53ae9] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-9d8add] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-780c6c] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-674ba2] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-765101] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-789fef] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-c9796e] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-c2aa96] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:20)
- [x] `golem [t-70d083] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-cb57ba] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-4e8d47] --provider volcano --max-turns 30 "Health check: photos.py, git-activity, gap_junction_sync, cytokinesis, queue-gen, plan-exec.deprecated, golem-health, overnight-gather, centrosome, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-25aee4] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/infection.py. Mock external calls. Write assays/test_metabolism_infection.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-10cac0] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-983bfe] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-9abfb4] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitophagy.py. Mock external calls. Write assays/test_organelles_mitophagy.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ecfd32] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-57b41c] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-f5498e] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4983c9] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-42d353] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-1d16d6] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0c36a1] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-680707] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-254bca] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-7e0ece] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-067989] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-e8883e] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:27)
- [!] `golem [t-767ebb] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-18dbaf] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-9c78b8] --provider infini --max-turns 30 "Health check: rename-plists, immunosurveillance, cleanup-stuck, tmux-osc52.sh, disk-audit, receptor-health, update-coding-tools.sh, exocytosis.py, sortase, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c40e6e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rename.py. Mock external calls. Write assays/test_organelles_rename.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-57a2e9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/potentiation.py. Mock external calls. Write assays/test_organelles_potentiation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-343a71] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/entrainment.py. Mock external calls. Write assays/test_organelles_entrainment.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3efc60] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ba1257] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser.py. Mock external calls. Write assays/test_organelles_browser.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-de792a] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9b7366] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-608928] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6cbb4e] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cb0efa] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c74a77] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-ec0314] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-2979aa] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-959fe2] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0d7279] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cad42a] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 10:36)
- [!] `golem [t-86230a] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-2546c4] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-9d210b] --provider zhipu --max-turns 30 "Health check: centrosome, legatum-verify, regulatory-capture, respirometry, autoimmune.py, soma-snapshot, demethylase, channel, efferens, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-333707] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-3acc51] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/coaching_cli.py. Mock external calls. Write assays/test_sortase_coaching_cli.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-10bbc2] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/rheotaxis.py. Mock external calls. Write assays/test_enzymes_rheotaxis.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b80c89] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-abb48b] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/glycolysis_rate.py. Mock external calls. Write assays/test_organelles_glycolysis_rate.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-a2eec7] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-05c970] --provider infini --max-turns 30 "Write tests for effectors/soma-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-336ee8] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-fbe251] --provider zhipu --max-turns 30 "Write tests for effectors/soma-pull. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-e8a1a3] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-ace678] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [x] `golem [t-d0d9b9] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-af42cd] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-d40364] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-2d223c] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-94160f] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 10:40)
- [!] `golem [t-7f023a] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-9916f5] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-c0a940] --provider infini --max-turns 30 "Health check: update-coding-tools.sh, pharos-sync.sh, photos.py, queue-balance, consulting-card.py, electroreception, legatum, lacuna.py, respirometry, pharos-health.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-f58773] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-5792bd] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/differentiation.py. Mock external calls. Write assays/test_enzymes_differentiation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-97f45c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/infection.py. Mock external calls. Write assays/test_metabolism_infection.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-4da4cd] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/pinocytosis.py. Mock external calls. Write assays/test_enzymes_pinocytosis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-076067] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/efferens.py. Mock external calls. Write assays/test_enzymes_efferens.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-547e6e] --provider infini --max-turns 30 "Write tests for effectors/soma-pull. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-d5c114] --provider volcano --max-turns 30 "Write tests for effectors/soma-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-c60fd9] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-76c629] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-dea33e] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-78c4d0] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-d8483c] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [!] `golem [t-4e2d01] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [x] `golem [t-324f82] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-c87155] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-015f3f] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 02:48)
- [x] `golem [t-bc0c3e] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-b5197a] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-16b9aa] --provider infini --max-turns 30 "Health check: demethylase, test-dashboard, channel, circadian-probe.py, judge, translocon, poiesis, switch-layer, soma-bootstrap, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-00bcd3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/pseudopod.py. Mock external calls. Write assays/test_enzymes_pseudopod.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-055476] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/conjugation_engine.py. Mock external calls. Write assays/test_organelles_conjugation_engine.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-9565cf] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitosis.py. Mock external calls. Write assays/test_organelles_mitosis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-5f9daa] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/pinocytosis/interphase.py. Mock external calls. Write assays/test_pinocytosis_interphase.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-9e4216] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/signals.py. Mock external calls. Write assays/test_metabolism_signals.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6a2b8c] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5d9047] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-239fee] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-aa7843] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-40863c] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8c23fc] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-78c2bb] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-15ec11] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-21b3f4] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e1b739] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9e9f59] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:02)
- [!] `golem [t-fae7ab] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-479911] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-409ba2] --provider zhipu --max-turns 30 "Health check: receptor-health, dr-sync, pulse-review, importin, x-feed-to-lustro, launchagent-health, exocytosis.py, rheotaxis-local, lysis, oura-weekly-digest.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-9116eb] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8a8300] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rename.py. Mock external calls. Write assays/test_organelles_rename.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6c8219] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/baroreceptor.py. Mock external calls. Write assays/test_organelles_baroreceptor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f1ff57] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/integrin.py. Mock external calls. Write assays/test_enzymes_integrin.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-be7340] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/fitness.py. Mock external calls. Write assays/test_metabolism_fitness.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-50cb31] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e2b6c7] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cb98e3] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-57336c] --provider zhipu --max-turns 30 "Write tests for effectors/wacli-ro. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c55b5b] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-df614a] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-a37d09] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-9156b4] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [x] `golem [t-9ba63e] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-2c959d] --provider zhipu --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7734fa] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:05)
- [!] `golem [t-ff0d1b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-6b1dac] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-1d8e9e] --provider volcano --max-turns 30 "Health check: taste-score, update-compound-engineering, tm, golem-review, capco-prep, effector-usage, exocytosis.py, express, sortase, centrosome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-282eea] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/fitness.py. Mock external calls. Write assays/test_metabolism_fitness.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a3c852] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/pinocytosis/interphase.py. Mock external calls. Write assays/test_pinocytosis_interphase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-374260] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/sporulation.py. Mock external calls. Write assays/test_organelles_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b641aa] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/effector.py. Mock external calls. Write assays/test_organelles_effector.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d461c8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/praxis.py. Mock external calls. Write assays/test_organelles_praxis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d1a9b7] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-97f1da] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-5c7b6d] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-15b20c] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-914015] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-d8f5d0] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ba858e] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-b068f7] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit." (retry)`
- [x] `golem [t-7317c6] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-69b063] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a50c01] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:09)
- [x] `golem [t-6e625a] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-ffbd6e] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-8f9c9c] --provider zhipu --max-turns 30 "Health check: chat_history.py, cibus.py, phagocytosis.py, soma-watchdog, nightly, receptor-scan, photos.py, golem-daemon-wrapper.sh, transduction-daily-run, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-1045b7] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/endosomal.py. Mock external calls. Write assays/test_organelles_endosomal.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c995ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/monitors.py. Mock external calls. Write assays/test_respirometry_monitors.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9cc8be] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engram.py. Mock external calls. Write assays/test_organelles_engram.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f8f422] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/vasomotor_sensor.py. Mock external calls. Write assays/test_organelles_vasomotor_sensor.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6af058] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e0d1d7] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-498dcd] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b7e945] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6a6b0a] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8f9019] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-694e0c] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f6a6b4] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-72f8d6] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-47a2b3] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-107376] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-258fcd] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:15)
- [x] `golem [t-5e9ca9] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c17079] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-3460f0] --provider volcano --max-turns 30 "Health check: soma-pull, golem-daemon-wrapper.sh, proteostasis, grok, vesicle, golem-validate, skill-search, coverage-map, find, disk-audit. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-30c344] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/glycolysis_rate.py. Mock external calls. Write assays/test_organelles_glycolysis_rate.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5489c8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/sweep.py. Mock external calls. Write assays/test_metabolism_sweep.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ae39a7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/anatomy.py. Mock external calls. Write assays/test_resources_anatomy.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6f31a8] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/coaching_cli.py. Mock external calls. Write assays/test_sortase_coaching_cli.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7571f9] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/baroreceptor.py. Mock external calls. Write assays/test_organelles_baroreceptor.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-07fb8e] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-448fbd] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-749563] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ced9d7] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-59c76e] --provider zhipu --max-turns 30 "Write tests for effectors/soma-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b2d0ab] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-656b8a] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [x] `golem [t-e76a04] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-71a03c] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-20ab11] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-dd4835] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:23)
- [!] `golem [t-41e219] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e8eb1b] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-203f8a] --provider volcano --max-turns 30 "Health check: inflammasome-probe, centrosome, rheotaxis-local, circadian-probe.py, goose-worker, soma-bootstrap, golem-daemon-wrapper.sh, taste-score, receptor-health, gemmation-env. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-fe53c0] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-294cb9] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/coaching_cli.py. Mock external calls. Write assays/test_sortase_coaching_cli.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3066f8] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/glycolysis_rate.py. Mock external calls. Write assays/test_organelles_glycolysis_rate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4cc1a5] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2cc304] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/circadian.py. Mock external calls. Write assays/test_resources_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-18b8ef] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ae9272] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-47185c] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-fa5e48] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-447f95] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-26fe9f] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-941cf3] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [!] `golem [t-904d26] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-751d27] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-afc300] --provider volcano --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a70649] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:34)
- [x] `golem [t-b1ee89] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-1cef51] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-34c5f9] --provider infini --max-turns 30 "Health check: start-chrome-debug.sh, backfill-marks, nightly, soma-snapshot, phagocytosis.py, soma-scale, inflammasome-probe, golem-review, exocytosis.py, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-daf2d3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/mitosis.py. Mock external calls. Write assays/test_enzymes_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5db275] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/payments.py. Mock external calls. Write assays/test_respirometry_payments.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bd8b48] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/potentiation.py. Mock external calls. Write assays/test_organelles_potentiation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b73a10] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/tachometer.py. Mock external calls. Write assays/test_enzymes_tachometer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-771ab7] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitosis.py. Mock external calls. Write assays/test_organelles_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-482697] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5be80b] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5e9fd4] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8556d5] --provider infini --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-abf07f] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f2fe18] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-034aff] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-d12387] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-480c99] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-d440fd] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b63915] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 11:40)
- [!] `golem [t-f09807] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [x] `golem [t-645817] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b0871f] --provider infini --max-turns 30 "Health check: engram, mitosis-checkpoint.py, diapedesis, launchagent-health, disk-audit, golem-dash, cibus.py, quorum, ck, commensal. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-8e1975] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-9ae30c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engram.py. Mock external calls. Write assays/test_organelles_engram.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5a73cb] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/expression.py. Mock external calls. Write assays/test_enzymes_expression.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-4c9391] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-0c54d2] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitosis.py. Mock external calls. Write assays/test_organelles_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-97e153] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8e8675] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-141485] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-15a657] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-c8b636] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-10fbed] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-71956d] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-c92de3] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [x] `golem [t-5558fc] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-f8a15a] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-ce96fd] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:44)
- [x] `golem [t-e7841a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-fe8669] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-cd3f14] --provider volcano --max-turns 30 "Health check: golem-validate, immunosurveillance.py, importin, ck, methylation, engram, replisome, rotate-logs.py, tm, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-5b75f0] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-29ea41] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-a1163e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/expression.py. Mock external calls. Write assays/test_enzymes_expression.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-b7be84] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/infection.py. Mock external calls. Write assays/test_metabolism_infection.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4f2c47] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9db16c] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-efd13e] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ff5e40] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0b8548] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-c5c046] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c578d0] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-5f1be7] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-398478] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-49d7a1] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0586b2] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-e6098e] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (5 tasks @ 12:30)
- [x] `golem --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem --provider volcano --max-turns 30 "Health check: lacuna, golem-daemon-wrapper.sh, methylation-review, secrets-sync, effector-usage. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`

### Auto-requeue (5 tasks @ 13:30)
- [x] `golem --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem --provider infini --max-turns 30 "Health check: hkicpa, queue-gen, golem-top, backup-due.sh, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`

### Auto-requeue (5 tasks @ 14:30)
- [x] `golem --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem --provider volcano --max-turns 30 "Health check: disk-audit, update-coding-tools.sh, photos.py, grok, rheotaxis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`

### Auto-requeue (5 tasks @ 15:30)
- [!] `golem --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem --provider zhipu --max-turns 30 "Health check: soma-snapshot, weekly-gather, test-spec-gen, centrosome, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`

### Auto-requeue (19 tasks @ 15:42)
- [!] `golem [t-c88788] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7bf264] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-08b5ca] --provider infini --max-turns 30 "Health check: safe_search.py, lysis, orphan-scan, respirometry, skill-search, mismatch-repair, hetzner-bootstrap.sh, legatum-verify, golem, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-0e4188] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1af4fe] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-811fd2] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3d5012] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/pinocytosis.py. Mock external calls. Write assays/test_enzymes_pinocytosis.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3f78bc] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-89b624] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eb511b] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-062a2b] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4233ce] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7f8d25] --provider volcano --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-959be7] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-1d302e] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-7cf772] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-dc3e63] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1426bb] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f0f2c4] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:42)
- [!] `golem [t-954e8c] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3e67e5] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-03ece1] --provider volcano --max-turns 30 "Health check: oura-weekly-digest.py, quorum, grep, rheotaxis-local, soma-snapshot, hetzner-bootstrap.sh, browse, orphan-scan, compound-engineering-status, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f63cd1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b6b0a5] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-827052] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c6e164] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-442bb5] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a2f9d0] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cf94e8] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3116df] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d683b8] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c572ec] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c2e5f4] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-1eb311] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-b336f9] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-a675bf] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-232278] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0804ea] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:43)
- [!] `golem [t-3fecd0] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-757fb2] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-467116] --provider infini --max-turns 30 "Health check: nightly, regulatory-capture, receptor-health, queue-stats, circadian-probe.py, browser, legatum, git-activity, soma-pull, qmd-reindex.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-32c474] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-470458] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1fba2d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-065d5d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9ac0e1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ba082c] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5ef81c] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0922ea] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9eaf2b] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f7c42f] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3ddd92] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-07f4ed] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-7fecd4] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-b5fa04] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-daa513] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab475a] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:43)
- [!] `golem [t-e3e78e] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-424f3d] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-76ba44] --provider volcano --max-turns 30 "Health check: cytokinesis, wacli-ro, importin, proteostasis, test-dashboard, pharos-health.sh, autoimmune.py, plan-exec.deprecated, safe_search.py, soma-clean. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b79f63] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c31f46] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e62e9f] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ab21d3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9ac4b1] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-318a70] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b8c717] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4e4070] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3301b7] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-77728c] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4c2bde] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-9208be] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-41065d] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-e1a526] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3be216] --provider volcano --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a082d2] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:44)
- [!] `golem [t-24964d] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-ec798e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e4f07c] --provider infini --max-turns 30 "Health check: efferens, judge, paracrine, diapedesis, update-coding-tools.sh, channel, golem-reviewer, importin, bud, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b8e8ae] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/tachometer.py. Mock external calls. Write assays/test_organelles_tachometer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ffebbe] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f3c2a6] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-76a089] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d4cad7] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-751055] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e27285] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4a1890] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-90af4e] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-71d3c4] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9846c2] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-614f5a] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-38cb30] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-22622d] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4eab49] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-452519] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:44)
- [!] `golem [t-980ca0] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-078d7a] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-060544] --provider volcano --max-turns 30 "Health check: linkedin-monitor, receptor-scan, efferens, backup-due.sh, dr-sync, circadian-probe.py, golem-daemon-wrapper.sh, wewe-rss-health.py, update-compound-engineering, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-82e8c1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5304af] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b677a3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5a7c55] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-498743] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-de5cc6] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8d998d] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5452db] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2d04f3] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-17cbb8] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-27fba1] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-ff944d] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-0e658c] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-7db91c] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4444e6] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a0f9b8] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:45)
- [!] `golem [t-aeb083] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-66493f] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-940e54] --provider volcano --max-turns 30 "Health check: linkedin-monitor, agent-sync.sh, oura-weekly-digest.py, hetzner-bootstrap.sh, secrets-sync, qmd-reindex.sh, plan-exec.deprecated, rotate-logs.py, soma-health, soma-bootstrap. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-aa41d5] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2977c4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7d7dee] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d893aa] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0e742d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-54ad49] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-744d3b] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-680a50] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-74c0f2] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-70d58e] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-475a10] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-d98713] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-bc0335] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-8db045] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-bd6f96] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3badd9] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:46)
- [!] `golem [t-0a432e] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-4db632] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-2fa1d9] --provider infini --max-turns 30 "Health check: soma-snapshot, chromatin-decay-report.py, publish, git-activity, soma-wake, nightly, goose-worker, centrosome, judge, regulatory-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-acc74d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-39aa62] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-292ca6] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8ef92e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-605b01] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6778b2] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-70f062] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3f01c2] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2ed152] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1fcbd3] --provider volcano --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-394473] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-51cf69] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-0ac09c] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-b2da52] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-b3557b] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-55842b] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:46)
- [!] `golem [t-de1f10] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-be1848] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b37fbd] --provider zhipu --max-turns 30 "Health check: tmux-osc52.sh, orphan-scan, golem-health, search-guard, test-dashboard, start-chrome-debug.sh, commensal, provider-bench, soma-scale, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e8a794] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-96c6ba] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9e58c6] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0e7236] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/tachometer.py. Mock external calls. Write assays/test_organelles_tachometer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4f1569] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a3989f] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1272d8] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fad2f2] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-97a3a3] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-490cb3] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-89989c] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-f4bd44] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-971629] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-56913b] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9f1771] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-05c708] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:47)
- [!] `golem [t-8485a3] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e58864] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-09ac40] --provider infini --max-turns 30 "Health check: oura-weekly-digest.py, circadian-probe.py, synthase, methylation, search-guard, pharos-sync.sh, soma-wake, receptor-scan, browse, express. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-2091ca] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-088f5e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-323a18] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1f6e0d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-90bbba] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2d95a1] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c63ab2] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-08d44c] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5a41c7] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-31360f] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-df2d5a] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-326b45] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-94fbc7] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-eba31c] --provider zhipu --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0d122f] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e60282] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:48)
- [!] `golem [t-7626bc] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-675c1a] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-ad3324] --provider zhipu --max-turns 30 "Health check: coverage-map, switch-layer, oura-weekly-digest.py, safe_search.py, launchagent-health, transduction-daily-run, generate-solutions-index.py, conftest-gen, rename-plists, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c3fbf3] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a19746] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6c11e3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-043dba] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6ba2dd] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-74eb55] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ed9d74] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3ceec2] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4207f5] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d9c491] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f8ecff] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-6e34df] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-4aceaa] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-be822e] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-57e5d1] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f176ac] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:49)
- [!] `golem [t-dec107] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c443fe] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-fc5ac4] --provider zhipu --max-turns 30 "Health check: soma-scale, oci-arm-retry, oura-weekly-digest.py, rename-kindle-asins.py, cleanup-stuck, test-fixer, importin, soma-bootstrap, channel, centrosome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f24679] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c668b3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9d6bd1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-047ebc] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-83415a] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2cc6ce] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3ed8f0] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-90f30b] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-07b124] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-04dbe8] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4f8780] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-d6e95c] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-d466df] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-eb131e] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f563d7] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-47ead0] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:50)
- [!] `golem [t-deab6f] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3d0164] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-38380d] --provider infini --max-turns 30 "Health check: soma-watchdog, weekly-gather, test-fixer, tmux-workspace.py, tm, vesicle, lustro-analyze, complement, update-compound-engineering-skills.sh, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e30804] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d8efdd] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/tachometer.py. Mock external calls. Write assays/test_organelles_tachometer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5e4078] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d556fb] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-45ef52] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-680d2f] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4b02b7] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0f919b] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f73455] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4a957e] --provider volcano --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a6cefc] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-04e62c] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-0b22b0] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-ed9d1e] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1569a5] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d6473a] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:50)
- [!] `golem [t-ead018] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-710385] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-106fae] --provider volcano --max-turns 30 "Health check: perplexity.sh, plan-exec.deprecated, pharos-env.sh, methylation-review, test-fixer, inflammasome-probe, skill-sync, consulting-card.py, bud, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-9deb10] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-555eea] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-81b13c] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-714d3b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f7412e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-16a200] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d01d9e] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2aeb99] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1f581a] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-07068e] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-21dbb2] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-03738e] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-80cf50] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-398a1d] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9c05b1] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9b7b7e] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:51)
- [!] `golem [t-a89270] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-9695af] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d26a92] --provider volcano --max-turns 30 "Health check: cookie-sync, channel, golem-cost, rename-kindle-asins.py, golem-validate, proteostasis, vesicle, golem-top, queue-gen, compound-engineering-test. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b3d6eb] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5b12b7] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2373c5] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4f3051] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4fe196] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2f8edd] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-353633] --provider zhipu --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-16a321] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-536424] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-95161b] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fdfb6c] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-471069] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-ac0903] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-109357] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-92e70a] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-252ff4] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:52)
- [!] `golem [t-c89528] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-325363] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-06b9e2] --provider infini --max-turns 30 "Health check: chemoreception.py, secrets-sync, judge, inflammasome-probe, channel, compound-engineering-status, replisome, fix-symlinks, demethylase, council. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-31c981] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8704b5] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ae645b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-073b1d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3e9f61] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-43e685] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-09da63] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8ecbf7] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f7a064] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6fb129] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8736af] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-4abfec] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-0245ad] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-7438dc] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-764790] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fe6cf5] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:52)
- [!] `golem [t-b47e41] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-232c0a] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-a633cb] --provider zhipu --max-turns 30 "Health check: legatum-verify, pharos-sync.sh, oci-arm-retry, electroreception, diapedesis, soma-bootstrap, provider-bench, browser, methylation, phagocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-dda444] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-78354e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-88f87d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3a9fbb] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7f63d7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e49bf1] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-619698] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f2cc61] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-584b14] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5cad5f] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f44daa] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-2320fc] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-b0a477] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-6f19d2] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d2e611] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-662aef] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:53)
- [!] `golem [t-5685bb] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-18a898] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-878b9c] --provider zhipu --max-turns 30 "Health check: skill-sync, effector-usage, transduction-daily-run, golem-dash, importin, methylation-review, search-guard, bud, inflammasome-probe, golem-top. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-5fa1af] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-920937] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bbaa2b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ea79cd] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7839bf] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-14b6b3] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b50f8d] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d485b4] --provider volcano --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-99b99f] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-202162] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ddbeac] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-321274] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-3b3676] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e30ca9] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fcb541] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f24ea7] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:54)
- [!] `golem [t-7cec00] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-f583ea] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-7adf86] --provider infini --max-turns 30 "Health check: x-feed-to-lustro, agent-sync.sh, coaching-stats, fix-symlinks, assay, grok, cn-route, find, golem-health, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8704d4] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-39e864] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9fc4f9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-299223] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-64cb27] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ee9e95] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-01b4ec] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9a481b] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-43c773] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6adedc] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-81a4e2] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-d43d76] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-c58131] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-4a871d] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-747e7b] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-315568] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:54)
- [!] `golem [t-2aa52b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-17eff1] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b2c39d] --provider zhipu --max-turns 30 "Health check: linkedin-monitor, golem-cost, weekly-gather, tmux-osc52.sh, cytokinesis, legatum, phagocytosis.py, oura-weekly-digest.py, rheotaxis-local, skill-lint. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-754472] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a58574] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5c07d3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9fe60c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-795339] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-47144d] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f98444] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fee389] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6e9768] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2e746a] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5c9e4a] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-75cbd2] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-a4a243] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-4d0b86] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-14e4ef] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-40eef2] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:55)
- [!] `golem [t-157f7d] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-d97b48] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-a5dff7] --provider zhipu --max-turns 30 "Health check: compound-engineering-status, immunosurveillance, skill-search, test-fixer, regulatory-scan, perplexity.sh, auto-update-compound-engineering.sh, chromatin-backup.py, council, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-6deb49] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3d40d3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c01ce7] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-988716] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ebb49e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-630e29] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-227544] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-88ab73] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ff08b4] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5d4712] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8851b9] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-695a48] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-8972c4] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-18c373] --provider zhipu --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-b81fd6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3e2216] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:56)
- [!] `golem [t-e7d2c5] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-6893b5] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e9554b] --provider infini --max-turns 30 "Health check: vesicle, chromatin-backup.py, tm, test-dashboard, assay, cleanup-stuck, update-compound-engineering, council, update-coding-tools.sh, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-35688a] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-288eb6] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4d12a8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9f71ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-17b6f9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6c3b39] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4502d2] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-da804e] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1e0ed4] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e55847] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a91a15] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-e92f92] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-d5f19d] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-d1a4a8] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-be144d] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fddfb9] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:56)
- [!] `golem [t-913c9f] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-6a8deb] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-226d16] --provider zhipu --max-turns 30 "Health check: pharos-health.sh, importin, plan-exec, chemoreception.py, disk-audit, log-summary, vesicle, transduction-daily-run, lustro-analyze, consulting-card.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-37fe06] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1e495b] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-176a05] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a689fe] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-56a3ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d504ad] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2bfa88] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-35550f] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ca81d6] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-946f3b] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-32e66b] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-42fa5a] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-ad436e] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-417a17] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-54aacf] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f9eb50] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:57)
- [!] `golem [t-ca8386] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3fa996] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4ebc6f] --provider infini --max-turns 30 "Health check: skill-sync, log-summary, cibus.py, exocytosis.py, replisome, diapedesis, rg, ck, tmux-osc52.sh, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-614047] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6f9adf] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6d3bee] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e501ca] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e7141c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-52c5a2] --provider infini --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-096c23] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-26253d] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d1876d] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1b1bd8] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-45f3b8] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c72c72] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-d9c842] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-2a34fa] --provider zhipu --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-386cfd] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-2279f2] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:58)
- [!] `golem [t-4db48a] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-408190] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-64708c] --provider infini --max-turns 30 "Health check: lustro-analyze, start-chrome-debug.sh, receptor-health, paracrine, cleanup-stuck, backfill-marks, golem-cost, golem-health, dr-sync, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8021ae] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3a7c8c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-81359f] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4a7c06] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-07ed94] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5229ec] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eaf905] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5b62de] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-122a18] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7d7c47] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-dbc52f] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-028b8d] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-5c4a21] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-7bdfde] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-83b961] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e129eb] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:58)
- [!] `golem [t-55f243] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-0ea5d4] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-8c324f] --provider zhipu --max-turns 30 "Health check: diapedesis, browser, soma-activate, translocon, judge, coaching-stats, receptor-scan, generate-solutions-index.py, hkicpa, photos.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e883aa] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-15962c] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c7a35e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4836c8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5f9065] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fba5c0] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ca9b60] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e18c9d] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0d8927] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d1b0ce] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8426ea] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-12390d] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-502e6a] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-40e5bd] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d3bc5c] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d8d1d4] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:59)
- [!] `golem [t-36b268] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-eeddf2] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-384864] --provider zhipu --max-turns 30 "Health check: pharos-health.sh, chromatin-backup.py, regulatory-capture, capco-prep, rename-plists, backfill-marks, phagocytosis.py, taste-score, commensal, tmux-url-select.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a248f4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4321d6] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-476f32] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a32f37] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ab6c72] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-49ad9e] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-27637d] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-385620] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-92cdfd] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9d4d8e] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fedd1e] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e4bc59] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-a0a5da] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-253a49] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-394b4d] --provider zhipu --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1028d1] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:00)
- [!] `golem [t-aa489f] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-50aa44] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-41bcaf] --provider zhipu --max-turns 30 "Health check: council, phagocytosis.py, golem-validate, grep, rheotaxis, qmd-reindex.sh, update-coding-tools.sh, commensal, gemmation-env, start-chrome-debug.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-975731] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d885db] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-81eb72] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7197af] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6451ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-824583] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b88609] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6081a1] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-857c6e] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-411584] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d86cde] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-667cff] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-e3d623] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-3e72b4] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cf267d] --provider zhipu --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-dd251b] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:00)
- [!] `golem [t-f7bbc9] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-eb9ecc] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-5d5488] --provider infini --max-turns 30 "Health check: complement, replisome, rg, vesicle, soma-health, effector-usage, rename-plists, photos.py, update-compound-engineering, oura-weekly-digest.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-971b88] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0346ae] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b9379c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6198d4] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-738a7d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-abeebe] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2457cc] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-496f08] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b77088] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b92b3e] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-770677] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-998226] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-38bcb7] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c0ba9a] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-734a4b] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-90e765] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:01)
- [!] `golem [t-063949] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-ce2263] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1ab69a] --provider infini --max-turns 30 "Health check: tmux-url-select.sh, methylation-review, rotate-logs.py, soma-wake, rename-kindle-asins.py, plan-exec.deprecated, compound-engineering-status, search-guard, skill-search, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8d16a9] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1ef80d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c4601d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e25713] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8438ff] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8f688e] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-71756d] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-809bfd] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5d89c7] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2b82c3] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2eafed] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-e9e495] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-80a926] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-9553b8] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-73bf8d] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-03d973] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:02)
- [!] `golem [t-4a2af0] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-0cc4ba] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e51a6b] --provider volcano --max-turns 30 "Health check: plan-exec.deprecated, update-compound-engineering-skills.sh, pharos-env.sh, mismatch-repair, immunosurveillance, bud, receptor-scan, replisome, demethylase, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8db962] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ab32bd] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5e6f5d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fff6df] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d8ff95] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d858e7] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d8a20b] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d4ea46] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-61f5dd] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6bfa8b] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1c3095] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ff01c4] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-33515b] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-6fe553] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4c53c8] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e866de] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:02)
- [!] `golem [t-34f2c0] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5bd497] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-81a3d0] --provider zhipu --max-turns 30 "Health check: telophase, soma-bootstrap, log-summary, queue-stats, tmux-osc52.sh, respirometry, rheotaxis, lacuna.py, demethylase, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-3cca6b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f67234] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-280908] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f29c84] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f1be22] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-89dfb0] --provider zhipu --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b06b7d] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5adb9d] --provider volcano --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-44f0a0] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e6580e] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-faf289] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-6aab57] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-d78283] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-30a732] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-067d77] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5047d5] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:03)
- [!] `golem [t-3f89fc] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-bf3c18] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-de7757] --provider infini --max-turns 30 "Health check: golem-review, legatum-verify, auto-update-compound-engineering.sh, x-feed-to-lustro, rotate-logs.py, electroreception, golem, grok, immunosurveillance.py, golem-cost. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c44e57] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c07d94] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8b842b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-146a29] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-82dd2a] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e9e096] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d53d9b] --provider volcano --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-21dc54] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0d0d2c] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7966d2] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6f0c58] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-068a44] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-47a77c] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-9a4216] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1eff24] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a44833] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:04)
- [!] `golem [t-9b4c89] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5acadd] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-de52b8] --provider zhipu --max-turns 30 "Health check: hetzner-bootstrap.sh, coverage-map, x-feed-to-lustro, grep, test-fixer, proteostasis, cn-route, publish, inflammasome-probe, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-d9319c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-588657] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a43c92] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f986ed] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e03856] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-852e38] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-affae3] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-73ff33] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-78c444] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6c7c22] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1e1c3a] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-a6e375] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e5b366] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-a5eb4c] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fe088d] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9ce446] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:04)
- [!] `golem [t-84a0c1] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-392cf6] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1074dc] --provider zhipu --max-turns 30 "Health check: switch-layer, chromatin-backup.py, linkedin-monitor, lustro-analyze, engram, soma-scale, safe_search.py, pharos-sync.sh, plan-exec.deprecated, taste-score. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-6387d0] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d480f5] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e5445a] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b89f3d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6d4b0f] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-149703] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bcecb7] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3b3587] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6cbee1] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-defb86] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c81846] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-f929e2] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ca9590] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-8b740a] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-52ea18] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4207b1] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:05)
- [!] `golem [t-1baa02] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-103da0] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-6d78cd] --provider zhipu --max-turns 30 "Health check: dr-sync, test-dashboard, synthase, council, gemmation-env, safe_rm.py, plan-exec, pinocytosis, bud, legatum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-4bd16e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-db57a2] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-be1a8d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-dd0c3a] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-21101b] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5c63f4] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f70033] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6c5077] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8f11e7] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8a5752] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f4b75f] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-828db7] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-686724] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-00875c] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-886d6c] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-8f6ab6] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:06)
- [!] `golem [t-e31cb6] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-67ec5b] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-bf76e0] --provider zhipu --max-turns 30 "Health check: backup-due.sh, chat_history.py, golem-review, agent-sync.sh, soma-bootstrap, electroreception, photos.py, find, cytokinesis, lustro-analyze. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f210a4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-32e306] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-493fb1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cb1ad4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3f42df] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-29c9fc] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-099052] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4ad04d] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8c15f4] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b3c5b2] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-722552] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fe6e97] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-8f2b7c] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-8e4fbf] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-295229] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cc7b0a] --provider infini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:06)
- [!] `golem [t-dbd5ae] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-2ee44d] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1607e2] --provider infini --max-turns 30 "Health check: queue-balance, oura-weekly-digest.py, synthase, cibus.py, auto-update-compound-engineering.sh, tmux-workspace.py, channel, poiesis, perplexity.sh, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a6c58a] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-64c023] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3a5e3c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-44c5e5] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-94752d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0679a3] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d037a7] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b38d0c] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-48071f] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-51d9a3] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-78ea59] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-c0b6ff] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-eed2c5] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-05565e] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-14c970] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cf8ec5] --provider volcano --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:07)
- [!] `golem [t-44bb6d] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7c3884] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d147f9] --provider volcano --max-turns 30 "Health check: methylation-review, immunosurveillance, agent-sync.sh, cibus.py, chromatin-decay-report.py, golem-validate, rheotaxis, importin, launchagent-health, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1ddf54] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8c730f] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fe3db7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fe00ed] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e73616] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d11635] --provider volcano --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d649f3] --provider zhipu --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-916eb5] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b5cfe2] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-529735] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fc2dd3] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-6caa07] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-a718ab] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-c38632] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-b82455] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-257f61] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:08)
- [!] `golem [t-a1a6cb] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a7b5a3] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d1ccec] --provider volcano --max-turns 30 "Health check: coaching-stats, immunosurveillance, overnight-gather, skill-search, receptor-health, transduction-daily-run, gemmule-sync, poiesis, immunosurveillance.py, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1edb8f] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5d626e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eb8c55] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-352ebb] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7445ab] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c356d2] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2fa562] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-da3383] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-08731d] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-331819] --provider zhipu --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8e6c5c] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-b9bee2] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-9520ef] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-e27246] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-78676f] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ae8cde] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:08)
- [!] `golem [t-a1d53b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-fa7497] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-643b35] --provider volcano --max-turns 30 "Health check: engram, commensal, vesicle, express, cytokinesis, pharos-env.sh, wacli-ro, channel, search-guard, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-323fdf] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b37655] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d157cb] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-84d32e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-427b29] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1d5860] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-859842] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2562a8] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-636e4c] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9b0c8a] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a750b7] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-3b41d4] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-1f3c5e] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-680b6a] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-dfa8ec] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f1356c] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:09)
- [!] `golem [t-8ea565] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5e4b50] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-916465] --provider infini --max-turns 30 "Health check: golem-daemon-wrapper.sh, poiesis, compound-engineering-test, secrets-sync, plan-exec, methylation, queue-balance, centrosome, chat_history.py, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-0e797d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2c82f6] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-31ab03] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0b86c1] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ca32dd] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2b1bc0] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-490de5] --provider volcano --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2e1800] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-30de60] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b490a4] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c6d691] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-754ff4] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-0e0887] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3b39ee] --provider zhipu --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f55d9b] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-112119] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:10)
- [!] `golem [t-019097] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a741b7] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1fcce4] --provider zhipu --max-turns 30 "Health check: hetzner-bootstrap.sh, gemmation-env, pulse-review, capco-prep, skill-lint, lacuna, golem-top, dr-sync, skill-search, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1884b7] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-36bedc] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-20bb49] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4bb63e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f4fb07] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f9f4e8] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-af1be4] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-37c0a2] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-973364] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-aeed16] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a9a571] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-f2ad8b] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-7d11e4] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-1787f1] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7c0d18] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f46c4c] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:10)
- [!] `golem [t-68b463] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c9d58e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-cf2b3d] --provider infini --max-turns 30 "Health check: browser, cookie-sync, quorum, legatum, sortase, soma-health, search-guard, soma-scale, centrosome, golem-daemon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-590d4c] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-33fd08] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f4a332] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-500279] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9b3ff9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d6c700] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-357e18] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7baa1a] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a3df16] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b43de4] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c7fcc9] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e88edb] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-722000] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-d03c10] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ce42e7] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-05713f] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:11)
- [!] `golem [t-af8762] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e10e7b] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-2c9481] --provider infini --max-turns 30 "Health check: tmux-osc52.sh, auto-update-compound-engineering.sh, hetzner-bootstrap.sh, agent-sync.sh, safe_search.py, browser, receptor-scan, qmd-reindex.sh, quorum, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-ae996f] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c3a5d3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-33adf4] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-760406] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-94c49e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-54ba30] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-78999d] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-55c4ce] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-adda17] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-75828f] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-202eb9] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-ce270b] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-570465] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-47c413] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-21ab83] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-622bbb] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:12)
- [!] `golem [t-5c49bc] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-13028e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4c9561] --provider infini --max-turns 30 "Health check: grep, update-compound-engineering, provider-bench, test-dashboard, orphan-scan, wacli-ro, immunosurveillance.py, golem-top, effector-usage, chemoreception.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a00fe6] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3a4d10] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5097ea] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-159b15] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-35d064] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-37df34] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d69e3f] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1b7649] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-904d2a] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-540808] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b6832a] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-87248e] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-43452e] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-6c1f4f] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-aa55a9] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-22468f] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:12)
- [!] `golem [t-4104b3] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-8c6c7e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-206d34] --provider infini --max-turns 30 "Health check: log-summary, chromatin-decay-report.py, golem-top, plan-exec, agent-sync.sh, respirometry, linkedin-monitor, assay, golem-daemon, tmux-osc52.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8eebe3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e72d26] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-da5a9d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1dd7df] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-aa0007] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ca9068] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b6b0cc] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-261bf2] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d3a963] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-902f94] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2b3f02] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-11d873] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-372495] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-ead0a6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-793b49] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d3a31a] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:13)
- [!] `golem [t-7d827b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-58cec3] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-35e34d] --provider volcano --max-turns 30 "Health check: safe_rm.py, agent-sync.sh, golem, wacli-ro, browser, hkicpa, ck, gemmation-env, backup-due.sh, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-d00273] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eb509e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fca7e5] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-778e01] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-082cac] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-885c20] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-59d004] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e2a656] --provider infini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a15b32] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-155ce5] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-82997c] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-5605ab] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-0d0543] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-4c3a9f] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3518bc] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-63dc9e] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:15)
- [!] `golem [t-2dd235] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-665a97] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-dd1098] --provider volcano --max-turns 30 "Health check: commensal, search-guard, plan-exec.deprecated, express, pulse-review, lacuna, weekly-gather, rheotaxis, compound-engineering-test, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1f1f8d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d0b6a0] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e5b2cd] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7f3f53] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a24927] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f2f5a2] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9a90b9] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bc585a] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ebb6f7] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-df6934] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-54ae78] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-8ee61e] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-d8d3c8] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-58f871] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a89db9] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-bd9bf6] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:15)
- [!] `golem [t-f957b1] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-d9bab7] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-06baeb] --provider volcano --max-turns 30 "Health check: auto-update-compound-engineering.sh, tm, overnight-gather, immunosurveillance.py, compound-engineering-test, cg, grep, golem-reviewer, gemmule-sync, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-5c5a57] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-309a00] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/schema.py. Mock external calls. Write assays/test_respirometry_schema.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-670286] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2948ab] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-91a210] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8803ad] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4942ae] --provider zhipu --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-39b4f8] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-40aa4c] --provider volcano --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-08527f] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2cd1c8] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-8b3e73] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-fe5985] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-8df52f] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-db4757] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-bc2c81] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:16)
- [!] `golem [t-0e1d29] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-149820] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-ba1bb9] --provider infini --max-turns 30 "Health check: soma-clean, browse, golem-health, lacuna.py, find, auto-update-compound-engineering.sh, gap_junction_sync, git-activity, diapedesis, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e4808d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d3dbf1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-683c53] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2fc1ee] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2c09b5] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-85cb25] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-925f6a] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2a6db4] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-06bc0a] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eeee32] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-297294] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-743b25] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-ce70e4] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-099897] --provider zhipu --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-42b397] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0928db] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:17)
- [!] `golem [t-3cc090] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-fffe3a] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b35811] --provider zhipu --max-turns 30 "Health check: golem-health, update-compound-engineering-skills.sh, pharos-env.sh, tmux-osc52.sh, fix-symlinks, chemoreception.py, log-summary, golem, rotate-logs.py, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8b6fbd] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fd089d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-84e01e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-87deb2] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d224d3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d68abb] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-914247] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-194d30] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b1ad3a] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8d2d84] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-feae3a] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-9a36e0] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-541637] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fb536d] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f8a685] --provider zhipu --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-227f83] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:17)
- [!] `golem [t-f21cad] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-fb3461] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e1a299] --provider infini --max-turns 30 "Health check: efferens, tmux-url-select.sh, quorum, golem-review, paracrine, hkicpa, test-fixer, gemmule-sync, test-dashboard, auto-update-compound-engineering.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b4e550] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-649265] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9d3142] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-57050f] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3029d7] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0ca696] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a922d5] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3cc66c] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-831ca6] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-51266f] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-79d041] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-98f96e] --provider infini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-c568ad] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-5124c6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-eca29c] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-b53b49] --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:18)
- [!] `golem [t-774fa9] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-b1fb0b] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-22290c] --provider zhipu --max-turns 30 "Health check: backup-due.sh, cleanup-stuck, test-spec-gen, compound-engineering-test, bud, qmd-reindex.sh, synthase, skill-search, golem-reviewer, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-7a549d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4df0d8] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e97ba0] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4259ac] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ec9393] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3e9170] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2b5ef7] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e7d045] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-de147b] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-33e660] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d710fb] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-5a9956] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-d359ce] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-8bbd2d] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-6c22c0] --provider zhipu --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7bee36] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:19)
- [!] `golem [t-340c30] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-ee2527] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-dd2e74] --provider volcano --max-turns 30 "Health check: perplexity.sh, hetzner-bootstrap.sh, golem-review, find, linkedin-monitor, coverage-map, soma-pull, queue-stats, auto-update-compound-engineering.sh, electroreception. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-5e1057] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a9af3b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-84f5be] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4e3542] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4c64d0] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a472ae] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6e9d6e] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-57b822] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-681b8b] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ba662f] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bd6ac1] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-df6da7] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e4d02f] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-c756fd] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-17968a] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab8052] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:19)
- [!] `golem [t-10b7b4] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-acee61] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-016313] --provider infini --max-turns 30 "Health check: soma-snapshot, poiesis, rename-plists, grok, qmd-reindex.sh, immunosurveillance, coverage-map, chromatin-decay-report.py, consulting-card.py, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-fc6a5e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/preflight.py. Mock external calls. Write assays/test_metabolism_preflight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3bd7cc] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-183ff0] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8d2f0e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py. Mock external calls. Write assays/test_organelles_phenotype_translate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-765d13] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-512c8a] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c63f77] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-918f3e] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f1baf4] --provider infini --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-75d194] --provider volcano --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1bf6a4] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-359de6] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-f9659e] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-beb440] --provider zhipu --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-c15ff4] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5860de] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:20)
- [!] `golem [t-fa02d3] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-4000ff] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-bdcbf3] --provider volcano --max-turns 30 "Health check: provider-bench, respirometry, quorum, golem-top, complement, bud, update-coding-tools.sh, rheotaxis, rg, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-3982a2] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f70254] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-126fcf] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7c80e1] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e26b7c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-da6f4b] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-dde67f] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-989a84] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-dfb851] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-961d87] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-51db76] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-333eb9] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-84ab26] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-d826f8] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ffddf7] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab3085] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:21)
- [!] `golem [t-33027c] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7b1151] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-0345d9] --provider volcano --max-turns 30 "Health check: search-guard, cookie-sync, compound-engineering-status, compound-engineering-test, tm, cn-route, chromatin-backup.py, respirometry, tmux-workspace.py, golem-reviewer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-0a4a3d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-47b79e] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ebd0b7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sporulation.py. Mock external calls. Write assays/test_enzymes_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-59b836] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5a4c51] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-879ebd] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-94659c] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5dec9d] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-18c632] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b96025] --provider zhipu --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e69f95] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-bd3e5e] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-0f6745] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-da3220] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f2e2e1] --provider volcano --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-350b88] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:22)
- [!] `golem [t-dc9c1e] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a534bd] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-864ac9] --provider volcano --max-turns 30 "Health check: importin, dr-sync, overnight-gather, weekly-gather, electroreception, efferens, methylation, soma-wake, test-dashboard, switch-layer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-27a2c8] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/statolith.py. Mock external calls. Write assays/test_organelles_statolith.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-aa4a91] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bfd810] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/proteome.py. Mock external calls. Write assays/test_resources_proteome.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-812b7b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-106881] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f70ab9] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a816d7] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-14686b] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bbbf1a] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a0cf48] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-72861a] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-d65619] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-763247] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-b89e76] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-8d8f60] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cde7c4] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:23)
- [!] `golem [t-92b3f5] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-323155] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e66fb1] --provider volcano --max-turns 30 "Health check: hkicpa, soma-snapshot, rheotaxis-local, start-chrome-debug.sh, engram, git-activity, launchagent-health, grok, golem-dash, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-719137] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-49838c] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-430236] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3bb586] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/pathways/overnight.py. Mock external calls. Write assays/test_pathways_overnight.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-aec143] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f363f4] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4bf408] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8a7b2c] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-44dcb9] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fc546c] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-bb63bb] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-332c19] --provider volcano --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-5d32bc] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c463d0] --provider infini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3f69e8] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a79729] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:23)
- [!] `golem [t-439068] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-70065a] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-55d57f] --provider volcano --max-turns 30 "Health check: switch-layer, proteostasis, chat_history.py, soma-activate, auto-update-compound-engineering.sh, orphan-scan, soma-pull, complement, rename-kindle-asins.py, dr-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-34a68b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/mismatch_repair.py. Mock external calls. Write assays/test_metabolism_mismatch_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-300f22] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-133a4d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0be730] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cdd54d] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-823d74] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-980d5f] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-5b4679] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ecbfc1] --provider volcano --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6b3b2a] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-642720] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-d6819a] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-5541da] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-55d31f] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-06d75c] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d9ec29] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:24)
- [!] `golem [t-bc2a5a] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7bf3ee] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d69057] --provider infini --max-turns 30 "Health check: lustro-analyze, golem-daemon, rotate-logs.py, skill-search, receptor-scan, translocon, capco-prep, qmd-reindex.sh, conftest-gen, weekly-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-4eba8d] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-64a2e3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-2e9484] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c96c00] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a956d9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-d4df10] --provider infini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b0c29f] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e3ea6f] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ca86d3] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-eba13b] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e702ce] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-3c10cf] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-7bebf3] --provider volcano --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-fd6c8c] --provider zhipu --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5ac279] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-db2b95] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:25)
- [!] `golem [t-ab2b52] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e59e32] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1356d1] --provider volcano --max-turns 30 "Health check: update-compound-engineering, cytokinesis, tmux-url-select.sh, electroreception, cibus.py, golem, regulatory-scan, respirometry, gemmule-sync, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-3eef0e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9d9964] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-7e1bba] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-82078d] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ac610a] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-40b632] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-544662] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-52bd35] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4d0802] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-de2d6a] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b64247] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-81d628] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-0c63b7] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-471797] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5859b1] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-923acd] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:25)
- [!] `golem [t-29b603] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-694294] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-05dad3] --provider volcano --max-turns 30 "Health check: golem-cost, test-fixer, demethylase, oura-weekly-digest.py, skill-search, git-activity, perplexity.sh, council, rheotaxis-local, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-5f22e9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b40c99] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/complement.py. Mock external calls. Write assays/test_organelles_complement.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e395ef] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a3c838] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-80eeca] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-282f66] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c89501] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9f8d44] --provider infini --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-13c5be] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-af6b48] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a7b721] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-383cec] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-0d1033] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-15a704] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7ea3a7] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a7e2f0] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:26)
- [!] `golem [t-fa1e81] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-b5bbbc] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-721b12] --provider zhipu --max-turns 30 "Health check: ck, efferens, lustro-analyze, cookie-sync, oura-weekly-digest.py, demethylase, weekly-gather, secrets-sync, oci-arm-retry, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-cb05fc] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a82fe7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cdad56] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-fdfe49] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/oscillators.py. Mock external calls. Write assays/test_resources_oscillators.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-4aca5a] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1ada59] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-be0e3e] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-260695] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-139003] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c2139c] --provider infini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ed4273] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-d078a0] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-b4cbd1] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-1e4c68] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-eefe35] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-191c39] --provider infini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:27)
- [ ] `golem [t-a02873] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-afbf28] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-011b94] --provider volcano --max-turns 30 "Health check: queue-stats, find, linkedin-monitor, pharos-env.sh, tmux-url-select.sh, nightly, poiesis, soma-clean, golem-top, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-7304f3] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py. Mock external calls. Write assays/test_enzymes_kinesin.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-cdfffd] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/repair.py. Mock external calls. Write assays/test_metabolism_repair.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-cb1d84] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-5b2380] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/histone.py. Mock external calls. Write assays/test_enzymes_histone.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-6c6380] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-81684d] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-ae51e0] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-5209b7] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-d90b83] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-ba4d92] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-94223a] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-d6a6c7] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-49b62e] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [ ] `golem [t-899813] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-bab3a7] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-6819e5] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:27)
- [ ] `golem [t-916177] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-efaf80] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-3f1eff] --provider volcano --max-turns 30 "Health check: lacuna.py, fix-symlinks, inflammasome-probe, secrets-sync, grok, queue-balance, vesicle, mitosis-checkpoint.py, pharos-env.sh, backfill-marks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-4062f9] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-b37671] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-797032] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/crispr.py. Mock external calls. Write assays/test_organelles_crispr.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-980063] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-810bba] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-93e7a0] --provider volcano --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-86fae9] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-83a43d] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-add2dd] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-e5bdd5] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-4e00ad] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-d584a5] --provider volcano --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-fa0ded] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [ ] `golem [t-823ef1] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-0f42ce] --provider volcano --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-45d201] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:28)
- [ ] `golem [t-162c57] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-888445] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-95e921] --provider volcano --max-turns 30 "Health check: grok, switch-layer, ck, orphan-scan, golem-top, coverage-map, soma-snapshot, cn-route, replisome, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-938958] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/chromatin_stats.py. Mock external calls. Write assays/test_resources_chromatin_stats.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-e54436] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/golgi.py. Mock external calls. Write assays/test_organelles_golgi.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-699b26] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-cac86c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/ingestion.py. Mock external calls. Write assays/test_enzymes_ingestion.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-bf4f3b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-9bb1ef] --provider volcano --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-0116ad] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-fcaab2] --provider infini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-45b4b6] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-9ac051] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-f3eafd] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-1ca3c1] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-36af34] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-e02501] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-02201b] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-5ce644] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`
## Done (2026-03-31)


### Build — circadian-aware auto-requeue

- [x] `golem [t-313701] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Find the auto_requeue function. Enhance it to be circadian-aware: (1) Read ~/germline/loci/priorities.md for current north stars and deadlines. (2) Check current hour (HKT). (3) Night (22-06): weight toward tests 50%, hardening 30%, consulting 20%. (4) Morning (06-09): weight toward consulting IP 50%, digests 30%, fixes 20%. (5) Daytime (09-22): weight toward fixes 40%, features 30%, consulting 30%. (6) If priorities.md mentions a deadline within 3 days: boost that category to 60%. Write the priority logic as a separate function circadian_priorities() -> dict[str, float]. Write tests. Run uv run pytest. Commit."`

- [!] `golem [t-35fcf3] --provider infini --max-turns 30 "Create ~/germline/loci/priorities.md with this structure: north_stars (3 items with deadline), current_focus (what to prioritize now), blocked (what to skip). Initial content: (1) Capco readiness — deadline Apr 8 — consulting IP, regulatory briefs, case studies (2) Organism robustness — ongoing — fix tests, effector health (3) Consulting arsenal — ongoing — frameworks, templates. CC will update this file each session."`


### Build — wire circulation into golem-daemon

- [x] `golem [t-0263fc] --provider zhipu --max-turns 50 "Read metabolon/organelles/circulation.py (535 lines). Read effectors/golem-daemon auto_requeue function. Design integration: (1) Create effectors/circulate-dispatch as Python. It runs circulation.select_goals() to get intelligent goal list, then converts each goal into a golem queue entry in loci/golem-queue.md. Uses symbiont.transduce_safe() for CC-powered goal selection (reads Tonus.md + priorities.md + calendar). Writes queue entries. Usage: circulate-dispatch [--max-goals 8]. (2) Wire this into golem-daemon auto_requeue: when queue < 50, call circulate-dispatch instead of random task generation. Write tests. Run uv run pytest. Commit."`

- [!] `golem [t-0ed7c8] --provider infini --max-turns 40 "Read metabolon/organelles/circulation.py. Extract the evaluate() and compound() functions into a standalone effectors/circulate-evaluate as Python. After golem tasks complete, this reads results and: (1) updates coaching notes if new failure patterns found, (2) updates priorities.md if goals were completed, (3) writes a cycle report. Called by golem-reviewer periodically. Write tests. Run uv run pytest. Commit." (retry)`


### High-priority — infra + task IDs (queued by CC)

#### Add task IDs to golem-daemon
- [!] `golem [t-19855e] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Add unique task IDs: 1) In parse_queue(), generate a short ID (t-xxxx, 6 hex chars) for each task that doesn't have one — prepend it inside the backtick like 'golem [t-a7f3] --provider ...'. 2) In run_golem(), extract the ID and pass it as env var GOLEM_TASK_ID. 3) In the JSONL output, add a 'task_id' field. 4) In mark_done/mark_failed, include the task ID in the result annotation. 5) In cmd_status, show task IDs of running tasks. Write tests in assays/test_golem_task_ids.py. Run uv run pytest on the test file. Commit." (retry)`

#### Fix all from __future__ duplicate bugs
- [x] `golem --provider zhipu --max-turns 30 "Find ALL Python files under /home/terry/germline/ and /home/terry/.claude/hooks/ that have 'from __future__ import annotations' appearing more than once. For each file, remove the SECOND occurrence (keep only the first at the top). Verify with py_compile. Commit."`

#### Fix collection errors blocking test suite
- [x] `golem --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common causes: hardcoded /Users/terry paths, bad imports, duplicate from __future__, missing modules. Run --co again until 0 errors. Commit."`

#### Fix top 10 failing tests
- [!] `golem --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -10. For each of the top 10 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Consulting IP — Capco prep (T-7)

#### AI risk management consulting cards
- [x] `golem --provider infini --max-turns 50 "Create 5 consulting insight cards for a management consultant joining Capco (financial services consulting). Topics: 1) AI model risk management in banking 2) LLM deployment regulatory expectations 3) AI vendor due diligence for banks 4) GenAI policy template for bank employees 5) AI incident response for financial services. Each card: 300+ words, problem statement, approach, key considerations, regulatory references. Write each to ~/epigenome/chromatin/euchromatin/consulting/cards/<slug>.md. Commit."`

#### HK regulatory landscape briefing
- [!] `golem [t-211b2c] --provider zhipu --max-turns 40 "Write a comprehensive briefing on Hong Kong financial regulation for AI/technology: HKMA, SFC, IA key circulars and expectations around AI adoption in banking, insurance, securities. Include HKMA's Supervisory Policy Manual modules on technology risk (TM-E-1, OR-1). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hk-ai-regulatory-landscape.md. 500+ words. Commit." (retry)`

### System hardening

#### Add periodic rsync from Mac to gemmule
- [x] `golem [t-0f22c4] --provider zhipu --max-turns 30 "Create effectors/gemmule-sync as a Python script. It should: 1) rsync terry@100.94.27.93:~/epigenome/chromatin/ ~/epigenome/chromatin/ 2) rsync terry@100.94.27.93:~/notes/ ~/notes/ 3) rsync terry@100.94.27.93:~/code/acta/ ~/code/acta/ 4) Log results to ~/.local/share/vivesca/gemmule-sync.log. Add --dry-run flag. Make it idempotent. Write tests. Commit."`

#### Scan and fix hardcoded macOS paths
- [!] `golem --provider volcano --max-turns 30 "Find ALL files in ~/germline/ containing /Users/terry. Replace with Path.home() (Python) or $HOME (shell). Verify nothing breaks. Commit." (retry)`

### Research — workflow orchestration for golem-daemon

#### Landscape: Temporal vs alternatives for AI task orchestration
- [x] `golem --provider zhipu --max-turns 50 "Research workflow orchestration systems for replacing a custom Python task queue daemon that dispatches AI coding agents (Claude Code). Current system: markdown-file queue, 30 concurrent workers across 3 providers, retry logic, auto-commit. Requirements: task IDs, visibility/UI, durable execution, heartbeating, concurrency control, Python SDK. Compare: 1) Temporal.io — self-hosted vs Cloud, Python SDK maturity, resource footprint 2) Hatchet — AI-native, lighter weight 3) Inngest — serverless model 4) Prefect/Dagster — data pipeline focused but flexible 5) BullMQ/Celery — simpler task queues 6) Plain PostgreSQL+LISTEN/NOTIFY — minimal infra. For each: install complexity, resource overhead (RAM/CPU), cost (self-hosted vs cloud), Python SDK quality, UI/visibility, suitability for 20-50 concurrent AI agent tasks. Also note: the user is a consultant at Capco (financial services) — which systems have enterprise/banking adoption? Write findings to ~/epigenome/chromatin/euchromatin/consulting/cards/workflow-orchestration-landscape.md. 500+ words with recommendation. Commit."`

### Resilience — vivesca self-healing and hardening

#### Daemon auto-restart via supervisor
- [!] `golem [t-fd4826] --provider zhipu --max-turns 30 "Read the supervisor config for golem-daemon. If none exists, check /etc/supervisor/conf.d/. Create or fix a supervisor config at /etc/supervisor/conf.d/golem-daemon.conf that: 1) runs 'python3 /home/terry/germline/effectors/golem-daemon start --foreground' as user terry 2) auto-restarts on crash 3) sets environment from /home/terry/.env.fly (source it in a wrapper script if needed) 4) logs stdout/stderr to /home/terry/.local/share/vivesca/. Write tests. Commit." (retry)`

#### Git auto-backup — push epigenome to remote
- [x] `golem [t-e72448] --provider infini --max-turns 40 "The epigenome repo at ~/epigenome has 15K+ chromatin files that are NOT tracked in git. This caused data loss during a disk-full incident. Fix: 1) cd ~/epigenome && git add chromatin/ 2) Check .gitignore doesn't exclude chromatin 3) git commit -m 'backup: track all chromatin files' 4) git push. If push fails due to size, set up git-lfs for large files. Also add a .gitattributes for *.md files if > 1MB. Commit."`

#### Provider failover in golem
- [x] `golem [t-31363b] --provider zhipu --max-turns 40 "Read effectors/golem (the golem script, not golem-daemon). Add provider failover: if the primary provider returns HTTP 429 (rate limit) or 5xx, automatically retry with the next provider in priority order (zhipu -> infini -> volcano). Add a --fallback flag to opt-in. Log the failover. Write tests in assays/test_golem_failover.py. Commit." (retry)`

#### Watchdog — detect and fix stuck golems
- [!] `golem [t-cb5765] --provider infini --max-turns 40 "Read effectors/golem-daemon. Add a watchdog: every 5 poll cycles, check if any running golem has exceeded GOLEM_TIMEOUT (1800s). If so: 1) kill the subprocess 2) mark task as failed with 'timeout' 3) log a warning. Currently the ThreadPoolExecutor handles timeouts but subprocess.run may hang. Add subprocess-level kill via os.kill(). Write tests. Commit."`

#### Graceful shutdown — commit before dying
- [x] `golem [t-ad7830] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Improve the SIGTERM handler: on shutdown signal, 1) stop accepting new tasks 2) wait up to 60s for running golems to finish 3) auto-commit any uncommitted work 4) push to remote 5) then exit. Currently it just removes the pidfile. Write tests. Commit."`

#### Config validation on daemon start
- [x] `golem [t-fc42d9] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a validate_config() function that runs on startup and checks: 1) QUEUE_FILE exists and is readable 2) all providers in PROVIDER_LIMITS have valid API keys in env 3) git repo is clean enough to commit 4) disk space > 2GB 5) uv sync is up to date (uv run python -c 'import metabolon'). If any check fails, log a clear error and exit 1. Write tests. Commit."`

#### Self-healing — auto-fix common breakages
- [!] `golem [t-9eecea] --provider infini --max-turns 50 "Create effectors/mismatch-repair as a Python script (biology: mismatch repair fixes DNA errors). It should detect and fix common vivesca breakages: 1) Duplicate 'from __future__ import annotations' in any .py file under ~/germline/ or ~/.claude/hooks/ — remove the second occurrence 2) Hardcoded /Users/terry paths — replace with Path.home() 3) Broken symlinks in ~/ — report them 4) Stale .pyc files — delete 5) pytest collection errors — run --co and report. Add --fix flag to auto-repair vs --check for dry-run. Write tests in assays/test_mismatch_repair.py. Commit."`

#### Network resilience — retry git operations
- [!] `golem [t-9dffa6] --provider volcano --max-turns 30 "Read effectors/golem-daemon, specifically auto_commit(). Add retry logic: if git push fails (network error), retry 3 times with 30s backoff. If all retries fail, log error but don't crash daemon. Also add: if git pull fails at startup, continue with local state rather than crashing. Write tests. Commit." (retry)`

#### Backup marks/memory to git
- [!] `golem [t-a6dcae] --provider zhipu --max-turns 30 "The epigenome/marks directory contains critical behavioral memory files. Ensure they are tracked in git: cd ~/epigenome && git add marks/ && git status. If there are untracked marks, commit them. Also create a pre-push hook or effector that validates all marks have valid YAML frontmatter. Write tests. Commit."`

### Temporal migration — Phase 1

#### Scaffold Temporal-based golem orchestrator
- [!] `golem [t-c500c0] --provider zhipu --max-turns 50 "Build a Temporal.io-based orchestrator to replace the golem-daemon markdown queue. Phase 1 — scaffold only. 1) Create effectors/temporal-golem/ directory 2) Add pyproject.toml with temporalio SDK dependency 3) Create worker.py — a Temporal worker that polls a 'golem-tasks' task queue and executes golem commands as activities. Each activity: runs 'bash effectors/golem --provider X task', heartbeats every 30s, has 30min timeout, retry policy (3 attempts, backoff). 4) Create workflow.py — a GolemDispatchWorkflow that accepts a list of tasks, dispatches them respecting per-provider concurrency (zhipu:8, infini:8, volcano:16), and reports results. 5) Create cli.py — CLI to submit workflows: 'temporal-golem submit --provider zhipu --task ...' and 'temporal-golem status'. 6) Create docker-compose.yml for Temporal server + PostgreSQL + Web UI. 7) Write a README.md explaining the setup. 8) Write tests in assays/test_temporal_golem.py (mock the Temporal client). Commit everything." (retry)`

#### Docker compose for Temporal server
- [!] `golem [t-74f0cc] --provider infini --max-turns 30 "Create effectors/temporal-golem/docker-compose.yml for running Temporal locally. Include: 1) temporal-server (temporalio/server:latest) 2) PostgreSQL 15 for persistence 3) temporal-web (temporalio/web:latest) on port 8080 4) temporal-admin-tools for CLI access. Use environment variables for config. Add a startup script effectors/temporal-golem/start.sh that does 'docker compose up -d' and waits for health check. Write to effectors/temporal-golem/. Commit." (retry)`

### Provider troubleshooting

#### Diagnose and fix Volcano provider failures
- [!] `golem [t-f8bcd2] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Volcano provider (ark-code-latest) is returning exit=2 with 0s duration — the golem process fails before starting. Debug: 1) Check how volcano auth works (VOLCANO_API_KEY vs ANTHROPIC_AUTH_TOKEN) 2) Test the volcano endpoint directly with curl: curl -s https://ark.cn-beijing.volces.com/api/v3/chat/completions -H 'Authorization: Bearer $VOLCANO_API_KEY' 3) Check if the Claude Code --provider flag accepts volcano's URL format 4) Read recent daemon logs for volcano error messages. If the issue is auth token format, fix it in the golem script. If it's rate limiting, add exponential backoff. Write findings and fix to effectors/golem. Write tests. Commit." (retry)`

#### Diagnose and fix Infini provider failures  
- [!] `golem [t-f1adb3] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Infini provider (deepseek-v3.2 at cloud.infini-ai.com) has intermittent exit=2 failures with 0s duration. Debug: 1) Check INFINI_API_KEY is correctly formatted 2) Test the endpoint directly: curl -s https://cloud.infini-ai.com/maas/coding/v1/chat/completions -H 'Authorization: Bearer $INFINI_API_KEY' -H 'Content-Type: application/json' -d '{\"model\":\"deepseek-v3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}' 3) Check if rate limiting or quota exhaustion is the cause 4) Read daemon logs for infini-specific error patterns. If rate limited, implement per-provider cooldown in golem-daemon. Write findings and fix. Commit." (retry)`

### Hatchet features — wire up advanced capabilities

#### Rate limits — per-provider server-side throttling
- [!] `golem [t-595036] --provider zhipu --max-turns 50 "Read effectors/hatchet-golem/worker.py. Add Hatchet server-side rate limits for each provider. Use h.rate_limits.put() to create rate limit keys: 'zhipu-rpm' (1000 req/5hr = 200/hr), 'infini-rpm' (1000 req/5hr = 200/hr), 'volcano-rpm' (1000 req/5hr = 200/hr), 'gemini-rpm' (60/min). Then add rate_limits=[RateLimit(key='<provider>-rpm', units=1)] to each @hatchet.task decorator. This replaces the manual cooldown in golem-daemon. Write tests in assays/test_hatchet_rate_limits.py. Commit." (retry)`

#### Cron — scheduled auto-requeue and health checks
- [x] `golem [t-242f4d] --provider zhipu --max-turns 50 "Read effectors/hatchet-golem/worker.py and effectors/hatchet-golem/dispatch.py. Add two cron-triggered Hatchet tasks: 1) @hatchet.task with on_crons=['*/30 * * * *'] named 'golem-requeue' that checks if golem-queue.md has < 20 pending tasks and auto-generates new ones (port the auto_requeue logic from effectors/golem-daemon). 2) @hatchet.task with on_crons=['*/15 * * * *'] named 'golem-health' that runs effectors/gemmule-health --daemon and logs the result. Register both in the worker. Write tests. Commit."`

#### Metrics — task stats and Prometheus endpoint
- [!] `golem [t-2e6bc8] --provider zhipu --max-turns 40 "Read the Hatchet SDK metrics API. Create effectors/hatchet-golem/stats.py that: 1) Calls h.metrics.get_task_metrics() and h.metrics.get_queue_metrics() 2) Prints a summary: tasks completed/failed/pending per provider, avg duration, queue depth 3) Optionally outputs as JSON (--json flag) 4) Add a 'golem-metrics' @hatchet.task with on_crons=['0 * * * *'] that logs hourly stats to ~/.local/share/vivesca/hatchet-metrics.jsonl. Write tests. Commit."`

#### Event-driven dispatch — git push triggers task pickup
- [x] `golem [t-5f4e68] --provider zhipu --max-turns 40 "Read effectors/hatchet-golem/dispatch.py. Add an event-driven mode: create a @hatchet.task named 'golem-queue-changed' triggered by on_events=['queue:updated']. When triggered, it reads golem-queue.md and dispatches any new pending tasks. Then create a git post-commit hook at ~/germline/.git/hooks/post-commit that calls 'python3 -c \"from hatchet_sdk import Hatchet; h=Hatchet(); h.event.push('queue:updated', {})\"' when golem-queue.md changes. This replaces polling with event-driven dispatch. Write tests. Commit."`

#### Durable tasks — survive worker restarts
- [x] `golem [t-d274eb] --provider zhipu --max-turns 40 "Read the Hatchet SDK durable_task API. Convert the golem-zhipu task in effectors/hatchet-golem/worker.py to use @hatchet.durable_task instead of @hatchet.task. This means if the worker restarts mid-task, Hatchet will resume from the last checkpoint. Add context.save_state() calls before and after the subprocess.run. Write tests showing checkpoint/resume behavior. Commit."`

#### Logs — centralized task logging
- [x] `golem [t-8b0c43] --provider zhipu --max-turns 30 "Read the Hatchet SDK logs API. In effectors/hatchet-golem/worker.py, add context.log() calls inside _run_golem: log the command being run, the exit code, and a snippet of stdout/stderr. Then create effectors/hatchet-golem/logs.py that queries h.logs.list() to show recent task logs with filtering by provider and status. Add --tail flag for live following. Write tests. Commit."`

---

### Python rewrites of Rust CLIs (eliminate cargo from Docker build)

All tools: single Python file at ~/bin/<name>, #!/usr/bin/env python3, use requests or urllib, argparse with subcommands matching the Rust CLI exactly. chmod +x after creation. Test each command. Use env vars for API keys (no hardcoded secrets).

#### Tier 1 — daily use

- [x] `golem [t-110132] --provider zhipu --max-turns 30 "Build ~/bin/noesis as a Python CLI wrapping the Perplexity API. Env: PERPLEXITY_API_KEY. Subcommands: search (sonar, ~0.006), ask (sonar-pro, ~0.01), research (sonar-deep-research, ~0.40), reason (sonar-reasoning-pro, ~0.01), log (show usage from ~/.local/share/noesis/log.jsonl). Flags: --raw (print raw JSON), --no-log (skip logging). POST to https://api.perplexity.ai/chat/completions. Log each query as JSONL with timestamp, model, cost estimate, query. Print extracted text answer + numbered source URLs. Test with: noesis search 'what is the weather in Hong Kong'. chmod +x ~/bin/noesis."`

- [x] `golem [t-7264a7] --provider zhipu --max-turns 30 "Build ~/bin/caelum as a Python CLI. Fetches HK Observatory weather from https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=en (current forecast) and https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en (current temp/humidity). No args needed — just run 'caelum' and print one line: temp range, condition summary. Use urllib.request (no deps). Test it. chmod +x."`

- [x] `golem [t-ba1380] --provider zhipu --max-turns 30 "Build ~/bin/consilium as a Python CLI for multi-model deliberation. Env: uses ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY. Takes a question as positional arg. Modes: --quick (parallel query to 3+ models, print each answer), --council (blind answers -> debate -> judge synthesizes), --redteam (adversarial stress test). Use requests to call each API. Models: Claude via Anthropic API, GPT-4o via OpenAI API, Gemini via Google AI API. Print each model's response labeled. Default mode: --quick. Test with: consilium --quick 'what is 2+2'. chmod +x."`

- [!] `golem [t-816e83] --provider zhipu --max-turns 30 "Build ~/bin/stips as a Python CLI for OpenRouter credits. Env: OPENROUTER_API_KEY. Subcommands: credits (GET https://openrouter.ai/api/v1/auth/key — print balance), usage (GET https://openrouter.ai/api/v1/activity — print recent usage), key (print masked key). Use requests. Test with: stips credits. chmod +x."`

#### Tier 2 — weekly use

- [!] `golem [t-0a3b79] --provider zhipu --max-turns 30 "Build ~/bin/fasti as a Python CLI wrapping Google Calendar API. Env: GOOGLE_API_KEY. Subcommands: list [date] (list events for a date, default today), move <event-id> <new-datetime>, delete <event-id>. Use the Google Calendar REST API with API key auth. For OAuth operations that need write access, use a service account or stored refresh token at ~/.config/fasti/credentials.json. Print events as: time | title | location. Test with: fasti list. chmod +x."`

- [x] `golem [t-2895d5] --provider zhipu --max-turns 30 "Build ~/bin/grapho as a Python CLI for managing MEMORY.md. The file is at ~/epigenome/marks/MEMORY.md (or ~/.claude/projects/-home-terry/memory/MEMORY.md via symlink). Subcommands: status (show line count, budget usage — budget is 60 lines), add (interactive: prompt for title, file, description — append entry to MEMORY.md and create the memory file), demote <title> (move entry from MEMORY.md to ~/epigenome/chromatin/immunity/memory-overflow.md), promote <title> (reverse), review (list overflow entries), solution <name> (scaffold ~/docs/solutions/<name>.md). Flags: --format human|json. Test with: grapho status. chmod +x."`

- [x] `golem [t-267c1c] --provider zhipu --max-turns 30 "Build ~/bin/pondus as a Python CLI for AI model benchmark aggregation. Subcommands: rank (fetch and merge rankings from multiple benchmark sources — Chatbot Arena at https://lmarena.ai, LiveBench, MMLU — print sorted table), check <model> (show one model across sources), compare <modelA> <modelB> (head-to-head), sources (list all sources and cache status), refresh (clear cache at ~/.cache/pondus/), recommend <task-type> (suggest models for coding/reasoning/creative). Cache results for 24h in ~/.cache/pondus/. Flags: --format json|table|markdown. Use requests + simple HTML parsing. Test with: pondus sources. chmod +x."`

- [!] `golem [t-b1e7c2] --provider zhipu --max-turns 30 "Build ~/bin/sarcio as a Python CLI for managing a digital garden. Posts live at ~/notes/Writing/Blog/Published/. Subcommands: new <title> (create a new draft .md file with frontmatter: title, date, tags, status=draft), list (list all posts with status), publish <filename> (set status=published in frontmatter, add published_date), revise <filename> (open in EDITOR), open <filename> (open in EDITOR), index (regenerate index.md listing all published posts). Use pathlib and yaml (PyYAML or frontmatter parsing). Test with: sarcio list. chmod +x."`

#### Tier 3 — specialized

- [x] `golem [t-dbfdc1] --provider zhipu --max-turns 30 "Build ~/bin/keryx as a Python CLI wrapping wacli (WhatsApp CLI at ~/germline/effectors/wacli-ro). Subcommands: read <name> [--n N] (resolve contact name to JID, call wacli-ro read, merge dual-JID conversations), send <name> <message> [--execute] (print or execute wacli send command), chats [--n N] (list recent chats via wacli-ro chats), sync start|stop|status (manage wacli sync daemon). Contact resolution: maintain ~/.config/keryx/contacts.json mapping names to JIDs. Use subprocess to call wacli-ro. Test with: keryx chats. chmod +x."`

- [!] `golem [t-6e540c] --provider zhipu --max-turns 30 "Build ~/bin/moneo as a Python CLI for Due app reminders. Due stores data in ~/Library/Group Containers/ on Mac but on Linux we use a synced JSON file at ~/.config/moneo/reminders.json. Subcommands: ls (list all reminders sorted by date), add <title> --date <datetime> [--repeat <interval>] (add reminder), rm <title> (delete by title match), edit <index> --title/--date (edit fields), log (show completion history from ~/.config/moneo/completions.jsonl). Print reminders as: date | title | repeat. Test with: moneo ls (should show empty or create sample data). chmod +x."`

- [x] `golem [t-d54f38] --provider zhipu --max-turns 30 "Build ~/bin/anam as a Python CLI for searching AI chat history. Scans ~/.claude/projects/ for session JSONL files. Subcommands: (default) [date] (scan sessions for a date — default today — show prompts with timestamps), search <pattern> (grep across all session files for a regex pattern). Flags: --full (show all, not just last 50), --json (output as JSON), --tool claude|codex|opencode (filter by tool). Use glob + json. Test with: anam today. chmod +x."`

- [x] `golem [t-e53737] --provider zhipu --max-turns 30 "Build ~/bin/auceps as a Python CLI wrapping the bird CLI (X/Twitter). Subcommands: (default) <input> (auto-route: if URL -> fetch tweet, if @handle -> fetch timeline, else -> search), thread <url> (follow quote-tweet chains), bird <args> (passthrough to bird CLI), post <text> (post via bird). Flags: --vault (output as Obsidian markdown), --lustro (output as lustro JSON), -n/--limit N (default 20). Use subprocess to call bird. Test with: auceps --help. chmod +x."`

### Hatchet dogfooding — advanced features

#### Webhooks — trigger from GitHub push
- [!] `golem [t-013aa4] --provider zhipu --max-turns 40 "Read Hatchet webhooks API. Create a webhook endpoint that GitHub can call on push to vivesca repo. When triggered, dispatch new pending tasks from golem-queue.md. Steps: 1) Use h.webhooks.create() to register a webhook 2) Create effectors/hatchet-golem/webhook.py that handles the GitHub payload 3) Update .github/workflows/gemmule-wake.yml to also POST to the Hatchet webhook after waking gemmule. This replaces polling — tasks dispatch on push. Write tests. Commit."`

#### Worker labels + sticky sessions — provider affinity
- [x] `golem [t-c7a3b1] --provider zhipu --max-turns 40 "Read Hatchet worker labels and sticky session docs. Modify effectors/hatchet-golem/worker.py to: 1) Register workers with labels like {provider: 'zhipu', region: 'cn'} 2) Use desired_worker_labels on tasks so zhipu tasks prefer zhipu-labeled workers 3) Add sticky=StickyStrategy.SOFT so repeated tasks from the same queue entry stick to the same worker (warm cache). Write tests. Commit."`

#### Priority queuing — high-priority tasks first
- [x] `golem [t-8d9c37] --provider zhipu --max-turns 30 "Read Hatchet priority docs. Modify effectors/hatchet-golem/dispatch.py to: 1) Parse [!!] (high-priority) tasks and set default_priority=3 2) Parse [ ] (normal) tasks and set default_priority=1 3) This means Capco prep and fix tasks run before test-writing tasks. Write tests. Commit."`

#### Listener — real-time task completion stream
- [x] `golem [t-3cb616] --provider zhipu --max-turns 40 "Read Hatchet listener API (h.listener.stream, h.listener.on). Create effectors/hatchet-golem/monitor.py that: 1) Streams task completion events in real-time 2) On success: runs git add + auto-commit (port from golem-daemon's auto_commit) 3) On failure: logs to ~/.local/share/vivesca/hatchet-failures.log 4) Prints a live dashboard: '[OK] t-abc123 zhipu 45s | [FAIL] t-def456 infini 2s | Running: 8 zhipu, 3 infini'. Write tests. Commit."`

#### Backoff — exponential retry for rate limits
- [x] `golem [t-cd496a] --provider zhipu --max-turns 30 "Modify the golem tasks in effectors/hatchet-golem/worker.py. Add backoff_factor=2.0 and backoff_max_seconds=600 to each @hatchet.task decorator. This means: first retry after execution_timeout, second after 2x, third after 4x, capped at 10 min. Much better than the daemon's simple 1-retry. Write tests. Commit."`

#### Filters — route tasks by content
- [x] `golem [t-dcf063] --provider zhipu --max-turns 40 "Read Hatchet filters API. Create filters that auto-route tasks: 1) Tasks containing 'consulting' or 'Capco' get priority=3 2) Tasks containing 'test' get priority=1 3) Tasks containing 'fix' or 'broken' get priority=2. Use h.filters.create() to set these up. Modify dispatch.py to attach additional_metadata={'category': 'consulting|test|fix|other'} to each run. Write tests. Commit."`

#### Multi-worker scaling — separate workers per provider
- [x] `golem [t-491dc5] --provider zhipu --max-turns 40 "Refactor effectors/hatchet-golem/worker.py into per-provider workers. Create worker-zhipu.py, worker-infini.py, worker-volcano.py, worker-gemini.py — each registers only its own task. Then create effectors/hatchet-golem/start-workers.sh that launches all 4 in parallel with supervisor-style restart. This enables independent scaling: run 2 zhipu workers during peak. Write tests. Commit."`

#### Prometheus + Grafana observability
- [x] `golem [t-bea486] --provider zhipu --max-turns 40 "Add a Prometheus + Grafana stack to effectors/hatchet-golem/docker-compose.yml. 1) Add prometheus container scraping Hatchet metrics via h.metrics.scrape_tenant_prometheus_metrics() endpoint 2) Add grafana container with a pre-built dashboard showing: tasks/min by provider, failure rate, queue depth, avg duration 3) Grafana on port 3000. Write a README section. Commit."`

### Consulting IP — Hatchet vs Temporal for banking clients

#### Hatchet vs Temporal comparison card for financial services
- [x] `golem [t-886dee] --provider zhipu --max-turns 50 "Write a consulting insight card comparing Hatchet and Temporal for AI agent orchestration in financial services. Structure: 1) Executive summary (2 sentences) 2) Problem statement — banks deploying AI agents need orchestration beyond simple task queues 3) Head-to-head comparison table: setup complexity, Python SDK maturity, concurrency model, rate limiting, observability, enterprise adoption, self-hosting, cost, AI-native features 4) When to recommend Temporal: regulated environments needing audit trails, existing Java/Go teams, complex multi-step compliance workflows 5) When to recommend Hatchet: AI-first teams, rapid prototyping, per-provider rate limiting, simpler ops 6) Hands-on experience section: 'We run both in production — Hatchet dispatches 30+ concurrent AI coding agents across 5 LLM providers with built-in rate limiting and concurrency control. Temporal provides durable execution for long-running compliance workflows.' 7) Key risks: Hatchet maturity (18 months old), Temporal operational complexity. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hatchet-vs-temporal-banking.md. 800+ words. Commit."`

#### AI agent orchestration patterns for enterprise
- [!] `golem [t-fbf738] --provider zhipu --max-turns 50 "Write a consulting brief on AI agent orchestration patterns for enterprise banking. Cover: 1) The problem — banks running multiple AI agents (coding assistants, document processors, compliance checkers) need infrastructure beyond cron jobs 2) Pattern 1: Task queue (Celery/BullMQ) — simple but no durability 3) Pattern 2: Workflow engine (Temporal/Cadence) — durable but complex 4) Pattern 3: AI-native orchestrator (Hatchet) — built for LLM workloads 5) Pattern 4: Custom daemon — what most teams start with, why they outgrow it 6) Decision framework: when to use which 7) Reference architecture for a bank running 50+ AI agents 8) Our experience: migrated from custom daemon to Hatchet in one session, 2x reduction in code, built-in rate limiting replaced manual cooldown. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-agent-orchestration-patterns.md. 1000+ words. Commit." (retry)`

#### Hatchet quick-start guide for technical audience
- [x] `golem [t-081685] --provider zhipu --max-turns 40 "Write a technical quick-start guide for Hatchet aimed at a bank's platform engineering team. Include: 1) What Hatchet is (one paragraph) 2) docker-compose setup (exact YAML for postgres + rabbitmq + engine + dashboard) 3) Python worker example — a simple task that calls an LLM API 4) Concurrency control — per-model rate limiting 5) Monitoring — dashboard + metrics API 6) Security considerations for banking (self-hosted, data sovereignty, auth tokens) 7) Comparison with what they're probably using (Airflow/Celery). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hatchet-quickstart-banking.md. Commit."`

#### Build vs buy for AI orchestration — honest consulting card
- [x] `golem [t-c0e7cf] --provider zhipu --max-turns 50 "Write a consulting insight card: 'Build vs Buy for AI Agent Orchestration'. This must be brutally honest — no vendor cheerleading. Structure: 1) The pattern: every team starts with a custom script (cron + subprocess + retry loop). It works at 10-30 agents. 2) When custom is enough: single team, single provider, tasks under 10 min, no crash recovery needed, one developer maintaining it. Most bank PoCs fit here. 3) When you outgrow custom: multiple providers with different rate limits, workers that crash mid-task (durable execution), need to scale workers independently, need audit trail for compliance, multiple teams sharing infra. 4) The options with honest trade-offs: Temporal (battle-tested, complex ops, Java heritage), Hatchet (AI-native, young, simpler), Airflow (wrong tool but everyone has it), Custom++ (add Postgres queue, get 80% there). 5) Decision framework: 'If your AI agents are a PoC, keep the script. If they're going to production with SLA, pick Temporal. If your team is Python-first and AI-focused, evaluate Hatchet.' 6) Our experience: ran custom daemon at 30 agents across 5 providers for weeks. Migrated to Hatchet — code dropped from 900 to 110 lines. The real win was durable execution and server-side rate limits, not the dashboard. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/build-vs-buy-ai-orchestration.md. 800+ words. Commit."`

### Resilience & DR (organism survival)

#### DR runbook: iMac as warm standby for soma
Write a disaster recovery runbook at ~/epigenome/chromatin/System/soma-dr-runbook.md. Scenario: Fly.io dies or soma is unreachable for >1hr. The iMac (m3, Tailscale hostname m3) becomes primary. Cover: 1) Pre-requisites already on iMac (supervisor, repos, API keys in Keychain) 2) What needs to be synced: germline, epigenome, .claude config, .env equivalents 3) A single script `soma-failover` that: pulls latest from GitHub for germline+epigenome, starts supervisor with local soma.conf equivalent, starts Hatchet worker, verifies MCP server 4) What DOESN'T work on iMac (Docker golems, some Linux-only tools) and workarounds 5) Failback procedure once Fly recovers. Keep it under 200 lines. Commit.

#### Build soma-failover script
Write ~/germline/effectors/soma-failover as a Python script. When run on iMac: 1) git pull germline + epigenome 2) Check/start supervisor with macOS-adapted config 3) Start hatchet-worker 4) Start vivesca MCP 5) Run integrin health check 6) Report status. Should be idempotent — safe to run multiple times. Commit.

#### Build soma-health-check endpoint
Add a /health endpoint to vivesca MCP server that returns JSON: {status, uptime, supervisor_procs, disk_free_pct, last_golem_run, git_status}. This becomes the liveness probe — if soma stops responding, iMac failover triggers. Check if vivesca already has a health route first. Commit.

#### Automated soma backup to iMac
Write ~/germline/effectors/soma-backup as a Python script that rsyncs critical state from soma to iMac via Tailscale: ~/.claude/, ~/.env.fly, ~/tmp/supervisord.log, ~/epigenome/ (if not git-pushed). Run as a cron every 6 hours. Skip if iMac is offline (Tailscale status check). Commit.

#### Multi-cloud readiness: Oracle free tier bootstrap
Write a bootstrap script ~/germline/effectors/soma-oracle-bootstrap that provisions a free Oracle Cloud ARM instance as a cold standby. Similar to hetzner-bootstrap.sh but for Oracle free tier (4 OCPU, 24GB RAM ARM). Install same stack as soma Dockerfile. Don't auto-provision — just the script ready to run. Commit.

#### Supervisor config portability
Make soma.conf work on both Linux (Fly) and macOS (iMac). Currently hardcoded to /home/terry paths. Write a script ~/germline/effectors/soma-supervisor-gen that generates the right supervisord.conf for the current OS (detects Linux vs macOS, adjusts paths, skips Docker-only services on macOS). Commit.

#### Hatchet self-hosted resilience
The self-hosted Hatchet runs in Docker on soma. If Docker dies, all golem dispatch stops. Write ~/germline/effectors/hatchet-recover that: 1) Checks if Hatchet containers are running 2) If not, docker compose up -d 3) Waits for health 4) Restarts hatchet-worker supervisor process 5) Replays any tasks that were in-flight. Check docker-compose location first. Commit.

#### Golem provider failover chain
Review ~/germline/effectors/golem and document the current failover logic. Then enhance: if primary provider fails 3x, auto-rotate to next available provider (zhipu→gemini→codex→infini→volcano). Currently fallback exists but may not cover all providers. Add codex to the fallback chain. Commit.

#### Volume snapshot automation
Write ~/germline/effectors/soma-snapshot that creates a Fly volume snapshot via `fly volumes snapshots create`. Run weekly as a cron. Needs FLY_API_TOKEN. Check if fly CLI is installed first. Commit.

#### Network partition handling
What happens if Tailscale goes down? Document in ~/epigenome/chromatin/System/network-partition-playbook.md: 1) Direct SSH via fly ssh console 2) fly proxy for port forwarding 3) Direct IP access if allocated 4) What breaks without Tailscale (iMac↔soma, inter-service mesh). Keep under 100 lines. Commit.

### High-value batch (lunch run, 2026-04-01 12:20)
- [x] `golem --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Run --co again until 0 errors. Commit."`
- [x] `golem --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -10. For each top-5 failing file: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem --provider infini --max-turns 40 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | tail -5. Fix these 5 failing test files. Commit."`
- [x] `golem --provider volcano --max-turns 30 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Scan assays/ for hardcoded /Users/terry/ paths. Replace with Path.home(). Commit."`
- [x] `golem --provider infini --max-turns 30 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem --provider volcano --max-turns 30 "Find test files with SyntaxError via python3 -m py_compile on each assays/test_*.py. Fix syntax. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem --provider infini --max-turns 40 "List all Python files in metabolon/ that have no corresponding test in assays/. Pick the 5 smallest by line count. Write tests for each. Run uv run pytest. Fix failures. Commit."`
- [x] `golem --provider zhipu --max-turns 40 "List all Python files in metabolon/ that have no corresponding test in assays/. Pick files 6-10 by line count. Write tests for each. Run uv run pytest. Fix failures. Commit."`
- [x] `golem --provider volcano --max-turns 40 "List all effectors that are Python scripts with no test in assays/. Pick 5. Write tests using subprocess.run. Run uv run pytest. Fix failures. Commit."`
- [x] `golem --provider infini --max-turns 40 "List all effectors that are Python scripts with no test in assays/. Pick 5 different ones from the first batch. Write tests using subprocess.run. Run uv run pytest. Fix failures. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Find all Python files importing deprecated modules (imp, optparse, distutils). Modernise imports. Run tests. Commit."`
- [x] `golem --provider volcano --max-turns 30 "Scan effectors/ for any script missing a shebang line. Add #!/usr/bin/env python3 or #!/usr/bin/env bash as appropriate. Commit."`
- [x] `golem --provider infini --max-turns 30 "Find duplicate test functions (same name in different files) in assays/. Rename to be unique. Run uv run pytest --co. Commit."`
- [x] `golem --provider zhipu --max-turns 40 "Write a consulting insight card: AI agent orchestration patterns (Hatchet vs Temporal vs custom). Real-world trade-offs from production use. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/agent-orchestration-patterns.md. 500 words."`
- [x] `golem --provider infini --max-turns 40 "Write a consulting insight card: Cost optimisation for AI coding agents — multi-provider routing, rate limit handling, fallback chains. Real patterns from golem. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-coding-cost-optimisation.md. 500 words."`
- [x] `golem --provider volcano --max-turns 40 "Write a consulting insight card: Building self-sustaining AI development pipelines — auto-requeue, test generation, quality gates. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/self-sustaining-ai-pipelines.md. 500 words."`
