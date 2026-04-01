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
- [ ] `golem [t-5e5210] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 08:02)
- [!] `golem --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [ ] `golem [t-8ce0c6] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-b61fe0] --provider infini --max-turns 30 "Health check: x-feed-to-lustro, pinocytosis, complement, update-compound-engineering-skills.sh, launchagent-health, test-fixer, chromatin-backup.sh, circadian-probe.py, paracrine, replisome. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/integrin.py. Mock external calls. Write assays/test_enzymes_integrin.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-026e0c] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/demethylase.py. Mock external calls. Write assays/test_organelles_demethylase.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-b5a8d6] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/tissue_routing.py. Mock external calls. Write assays/test_organelles_tissue_routing.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/lysis.py. Mock external calls. Write assays/test_enzymes_lysis.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [x] `golem [t-fd9639] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/retrograde.py. Mock external calls. Write assays/test_organelles_retrograde.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-bdcc27] --provider infini --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-8184de] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-504602] --provider infini --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-0cb093] --provider zhipu --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit." (retry)`
- [!] `golem [t-89ab22] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit." (retry)`
- [!] `golem --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [ ] `golem [t-101bf6] --provider zhipu --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-d1108f] --provider infini --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem --provider volcano --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 08:14)
- [ ] `golem [t-aba479] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-bfd333] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [ ] `golem [t-3ff001] --provider zhipu --max-turns 30 "Health check: plan-exec.deprecated, mismatch-repair, queue-gen, golem-top, update-compound-engineering, x-feed-to-lustro, test-spec-gen, receptor-health, pharos-health.sh, grok. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-b6972b] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/quorum.py. Mock external calls. Write assays/test_organelles_quorum.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-cbccf6] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/vitals.py. Mock external calls. Write assays/test_resources_vitals.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-2c7790] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/metabolism_loop.py. Mock external calls. Write assays/test_organelles_metabolism_loop.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-f6a512] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/lysin/cli.py. Mock external calls. Write assays/test_lysin_cli.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-64383c] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/nociceptor.py. Mock external calls. Write assays/test_metabolism_nociceptor.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-106c9d] --provider zhipu --max-turns 30 "Write tests for effectors/transduction-daily-run. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-4a7cfe] --provider infini --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-c9abe1] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-2f2c01] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-9a450f] --provider infini --max-turns 30 "Write tests for effectors/tm. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-86c4c7] --provider volcano --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [ ] `golem [t-7af5ce] --provider zhipu --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [ ] `golem [t-5c2df2] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-46c2fc] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [ ] `golem [t-450d8f] --provider zhipu --max-turns 30 "Write a consulting insight card: AI skills gap assessment for banking technology teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-skills-gap.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-5e4a13] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`

### Auto-requeue (19 tasks @ 01:16)
- [ ] `golem [t-218472] --provider infini --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [ ] `golem [t-f1c201] --provider volcano --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [ ] `golem [t-c05334] --provider zhipu --max-turns 30 "Health check: synthase, grep, oura-weekly-digest.py, safe_rm.py, gemmule-wake, importin, overnight-gather, queue-gen, rotate-logs.py, conftest-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [ ] `golem [t-255368] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/sortase/diff_viewer.py. Mock external calls. Write assays/test_sortase_diff_viewer.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-0b4638] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/porta.py. Mock external calls. Write assays/test_organelles_porta.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-8fe655] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/reflexes.py. Mock external calls. Write assays/test_resources_reflexes.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-88d9e2] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-103725] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-b35017] --provider zhipu --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-427595] --provider infini --max-turns 30 "Write tests for effectors/gemmule-snapshot. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-80438b] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-669100] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-0c426b] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-af1d4a] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [ ] `golem [t-13f1ff] --provider zhipu --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [ ] `golem [t-26de37] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-660d4b] --provider volcano --max-turns 30 "Write a consulting insight card: AI audit methodology for internal audit teams. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-audit-methodology.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [ ] `golem [t-9409a7] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-e8aba5] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit." (retry)`
## Done (2026-03-31)


### Build — circadian-aware auto-requeue

- [ ] `golem [t-313701] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Find the auto_requeue function. Enhance it to be circadian-aware: (1) Read ~/germline/loci/priorities.md for current north stars and deadlines. (2) Check current hour (HKT). (3) Night (22-06): weight toward tests 50%, hardening 30%, consulting 20%. (4) Morning (06-09): weight toward consulting IP 50%, digests 30%, fixes 20%. (5) Daytime (09-22): weight toward fixes 40%, features 30%, consulting 30%. (6) If priorities.md mentions a deadline within 3 days: boost that category to 60%. Write the priority logic as a separate function circadian_priorities() -> dict[str, float]. Write tests. Run uv run pytest. Commit."`

- [ ] `golem [t-35fcf3] --provider infini --max-turns 30 "Create ~/germline/loci/priorities.md with this structure: north_stars (3 items with deadline), current_focus (what to prioritize now), blocked (what to skip). Initial content: (1) Capco readiness — deadline Apr 8 — consulting IP, regulatory briefs, case studies (2) Organism robustness — ongoing — fix tests, effector health (3) Consulting arsenal — ongoing — frameworks, templates. CC will update this file each session."`


### Build — wire circulation into golem-daemon

- [x] `golem [t-0263fc] --provider zhipu --max-turns 50 "Read metabolon/organelles/circulation.py (535 lines). Read effectors/golem-daemon auto_requeue function. Design integration: (1) Create effectors/circulate-dispatch as Python. It runs circulation.select_goals() to get intelligent goal list, then converts each goal into a golem queue entry in loci/golem-queue.md. Uses symbiont.transduce_safe() for CC-powered goal selection (reads Tonus.md + priorities.md + calendar). Writes queue entries. Usage: circulate-dispatch [--max-goals 8]. (2) Wire this into golem-daemon auto_requeue: when queue < 50, call circulate-dispatch instead of random task generation. Write tests. Run uv run pytest. Commit."`

- [ ] `golem [t-0ed7c8] --provider infini --max-turns 40 "Read metabolon/organelles/circulation.py. Extract the evaluate() and compound() functions into a standalone effectors/circulate-evaluate as Python. After golem tasks complete, this reads results and: (1) updates coaching notes if new failure patterns found, (2) updates priorities.md if goals were completed, (3) writes a cycle report. Called by golem-reviewer periodically. Write tests. Run uv run pytest. Commit."`


### High-priority — infra + task IDs (queued by CC)

#### Add task IDs to golem-daemon
- [!!] `golem [t-19855e] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Add unique task IDs: 1) In parse_queue(), generate a short ID (t-xxxx, 6 hex chars) for each task that doesn't have one — prepend it inside the backtick like 'golem [t-a7f3] --provider ...'. 2) In run_golem(), extract the ID and pass it as env var GOLEM_TASK_ID. 3) In the JSONL output, add a 'task_id' field. 4) In mark_done/mark_failed, include the task ID in the result annotation. 5) In cmd_status, show task IDs of running tasks. Write tests in assays/test_golem_task_ids.py. Run uv run pytest on the test file. Commit."`

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
- [ ] `golem [t-211b2c] --provider zhipu --max-turns 40 "Write a comprehensive briefing on Hong Kong financial regulation for AI/technology: HKMA, SFC, IA key circulars and expectations around AI adoption in banking, insurance, securities. Include HKMA's Supervisory Policy Manual modules on technology risk (TM-E-1, OR-1). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hk-ai-regulatory-landscape.md. 500+ words. Commit." (retry)`

### System hardening

#### Add periodic rsync from Mac to gemmule
- [ ] `golem [t-0f22c4] --provider zhipu --max-turns 30 "Create effectors/gemmule-sync as a Python script. It should: 1) rsync terry@100.94.27.93:~/epigenome/chromatin/ ~/epigenome/chromatin/ 2) rsync terry@100.94.27.93:~/notes/ ~/notes/ 3) rsync terry@100.94.27.93:~/code/acta/ ~/code/acta/ 4) Log results to ~/.local/share/vivesca/gemmule-sync.log. Add --dry-run flag. Make it idempotent. Write tests. Commit."`

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
- [ ] `golem [t-31363b] --provider zhipu --max-turns 40 "Read effectors/golem (the golem script, not golem-daemon). Add provider failover: if the primary provider returns HTTP 429 (rate limit) or 5xx, automatically retry with the next provider in priority order (zhipu -> infini -> volcano). Add a --fallback flag to opt-in. Log the failover. Write tests in assays/test_golem_failover.py. Commit."`

#### Watchdog — detect and fix stuck golems
- [ ] `golem [t-cb5765] --provider infini --max-turns 40 "Read effectors/golem-daemon. Add a watchdog: every 5 poll cycles, check if any running golem has exceeded GOLEM_TIMEOUT (1800s). If so: 1) kill the subprocess 2) mark task as failed with 'timeout' 3) log a warning. Currently the ThreadPoolExecutor handles timeouts but subprocess.run may hang. Add subprocess-level kill via os.kill(). Write tests. Commit."`

#### Graceful shutdown — commit before dying
- [ ] `golem [t-ad7830] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Improve the SIGTERM handler: on shutdown signal, 1) stop accepting new tasks 2) wait up to 60s for running golems to finish 3) auto-commit any uncommitted work 4) push to remote 5) then exit. Currently it just removes the pidfile. Write tests. Commit."`

#### Config validation on daemon start
- [ ] `golem [t-fc42d9] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a validate_config() function that runs on startup and checks: 1) QUEUE_FILE exists and is readable 2) all providers in PROVIDER_LIMITS have valid API keys in env 3) git repo is clean enough to commit 4) disk space > 2GB 5) uv sync is up to date (uv run python -c 'import metabolon'). If any check fails, log a clear error and exit 1. Write tests. Commit."`

#### Self-healing — auto-fix common breakages
- [ ] `golem [t-9eecea] --provider infini --max-turns 50 "Create effectors/mismatch-repair as a Python script (biology: mismatch repair fixes DNA errors). It should detect and fix common vivesca breakages: 1) Duplicate 'from __future__ import annotations' in any .py file under ~/germline/ or ~/.claude/hooks/ — remove the second occurrence 2) Hardcoded /Users/terry paths — replace with Path.home() 3) Broken symlinks in ~/ — report them 4) Stale .pyc files — delete 5) pytest collection errors — run --co and report. Add --fix flag to auto-repair vs --check for dry-run. Write tests in assays/test_mismatch_repair.py. Commit."`

#### Network resilience — retry git operations
- [ ] `golem [t-9dffa6] --provider volcano --max-turns 30 "Read effectors/golem-daemon, specifically auto_commit(). Add retry logic: if git push fails (network error), retry 3 times with 30s backoff. If all retries fail, log error but don't crash daemon. Also add: if git pull fails at startup, continue with local state rather than crashing. Write tests. Commit."`

#### Backup marks/memory to git
- [ ] `golem [t-a6dcae] --provider zhipu --max-turns 30 "The epigenome/marks directory contains critical behavioral memory files. Ensure they are tracked in git: cd ~/epigenome && git add marks/ && git status. If there are untracked marks, commit them. Also create a pre-push hook or effector that validates all marks have valid YAML frontmatter. Write tests. Commit."`

### Temporal migration — Phase 1

#### Scaffold Temporal-based golem orchestrator
- [!!] `golem [t-c500c0] --provider zhipu --max-turns 50 "Build a Temporal.io-based orchestrator to replace the golem-daemon markdown queue. Phase 1 — scaffold only. 1) Create effectors/temporal-golem/ directory 2) Add pyproject.toml with temporalio SDK dependency 3) Create worker.py — a Temporal worker that polls a 'golem-tasks' task queue and executes golem commands as activities. Each activity: runs 'bash effectors/golem --provider X task', heartbeats every 30s, has 30min timeout, retry policy (3 attempts, backoff). 4) Create workflow.py — a GolemDispatchWorkflow that accepts a list of tasks, dispatches them respecting per-provider concurrency (zhipu:8, infini:8, volcano:16), and reports results. 5) Create cli.py — CLI to submit workflows: 'temporal-golem submit --provider zhipu --task ...' and 'temporal-golem status'. 6) Create docker-compose.yml for Temporal server + PostgreSQL + Web UI. 7) Write a README.md explaining the setup. 8) Write tests in assays/test_temporal_golem.py (mock the Temporal client). Commit everything."`

#### Docker compose for Temporal server
- [!] `golem [t-74f0cc] --provider infini --max-turns 30 "Create effectors/temporal-golem/docker-compose.yml for running Temporal locally. Include: 1) temporal-server (temporalio/server:latest) 2) PostgreSQL 15 for persistence 3) temporal-web (temporalio/web:latest) on port 8080 4) temporal-admin-tools for CLI access. Use environment variables for config. Add a startup script effectors/temporal-golem/start.sh that does 'docker compose up -d' and waits for health check. Write to effectors/temporal-golem/. Commit." (retry)`

### Provider troubleshooting

#### Diagnose and fix Volcano provider failures
- [!!] `golem [t-f8bcd2] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Volcano provider (ark-code-latest) is returning exit=2 with 0s duration — the golem process fails before starting. Debug: 1) Check how volcano auth works (VOLCANO_API_KEY vs ANTHROPIC_AUTH_TOKEN) 2) Test the volcano endpoint directly with curl: curl -s https://ark.cn-beijing.volces.com/api/v3/chat/completions -H 'Authorization: Bearer $VOLCANO_API_KEY' 3) Check if the Claude Code --provider flag accepts volcano's URL format 4) Read recent daemon logs for volcano error messages. If the issue is auth token format, fix it in the golem script. If it's rate limiting, add exponential backoff. Write findings and fix to effectors/golem. Write tests. Commit."`

#### Diagnose and fix Infini provider failures  
- [!!] `golem [t-f1adb3] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Infini provider (deepseek-v3.2 at cloud.infini-ai.com) has intermittent exit=2 failures with 0s duration. Debug: 1) Check INFINI_API_KEY is correctly formatted 2) Test the endpoint directly: curl -s https://cloud.infini-ai.com/maas/coding/v1/chat/completions -H 'Authorization: Bearer $INFINI_API_KEY' -H 'Content-Type: application/json' -d '{\"model\":\"deepseek-v3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}' 3) Check if rate limiting or quota exhaustion is the cause 4) Read daemon logs for infini-specific error patterns. If rate limited, implement per-provider cooldown in golem-daemon. Write findings and fix. Commit."`
