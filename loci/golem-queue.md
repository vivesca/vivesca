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

- [!] `golem [t-ddf8d2] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-operating-model.md — consulting insight card on AI operating model design for banks. Cover: centralized vs federated vs hub-and-spoke, Center of Excellence patterns, embedding AI in business lines, reporting lines, common pitfalls. 500-800 words. Commit."`
- [!] `golem [t-a4b7ef] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-data-strategy-banking.md — consulting insight card on data strategy for AI in banking. Cover: data quality as AI bottleneck, data lineage requirements, feature stores, synthetic data for testing, data mesh vs warehouse for ML, regulatory data constraints. 500-800 words. Commit."`
- [!] `golem [t-7a34d6] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/conversational-ai-banking.md — consulting insight card on conversational AI deployment in banking. Cover: chatbot maturity model, IVR modernization, agent assist vs full automation, measuring deflection and CSAT, compliance recording requirements, vendor landscape. 500-800 words. Commit."`
- [!] `golem [t-2afc07] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-in-credit-risk.md — consulting insight card on AI in credit risk. Cover: traditional scorecards vs ML models, explainability requirements (HKMA/ECOA), challenger model framework, monitoring for drift, regulatory approval process, back-testing requirements. 500-800 words. Commit."`
- [!] `golem [t-159add] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-aml-kyc.md — consulting insight card on AI for AML/KYC in banking. Cover: transaction monitoring ML, name screening NLP, network analysis for suspicious patterns, false positive reduction, regulatory expectations (HKMA 2024 AML circular), vendor landscape. 500-800 words. Commit."`
- [!] `golem [t-afa884] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-testing-validation.md — consulting insight card on AI testing and validation for banks. Cover: unit testing for ML pipelines, A/B testing in production, shadow deployment, champion-challenger, bias testing, adversarial testing, regulatory validation requirements. 500-800 words. Commit."`
- [!] `golem [t-de4aa4] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-change-management.md — consulting insight card on change management for AI initiatives in banks. Cover: stakeholder alignment, fear of job displacement, training programs, quick wins strategy, executive sponsorship, communication plan, measuring adoption. 500-800 words. Commit."`
- [!] `golem [t-a12f1a] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/cards/ai-ethics-board.md — consulting insight card on establishing an AI ethics board/committee in a bank. Cover: composition, charter, decision authority, escalation criteria, case study review process, integration with existing risk governance, common failures. 500-800 words. Commit."`

#### Fix operon — test failures wave 2 (5 tasks)

- [!] `golem [t-9cdd40] --provider codex --max-turns 50 "Run uv run pytest assays/test_sortase*.py -q --tb=short 2>&1 | head -80. Read all failures. Read the source modules they test. Fix root causes. Iterate until all sortase tests pass. Commit." (retry)`
- [!] `golem [t-6cb28f] --provider gemini --max-turns 50 "Run uv run pytest assays/test_golem*.py -q --tb=short 2>&1 | head -80. Read failures and source. Fix all golem test failures. Commit."`
- [!] `golem [t-3bfa9e] --provider codex --max-turns 40 "Run uv run pytest assays/test_effector*.py assays/test_browser*.py -q --tb=short 2>&1 | head -80. Fix all failures in effector and browser tests. Commit." (retry)`
- [!] `golem [t-d1c85f] --provider gemini --max-turns 40 "Run uv run pytest assays/test_respirometry*.py -q --tb=short 2>&1 | head -80. Fix all respirometry test failures. Commit."`
- [!] `golem [t-a213ab] --provider codex --max-turns 40 "Run uv run pytest assays/test_circulation*.py assays/test_chromatin*.py -q --tb=short 2>&1 | head -80. Fix all circulation and chromatin test failures. Commit." (retry)`

<!-- TRIMMED: #### Test coverage — untested metabolon modules (15 tasks) -->
<!-- TRIMMED: #### Test coverage — untested effectors (10 tasks) -->
#### Builds — organism health (5 tasks)

- [!] `golem [t-43f803] --provider gemini --max-turns 40 "Create effectors/queue-stats as a Python script. It should read loci/golem-queue.md and output: total pending, total done, total failed, per-provider breakdown, average estimated turns. Add --json flag. Make it executable. Write tests in assays/test_queue_stats.py. Run pytest. Commit."`
- [!] `golem [t-f074fa] --provider zhipu --max-turns 40 "Read effectors/soma-health. Enhance it to also check: (1) disk usage on /data, (2) number of running golem processes, (3) Hatchet container health via docker ps. Output a structured health report. Write tests. Run pytest. Commit."`
- [!] `golem [t-a23254] --provider gemini --max-turns 40 "Create effectors/golem-cost as a Python script. Read ~/.local/share/vivesca/golem.jsonl. Calculate: total runs per provider, success rate per provider, average duration, estimated token cost (ZhiPu=cheap, Infini=medium, Volcano=cheap). Output table. Add --json and --since flags. Write tests. Commit."`
- [!] `golem [t-a63844] --provider codex --max-turns 30 "Scan all assays/test_*.py files. Find any that import modules using hardcoded absolute paths like /Users/terry/ or /home/terry/. Replace with Path.home() or relative paths. Run pytest --co to verify collection. Commit." (retry)`
- [!] `golem [t-bf70fe] --provider gemini --max-turns 30 "Scan effectors/ for any Python scripts missing a shebang line (#!/usr/bin/env python3). Add missing shebangs. Also check all Python effectors parse without SyntaxError using ast.parse. Fix any syntax errors. Commit."`

#### Consulting IP — case study shells (5 tasks)

- [!] `golem [t-538257] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/genai-customer-service.md — a case study shell for a GenAI-powered customer service transformation at a mid-size HK bank. Structure: situation (bank context, pain points), approach (phases, technology choices), results (metrics), lessons learned, Capco role. 600-1000 words. Commit."`
- [!] `golem [t-02875f] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ml-credit-scoring.md — a case study shell for ML-based credit scoring at a retail bank. Cover: legacy scorecard limitations, model development approach, explainability solution, regulatory approval process, production deployment, results. 600-1000 words. Commit."`
- [!] `golem [t-89b52a] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ai-operating-model.md — a case study shell for establishing an AI Center of Excellence at an APAC bank. Cover: starting from zero, talent acquisition, governance framework, first 5 use cases, scaling challenges, 18-month roadmap. 600-1000 words. Commit."`
- [!] `golem [t-fb81f2] --provider zhipu --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/data-quality-ai-readiness.md — a case study shell for data quality remediation enabling AI adoption. Cover: data assessment findings, data lineage gaps, remediation program, feature store implementation, measurable improvement in model performance. 600-1000 words. Commit."`

### Mitogen wave 3 -- 50 tasks (2026-04-01 afternoon)

<!-- TRIMMED: #### Test coverage -- metabolon organelles (12 tasks) -->
<!-- TRIMMED: #### Test coverage -- endocytosis subsystem (6 tasks) -->
<!-- TRIMMED: #### Test coverage -- metabolism + resources (8 tasks) -->
<!-- TRIMMED: #### Test coverage -- more effectors (8 tasks) -->
<!-- TRIMMED: #### Test coverage -- sortase + respirometry (4 tasks) -->
#### Hardening -- codebase quality (6 tasks)

- [!] `golem [t-c11f74] --provider gemini --max-turns 30 "Scan metabolon/ for any Python files with unused imports. Remove unused imports. Run uv run pytest --co to verify nothing broke. Commit."`
- [!] `golem [t-a74a4f] --provider gemini --max-turns 30 "Find all subprocess.run calls in metabolon/ and effectors/ that lack a timeout parameter. Add timeout=300 to each. Run pytest --co to verify. Commit."`
- [!] `golem [t-9815e4] --provider gemini --max-turns 30 "Scan assays/ for test files that shell out to commands not available on Linux (e.g. macOS-only: open, pbcopy, osascript). Mock or skip those tests on Linux. Run pytest --co. Commit."`
- [!] `golem [t-3aa379] --provider zhipu --max-turns 30 "Find all open() calls in metabolon/ that don't use a context manager (with statement). Refactor to use with. Run pytest --co. Commit."`
- [!] `golem [t-f8012f] --provider gemini --max-turns 40 "Run uv run pytest -q --tb=no 2>&1 | grep FAILED | wc -l. Then run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep ERROR | wc -l. Report both counts. Fix any collection errors. Commit."`
- [!] `golem [t-5fca92] --provider gemini --max-turns 30 "Check all Python files in metabolon/ have proper __all__ exports or are internal. For any public module missing __all__, add one. Run pytest --co. Commit."`

#### Builds -- organism tooling (6 tasks)

- [!] `golem [t-b4dcd3] --provider gemini --max-turns 40 "Create effectors/coverage-map as a Python script. It reads assays/ and metabolon/ to produce a coverage matrix: which modules have tests, which don't, percentage covered. Output as table. Add --json flag. Write tests. Run pytest. Commit."`
- [!] `golem [t-fa69fa] --provider zhipu --max-turns 40 "Create effectors/effector-usage as a Python script. Scan ~/.claude/ skills and hooks for references to effectors. Report which effectors are actively used by skills/hooks and which are orphaned. Add --json flag. Write tests. Commit."`
- [!] `golem [t-7a0356] --provider gemini --max-turns 40 "Read effectors/golem. Add a --summary flag that shows stats from the last N runs: success rate, average duration, per-provider breakdown. Read from ~/.local/share/vivesca/golem.jsonl. Write tests. Commit."`
- [!] `golem [t-b7aa1c] --provider zhipu --max-turns 40 "Create effectors/test-fixer as a Python script. It runs pytest -q --tb=line, parses failures, groups by file, and outputs a markdown report of what's broken and likely causes. Add --json flag. Write tests. Commit."`
- [!] `golem [t-1d36fa] --provider gemini --max-turns 40 "Read effectors/queue-balance. If it doesn't exist, create it as a Python script that reads loci/golem-queue.md and reports: tasks per provider, suggested rebalancing to maximize throughput given provider concurrency limits. Write tests. Commit."`
- [!] `golem [t-d243c1] --provider zhipu --max-turns 40 "Read effectors/provider-bench. If it doesn't exist, create it as a Python script that dispatches a small test task to each provider (zhipu, infini, volcano) and measures TTFB and completion time. Reports in a table. Write tests. Commit."`



### Provider resilience (2026-04-01 evening)

#### Quota tracking dashboard

- [!] `golem [t-10328d] --provider gemini --max-turns 40 "Read effectors/golem-daemon. It already tracks cooldowns in-memory but loses them on restart. Add a persistent quota state file at ~/.local/share/vivesca/provider-quota.json that records: (1) last rate-limit hit timestamp per provider, (2) estimated reset time, (3) cumulative requests today. Update it on every task completion and rate-limit detection. Read it on daemon start to restore cooldown state. Add a 'golem-daemon quota' subcommand that prints a table of provider quota status. Write tests. Commit."`
- [!] `golem [t-193f9c] --provider gemini --max-turns 30 "Read effectors/golem. Add a --quota flag that reads ~/.local/share/vivesca/provider-quota.json and prints current quota status for all providers in a table: provider, requests today, last rate-limit, estimated reset time, status (ok/cooldown/exhausted). Exit 0. Write tests. Commit."`



#### Codex provider fix

- [!] `golem [t-2efba8] --provider gemini --max-turns 30 "Read effectors/golem. The codex provider invokes codex exec but does not pass --dangerously-bypass-approvals-and-sandbox. Without it, codex prompts for approval and hangs. Add the flag to the codex exec command on line ~366. Also add codex and gemini to the fallback_provider mapping. Run a test: golem --provider gemini --max-turns 1 'echo test'. Commit."`

#### golem-daemon provider concurrency tuning

- [!] `golem [t-3df601] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. The PROVIDER_LIMITS dict has infini=1 which is too conservative (causes 33 tasks to queue behind 1 slot). Check the Infini plan limit -- if it is 1000 req/5hr, then 4 concurrent with 5min avg task = ~48 req/hr = well within limit. Update infini to 4. Also add codex and gemini entries: codex=4, gemini=4. Commit."`

#### Add codex+gemini to golem-daemon provider tracking

- [!] `golem [t-90be4d] --provider gemini --max-turns 30 "Read effectors/golem-daemon. Verify that codex and gemini providers are recognized by the daemon's queue parser and task runner. The golem script already handles them -- daemon just needs to not reject unknown providers. Test by adding a codex task to the queue and checking daemon status shows it. Commit."`



### Mitogen wave 5 -- Capco readiness (2026-04-01 evening)

#### HSBC + regulatory refresh (perishable)

- [!] `golem [t-476439] --provider gemini --max-turns 40 "Search the web for HKMA circulars and announcements from March 25 to April 1, 2026. Focus on anything related to AI, GenAI, technology risk, or digital transformation. For each new circular found, write a 200-word briefing to ~/epigenome/chromatin/euchromatin/regulatory/ with filename hkma-YYYY-MM-topic.md. Include: what it says, implications for banks, what a consultant should know. Commit."`
- [!] `golem [t-0c9f24] --provider gemini --max-turns 40 "Search the web for SFC (Hong Kong Securities and Futures Commission) announcements from March 25 to April 1, 2026 related to AI, algorithmic trading, technology risk, or digital assets. Write briefings to ~/epigenome/chromatin/euchromatin/regulatory/ with filename sfc-YYYY-MM-topic.md. Commit."`
- [!] `golem [t-227ede] --provider zhipu --max-turns 40 "Search the web for HSBC AI news, announcements, blog posts, and press releases from the last 30 days (March 2026). Look for: new AI products, leadership changes in AI/data/digital, partnerships, regulatory filings mentioning AI, earnings call AI mentions. Write findings to ~/epigenome/chromatin/euchromatin/consulting/hsbc-ai-update-apr-2026.md. Commit."`
- [!] `golem [t-ff73ac] --provider gemini --max-turns 40 "Search the web for Evident AI Banking Brief and Evident AI Index updates from March 15 to April 1, 2026. Evident Insights publishes weekly briefings on AI in banking at evidentinsights.com. For each issue found, extract key findings and write to ~/epigenome/chromatin/Transduction/Extractions/ with appropriate filename. Commit."`
- [!] `golem [t-243c1f] --provider gemini --max-turns 40 "Search the web for the biggest AI news and model releases from March 20 to April 1, 2026. Focus on: new foundation model releases, major product launches, regulatory actions, notable enterprise AI deployments. Write a concise briefing (top 10 developments) to ~/epigenome/chromatin/euchromatin/consulting/ai-landscape-update-apr-2026.md. Each item: what happened, why it matters for banking, talking point for a consultant. Commit."`

#### HSBC engagement prep refresh

- [!] `golem [t-4b6b22] --provider gemini --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/HSBC AI Intelligence - Mar 2026.md. Search the web for any updates to the topics covered since that document was written. Write an addendum file ~/epigenome/chromatin/euchromatin/consulting/hsbc-ai-intelligence-addendum-apr-2026.md covering only NEW developments not in the original. Commit."`
- [!] `golem [t-a48523] --provider zhipu --max-turns 40 "Search the web for Capco recent news, blog posts, and thought leadership from the last 30 days. Focus on their AI/data practice, new client wins, published articles, conference talks. Write to ~/epigenome/chromatin/euchromatin/consulting/capco-practice-update-apr-2026.md. Commit."`
- [!] `golem [t-88d43b] --provider gemini --max-turns 40 "Read ~/epigenome/chromatin/euchromatin/consulting/cards/. List all existing insight card topics. Then search the web for trending AI-in-banking topics from the last 2 weeks that are NOT already covered by existing cards. Write 3 new cards on the most relevant gaps to ~/epigenome/chromatin/euchromatin/consulting/cards/. Each card 500-800 words. Commit."`

#### Week 1 conversation assets

- [!] `golem [t-9e698a] --provider gemini --max-turns 30 "Write ~/epigenome/chromatin/euchromatin/consulting/week1-talking-points.md -- 10 sharp, specific talking points about AI in HK banking for first-week conversations at Capco. Each point: the claim (1 sentence), the evidence (specific data point or example), the contrarian angle (what most people get wrong). Draw from HKMA circulars, HSBC specifics, and recent AI developments. Not generic -- each point should demonstrate deep domain knowledge. Commit."`
- [!] `golem [t-d012c2] --provider gemini --max-turns 30 "Write ~/epigenome/chromatin/euchromatin/consulting/60-second-intro.md -- three versions of a 60-second professional introduction for someone joining Capco's AI practice. Version 1: for peers (other consultants). Version 2: for clients (bank executives). Version 3: for leadership (Capco partners). Each emphasizes different aspects of the background: hands-on AI building, regulatory awareness, banking domain, consulting frameworks. Commit."`




### CLI setup -- Gemini + Codex parity (2026-04-01)

#### Codex config

- [!] `golem [t-0319e8] --provider zhipu --max-turns 30 "Read ~/.codex/config.toml. Add: (1) approval_policy = 'auto-edit' under [projects.'/home/terry/germline'] so codex doesn't prompt. (2) Add sandbox_permissions = ['disk-full-read-access', 'disk-write-access'] for full file access. (3) Verify the config by running: codex exec --skip-git-repo-check 'echo hello' and confirm it runs without prompting. Commit the config."`
- [!] `golem [t-097913] --provider gemini --max-turns 30 "Read ~/germline/CLAUDE.md (the project instruction file for Claude Code). Create ~/germline/AGENTS.md with the same content adapted for Codex -- Codex reads AGENTS.md as its project instruction file. Remove CC-specific references (hooks, skills, slash commands) but keep: codebase conventions, testing patterns, bio naming, directory layout. Commit."`

#### Gemini config

- [!] `golem [t-54a938] --provider gemini --max-turns 30 "Read ~/germline/CLAUDE.md. Create ~/germline/.gemini/GEMINI.md with equivalent instructions adapted for Gemini CLI. Gemini reads .gemini/GEMINI.md as its project instruction file. Keep: codebase conventions, testing patterns, bio naming, directory layout. Remove CC-specific hooks/skills references. Commit."`
- [!] `golem [t-691fe8] --provider gemini --max-turns 30 "Read ~/.gemini/settings.json. Update it to enable: (1) sandbox with full disk access if available, (2) auto-approve tool use. Check gemini --help for available settings. Apply and test with: gemini -p 'list files in current directory'. Commit."`

#### Golem script fixes for non-CC providers

- [!] `golem [t-1c37bf] --provider zhipu --max-turns 40 "Read effectors/golem lines 355-375 (the codex and gemini execution paths). Fix: (1) codex exec needs --dangerously-bypass-approvals-and-sandbox flag to avoid prompting. (2) gemini -p needs to work without shell tool access -- check if gemini has a sandbox/tools config flag. (3) Test both: golem --provider codex --max-turns 1 'echo test' and golem --provider codex --max-turns 1 'echo test'. Commit."`


### Provider quality experiment -- same prompt x 4 providers (2026-04-01)

- [!] `golem [t-43a865] --provider gemini --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-zhipu-apr2026.md. Commit."`
- [!] `golem [t-aa1b9b] --provider gemini --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-gemini-apr2026.md. Commit."`
- [!] `golem [t-8f95b5] --provider zhipu --max-turns 30 "Search the web for the 5 most significant AI developments in banking from March 15 to April 1, 2026. For each: what happened (2 sentences), why it matters for a bank CTO (2 sentences), contrarian take (1 sentence). Write to ~/epigenome/chromatin/euchromatin/consulting/ai-banking-top5-codex-apr2026.md. Commit."`


### Mitogen wave 4 -- infra + orchestration (2026-04-01 evening)

#### Fix Hatchet worker (experimental)

- [!] `golem [t-460fd3] --provider gemini --max-turns 40 "Read effectors/hatchet-golem/worker.py. The action listener subprocess dies after ~1 task. Add try/except + file logging in _run_golem to /tmp/hatchet-golem-debug.log. Check if gRPC stream closes after first response. Write findings to effectors/hatchet-golem/TROUBLESHOOTING.md. Commit."`
- [!] `golem [t-a8ed0b] --provider gemini --max-turns 30 "Read effectors/hatchet-golem/worker.py. Refactor golem_zhipu (durable_task) to use _run_golem instead of duplicated inline parsing. Run uv run pytest assays/test_*hatchet* if tests exist. Commit."`
- [!] `golem [t-8db9f3] --provider gemini --max-turns 30 "Read effectors/hatchet-golem/docker-compose.yml. Add port mapping 8080:80 to the dashboard service so the SDK token reaches the REST API. Add a comment explaining why. Commit."`

#### Fix Temporal setup (experimental)

- [!] `golem [t-2a1782] --provider zhipu --max-turns 40 "Read effectors/temporal-golem/docker-compose.yml. Fix: DB=postgres12, POSTGRES_USER/POSTGRES_PWD/POSTGRES_SEEDS env vars, port 5433:5432 to avoid conflicts. Commit."`
- [!] `golem [t-2355d2] --provider gemini --max-turns 40 "Read effectors/temporal-golem/workflow.py and cli.py. Fix import paths. Write smoke test in assays/test_temporal_golem.py that mocks the Temporal client. Commit."`

#### Formalize golem-daemon as primary

- [!] `golem [t-6bf518] --provider gemini --max-turns 30 "Read effectors/golem-daemon. Add --foreground flag that skips nohup/background, runs main loop in current process (for supervisor). Write tests. Commit."`
- [!] `golem [t-dfce9c] --provider gemini --max-turns 30 "Write effectors/golem-daemon-supervisor.conf -- proposed supervisor config for golem-daemon. Model on hatchet-worker in /etc/supervisor/conf.d/soma.conf. Use --foreground flag. Commit."`

#### Retries -- consulting case studies + tooling

- [!] `golem [t-44c34b] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ml-credit-scoring.md -- case study shell for ML credit scoring. 600-1000 words. Commit."`
- [!] `golem [t-614b9c] --provider gemini --max-turns 40 "Create ~/epigenome/chromatin/euchromatin/consulting/case-studies/ai-operating-model.md -- case study shell for AI CoE at an APAC bank. 600-1000 words. Commit."`
- [!] `golem [t-175bcf] --provider gemini --max-turns 40 "Create effectors/coverage-map as Python script. Read assays/ and metabolon/ to produce coverage matrix. Add --json flag. Write tests. Commit."`
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
- [!] `golem [t-ba2828] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:33)
- [!] `golem [t-9044f1] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:39)

### Auto-requeue (19 tasks @ 07:44)
- [!] `golem [t-5c089a] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:49)
- [!] `golem [t-158f13] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-6129f5] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`

### Auto-requeue (19 tasks @ 07:53)
- [!] `golem [t-0b1c3f] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-26ae70] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-e8b985] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 07:57)
- [!] `golem [t-eae2a5] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/gates.py. Mock external calls. Write assays/test_metabolism_gates.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon.py. Mock external calls. Write assays/test_organelles_translocon.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8f649b] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [x] `golem [t-69456b] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-5e5210] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 08:02)
- [!] `golem [t-fd5a39] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-8ce0c6] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-b61fe0] --provider gemini --max-turns 30 "Health check: x-feed-to-lustro, pinocytosis, complement, update-compound-engineering-skills.sh, launchagent-health, test-fixer, chromatin-backup.sh, circadian-probe.py, paracrine, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-026e0c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/demethylase.py. Mock external calls. Write assays/test_organelles_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fd9639] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/retrograde.py. Mock external calls. Write assays/test_organelles_retrograde.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bdcc27] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0cb093] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-89ab22] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit." (retry)`
- [!] `golem [t-7de36d] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [x] `golem [t-101bf6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d1108f] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-bbcf8d] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 08:14)
- [!] `golem [t-aba479] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-bfd333] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-3ff001] --provider zhipu --max-turns 30 "Health check: plan-exec.deprecated, mismatch-repair, queue-gen, golem-top, update-compound-engineering, x-feed-to-lustro, test-spec-gen, receptor-health, pharos-health.sh, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-f6a512] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/lysin/cli.py. Mock external calls. Write assays/test_lysin_cli.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-106c9d] --provider zhipu --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4a7cfe] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-86c4c7] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-7af5ce] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-5c2df2] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [x] `golem [t-450d8f] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5e4a13] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 01:16)
- [!] `golem [t-218472] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-f1c201] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-c05334] --provider zhipu --max-turns 30 "Health check: synthase, grep, oura-weekly-digest.py, safe_rm.py, gemmule-wake, importin, overnight-gather, queue-gen, rotate-logs.py, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-8fe655] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/reflexes.py. Mock external calls. Write assays/test_resources_reflexes.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-80438b] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-669100] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-af1d4a] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-13f1ff] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-26de37] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-660d4b] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9409a7] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e8aba5] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 01:26)
- [x] `golem [t-b494d9] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-409b84] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-b0e802] --provider gemini --max-turns 30 "Health check: gemmule-wake, golem-dash, qmd-reindex.sh, lysis, complement, quorum, taste-score, backfill-marks, plan-exec, golem-daemon-wrapper.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-faeb3b] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/receptome.py. Mock external calls. Write assays/test_resources_receptome.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ce2f80] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0fd2ab] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-66ea82] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-319968] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-514bb1] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-1f5574] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:34)
- [!] `golem [t-0b726d] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c56b76] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-d7de5c] --provider zhipu --max-turns 30 "Health check: provider-bench, transduction-daily-run, update-compound-engineering-skills.sh, golem-daemon, start-chrome-debug.sh, pharos-health.sh, queue-balance, lacuna, gemmule-snapshot, vesicle. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-30c5ab] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-b8374f] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-f0b5f0] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-0cd68b] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-96f1e2] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:44)
- [!] `golem [t-8ba6c5] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a62838] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-8d4065] --provider zhipu --max-turns 30 "Health check: gemmule-wake, centrosome, diapedesis, pharos-env.sh, chemoreception.py, test-spec-gen, channel, proteostasis, weekly-gather, circadian-probe.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-0799b9] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-04c730] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-41983e] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-f6ee5b] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0aa0c0] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:45)
- [!] `golem [t-2c460e] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-cd543b] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-39ba9f] --provider gemini --max-turns 30 "Health check: git-activity, weekly-gather, qmd-reindex.sh, methylation-review, golem-daemon, poiesis, update-coding-tools.sh, capco-prep, golem-daemon-wrapper.sh, consulting-card.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-6432ac] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [!] `golem [t-91e3ba] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-7ea4a1] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-4c5315] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-ff9d44] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:50)
- [x] `golem [t-e2b8ac] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3cb054] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-3f98ef] --provider gemini --max-turns 30 "Health check: launchagent-health, golem-top, legatum, judge, lysis, test-fixer, skill-sync, orphan-scan, plan-exec, queue-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-f66542] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/judge.py. Mock external calls. Write assays/test_enzymes_judge.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bae6f6] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-130f0f] --provider zhipu --max-turns 30 "Write tests for effectors/soma-activate. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-948041] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3e00f5] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-2b11d2] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-95083d] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-133735] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:52)
- [!] `golem [t-a1a8f4] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-553a58] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4fb97a] --provider gemini --max-turns 30 "Health check: compound-engineering-test, gemmation-env, provider-bench, lacuna, channel, phagocytosis.py, engram, safe_search.py, replisome, compound-engineering-status. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a2fcb7] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e89d17] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-8c5a97] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e9a281] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [!] `golem [t-7132c1] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3997be] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:01)
- [!] `golem [t-e63bf5] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-133a30] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-43e327] --provider zhipu --max-turns 30 "Health check: exocytosis.py, conftest-gen, skill-search, vesicle, log-summary, goose-worker, tmux-url-select.sh, provider-bench, chromatin-decay-report.py, update-compound-engineering-skills.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-93b283] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c91c68] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e235e1] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-8110e1] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cd6401] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:03)
- [!] `golem [t-c869bc] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-1d2ce7] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-d55220] --provider gemini --max-turns 30 "Health check: pharos-sync.sh, gemmule-clean, respirometry, chat_history.py, search-guard, switch-layer, browser, capco-prep, golem-reviewer, rename-plists. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-b52b3e] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sortase.py. Mock external calls. Write assays/test_enzymes_sortase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ccaed8] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-6ba816] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-b25a25] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [x] `golem [t-9dad86] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fb19d4] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-94b1e4] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-181317] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:14)
- [x] `golem [t-4b5b95] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c36713] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-6e62de] --provider gemini --max-turns 30 "Health check: test-fixer, overnight-gather, safe_rm.py, chromatin-decay-report.py, wewe-rss-health.py, express, golem-health, vesicle, soma-bootstrap, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-01b309] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-9d8add] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-780c6c] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-674ba2] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-765101] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-789fef] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-c2aa96] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:20)
- [x] `golem [t-70d083] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-cb57ba] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-4e8d47] --provider gemini --max-turns 30 "Health check: photos.py, git-activity, gap_junction_sync, cytokinesis, queue-gen, plan-exec.deprecated, golem-health, overnight-gather, centrosome, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-9abfb4] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitophagy.py. Mock external calls. Write assays/test_organelles_mitophagy.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f5498e] --provider zhipu --max-turns 30 "Write tests for effectors/golem-daemon-wrapper.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-1d16d6] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-0c36a1] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-680707] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-254bca] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-067989] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-e8883e] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 02:27)
- [!] `golem [t-767ebb] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-18dbaf] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-9c78b8] --provider zhipu --max-turns 30 "Health check: rename-plists, immunosurveillance, cleanup-stuck, tmux-osc52.sh, disk-audit, receptor-health, update-coding-tools.sh, exocytosis.py, sortase, golem-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-ba1257] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser.py. Mock external calls. Write assays/test_organelles_browser.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-608928] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c74a77] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-ec0314] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-2979aa] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-959fe2] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cad42a] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 10:36)
- [!] `golem [t-86230a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-2546c4] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-9d210b] --provider gemini --max-turns 30 "Health check: centrosome, legatum-verify, regulatory-capture, respirometry, autoimmune.py, soma-snapshot, demethylase, channel, efferens, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-10bbc2] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/rheotaxis.py. Mock external calls. Write assays/test_enzymes_rheotaxis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a2eec7] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-ace678] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [x] `golem [t-d0d9b9] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-af42cd] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-d40364] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [x] `golem [t-2d223c] --provider zhipu --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-94160f] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 10:40)
- [!] `golem [t-7f023a] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-9916f5] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-c0a940] --provider gemini --max-turns 30 "Health check: update-coding-tools.sh, pharos-sync.sh, photos.py, queue-balance, consulting-card.py, electroreception, legatum, lacuna.py, respirometry, pharos-health.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-5792bd] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/differentiation.py. Mock external calls. Write assays/test_enzymes_differentiation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-076067] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/efferens.py. Mock external calls. Write assays/test_enzymes_efferens.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-78c4d0] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit." (retry)`
- [!] `golem [t-d8483c] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [!] `golem [t-4e2d01] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [x] `golem [t-324f82] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-c87155] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-015f3f] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 02:48)
- [x] `golem [t-bc0c3e] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-b5197a] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-16b9aa] --provider zhipu --max-turns 30 "Health check: demethylase, test-dashboard, channel, circadian-probe.py, judge, translocon, poiesis, switch-layer, soma-bootstrap, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-00bcd3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/pseudopod.py. Mock external calls. Write assays/test_enzymes_pseudopod.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-055476] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/conjugation_engine.py. Mock external calls. Write assays/test_organelles_conjugation_engine.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-9e4216] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/signals.py. Mock external calls. Write assays/test_metabolism_signals.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5d9047] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-40863c] --provider volcano --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-8c23fc] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-78c2bb] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-15ec11] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-21b3f4] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9e9f59] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:02)
- [!] `golem [t-fae7ab] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-479911] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-409ba2] --provider gemini --max-turns 30 "Health check: receptor-health, dr-sync, pulse-review, importin, x-feed-to-lustro, launchagent-health, exocytosis.py, rheotaxis-local, lysis, oura-weekly-digest.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-8a8300] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rename.py. Mock external calls. Write assays/test_organelles_rename.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-be7340] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/fitness.py. Mock external calls. Write assays/test_metabolism_fitness.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cb98e3] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-df614a] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-a37d09] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-9156b4] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [x] `golem [t-9ba63e] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7734fa] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:05)
- [!] `golem [t-ff0d1b] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-6b1dac] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-1d8e9e] --provider volcano --max-turns 30 "Health check: taste-score, update-compound-engineering, tm, golem-review, capco-prep, effector-usage, exocytosis.py, express, sortase, centrosome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-a3c852] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/pinocytosis/interphase.py. Mock external calls. Write assays/test_pinocytosis_interphase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-374260] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/sporulation.py. Mock external calls. Write assays/test_organelles_sporulation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b641aa] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/effector.py. Mock external calls. Write assays/test_organelles_effector.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d461c8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/praxis.py. Mock external calls. Write assays/test_organelles_praxis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d1a9b7] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-15b20c] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-d8f5d0] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ba858e] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-b068f7] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit." (retry)`
- [x] `golem [t-7317c6] --provider infini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-69b063] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a50c01] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:09)
- [x] `golem [t-6e625a] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-ffbd6e] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-8f9c9c] --provider zhipu --max-turns 30 "Health check: chat_history.py, cibus.py, phagocytosis.py, soma-watchdog, nightly, receptor-scan, photos.py, golem-daemon-wrapper.sh, transduction-daily-run, lacuna. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-1045b7] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/endosomal.py. Mock external calls. Write assays/test_organelles_endosomal.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c995ce] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/monitors.py. Mock external calls. Write assays/test_respirometry_monitors.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-f8f422] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/vasomotor_sensor.py. Mock external calls. Write assays/test_organelles_vasomotor_sensor.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6af058] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-498dcd] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b7e945] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8f9019] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-694e0c] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f6a6b4] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-72f8d6] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-47a2b3] --provider volcano --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-107376] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-258fcd] --provider infini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:15)
- [x] `golem [t-5e9ca9] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c17079] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-3460f0] --provider volcano --max-turns 30 "Health check: soma-pull, golem-daemon-wrapper.sh, proteostasis, grok, vesicle, golem-validate, skill-search, coverage-map, find, disk-audit. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-5489c8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/sweep.py. Mock external calls. Write assays/test_metabolism_sweep.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ae39a7] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/anatomy.py. Mock external calls. Write assays/test_resources_anatomy.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6f31a8] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/coaching_cli.py. Mock external calls. Write assays/test_sortase_coaching_cli.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7571f9] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/baroreceptor.py. Mock external calls. Write assays/test_organelles_baroreceptor.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-07fb8e] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-749563] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-59c76e] --provider zhipu --max-turns 30 "Write tests for effectors/soma-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b2d0ab] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [!] `golem [t-656b8a] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit." (retry)`
- [x] `golem [t-e76a04] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-71a03c] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-20ab11] --provider volcano --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-dd4835] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:23)
- [!] `golem [t-41e219] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e8eb1b] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-203f8a] --provider gemini --max-turns 30 "Health check: inflammasome-probe, centrosome, rheotaxis-local, circadian-probe.py, goose-worker, soma-bootstrap, golem-daemon-wrapper.sh, taste-score, receptor-health, gemmation-env. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-294cb9] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/coaching_cli.py. Mock external calls. Write assays/test_sortase_coaching_cli.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-3066f8] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/glycolysis_rate.py. Mock external calls. Write assays/test_organelles_glycolysis_rate.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2cc304] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/circadian.py. Mock external calls. Write assays/test_resources_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-18b8ef] --provider volcano --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fa5e48] --provider volcano --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-26fe9f] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-941cf3] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [!] `golem [t-904d26] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-751d27] --provider infini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-afc300] --provider volcano --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a70649] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 03:34)
- [x] `golem [t-b1ee89] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-1cef51] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-34c5f9] --provider infini --max-turns 30 "Health check: start-chrome-debug.sh, backfill-marks, nightly, soma-snapshot, phagocytosis.py, soma-scale, inflammasome-probe, golem-review, exocytosis.py, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-daf2d3] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/mitosis.py. Mock external calls. Write assays/test_enzymes_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5db275] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/payments.py. Mock external calls. Write assays/test_respirometry_payments.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-bd8b48] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/potentiation.py. Mock external calls. Write assays/test_organelles_potentiation.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b73a10] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/tachometer.py. Mock external calls. Write assays/test_enzymes_tachometer.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-482697] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5be80b] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-8556d5] --provider infini --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-abf07f] --provider volcano --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-f2fe18] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-034aff] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-d12387] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-d440fd] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b63915] --provider volcano --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 11:40)
- [!] `golem [t-f09807] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [x] `golem [t-645817] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b0871f] --provider zhipu --max-turns 30 "Health check: engram, mitosis-checkpoint.py, diapedesis, launchagent-health, disk-audit, golem-dash, cibus.py, quorum, ck, commensal. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-9ae30c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engram.py. Mock external calls. Write assays/test_organelles_engram.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-5a73cb] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/expression.py. Mock external calls. Write assays/test_enzymes_expression.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-0c54d2] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/mitosis.py. Mock external calls. Write assays/test_organelles_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-97e153] --provider infini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-141485] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-15a657] --provider infini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-10fbed] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-71956d] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit." (retry)`
- [!] `golem [t-c92de3] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit." (retry)`
- [x] `golem [t-5558fc] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-f8a15a] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-ce96fd] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 03:44)
- [x] `golem [t-e7841a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-fe8669] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-cd3f14] --provider gemini --max-turns 30 "Health check: golem-validate, immunosurveillance.py, importin, ck, methylation, engram, replisome, rotate-logs.py, tm, bud. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [x] `golem [t-5b75f0] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-29ea41] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/case_study.py. Mock external calls. Write assays/test_organelles_case_study.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-b7be84] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/infection.py. Mock external calls. Write assays/test_metabolism_infection.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-4f2c47] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-efd13e] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ff5e40] --provider infini --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c5c046] --provider zhipu --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c578d0] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-5f1be7] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [x] `golem [t-398478] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-49d7a1] --provider infini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0586b2] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
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
- [!] `golem [t-d054be] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5b4cef] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-c92a55] --provider zhipu --max-turns 30 "Health check: soma-snapshot, weekly-gather, test-spec-gen, centrosome, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-9bde40] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-adf0dd] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`

### Auto-requeue (19 tasks @ 15:42)
- [!] `golem [t-c88788] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7bf264] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-08b5ca] --provider gemini --max-turns 30 "Health check: safe_search.py, lysis, orphan-scan, respirometry, skill-search, mismatch-repair, hetzner-bootstrap.sh, legatum-verify, golem, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-959be7] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-1d302e] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-7cf772] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-dc3e63] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f0f2c4] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:42)
- [!] `golem [t-954e8c] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3e67e5] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-03ece1] --provider zhipu --max-turns 30 "Health check: oura-weekly-digest.py, quorum, grep, rheotaxis-local, soma-snapshot, hetzner-bootstrap.sh, browse, orphan-scan, compound-engineering-status, backup-due.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c2e5f4] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-1eb311] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-b336f9] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-232278] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0804ea] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:43)
- [!] `golem [t-3fecd0] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-757fb2] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-467116] --provider gemini --max-turns 30 "Health check: nightly, regulatory-capture, receptor-health, queue-stats, circadian-probe.py, browser, legatum, git-activity, soma-pull, qmd-reindex.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-3ddd92] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-07f4ed] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-7fecd4] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-b5fa04] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab475a] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:43)
- [!] `golem [t-e3e78e] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-424f3d] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-76ba44] --provider gemini --max-turns 30 "Health check: cytokinesis, wacli-ro, importin, proteostasis, test-dashboard, pharos-health.sh, autoimmune.py, plan-exec.deprecated, safe_search.py, soma-clean. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-4c2bde] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-9208be] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-41065d] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-e1a526] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3be216] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a082d2] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:44)
- [!] `golem [t-24964d] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-ec798e] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e4f07c] --provider gemini --max-turns 30 "Health check: efferens, judge, paracrine, diapedesis, update-coding-tools.sh, channel, golem-reviewer, importin, bud, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-9846c2] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-614f5a] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-38cb30] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-22622d] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-452519] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:44)
- [!] `golem [t-980ca0] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-078d7a] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-060544] --provider gemini --max-turns 30 "Health check: linkedin-monitor, receptor-scan, efferens, backup-due.sh, dr-sync, circadian-probe.py, golem-daemon-wrapper.sh, wewe-rss-health.py, update-compound-engineering, find. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-27fba1] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-ff944d] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-0e658c] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-4444e6] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a0f9b8] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:45)
- [!] `golem [t-aeb083] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-66493f] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-940e54] --provider gemini --max-turns 30 "Health check: linkedin-monitor, agent-sync.sh, oura-weekly-digest.py, hetzner-bootstrap.sh, secrets-sync, qmd-reindex.sh, plan-exec.deprecated, rotate-logs.py, soma-health, soma-bootstrap. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-475a10] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-d98713] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-bc0335] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-8db045] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3badd9] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:46)
- [!] `golem [t-0a432e] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-4db632] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-2fa1d9] --provider zhipu --max-turns 30 "Health check: soma-snapshot, chromatin-decay-report.py, publish, git-activity, soma-wake, nightly, goose-worker, centrosome, judge, regulatory-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-394473] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-51cf69] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-0ac09c] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-b3557b] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-55842b] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:46)
- [!] `golem [t-de1f10] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-be1848] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b37fbd] --provider gemini --max-turns 30 "Health check: tmux-osc52.sh, orphan-scan, golem-health, search-guard, test-dashboard, start-chrome-debug.sh, commensal, provider-bench, soma-scale, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-89989c] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-f4bd44] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-971629] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-56913b] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-05c708] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:47)
- [!] `golem [t-8485a3] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e58864] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-09ac40] --provider gemini --max-turns 30 "Health check: oura-weekly-digest.py, circadian-probe.py, synthase, methylation, search-guard, pharos-sync.sh, soma-wake, receptor-scan, browse, express. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-df2d5a] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-326b45] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-94fbc7] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-0d122f] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e60282] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:48)
- [!] `golem [t-7626bc] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-675c1a] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-ad3324] --provider gemini --max-turns 30 "Health check: coverage-map, switch-layer, oura-weekly-digest.py, safe_search.py, launchagent-health, transduction-daily-run, generate-solutions-index.py, conftest-gen, rename-plists, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f8ecff] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-6e34df] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-4aceaa] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-be822e] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f176ac] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:49)
- [!] `golem [t-dec107] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c443fe] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-fc5ac4] --provider zhipu --max-turns 30 "Health check: soma-scale, oci-arm-retry, oura-weekly-digest.py, rename-kindle-asins.py, cleanup-stuck, test-fixer, importin, soma-bootstrap, channel, centrosome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-4f8780] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-d6e95c] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-d466df] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-f563d7] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-47ead0] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:50)
- [!] `golem [t-deab6f] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3d0164] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-38380d] --provider gemini --max-turns 30 "Health check: soma-watchdog, weekly-gather, test-fixer, tmux-workspace.py, tm, vesicle, lustro-analyze, complement, update-compound-engineering-skills.sh, demethylase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a6cefc] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-04e62c] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-0b22b0] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-ed9d1e] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d6473a] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:50)
- [!] `golem [t-ead018] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-710385] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-106fae] --provider gemini --max-turns 30 "Health check: perplexity.sh, plan-exec.deprecated, pharos-env.sh, methylation-review, test-fixer, inflammasome-probe, skill-sync, consulting-card.py, bud, receptor-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-21dbb2] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-03738e] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-80cf50] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-9c05b1] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9b7b7e] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:51)
- [!] `golem [t-a89270] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-9695af] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d26a92] --provider gemini --max-turns 30 "Health check: cookie-sync, channel, golem-cost, rename-kindle-asins.py, golem-validate, proteostasis, vesicle, golem-top, queue-gen, compound-engineering-test. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-fdfb6c] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-471069] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-ac0903] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-109357] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-252ff4] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:52)
- [!] `golem [t-c89528] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-325363] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-06b9e2] --provider zhipu --max-turns 30 "Health check: chemoreception.py, secrets-sync, judge, inflammasome-probe, channel, compound-engineering-status, replisome, fix-symlinks, demethylase, council. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8736af] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-4abfec] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-0245ad] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-764790] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fe6cf5] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:52)
- [!] `golem [t-b47e41] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-232c0a] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-a633cb] --provider gemini --max-turns 30 "Health check: legatum-verify, pharos-sync.sh, oci-arm-retry, electroreception, diapedesis, soma-bootstrap, provider-bench, browser, methylation, phagocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f44daa] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-2320fc] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-b0a477] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-6f19d2] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-662aef] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:53)
- [!] `golem [t-5685bb] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-18a898] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-878b9c] --provider gemini --max-turns 30 "Health check: skill-sync, effector-usage, transduction-daily-run, golem-dash, importin, methylation-review, search-guard, bud, inflammasome-probe, golem-top. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-ddbeac] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-321274] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-3b3676] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fcb541] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f24ea7] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:54)
- [!] `golem [t-7cec00] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-f583ea] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-7adf86] --provider gemini --max-turns 30 "Health check: x-feed-to-lustro, agent-sync.sh, coaching-stats, fix-symlinks, assay, grok, cn-route, find, golem-health, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-81a4e2] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-d43d76] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-c58131] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-4a871d] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-315568] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:54)
- [!] `golem [t-2aa52b] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-17eff1] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-b2c39d] --provider zhipu --max-turns 30 "Health check: linkedin-monitor, golem-cost, weekly-gather, tmux-osc52.sh, cytokinesis, legatum, phagocytosis.py, oura-weekly-digest.py, rheotaxis-local, skill-lint. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-5c9e4a] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-75cbd2] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-a4a243] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-14e4ef] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-40eef2] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:55)
- [!] `golem [t-157f7d] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-d97b48] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-a5dff7] --provider gemini --max-turns 30 "Health check: compound-engineering-status, immunosurveillance, skill-search, test-fixer, regulatory-scan, perplexity.sh, auto-update-compound-engineering.sh, chromatin-backup.py, council, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8851b9] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-695a48] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-8972c4] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-18c373] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3e2216] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:56)
- [!] `golem [t-e7d2c5] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-6893b5] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e9554b] --provider gemini --max-turns 30 "Health check: vesicle, chromatin-backup.py, tm, test-dashboard, assay, cleanup-stuck, update-compound-engineering, council, update-coding-tools.sh, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a91a15] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-e92f92] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-d5f19d] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-be144d] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fddfb9] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:56)
- [!] `golem [t-913c9f] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-6a8deb] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-226d16] --provider gemini --max-turns 30 "Health check: pharos-health.sh, importin, plan-exec, chemoreception.py, disk-audit, log-summary, vesicle, transduction-daily-run, lustro-analyze, consulting-card.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-32e66b] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-42fa5a] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-ad436e] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-417a17] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f9eb50] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:57)
- [!] `golem [t-ca8386] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3fa996] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4ebc6f] --provider zhipu --max-turns 30 "Health check: skill-sync, log-summary, cibus.py, exocytosis.py, replisome, diapedesis, rg, ck, tmux-osc52.sh, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-45f3b8] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c72c72] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-d9c842] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-386cfd] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-2279f2] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:58)
- [!] `golem [t-4db48a] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-408190] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-64708c] --provider gemini --max-turns 30 "Health check: lustro-analyze, start-chrome-debug.sh, receptor-health, paracrine, cleanup-stuck, backfill-marks, golem-cost, golem-health, dr-sync, complement. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-dbc52f] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-028b8d] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-5c4a21] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-7bdfde] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e129eb] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:58)
- [!] `golem [t-55f243] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-0ea5d4] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-8c324f] --provider gemini --max-turns 30 "Health check: diapedesis, browser, soma-activate, translocon, judge, coaching-stats, receptor-scan, generate-solutions-index.py, hkicpa, photos.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8426ea] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-12390d] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-502e6a] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-d3bc5c] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d8d1d4] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 15:59)
- [!] `golem [t-36b268] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-eeddf2] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-384864] --provider gemini --max-turns 30 "Health check: pharos-health.sh, chromatin-backup.py, regulatory-capture, capco-prep, rename-plists, backfill-marks, phagocytosis.py, taste-score, commensal, tmux-url-select.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-fedd1e] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e4bc59] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-a0a5da] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-253a49] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1028d1] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:00)
- [!] `golem [t-aa489f] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-50aa44] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-41bcaf] --provider zhipu --max-turns 30 "Health check: council, phagocytosis.py, golem-validate, grep, rheotaxis, qmd-reindex.sh, update-coding-tools.sh, commensal, gemmation-env, start-chrome-debug.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-d86cde] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-667cff] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-e3d623] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-cf267d] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-dd251b] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:00)
- [!] `golem [t-f7bbc9] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-eb9ecc] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-5d5488] --provider gemini --max-turns 30 "Health check: complement, replisome, rg, vesicle, soma-health, effector-usage, rename-plists, photos.py, update-compound-engineering, oura-weekly-digest.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-770677] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-998226] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-38bcb7] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-c0ba9a] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-90e765] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:01)
- [!] `golem [t-063949] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-ce2263] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1ab69a] --provider gemini --max-turns 30 "Health check: tmux-url-select.sh, methylation-review, rotate-logs.py, soma-wake, rename-kindle-asins.py, plan-exec.deprecated, compound-engineering-status, search-guard, skill-search, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-2eafed] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-e9e495] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-80a926] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-73bf8d] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-03d973] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:02)
- [!] `golem [t-4a2af0] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-0cc4ba] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e51a6b] --provider gemini --max-turns 30 "Health check: plan-exec.deprecated, update-compound-engineering-skills.sh, pharos-env.sh, mismatch-repair, immunosurveillance, bud, receptor-scan, replisome, demethylase, soma-pull. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1c3095] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ff01c4] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-33515b] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-6fe553] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e866de] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:02)
- [!] `golem [t-34f2c0] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5bd497] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-81a3d0] --provider zhipu --max-turns 30 "Health check: telophase, soma-bootstrap, log-summary, queue-stats, tmux-osc52.sh, respirometry, rheotaxis, lacuna.py, demethylase, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-faf289] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-6aab57] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-d78283] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-067d77] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5047d5] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:03)
- [!] `golem [t-3f89fc] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-bf3c18] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-de7757] --provider gemini --max-turns 30 "Health check: golem-review, legatum-verify, auto-update-compound-engineering.sh, x-feed-to-lustro, rotate-logs.py, electroreception, golem, grok, immunosurveillance.py, golem-cost. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-6f0c58] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-068a44] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-47a77c] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-9a4216] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a44833] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:04)
- [!] `golem [t-9b4c89] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5acadd] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-de52b8] --provider gemini --max-turns 30 "Health check: hetzner-bootstrap.sh, coverage-map, x-feed-to-lustro, grep, test-fixer, proteostasis, cn-route, publish, inflammasome-probe, browse. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1e1c3a] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-a6e375] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-e5b366] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-fe088d] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-9ce446] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:04)
- [!] `golem [t-84a0c1] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-392cf6] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1074dc] --provider gemini --max-turns 30 "Health check: switch-layer, chromatin-backup.py, linkedin-monitor, lustro-analyze, engram, soma-scale, safe_search.py, pharos-sync.sh, plan-exec.deprecated, taste-score. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c81846] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-f929e2] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-ca9590] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-8b740a] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4207b1] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:05)
- [!] `golem [t-1baa02] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-103da0] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-6d78cd] --provider zhipu --max-turns 30 "Health check: dr-sync, test-dashboard, synthase, council, gemmation-env, safe_rm.py, plan-exec, pinocytosis, bud, legatum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f4b75f] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-828db7] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-686724] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-886d6c] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-8f6ab6] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:06)
- [!] `golem [t-e31cb6] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-67ec5b] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-bf76e0] --provider gemini --max-turns 30 "Health check: backup-due.sh, chat_history.py, golem-review, agent-sync.sh, soma-bootstrap, electroreception, photos.py, find, cytokinesis, lustro-analyze. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-722552] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-fe6e97] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-8f2b7c] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-8e4fbf] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cc7b0a] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:06)
- [!] `golem [t-dbd5ae] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-2ee44d] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1607e2] --provider gemini --max-turns 30 "Health check: queue-balance, oura-weekly-digest.py, synthase, cibus.py, auto-update-compound-engineering.sh, tmux-workspace.py, channel, poiesis, perplexity.sh, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-78ea59] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-c0b6ff] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-eed2c5] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-14c970] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-cf8ec5] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:07)
- [!] `golem [t-44bb6d] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-7c3884] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d147f9] --provider gemini --max-turns 30 "Health check: methylation-review, immunosurveillance, agent-sync.sh, cibus.py, chromatin-decay-report.py, golem-validate, rheotaxis, importin, launchagent-health, chat_history.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-fc2dd3] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-6caa07] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-a718ab] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-c38632] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-257f61] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:08)
- [ ] `golem [t-a1a6cb] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a7b5a3] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-d1ccec] --provider zhipu --max-turns 30 "Health check: coaching-stats, immunosurveillance, overnight-gather, skill-search, receptor-health, transduction-daily-run, gemmule-sync, poiesis, immunosurveillance.py, secrets-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8e6c5c] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-b9bee2] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-9520ef] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-78676f] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-ae8cde] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:08)
- [!] `golem [t-a1d53b] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-fa7497] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-643b35] --provider gemini --max-turns 30 "Health check: engram, commensal, vesicle, express, cytokinesis, pharos-env.sh, wacli-ro, channel, search-guard, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-a750b7] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-3b41d4] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-1f3c5e] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-680b6a] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f1356c] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:09)
- [ ] `golem [t-8ea565] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-5e4b50] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-916465] --provider gemini --max-turns 30 "Health check: golem-daemon-wrapper.sh, poiesis, compound-engineering-test, secrets-sync, plan-exec, methylation, queue-balance, centrosome, chat_history.py, cookie-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c6d691] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-754ff4] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-0e0887] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-f55d9b] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-112119] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:10)
- [!] `golem [t-019097] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-a741b7] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1fcce4] --provider gemini --max-turns 30 "Health check: hetzner-bootstrap.sh, gemmation-env, pulse-review, capco-prep, skill-lint, lacuna, golem-top, dr-sync, skill-search, tmux-workspace.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-a9a571] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-f2ad8b] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [ ] `golem [t-7d11e4] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-1787f1] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-f46c4c] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:10)
- [ ] `golem [t-68b463] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c9d58e] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-cf2b3d] --provider zhipu --max-turns 30 "Health check: browser, cookie-sync, quorum, legatum, sortase, soma-health, search-guard, soma-scale, centrosome, golem-daemon. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-c7fcc9] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-e88edb] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-722000] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-ce42e7] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-05713f] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:11)
- [!] `golem [t-af8762] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-e10e7b] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-2c9481] --provider gemini --max-turns 30 "Health check: tmux-osc52.sh, auto-update-compound-engineering.sh, hetzner-bootstrap.sh, agent-sync.sh, safe_search.py, browser, receptor-scan, qmd-reindex.sh, quorum, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-202eb9] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-ce270b] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-570465] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-47c413] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-622bbb] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:12)
- [ ] `golem [t-5c49bc] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-13028e] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-4c9561] --provider gemini --max-turns 30 "Health check: grep, update-compound-engineering, provider-bench, test-dashboard, orphan-scan, wacli-ro, immunosurveillance.py, golem-top, effector-usage, chemoreception.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-b6832a] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-87248e] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-43452e] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-aa55a9] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-22468f] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:12)
- [!] `golem [t-4104b3] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-8c6c7e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-206d34] --provider gemini --max-turns 30 "Health check: log-summary, chromatin-decay-report.py, golem-top, plan-exec, agent-sync.sh, respirometry, linkedin-monitor, assay, golem-daemon, tmux-osc52.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-2b3f02] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-11d873] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-372495] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-ead0a6] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d3a31a] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:13)
- [ ] `golem [t-7d827b] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-58cec3] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-35e34d] --provider zhipu --max-turns 30 "Health check: safe_rm.py, agent-sync.sh, golem, wacli-ro, browser, hkicpa, ck, gemmation-env, backup-due.sh, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-82997c] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-5605ab] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-0d0543] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-3518bc] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-63dc9e] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:15)
- [!] `golem [t-2dd235] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-665a97] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-dd1098] --provider gemini --max-turns 30 "Health check: commensal, search-guard, plan-exec.deprecated, express, pulse-review, lacuna, weekly-gather, rheotaxis, compound-engineering-test, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-54ae78] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-8ee61e] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-d8d3c8] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-58f871] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-bd9bf6] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:15)
- [ ] `golem [t-f957b1] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-d9bab7] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-06baeb] --provider gemini --max-turns 30 "Health check: auto-update-compound-engineering.sh, tm, overnight-gather, immunosurveillance.py, compound-engineering-test, cg, grep, golem-reviewer, gemmule-sync, channel. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-2cd1c8] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [ ] `golem [t-8b3e73] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-fe5985] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-db4757] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-bc2c81] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:16)
- [!] `golem [t-0e1d29] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-149820] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-ba1bb9] --provider gemini --max-turns 30 "Health check: soma-clean, browse, golem-health, lacuna.py, find, auto-update-compound-engineering.sh, gap_junction_sync, git-activity, diapedesis, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-297294] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-743b25] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-ce70e4] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-099897] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0928db] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:17)
- [ ] `golem [t-3cc090] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-fffe3a] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-b35811] --provider zhipu --max-turns 30 "Health check: golem-health, update-compound-engineering-skills.sh, pharos-env.sh, tmux-osc52.sh, fix-symlinks, chemoreception.py, log-summary, golem, rotate-logs.py, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-feae3a] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-9a36e0] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-541637] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-f8a685] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-227f83] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:17)
- [!] `golem [t-f21cad] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-fb3461] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e1a299] --provider gemini --max-turns 30 "Health check: efferens, tmux-url-select.sh, quorum, golem-review, paracrine, hkicpa, test-fixer, gemmule-sync, test-dashboard, auto-update-compound-engineering.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-79d041] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-98f96e] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-c568ad] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-5124c6] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-b53b49] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:18)
- [ ] `golem [t-774fa9] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-b1fb0b] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-22290c] --provider gemini --max-turns 30 "Health check: backup-due.sh, cleanup-stuck, test-spec-gen, compound-engineering-test, bud, qmd-reindex.sh, synthase, skill-search, golem-reviewer, chromatin-backup.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-d710fb] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-5a9956] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-d359ce] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-6c22c0] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-7bee36] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:19)
- [!] `golem [t-340c30] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-ee2527] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-dd2e74] --provider gemini --max-turns 30 "Health check: perplexity.sh, hetzner-bootstrap.sh, golem-review, find, linkedin-monitor, coverage-map, soma-pull, queue-stats, auto-update-compound-engineering.sh, electroreception. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-bd6ac1] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-df6da7] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-e4d02f] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-c756fd] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab8052] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:19)
- [ ] `golem [t-10b7b4] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-acee61] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-016313] --provider zhipu --max-turns 30 "Health check: soma-snapshot, poiesis, rename-plists, grok, qmd-reindex.sh, immunosurveillance, coverage-map, chromatin-decay-report.py, consulting-card.py, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-1bf6a4] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-359de6] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-f9659e] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-c15ff4] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-5860de] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:20)
- [!] `golem [t-fa02d3] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-4000ff] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-bdcbf3] --provider gemini --max-turns 30 "Health check: provider-bench, respirometry, quorum, golem-top, complement, bud, update-coding-tools.sh, rheotaxis, rg, gap_junction_sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-51db76] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-333eb9] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-84ab26] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-d826f8] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-ab3085] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:21)
- [ ] `golem [t-33027c] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7b1151] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-0345d9] --provider gemini --max-turns 30 "Health check: search-guard, cookie-sync, compound-engineering-status, compound-engineering-test, tm, cn-route, chromatin-backup.py, respirometry, tmux-workspace.py, golem-reviewer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e69f95] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [ ] `golem [t-bd3e5e] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-0f6745] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-f2e2e1] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-350b88] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:22)
- [!] `golem [t-dc9c1e] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-a534bd] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-864ac9] --provider gemini --max-turns 30 "Health check: importin, dr-sync, overnight-gather, weekly-gather, electroreception, efferens, methylation, soma-wake, test-dashboard, switch-layer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-72861a] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-d65619] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-763247] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-b89e76] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-cde7c4] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:23)
- [ ] `golem [t-92b3f5] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-323155] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-e66fb1] --provider zhipu --max-turns 30 "Health check: hkicpa, soma-snapshot, rheotaxis-local, start-chrome-debug.sh, engram, git-activity, launchagent-health, grok, golem-dash, telophase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-bb63bb] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-332c19] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-5d32bc] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3f69e8] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-a79729] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:23)
- [!] `golem [t-439068] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-70065a] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-55d57f] --provider gemini --max-turns 30 "Health check: switch-layer, proteostasis, chat_history.py, soma-activate, auto-update-compound-engineering.sh, orphan-scan, soma-pull, complement, rename-kindle-asins.py, dr-sync. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-642720] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-d6819a] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-5541da] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-55d31f] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-d9ec29] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:24)
- [ ] `golem [t-bc2a5a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7bf3ee] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-d69057] --provider gemini --max-turns 30 "Health check: lustro-analyze, golem-daemon, rotate-logs.py, skill-search, receptor-scan, translocon, capco-prep, qmd-reindex.sh, conftest-gen, weekly-gather. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-e702ce] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-3c10cf] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-7bebf3] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-5ac279] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-db2b95] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:25)
- [!] `golem [t-ab2b52] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-e59e32] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-1356d1] --provider gemini --max-turns 30 "Health check: update-compound-engineering, cytokinesis, tmux-url-select.sh, electroreception, cibus.py, golem, regulatory-scan, respirometry, gemmule-sync, provider-bench. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-b64247] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-81d628] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-0c63b7] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-471797] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-923acd] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:25)
- [ ] `golem [t-29b603] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-694294] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-05dad3] --provider zhipu --max-turns 30 "Health check: golem-cost, test-fixer, demethylase, oura-weekly-digest.py, skill-search, git-activity, perplexity.sh, council, rheotaxis-local, wewe-rss-health.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-a7b721] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [ ] `golem [t-383cec] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-0d1033] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-7ea3a7] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-a7e2f0] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:26)
- [!] `golem [t-fa1e81] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-b5bbbc] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-721b12] --provider gemini --max-turns 30 "Health check: ck, efferens, lustro-analyze, cookie-sync, oura-weekly-digest.py, demethylase, weekly-gather, secrets-sync, oci-arm-retry, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-ed4273] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-d078a0] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-b4cbd1] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-1e4c68] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-191c39] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:27)
- [ ] `golem [t-a02873] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-afbf28] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-011b94] --provider gemini --max-turns 30 "Health check: queue-stats, find, linkedin-monitor, pharos-env.sh, tmux-url-select.sh, nightly, poiesis, soma-clean, golem-top, tm. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-94223a] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-d6a6c7] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-49b62e] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-bab3a7] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-6819e5] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:27)
- [!] `golem [t-916177] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-efaf80] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-3f1eff] --provider gemini --max-turns 30 "Health check: lacuna.py, fix-symlinks, inflammasome-probe, secrets-sync, grok, queue-balance, vesicle, mitosis-checkpoint.py, pharos-env.sh, backfill-marks. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-4e00ad] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-d584a5] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-fa0ded] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-823ef1] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-45d201] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:28)
- [ ] `golem [t-162c57] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-888445] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-95e921] --provider zhipu --max-turns 30 "Health check: grok, switch-layer, ck, orphan-scan, golem-top, coverage-map, soma-snapshot, cn-route, replisome, engram. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-f3eafd] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-1ca3c1] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-36af34] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-02201b] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-5ce644] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:29)
- [!] `golem [t-ce7017] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-fac9ce] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-c8af62] --provider gemini --max-turns 30 "Health check: oci-arm-retry, cleanup-stuck, tmux-osc52.sh, pulse-review, golem-top, immunosurveillance.py, tm, tmux-url-select.sh, goose-worker, lysis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-70e788] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-a5ab65] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-929b4d] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-07d6d6] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a89e22] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:29)
- [ ] `golem [t-7c4bd2] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7d81e9] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-e59bd9] --provider gemini --max-turns 30 "Health check: auto-update-compound-engineering.sh, overnight-gather, soma-health, receptor-scan, test-dashboard, oura-weekly-digest.py, golem-top, golem-reviewer, secrets-sync, cytokinesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-bdebed] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-123823] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-248ffd] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-ee66b3] --provider gemini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-4d1d3a] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:30)
- [!] `golem [t-b851bb] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-7b9be4] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-78e9cb] --provider gemini --max-turns 30 "Health check: chat_history.py, golem-top, soma-clean, chromatin-backup.sh, agent-sync.sh, x-feed-to-lustro, ck, disk-audit, transduction-daily-run, sortase. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-799bfb] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-591b5f] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-ca2c79] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-92fed9] --provider gemini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-70e9a9] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:31)
- [ ] `golem [t-f9b2ec] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-7fc40e] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-8c9025] --provider zhipu --max-turns 30 "Health check: legatum-verify, receptor-health, soma-activate, fix-symlinks, circadian-probe.py, log-summary, x-feed-to-lustro, cn-route, soma-scale, grep. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-205360] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-1854f9] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e08568] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-53d3c1] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-5f5674] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:31)
- [!] `golem [t-e01958] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-49b023] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4905ca] --provider gemini --max-turns 30 "Health check: judge, x-feed-to-lustro, cytokinesis, goose-worker, commensal, translocon, engram, receptor-health, methylation, inflammasome-probe. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-73f6da] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-8dfb35] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-09d8f2] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-7864e8] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-0051a7] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:32)
- [ ] `golem [t-23fdd3] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-110bcd] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-a09f88] --provider gemini --max-turns 30 "Health check: backfill-marks, tm, proteostasis, soma-activate, pharos-env.sh, transduction-daily-run, cytokinesis, coaching-stats, chromatin-backup.sh, quorum. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-624d45] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-be2ef7] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-ff2690] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-f7f343] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-9f4bb9] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:32)
- [!] `golem [t-52246f] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-1808a9] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-c75121] --provider gemini --max-turns 30 "Health check: commensal, oci-arm-retry, chromatin-backup.sh, receptor-scan, electroreception, replisome, pulse-review, importin, golem-validate, rg. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-de9d5e] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-795f33] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-20444d] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-de09d3] --provider gemini --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-fdbb01] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:33)
- [ ] `golem [t-2bc127] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-4c0664] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-41ba30] --provider zhipu --max-turns 30 "Health check: cibus.py, vesicle, soma-pull, demethylase, soma-watchdog, cytokinesis, goose-worker, pulse-review, switch-layer, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-16e09d] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-623bcf] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-e3e6a6] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-f54c96] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-7e2662] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:34)
- [!] `golem [t-c88791] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-d2d39e] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-d9a9e0] --provider gemini --max-turns 30 "Health check: fix-symlinks, channel, lysis, circadian-probe.py, ck, test-dashboard, agent-sync.sh, soma-wake, gap_junction_sync, poiesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-ee59a8] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-dc7d7d] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-daa395] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-b5b00f] --provider gemini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-460f92] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:34)
- [ ] `golem [t-fbd875] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-25a291] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-599411] --provider gemini --max-turns 30 "Health check: commensal, chat_history.py, lacuna, council, golem-reviewer, pharos-env.sh, wacli-ro, overnight-gather, regulatory-scan, perplexity.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-30404e] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-917167] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-81e276] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-069984] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-013b25] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:35)
- [!] `golem [t-a289e6] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-4e6661] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-3cd869] --provider gemini --max-turns 30 "Health check: chemoreception.py, autoimmune.py, wacli-ro, transduction-daily-run, tmux-workspace.py, consulting-card.py, engram, generate-solutions-index.py, mismatch-repair, rheotaxis-local. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-21c812] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-544429] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-86bd0f] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-076717] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1664a3] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:35)
- [ ] `golem [t-a22abb] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-4cbc61] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-d8f473] --provider zhipu --max-turns 30 "Health check: transduction-daily-run, browse, chat_history.py, test-fixer, golem-daemon, golem-dash, cytokinesis, mismatch-repair, client-brief, judge. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-8839b5] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [ ] `golem [t-4cefba] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-e8f1ff] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-255c15] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-e978ec] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:36)
- [!] `golem [t-3f3cd0] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-a4f878] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-ad4ec1] --provider gemini --max-turns 30 "Health check: rg, chromatin-backup.sh, browse, linkedin-monitor, soma-bootstrap, immunosurveillance.py, generate-solutions-index.py, provider-bench, gemmation-env, lysis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-62d671] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-5e32e8] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-5843e0] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-def3d8] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-02c270] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:37)
- [ ] `golem [t-c4853d] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-c77ed8] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-93d301] --provider gemini --max-turns 30 "Health check: coverage-map, oci-arm-retry, diapedesis, test-spec-gen, tmux-osc52.sh, golem-daemon, agent-sync.sh, cleanup-stuck, grok, auto-update-compound-engineering.sh. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-4a953d] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [ ] `golem [t-d357b1] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-11a0cd] --provider gemini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-87c7e5] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-75d417] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:37)
- [!] `golem [t-581d4f] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-52ed5d] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-15825b] --provider gemini --max-turns 30 "Health check: goose-worker, golem, golem-validate, circadian-probe.py, vesicle, queue-stats, soma-snapshot, soma-health, plan-exec.deprecated, test-fixer. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-7958ff] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-d4faf4] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-9f80ed] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-c62787] --provider gemini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-735734] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:38)
- [ ] `golem [t-ca25c3] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-95a8e8] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-31d31a] --provider zhipu --max-turns 30 "Health check: council, lysis, exocytosis.py, centrosome, poiesis, grep, respirometry, skill-lint, methylation-review, pulse-review. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-10d1a2] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-45ee0d] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-527f61] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-6886b2] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-087f5f] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:39)
- [!] `golem [t-8cc4d6] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-27c9e2] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-e8b1b9] --provider gemini --max-turns 30 "Health check: find, channel, nightly, generate-solutions-index.py, receptor-scan, queue-stats, receptor-health, pharos-sync.sh, rg, skill-search. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-14c7fb] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-c65fd1] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-c620de] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-6932ca] --provider gemini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-12dcbf] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:39)
- [ ] `golem [t-647959] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-e8e7dc] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-9a28ed] --provider gemini --max-turns 30 "Health check: browse, diapedesis, rheotaxis, regulatory-capture, lacuna, assay, overnight-gather, golem-cost, orphan-scan, safe_search.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-861f6d] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-67cee1] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-39bc39] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-8a825e] --provider gemini --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-fd3444] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:40)
- [!] `golem [t-c4f526] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-e0dbe0] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-3b993a] --provider gemini --max-turns 30 "Health check: rheotaxis, cleanup-stuck, engram, grep, transduction-daily-run, backfill-marks, immunosurveillance, orphan-scan, assay, commensal. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-2b0ff6] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-c392c4] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-07a20b] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-37777f] --provider gemini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-a4d12e] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:41)
- [ ] `golem [t-8ad577] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-29d2f3] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-946314] --provider zhipu --max-turns 30 "Health check: exocytosis.py, golem-top, immunosurveillance.py, perplexity.sh, regulatory-capture, queue-gen, importin, safe_rm.py, coverage-map, goose-worker. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-07c809] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-62011c] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-16f98f] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-4ab3ca] --provider gemini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-6cd42f] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:41)
- [!] `golem [t-4ab9c5] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-7f1029] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-7443fc] --provider gemini --max-turns 30 "Health check: goose-worker, compound-engineering-status, golem-top, skill-lint, circadian-probe.py, soma-activate, tmux-url-select.sh, wacli-ro, weekly-gather, skill-search. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-c0b9d1] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-19842e] --provider gemini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [ ] `golem [t-214e7b] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-de6af1] --provider gemini --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-4432bb] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:42)
- [ ] `golem [t-596a4a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-952144] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-50083b] --provider gemini --max-turns 30 "Health check: pulse-review, complement, golem-dash, browser, disk-audit, effector-usage, immunosurveillance, rheotaxis-local, transduction-daily-run, soma-watchdog. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-13f70c] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-9debe6] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-2779d9] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-8c0299] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-980eaf] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:43)
- [!] `golem [t-764db2] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-6f5470] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-c5ef31] --provider gemini --max-turns 30 "Health check: methylation, immunosurveillance.py, plan-exec, legatum, wewe-rss-health.py, queue-gen, wacli-ro, soma-pull, agent-sync.sh, soma-snapshot. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-9e41f0] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-71ed83] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-3af6b9] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3c16bc] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-c80e91] --provider gemini --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:43)
- [ ] `golem [t-a60e37] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-0ee71c] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-bb69d8] --provider zhipu --max-turns 30 "Health check: pinocytosis, goose-worker, soma-snapshot, cg, gap_junction_sync, soma-watchdog, coaching-stats, chemoreception.py, electroreception, linkedin-monitor. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-105023] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-828f5e] --provider gemini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [!] `golem [t-0507bb] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-ab9663] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-747178] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:44)
- [!] `golem [t-b1eced] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-02dd75] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-7b3485] --provider gemini --max-turns 30 "Health check: compound-engineering-status, soma-pull, rename-kindle-asins.py, electroreception, hetzner-bootstrap.sh, start-chrome-debug.sh, synthase, rg, nightly, test-spec-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-72a11f] --provider zhipu --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a73f07] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-3835fe] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-7dc892] --provider gemini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-426e05] --provider gemini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-d897fe] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:45)
- [!] `golem [t-a56584] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-19b971] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-cea82d] --provider gemini --max-turns 30 "Health check: paracrine, soma-pull, git-activity, x-feed-to-lustro, publish, auto-update-compound-engineering.sh, phagocytosis.py, safe_rm.py, rheotaxis, effector-usage. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-dd888f] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-8f87f6] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-f1beb3] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/substrate.py. Mock external calls. Write assays/test_metabolism_substrate.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-47384f] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/talking_points.py. Mock external calls. Write assays/test_organelles_talking_points.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-d111ae] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-3a7d70] --provider gemini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-baacb1] --provider gemini --max-turns 30 "Write tests for effectors/oci-arm-retry. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a1ef6d] --provider gemini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-3d855c] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c43ef1] --provider gemini --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-d8f5a7] --provider gemini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [!] `golem [t-f78632] --provider gemini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-8ff51e] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [!] `golem [t-720ee6] --provider gemini --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-1bb250] --provider gemini --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 16:45)
- [ ] `golem [t-a82e47] --provider gemini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-a9f0a5] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [ ] `golem [t-2e505c] --provider zhipu --max-turns 30 "Health check: channel, weekly-gather, effector-usage, circadian-probe.py, rename-plists, soma-snapshot, agent-sync.sh, importin, methylation-review, soma-wake. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-da856e] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/turgor.py. Mock external calls. Write assays/test_enzymes_turgor.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-c3212b] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/translocon_metrics.py. Mock external calls. Write assays/test_organelles_translocon_metrics.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-897726] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-c83170] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/demethylase.py. Mock external calls. Write assays/test_enzymes_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-761387] --provider gemini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/gradient_sense.py. Mock external calls. Write assays/test_organelles_gradient_sense.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-41d8fb] --provider gemini --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-946da8] --provider gemini --max-turns 30 "Write tests for effectors/fix-symlinks. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-e215af] --provider zhipu --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9f5936] --provider gemini --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-343b81] --provider gemini --max-turns 30 "Write tests for effectors/soma-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-1d74a0] --provider gemini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-6f05d4] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-034f19] --provider gemini --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [ ] `golem [t-0f5421] --provider gemini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`
## Done (2026-03-31)


### Build — circadian-aware auto-requeue

- [x] `golem [t-313701] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Find the auto_requeue function. Enhance it to be circadian-aware: (1) Read ~/germline/loci/priorities.md for current north stars and deadlines. (2) Check current hour (HKT). (3) Night (22-06): weight toward tests 50%, hardening 30%, consulting 20%. (4) Morning (06-09): weight toward consulting IP 50%, digests 30%, fixes 20%. (5) Daytime (09-22): weight toward fixes 40%, features 30%, consulting 30%. (6) If priorities.md mentions a deadline within 3 days: boost that category to 60%. Write the priority logic as a separate function circadian_priorities() -> dict[str, float]. Write tests. Run uv run pytest. Commit."`

- [ ] `golem [t-35fcf3] --provider zhipu --max-turns 30 "Create ~/germline/loci/priorities.md with this structure: north_stars (3 items with deadline), current_focus (what to prioritize now), blocked (what to skip). Initial content: (1) Capco readiness — deadline Apr 8 — consulting IP, regulatory briefs, case studies (2) Organism robustness — ongoing — fix tests, effector health (3) Consulting arsenal — ongoing — frameworks, templates. CC will update this file each session."`


### Build — wire circulation into golem-daemon

- [x] `golem [t-0263fc] --provider zhipu --max-turns 50 "Read metabolon/organelles/circulation.py (535 lines). Read effectors/golem-daemon auto_requeue function. Design integration: (1) Create effectors/circulate-dispatch as Python. It runs circulation.select_goals() to get intelligent goal list, then converts each goal into a golem queue entry in loci/golem-queue.md. Uses symbiont.transduce_safe() for CC-powered goal selection (reads Tonus.md + priorities.md + calendar). Writes queue entries. Usage: circulate-dispatch [--max-goals 8]. (2) Wire this into golem-daemon auto_requeue: when queue < 50, call circulate-dispatch instead of random task generation. Write tests. Run uv run pytest. Commit."`

- [!] `golem [t-0ed7c8] --provider gemini --max-turns 40 "Read metabolon/organelles/circulation.py. Extract the evaluate() and compound() functions into a standalone effectors/circulate-evaluate as Python. After golem tasks complete, this reads results and: (1) updates coaching notes if new failure patterns found, (2) updates priorities.md if goals were completed, (3) writes a cycle report. Called by golem-reviewer periodically. Write tests. Run uv run pytest. Commit." (retry)`


### High-priority — infra + task IDs (queued by CC)

#### Add task IDs to golem-daemon
- [ ] `golem [t-19855e] --provider gemini --max-turns 50 "Read effectors/golem-daemon. Add unique task IDs: 1) In parse_queue(), generate a short ID (t-xxxx, 6 hex chars) for each task that doesn't have one — prepend it inside the backtick like 'golem [t-a7f3] --provider ...'. 2) In run_golem(), extract the ID and pass it as env var GOLEM_TASK_ID. 3) In the JSONL output, add a 'task_id' field. 4) In mark_done/mark_failed, include the task ID in the result annotation. 5) In cmd_status, show task IDs of running tasks. Write tests in assays/test_golem_task_ids.py. Run uv run pytest on the test file. Commit." (retry)`

#### Fix all from __future__ duplicate bugs
- [x] `golem --provider zhipu --max-turns 30 "Find ALL Python files under /home/terry/germline/ and /home/terry/.claude/hooks/ that have 'from __future__ import annotations' appearing more than once. For each file, remove the SECOND occurrence (keep only the first at the top). Verify with py_compile. Commit."`

#### Fix collection errors blocking test suite
- [x] `golem --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common causes: hardcoded /Users/terry paths, bad imports, duplicate from __future__, missing modules. Run --co again until 0 errors. Commit."`

#### Fix top 10 failing tests
- [!] `golem [t-58b1ff] --provider gemini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -10. For each of the top 10 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`

### Consulting IP — Capco prep (T-7)

#### AI risk management consulting cards
- [x] `golem --provider infini --max-turns 50 "Create 5 consulting insight cards for a management consultant joining Capco (financial services consulting). Topics: 1) AI model risk management in banking 2) LLM deployment regulatory expectations 3) AI vendor due diligence for banks 4) GenAI policy template for bank employees 5) AI incident response for financial services. Each card: 300+ words, problem statement, approach, key considerations, regulatory references. Write each to ~/epigenome/chromatin/euchromatin/consulting/cards/<slug>.md. Commit."`

#### HK regulatory landscape briefing
- [ ] `golem [t-211b2c] --provider zhipu --max-turns 40 "Write a comprehensive briefing on Hong Kong financial regulation for AI/technology: HKMA, SFC, IA key circulars and expectations around AI adoption in banking, insurance, securities. Include HKMA's Supervisory Policy Manual modules on technology risk (TM-E-1, OR-1). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hk-ai-regulatory-landscape.md. 500+ words. Commit." (retry)`

### System hardening

#### Add periodic rsync from Mac to gemmule
- [x] `golem [t-0f22c4] --provider zhipu --max-turns 30 "Create effectors/gemmule-sync as a Python script. It should: 1) rsync terry@100.94.27.93:~/epigenome/chromatin/ ~/epigenome/chromatin/ 2) rsync terry@100.94.27.93:~/notes/ ~/notes/ 3) rsync terry@100.94.27.93:~/code/acta/ ~/code/acta/ 4) Log results to ~/.local/share/vivesca/gemmule-sync.log. Add --dry-run flag. Make it idempotent. Write tests. Commit."`

#### Scan and fix hardcoded macOS paths
- [!] `golem [t-f031c4] --provider gemini --max-turns 30 "Find ALL files in ~/germline/ containing /Users/terry. Replace with Path.home() (Python) or $HOME (shell). Verify nothing breaks. Commit." (retry)`

### Research — workflow orchestration for golem-daemon

#### Landscape: Temporal vs alternatives for AI task orchestration
- [x] `golem --provider zhipu --max-turns 50 "Research workflow orchestration systems for replacing a custom Python task queue daemon that dispatches AI coding agents (Claude Code). Current system: markdown-file queue, 30 concurrent workers across 3 providers, retry logic, auto-commit. Requirements: task IDs, visibility/UI, durable execution, heartbeating, concurrency control, Python SDK. Compare: 1) Temporal.io — self-hosted vs Cloud, Python SDK maturity, resource footprint 2) Hatchet — AI-native, lighter weight 3) Inngest — serverless model 4) Prefect/Dagster — data pipeline focused but flexible 5) BullMQ/Celery — simpler task queues 6) Plain PostgreSQL+LISTEN/NOTIFY — minimal infra. For each: install complexity, resource overhead (RAM/CPU), cost (self-hosted vs cloud), Python SDK quality, UI/visibility, suitability for 20-50 concurrent AI agent tasks. Also note: the user is a consultant at Capco (financial services) — which systems have enterprise/banking adoption? Write findings to ~/epigenome/chromatin/euchromatin/consulting/cards/workflow-orchestration-landscape.md. 500+ words with recommendation. Commit."`

### Resilience — vivesca self-healing and hardening

#### Daemon auto-restart via supervisor
- [ ] `golem [t-fd4826] --provider gemini --max-turns 30 "Read the supervisor config for golem-daemon. If none exists, check /etc/supervisor/conf.d/. Create or fix a supervisor config at /etc/supervisor/conf.d/golem-daemon.conf that: 1) runs 'python3 /home/terry/germline/effectors/golem-daemon start --foreground' as user terry 2) auto-restarts on crash 3) sets environment from /home/terry/.env.fly (source it in a wrapper script if needed) 4) logs stdout/stderr to /home/terry/.local/share/vivesca/. Write tests. Commit." (retry)`

#### Git auto-backup — push epigenome to remote
- [x] `golem [t-e72448] --provider infini --max-turns 40 "The epigenome repo at ~/epigenome has 15K+ chromatin files that are NOT tracked in git. This caused data loss during a disk-full incident. Fix: 1) cd ~/epigenome && git add chromatin/ 2) Check .gitignore doesn't exclude chromatin 3) git commit -m 'backup: track all chromatin files' 4) git push. If push fails due to size, set up git-lfs for large files. Also add a .gitattributes for *.md files if > 1MB. Commit."`

#### Provider failover in golem
- [x] `golem [t-31363b] --provider zhipu --max-turns 40 "Read effectors/golem (the golem script, not golem-daemon). Add provider failover: if the primary provider returns HTTP 429 (rate limit) or 5xx, automatically retry with the next provider in priority order (zhipu -> infini -> volcano). Add a --fallback flag to opt-in. Log the failover. Write tests in assays/test_golem_failover.py. Commit." (retry)`

#### Watchdog — detect and fix stuck golems
- [!] `golem [t-cb5765] --provider gemini --max-turns 40 "Read effectors/golem-daemon. Add a watchdog: every 5 poll cycles, check if any running golem has exceeded GOLEM_TIMEOUT (1800s). If so: 1) kill the subprocess 2) mark task as failed with 'timeout' 3) log a warning. Currently the ThreadPoolExecutor handles timeouts but subprocess.run may hang. Add subprocess-level kill via os.kill(). Write tests. Commit."`

#### Graceful shutdown — commit before dying
- [x] `golem [t-ad7830] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Improve the SIGTERM handler: on shutdown signal, 1) stop accepting new tasks 2) wait up to 60s for running golems to finish 3) auto-commit any uncommitted work 4) push to remote 5) then exit. Currently it just removes the pidfile. Write tests. Commit."`

#### Config validation on daemon start
- [x] `golem [t-fc42d9] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a validate_config() function that runs on startup and checks: 1) QUEUE_FILE exists and is readable 2) all providers in PROVIDER_LIMITS have valid API keys in env 3) git repo is clean enough to commit 4) disk space > 2GB 5) uv sync is up to date (uv run python -c 'import metabolon'). If any check fails, log a clear error and exit 1. Write tests. Commit."`

#### Self-healing — auto-fix common breakages
- [ ] `golem [t-9eecea] --provider zhipu --max-turns 50 "Create effectors/mismatch-repair as a Python script (biology: mismatch repair fixes DNA errors). It should detect and fix common vivesca breakages: 1) Duplicate 'from __future__ import annotations' in any .py file under ~/germline/ or ~/.claude/hooks/ — remove the second occurrence 2) Hardcoded /Users/terry paths — replace with Path.home() 3) Broken symlinks in ~/ — report them 4) Stale .pyc files — delete 5) pytest collection errors — run --co and report. Add --fix flag to auto-repair vs --check for dry-run. Write tests in assays/test_mismatch_repair.py. Commit."`

#### Network resilience — retry git operations
- [!] `golem [t-9dffa6] --provider gemini --max-turns 30 "Read effectors/golem-daemon, specifically auto_commit(). Add retry logic: if git push fails (network error), retry 3 times with 30s backoff. If all retries fail, log error but don't crash daemon. Also add: if git pull fails at startup, continue with local state rather than crashing. Write tests. Commit." (retry)`

#### Backup marks/memory to git
- [ ] `golem [t-a6dcae] --provider gemini --max-turns 30 "The epigenome/marks directory contains critical behavioral memory files. Ensure they are tracked in git: cd ~/epigenome && git add marks/ && git status. If there are untracked marks, commit them. Also create a pre-push hook or effector that validates all marks have valid YAML frontmatter. Write tests. Commit."`

### Temporal migration — Phase 1

#### Scaffold Temporal-based golem orchestrator
- [!] `golem [t-c500c0] --provider gemini --max-turns 50 "Build a Temporal.io-based orchestrator to replace the golem-daemon markdown queue. Phase 1 — scaffold only. 1) Create effectors/temporal-golem/ directory 2) Add pyproject.toml with temporalio SDK dependency 3) Create worker.py — a Temporal worker that polls a 'golem-tasks' task queue and executes golem commands as activities. Each activity: runs 'bash effectors/golem --provider gemini task', heartbeats every 30s, has 30min timeout, retry policy (3 attempts, backoff). 4) Create workflow.py — a GolemDispatchWorkflow that accepts a list of tasks, dispatches them respecting per-provider concurrency (zhipu:8, infini:8, volcano:16), and reports results. 5) Create cli.py — CLI to submit workflows: 'temporal-golem submit --provider gemini --task ...' and 'temporal-golem status'. 6) Create docker-compose.yml for Temporal server + PostgreSQL + Web UI. 7) Write a README.md explaining the setup. 8) Write tests in assays/test_temporal_golem.py (mock the Temporal client). Commit everything." (retry)`

#### Docker compose for Temporal server
- [ ] `golem [t-74f0cc] --provider zhipu --max-turns 30 "Create effectors/temporal-golem/docker-compose.yml for running Temporal locally. Include: 1) temporal-server (temporalio/server:latest) 2) PostgreSQL 15 for persistence 3) temporal-web (temporalio/web:latest) on port 8080 4) temporal-admin-tools for CLI access. Use environment variables for config. Add a startup script effectors/temporal-golem/start.sh that does 'docker compose up -d' and waits for health check. Write to effectors/temporal-golem/. Commit." (retry)`

### Provider troubleshooting

#### Diagnose and fix Volcano provider failures
- [!] `golem [t-f8bcd2] --provider gemini --max-turns 40 "Read effectors/golem (the shell script). Volcano provider (ark-code-latest) is returning exit=2 with 0s duration — the golem process fails before starting. Debug: 1) Check how volcano auth works (VOLCANO_API_KEY vs ANTHROPIC_AUTH_TOKEN) 2) Test the volcano endpoint directly with curl: curl -s https://ark.cn-beijing.volces.com/api/v3/chat/completions -H 'Authorization: Bearer $VOLCANO_API_KEY' 3) Check if the Claude Code --provider gemini accepts volcano's URL format 4) Read recent daemon logs for volcano error messages. If the issue is auth token format, fix it in the golem script. If it's rate limiting, add exponential backoff. Write findings and fix to effectors/golem. Write tests. Commit." (retry)`

#### Diagnose and fix Infini provider failures  
- [ ] `golem [t-f1adb3] --provider gemini --max-turns 40 "Read effectors/golem (the shell script). Infini provider (deepseek-v3.2 at cloud.infini-ai.com) has intermittent exit=2 failures with 0s duration. Debug: 1) Check INFINI_API_KEY is correctly formatted 2) Test the endpoint directly: curl -s https://cloud.infini-ai.com/maas/coding/v1/chat/completions -H 'Authorization: Bearer $INFINI_API_KEY' -H 'Content-Type: application/json' -d '{\"model\":\"deepseek-v3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}' 3) Check if rate limiting or quota exhaustion is the cause 4) Read daemon logs for infini-specific error patterns. If rate limited, implement per-provider cooldown in golem-daemon. Write findings and fix. Commit." (retry)`

### Hatchet features — wire up advanced capabilities

#### Rate limits — per-provider server-side throttling
- [!] `golem [t-595036] --provider gemini --max-turns 50 "Read effectors/hatchet-golem/worker.py. Add Hatchet server-side rate limits for each provider. Use h.rate_limits.put() to create rate limit keys: 'zhipu-rpm' (1000 req/5hr = 200/hr), 'infini-rpm' (1000 req/5hr = 200/hr), 'volcano-rpm' (1000 req/5hr = 200/hr), 'gemini-rpm' (60/min). Then add rate_limits=[RateLimit(key='<provider>-rpm', units=1)] to each @hatchet.task decorator. This replaces the manual cooldown in golem-daemon. Write tests in assays/test_hatchet_rate_limits.py. Commit." (retry)`

#### Cron — scheduled auto-requeue and health checks
- [x] `golem [t-242f4d] --provider zhipu --max-turns 50 "Read effectors/hatchet-golem/worker.py and effectors/hatchet-golem/dispatch.py. Add two cron-triggered Hatchet tasks: 1) @hatchet.task with on_crons=['*/30 * * * *'] named 'golem-requeue' that checks if golem-queue.md has < 20 pending tasks and auto-generates new ones (port the auto_requeue logic from effectors/golem-daemon). 2) @hatchet.task with on_crons=['*/15 * * * *'] named 'golem-health' that runs effectors/gemmule-health --daemon and logs the result. Register both in the worker. Write tests. Commit."`

#### Metrics — task stats and Prometheus endpoint
- [!] `golem [t-2e6bc8] --provider codex --max-turns 40 "Read the Hatchet SDK metrics API. Create effectors/hatchet-golem/stats.py that: 1) Calls h.metrics.get_task_metrics() and h.metrics.get_queue_metrics() 2) Prints a summary: tasks completed/failed/pending per provider, avg duration, queue depth 3) Optionally outputs as JSON (--json flag) 4) Add a 'golem-metrics' @hatchet.task with on_crons=['0 * * * *'] that logs hourly stats to ~/.local/share/vivesca/hatchet-metrics.jsonl. Write tests. Commit."`

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

- [!] `golem [t-816e83] --provider gemini --max-turns 30 "Build ~/bin/stips as a Python CLI for OpenRouter credits. Env: OPENROUTER_API_KEY. Subcommands: credits (GET https://openrouter.ai/api/v1/auth/key — print balance), usage (GET https://openrouter.ai/api/v1/activity — print recent usage), key (print masked key). Use requests. Test with: stips credits. chmod +x."`

#### Tier 2 — weekly use

- [ ] `golem [t-0a3b79] --provider zhipu --max-turns 30 "Build ~/bin/fasti as a Python CLI wrapping Google Calendar API. Env: GOOGLE_API_KEY. Subcommands: list [date] (list events for a date, default today), move <event-id> <new-datetime>, delete <event-id>. Use the Google Calendar REST API with API key auth. For OAuth operations that need write access, use a service account or stored refresh token at ~/.config/fasti/credentials.json. Print events as: time | title | location. Test with: fasti list. chmod +x."`

- [x] `golem [t-2895d5] --provider zhipu --max-turns 30 "Build ~/bin/grapho as a Python CLI for managing MEMORY.md. The file is at ~/epigenome/marks/MEMORY.md (or ~/.claude/projects/-home-terry/memory/MEMORY.md via symlink). Subcommands: status (show line count, budget usage — budget is 60 lines), add (interactive: prompt for title, file, description — append entry to MEMORY.md and create the memory file), demote <title> (move entry from MEMORY.md to ~/epigenome/chromatin/immunity/memory-overflow.md), promote <title> (reverse), review (list overflow entries), solution <name> (scaffold ~/docs/solutions/<name>.md). Flags: --format human|json. Test with: grapho status. chmod +x."`

- [x] `golem [t-267c1c] --provider zhipu --max-turns 30 "Build ~/bin/pondus as a Python CLI for AI model benchmark aggregation. Subcommands: rank (fetch and merge rankings from multiple benchmark sources — Chatbot Arena at https://lmarena.ai, LiveBench, MMLU — print sorted table), check <model> (show one model across sources), compare <modelA> <modelB> (head-to-head), sources (list all sources and cache status), refresh (clear cache at ~/.cache/pondus/), recommend <task-type> (suggest models for coding/reasoning/creative). Cache results for 24h in ~/.cache/pondus/. Flags: --format json|table|markdown. Use requests + simple HTML parsing. Test with: pondus sources. chmod +x."`

- [!] `golem [t-b1e7c2] --provider gemini --max-turns 30 "Build ~/bin/sarcio as a Python CLI for managing a digital garden. Posts live at ~/notes/Writing/Blog/Published/. Subcommands: new <title> (create a new draft .md file with frontmatter: title, date, tags, status=draft), list (list all posts with status), publish <filename> (set status=published in frontmatter, add published_date), revise <filename> (open in EDITOR), open <filename> (open in EDITOR), index (regenerate index.md listing all published posts). Use pathlib and yaml (PyYAML or frontmatter parsing). Test with: sarcio list. chmod +x."`

#### Tier 3 — specialized

- [x] `golem [t-dbfdc1] --provider zhipu --max-turns 30 "Build ~/bin/keryx as a Python CLI wrapping wacli (WhatsApp CLI at ~/germline/effectors/wacli-ro). Subcommands: read <name> [--n N] (resolve contact name to JID, call wacli-ro read, merge dual-JID conversations), send <name> <message> [--execute] (print or execute wacli send command), chats [--n N] (list recent chats via wacli-ro chats), sync start|stop|status (manage wacli sync daemon). Contact resolution: maintain ~/.config/keryx/contacts.json mapping names to JIDs. Use subprocess to call wacli-ro. Test with: keryx chats. chmod +x."`

- [ ] `golem [t-6e540c] --provider gemini --max-turns 30 "Build ~/bin/moneo as a Python CLI for Due app reminders. Due stores data in ~/Library/Group Containers/ on Mac but on Linux we use a synced JSON file at ~/.config/moneo/reminders.json. Subcommands: ls (list all reminders sorted by date), add <title> --date <datetime> [--repeat <interval>] (add reminder), rm <title> (delete by title match), edit <index> --title/--date (edit fields), log (show completion history from ~/.config/moneo/completions.jsonl). Print reminders as: date | title | repeat. Test with: moneo ls (should show empty or create sample data). chmod +x."`

- [x] `golem [t-d54f38] --provider zhipu --max-turns 30 "Build ~/bin/anam as a Python CLI for searching AI chat history. Scans ~/.claude/projects/ for session JSONL files. Subcommands: (default) [date] (scan sessions for a date — default today — show prompts with timestamps), search <pattern> (grep across all session files for a regex pattern). Flags: --full (show all, not just last 50), --json (output as JSON), --tool claude|codex|opencode (filter by tool). Use glob + json. Test with: anam today. chmod +x."`

- [x] `golem [t-e53737] --provider zhipu --max-turns 30 "Build ~/bin/auceps as a Python CLI wrapping the bird CLI (X/Twitter). Subcommands: (default) <input> (auto-route: if URL -> fetch tweet, if @handle -> fetch timeline, else -> search), thread <url> (follow quote-tweet chains), bird <args> (passthrough to bird CLI), post <text> (post via bird). Flags: --vault (output as Obsidian markdown), --lustro (output as lustro JSON), -n/--limit N (default 20). Use subprocess to call bird. Test with: auceps --help. chmod +x."`

### Hatchet dogfooding — advanced features

#### Webhooks — trigger from GitHub push
- [!] `golem [t-013aa4] --provider gemini --max-turns 40 "Read Hatchet webhooks API. Create a webhook endpoint that GitHub can call on push to vivesca repo. When triggered, dispatch new pending tasks from golem-queue.md. Steps: 1) Use h.webhooks.create() to register a webhook 2) Create effectors/hatchet-golem/webhook.py that handles the GitHub payload 3) Update .github/workflows/gemmule-wake.yml to also POST to the Hatchet webhook after waking gemmule. This replaces polling — tasks dispatch on push. Write tests. Commit."`

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
