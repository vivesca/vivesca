# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly. Provider + turns baked in.
**ZhiPu fixed (stdin redirect). All 3 providers active: ZhiPu(4) + Infini(6) + Volcano(8) = 18 concurrent.**

## Pending

### IMPORTANT (perishable / high-impact — dispatch first)

#### Capco onboarding research

#### AI in banking regulatory briefing

#### Fix effector test coaching (prevents broken golem output)

#### Integrin health check (is the organism healthy?)

### Retries (split [!] failures into smaller tasks)

#### Sortase executor (33K — needs solo golem)

#### Sortase decompose + graph + logger (3 modules)

#### Lysin + endosomal (4 modules)

#### Morphology + codons (2 modules)

#### Pinocytosis + sporulation (4 modules)

#### Remaining tiny (3 modules)

### Fixes (mop up test failures)

#### Fix all remaining test failures

### Compound infra

#### Coaching enforcement — post-golem validation gate

### Builds (features > tests)

#### ZhiPu golem diagnosis

#### Golem auto-retry on [!]

#### Golem provider health check

#### Effector: test-dashboard

### Effector test blitz (24 tasks, 73 effectors)


### Builds + consulting prep (20 tasks)


### Effector tests with coaching (25 tasks)



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

- [x] `golem --provider zhipu --max-turns 35 "Create effectors/skill-search as Python. Searches all SKILL.md files by keyword. Returns matching skills with description. Like grep but skill-aware. Write tests. Run uv run pytest."`
- [x] `golem --provider zhipu --max-turns 35 "Create effectors/queue-balance as Python. Reads golem-queue.md. Reports task distribution by provider. Suggests rebalancing if one provider has >2x others. Write tests. Run uv run pytest."`
- [x] `golem --provider zhipu --max-turns 35 "Create effectors/golem-top as Python. Shows currently running golem processes (ps aux | grep golem). For each: PID, provider, duration, task snippet. Like top for golems. Write tests. Run uv run pytest." (retry)`
- [x] `golem --provider zhipu --max-turns 35 "Create effectors/effector-usage as Python. Scans golem.jsonl + golem-daemon.log for effector mentions. Reports: most used, never used, recently broken. Write tests. Run uv run pytest." (retry)`
- [x] `golem --provider zhipu --max-turns 35 "Create effectors/golem-cost as Python. Estimates cost of golem runs. Reads golem.jsonl. Calculates: tokens estimated per run (turns * ~4K), total tokens, cost if metered. Write tests. Run uv run pytest."`
- [x] `golem --provider zhipu --max-turns 35 "Create effectors/git-activity as Python. Shows git activity across germline + epigenome: commits today, files changed, top contributors (golem vs human). Quick pulse check. Write tests. Run uv run pytest." (retry)`


### Overnight fill — consulting IP + hardening + enhancements

- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI model risk management — HSBC perspective — global G-SIB with multi-jurisdiction requirements. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: Responsible AI governance — comparison of HKMA vs MAS vs PRA expectations. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: Third-party AI risk — vendor assessment scorecard with weighted criteria. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI explainability — customer-facing explanations for credit decisions — templates. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI in AML/KYC — transaction monitoring model comparison — rules vs ML vs hybrid. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: Cloud AI services — data residency mapping for APAC banking jurisdictions. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: GenAI policy for banks — acceptable use policy template with examples. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI incident response — post-incident review template with root cause taxonomy. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI model validation — validation framework adapted from SR 11-7 for ML models. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: RegTech landscape — build vs buy decision framework for compliance AI. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI fraud detection — ROC/precision trade-offs for different fraud types. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: Board AI reporting — materiality threshold framework — when to escalate AI issues. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: DORA implications — AI-specific requirements extracted from DORA articles. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 35 "Write a consulting deep-dive on: AI ethics — customer consent framework for AI-driven services. Structure: Executive summary (3 sentences), Context (why now, regulatory drivers), Analysis (the core content, 4-6 sections with detail), Recommendations (5 numbered, actionable), Appendix (references, further reading). Write to ~/epigenome/chromatin/euchromatin/consulting/deep-dives/ with slugified filename. 800-1200 words, professional consulting tone."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: GenAI document processing for trade finance operations. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: AI model risk framework implementation — 16-week program. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Real-time fraud detection ML pipeline — architecture and results. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Intelligent document extraction for KYC onboarding. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Chatbot compliance monitoring — ensuring regulatory adherence. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: NLP for regulatory change management — tracking 500+ updates/year. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Data quality framework for ML pipelines at a custodian bank. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Cross-border data governance for AI in a multi-jurisdiction bank. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: AI red team exercise — adversarial testing of banking LLMs. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write a consulting case study template: Digital twin for branch network optimization using AI. Structure: Client context (disguised), Challenge, Approach (phased), Key decisions, Results (with metrics — invent plausible ones), Lessons learned, Capco differentiator. Write to ~/epigenome/chromatin/euchromatin/consulting/case-studies/ with slugified filename. 600-900 words."`
- [x] `golem --provider zhipu --max-turns 30 "Write: Capco-specific interview prep — company values, recent projects, culture. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 30 "Write: Estimation questions for AI projects — how to size effort and cost. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 30 "Write: AI readiness assessment questionnaire — 30 questions for bank self-assessment. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 30 "Write: Regulatory examination prep — what examiners ask about AI/ML models. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 30 "Write: AI project failure modes — 15 anti-patterns and how to avoid them. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 30 "Write: AI demo preparation — how to showcase AI capabilities to bank executives. Practical, actionable, consulting-grade quality. Write to ~/epigenome/chromatin/euchromatin/consulting/prep/ with slugified filename."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: HKMA SPM module on technology risk management — extract AI-relevant requirements. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: PRA SS1/23 model risk management — ML-specific interpretation guide. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: EU AI Act — banking-specific obligations by risk category. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: OCC bulletin on model risk — how it applies to GenAI. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: HKMA supervisory expectations on cybersecurity — AI security angle. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: EBA guidelines on ICT risk management — AI-specific controls. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 40 "Research and write: Singapore PDPA — AI model training data requirements. Use rheotaxis_search to find the actual regulatory text or summary. Extract key requirements. Write consulting-ready analysis to ~/epigenome/chromatin/euchromatin/regulatory/deep-dives/ with slugified filename. Include: source document, key requirements, bank obligations, common gaps, consulting opportunity."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/golem. Add --quiet flag that suppresses all output except the final exit code. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add cmd_retry-all — re-queue all [!] failed tasks as [ ] for another attempt. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add priority queue support — tasks marked [!!] run before [ ]. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/legatum. Add --format json flag for machine-readable output. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read effectors/chromatin-backup.sh. Convert to Python for nociceptor compatibility. Keep same functionality.. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/server.py. Add request logging — log tool name, duration, success/fail to a JSONL file. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/codons/templates.py. Audit template strings for stale references to renamed tools. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/organelles/sporulation.py. Add checkpoint listing — show all saved checkpoints with dates. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 30 "Read metabolon/sortase/graph.py. Add visualization output — DOT format for task dependency graph. Write/update tests. Run uv run pytest. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Scan ALL .py files for bare except: clauses. Replace with specific exceptions. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check ALL assays/test_*.py for deterministic tests (no time.time, random, network calls without mock). Report non-deterministic tests."`
- [x] `golem --provider zhipu --max-turns 25 "Find ALL Python files missing from __future__ import annotations. Add where type hints are used. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check ALL test files use assays/ flat structure. Move any in subdirectories. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Scan for ANY remaining ~/ hardcoded paths across entire repo. Fix ALL. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check ALL async functions for missing await calls. Fix. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Verify ALL git hooks in .git/hooks/ still work. Remove broken ones. Commit."`
- [x] `golem --provider zhipu --max-turns 25 "Check ALL test fixtures clean up after themselves (temp files, env vars). Fix leaks. Commit." (retry)`
- [x] `golem --provider zhipu --max-turns 25 "Verify ALL pathlib usage is cross-platform (no hardcoded / separators). Fix. Commit." (retry)`
- [!] `golem --provider zhipu --max-turns 25 "Check ALL file writes use atomic write pattern (write to .tmp, rename). Fix critical ones. Commit." (retry)`


### Post-batch synthesis (run after overnight batch drains)

#### Synthesis — overnight output digest
- [!] `golem --provider zhipu --max-turns 50 "You are running after a mega batch of 900 golem tasks. Create a digest of everything produced overnight. (1) List all new files in ~/epigenome/chromatin/euchromatin/consulting/ — group by type (cards, deep-dives, case-studies, prep, regulatory). Count each. (2) List all new/modified files in ~/germline/assays/ — count new tests, fixed tests. (3) List all new/modified effectors in ~/germline/effectors/. (4) Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | tail -5 — record pass/fail. (5) Read golem summary stats from ~/.local/share/vivesca/golem.jsonl — pass/fail by provider. Write a structured morning digest to ~/epigenome/chromatin/euchromatin/consulting/overnight-digest.md. Include: what was produced, what worked, what failed, what needs human review." (retry)`

#### Synthesis — consulting IP executive summary

#### Synthesis — regulatory landscape summary

### Lustro content analysis — process cached articles

#### Build — lustro batch analyzer
- [!] `golem --provider zhipu --max-turns 40 "Create effectors/lustro-analyze as Python. Reads all articles from ~/.cache/lustro-articles/. For each .json or .md file: extract title, source, date, content snippet. Classify by topic: AI, banking, regulation, technology, other. Output: (1) summary table of all articles by topic, (2) top 20 most relevant to banking AI consulting, (3) key themes across all articles. Usage: lustro-analyze [--top N] [--topic banking]. Write to stdout or --output file. Write assays/test_lustro_analyze.py. Run uv run pytest." (retry)`

#### Process — lustro articles → consulting signals

#### Process — endocytosis content → Capco prep

#### Process — lustro financial articles
- [x] `golem --provider zhipu --full --max-turns 40 "Read files in ~/.cache/lustro-articles/ that contain keywords: bank, HSBC, fintech, regulation, compliance, risk. For each matching article: extract title + 1 key takeaway. Compile into: (1) Banking industry signals this week, (2) Technology trends affecting banks, (3) Regulatory developments. Write to ~/epigenome/chromatin/euchromatin/consulting/lustro-banking-signals.md."`

#### Process — lustro AI/tech articles

#### Synthesis — weekly intelligence brief


### Meta-golem — self-sustaining review + requeue loop

#### Build — review-and-requeue effector (runs this once, then daemon picks up the cycle)
- [ ] `golem --provider zhipu --max-turns 50 "Create effectors/golem-review as Python. This is a META-GOLEM — it reviews other golem output and queues more work. Steps: (1) Read golem-daemon.log, find tasks completed in last 30 min. (2) For each completed task: check if output files were created (git diff --name-only HEAD~5). (3) For new test files: run uv run pytest on each, count pass/fail. (4) For new consulting content: check file exists and has >200 words. (5) For failed tasks: read the log tail, diagnose common failures (path issues, import errors, timeout), write a FIXED version of the task to loci/golem-queue.md. (6) Generate a review summary to loci/copia/golem-review-latest.md. (7) If queue has <50 pending tasks: auto-generate 50 more from untested modules/effectors. Usage: golem-review [--auto-requeue] [--since 30m]. Write assays/test_golem_review.py. Run uv run pytest."`

#### Review cycle 1 (fires ~1h into batch)

#### Review cycle 2 (fires ~2h into batch)

#### Review cycle 3 (fires ~3h into batch)
- [!] `golem --provider zhipu --max-turns 40 "Review golem output — third cycle. (1) Count consulting IP produced so far: cards, deep-dives, case-studies, prep, regulatory. (2) Quality check: read 5 random deep-dives, score each 1-5 on: structure, depth, actionability. Report scores. (3) Check lustro analysis output — did the lustro tasks produce signal files? (4) If consulting IP is thin in any category: generate 10 more tasks for that category. (5) Commit any uncommitted golem output: git add ~/epigenome/chromatin/ ~/germline/assays/ ~/germline/effectors/ && git commit -m 'golem: batch checkpoint'. (6) Write review to loci/copia/review-cycle-3.md." (retry)`

#### Review cycle 4 (fires ~4h into batch)

#### Review cycle 5 — final synthesis (fires near end of batch)

## Done (2026-03-31)

