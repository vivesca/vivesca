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
- [ ] `golem [t-1f5574] --provider zhipu --max-turns 35 "Read effectors/golem. Add --json flag that outputs result as JSON instead of raw text. Useful for piping. Write tests. Run uv run pytest. Commit."`

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
- [ ] `golem [t-2c460e] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [!] `golem [t-cd543b] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-39ba9f] --provider volcano --max-turns 30 "Health check: git-activity, weekly-gather, qmd-reindex.sh, methylation-review, golem-daemon, poiesis, update-coding-tools.sh, capco-prep, golem-daemon-wrapper.sh, consulting-card.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [!] `golem [t-ae21ca] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/rheotaxis_engine.py. Mock external calls. Write assays/test_organelles_rheotaxis_engine.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b2b335] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/sortase.py. Mock external calls. Write assays/test_enzymes_sortase.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-255d63] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/respirometry/payments.py. Mock external calls. Write assays/test_respirometry_payments.py. Run uv run pytest. Fix failures. Commit."`
- [ ] `golem [t-e49209] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/interoception.py. Mock external calls. Write assays/test_enzymes_interoception.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-773d65] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-0fa735] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-c887a8] --provider zhipu --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-665d64] --provider infini --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-08da2d] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-43d345] --provider zhipu --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-6432ac] --provider infini --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit." (retry)`
- [!] `golem [t-91e3ba] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [ ] `golem [t-7ea4a1] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [!] `golem [t-4c5315] --provider infini --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-8515d5] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [!] `golem [t-ff9d44] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:50)
- [ ] `golem [t-e2b8ac] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [!] `golem [t-3cb054] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [!] `golem [t-3f98ef] --provider volcano --max-turns 30 "Health check: launchagent-health, golem-top, legatum, judge, lysis, test-fixer, skill-sync, orphan-scan, plan-exec, queue-gen. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit." (retry)`
- [ ] `golem [t-f66542] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/judge.py. Mock external calls. Write assays/test_enzymes_judge.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-02cf63] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/polarization.py. Mock external calls. Write assays/test_enzymes_polarization.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [!] `golem [t-017dec] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/consolidation.py. Mock external calls. Write assays/test_resources_consolidation.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-747dcc] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/engagement_scope.py. Mock external calls. Write assays/test_organelles_engagement_scope.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a0e9b8] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/browser_stealth.py. Mock external calls. Write assays/test_organelles_browser_stealth.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-728d02] --provider volcano --max-turns 30 "Write tests for effectors/tmux-url-select.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-bae6f6] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-67a483] --provider infini --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-945eab] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-130f0f] --provider zhipu --max-turns 30 "Write tests for effectors/soma-activate. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-948041] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [!] `golem [t-3e00f5] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [ ] `golem [t-2b11d2] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded /Users/terry paths. Replace with Path.home(). Commit."`
- [!] `golem [t-95083d] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-71bc8e] --provider volcano --max-turns 30 "Write a consulting insight card: Board-level AI risk reporting template for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/board-ai-risk-reporting.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words." (retry)`
- [ ] `golem [t-133735] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (19 tasks @ 01:52)
- [!] `golem [t-a1a8f4] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit." (retry)`
- [ ] `golem [t-553a58] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [!] `golem [t-4fb97a] --provider infini --max-turns 30 "Health check: compound-engineering-test, gemmation-env, provider-bench, lacuna, channel, phagocytosis.py, engram, safe_search.py, replisome, compound-engineering-status. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [!] `golem [t-6a443e] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/organelles/circadian_clock.py. Mock external calls. Write assays/test_organelles_circadian_clock.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-3f1618] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/metabolism/variants.py. Mock external calls. Write assays/test_metabolism_variants.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e62838] --provider infini --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/circadian.py. Mock external calls. Write assays/test_enzymes_circadian.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-e2b1d4] --provider volcano --max-turns 30 "Write tests for /home/terry/germline/metabolon/resources/operons.py. Mock external calls. Write assays/test_resources_operons.py. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-6d21da] --provider zhipu --max-turns 30 "Write tests for /home/terry/germline/metabolon/enzymes/mitosis.py. Mock external calls. Write assays/test_enzymes_mitosis.py. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-889941] --provider infini --max-turns 30 "Write tests for effectors/gemmule-bootstrap. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-b9d23c] --provider volcano --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-a2fcb7] --provider zhipu --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-a06006] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-62ad6b] --provider volcano --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit." (retry)`
- [ ] `golem [t-e89d17] --provider zhipu --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [!] `golem [t-8c5a97] --provider infini --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [!] `golem [t-e9a281] --provider volcano --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit." (retry)`
- [ ] `golem [t-7132c1] --provider zhipu --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-80e3d8] --provider infini --max-turns 30 "Write a consulting insight card: LLM deployment risks in banking — regulatory expectations vs reality. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/llm-deployment-risks.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-3997be] --provider volcano --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`
## Done (2026-03-31)


### Build — circadian-aware auto-requeue

- [ ] `golem [t-313701] --provider zhipu --max-turns 50 "Read effectors/golem-daemon. Find the auto_requeue function. Enhance it to be circadian-aware: (1) Read ~/germline/loci/priorities.md for current north stars and deadlines. (2) Check current hour (HKT). (3) Night (22-06): weight toward tests 50%, hardening 30%, consulting 20%. (4) Morning (06-09): weight toward consulting IP 50%, digests 30%, fixes 20%. (5) Daytime (09-22): weight toward fixes 40%, features 30%, consulting 30%. (6) If priorities.md mentions a deadline within 3 days: boost that category to 60%. Write the priority logic as a separate function circadian_priorities() -> dict[str, float]. Write tests. Run uv run pytest. Commit."`

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
- [!] `golem [t-cb5765] --provider infini --max-turns 40 "Read effectors/golem-daemon. Add a watchdog: every 5 poll cycles, check if any running golem has exceeded GOLEM_TIMEOUT (1800s). If so: 1) kill the subprocess 2) mark task as failed with 'timeout' 3) log a warning. Currently the ThreadPoolExecutor handles timeouts but subprocess.run may hang. Add subprocess-level kill via os.kill(). Write tests. Commit."`

#### Graceful shutdown — commit before dying
- [ ] `golem [t-ad7830] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Improve the SIGTERM handler: on shutdown signal, 1) stop accepting new tasks 2) wait up to 60s for running golems to finish 3) auto-commit any uncommitted work 4) push to remote 5) then exit. Currently it just removes the pidfile. Write tests. Commit."`

#### Config validation on daemon start
- [ ] `golem [t-fc42d9] --provider zhipu --max-turns 30 "Read effectors/golem-daemon. Add a validate_config() function that runs on startup and checks: 1) QUEUE_FILE exists and is readable 2) all providers in PROVIDER_LIMITS have valid API keys in env 3) git repo is clean enough to commit 4) disk space > 2GB 5) uv sync is up to date (uv run python -c 'import metabolon'). If any check fails, log a clear error and exit 1. Write tests. Commit."`

#### Self-healing — auto-fix common breakages
- [!] `golem [t-9eecea] --provider infini --max-turns 50 "Create effectors/mismatch-repair as a Python script (biology: mismatch repair fixes DNA errors). It should detect and fix common vivesca breakages: 1) Duplicate 'from __future__ import annotations' in any .py file under ~/germline/ or ~/.claude/hooks/ — remove the second occurrence 2) Hardcoded /Users/terry paths — replace with Path.home() 3) Broken symlinks in ~/ — report them 4) Stale .pyc files — delete 5) pytest collection errors — run --co and report. Add --fix flag to auto-repair vs --check for dry-run. Write tests in assays/test_mismatch_repair.py. Commit."`

#### Network resilience — retry git operations
- [!] `golem [t-9dffa6] --provider volcano --max-turns 30 "Read effectors/golem-daemon, specifically auto_commit(). Add retry logic: if git push fails (network error), retry 3 times with 30s backoff. If all retries fail, log error but don't crash daemon. Also add: if git pull fails at startup, continue with local state rather than crashing. Write tests. Commit." (retry)`

#### Backup marks/memory to git
- [ ] `golem [t-a6dcae] --provider zhipu --max-turns 30 "The epigenome/marks directory contains critical behavioral memory files. Ensure they are tracked in git: cd ~/epigenome && git add marks/ && git status. If there are untracked marks, commit them. Also create a pre-push hook or effector that validates all marks have valid YAML frontmatter. Write tests. Commit."`

### Temporal migration — Phase 1

#### Scaffold Temporal-based golem orchestrator
- [!] `golem [t-c500c0] --provider zhipu --max-turns 50 "Build a Temporal.io-based orchestrator to replace the golem-daemon markdown queue. Phase 1 — scaffold only. 1) Create effectors/temporal-golem/ directory 2) Add pyproject.toml with temporalio SDK dependency 3) Create worker.py — a Temporal worker that polls a 'golem-tasks' task queue and executes golem commands as activities. Each activity: runs 'bash effectors/golem --provider X task', heartbeats every 30s, has 30min timeout, retry policy (3 attempts, backoff). 4) Create workflow.py — a GolemDispatchWorkflow that accepts a list of tasks, dispatches them respecting per-provider concurrency (zhipu:8, infini:8, volcano:16), and reports results. 5) Create cli.py — CLI to submit workflows: 'temporal-golem submit --provider zhipu --task ...' and 'temporal-golem status'. 6) Create docker-compose.yml for Temporal server + PostgreSQL + Web UI. 7) Write a README.md explaining the setup. 8) Write tests in assays/test_temporal_golem.py (mock the Temporal client). Commit everything." (retry)`

#### Docker compose for Temporal server
- [!] `golem [t-74f0cc] --provider infini --max-turns 30 "Create effectors/temporal-golem/docker-compose.yml for running Temporal locally. Include: 1) temporal-server (temporalio/server:latest) 2) PostgreSQL 15 for persistence 3) temporal-web (temporalio/web:latest) on port 8080 4) temporal-admin-tools for CLI access. Use environment variables for config. Add a startup script effectors/temporal-golem/start.sh that does 'docker compose up -d' and waits for health check. Write to effectors/temporal-golem/. Commit." (retry)`

### Provider troubleshooting

#### Diagnose and fix Volcano provider failures
- [!] `golem [t-f8bcd2] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Volcano provider (ark-code-latest) is returning exit=2 with 0s duration — the golem process fails before starting. Debug: 1) Check how volcano auth works (VOLCANO_API_KEY vs ANTHROPIC_AUTH_TOKEN) 2) Test the volcano endpoint directly with curl: curl -s https://ark.cn-beijing.volces.com/api/v3/chat/completions -H 'Authorization: Bearer $VOLCANO_API_KEY' 3) Check if the Claude Code --provider flag accepts volcano's URL format 4) Read recent daemon logs for volcano error messages. If the issue is auth token format, fix it in the golem script. If it's rate limiting, add exponential backoff. Write findings and fix to effectors/golem. Write tests. Commit." (retry)`

#### Diagnose and fix Infini provider failures  
- [!!] `golem [t-f1adb3] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Infini provider (deepseek-v3.2 at cloud.infini-ai.com) has intermittent exit=2 failures with 0s duration. Debug: 1) Check INFINI_API_KEY is correctly formatted 2) Test the endpoint directly: curl -s https://cloud.infini-ai.com/maas/coding/v1/chat/completions -H 'Authorization: Bearer $INFINI_API_KEY' -H 'Content-Type: application/json' -d '{\"model\":\"deepseek-v3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}' 3) Check if rate limiting or quota exhaustion is the cause 4) Read daemon logs for infini-specific error patterns. If rate limited, implement per-provider cooldown in golem-daemon. Write findings and fix. Commit."`

### Hatchet features — wire up advanced capabilities

#### Rate limits — per-provider server-side throttling
- [!!] `golem [t-595036] --provider zhipu --max-turns 50 "Read effectors/hatchet-golem/worker.py. Add Hatchet server-side rate limits for each provider. Use h.rate_limits.put() to create rate limit keys: 'zhipu-rpm' (1000 req/5hr = 200/hr), 'infini-rpm' (1000 req/5hr = 200/hr), 'volcano-rpm' (1000 req/5hr = 200/hr), 'gemini-rpm' (60/min). Then add rate_limits=[RateLimit(key='<provider>-rpm', units=1)] to each @hatchet.task decorator. This replaces the manual cooldown in golem-daemon. Write tests in assays/test_hatchet_rate_limits.py. Commit."`

#### Cron — scheduled auto-requeue and health checks
- [!!] `golem [t-242f4d] --provider zhipu --max-turns 50 "Read effectors/hatchet-golem/worker.py and effectors/hatchet-golem/dispatch.py. Add two cron-triggered Hatchet tasks: 1) @hatchet.task with on_crons=['*/30 * * * *'] named 'golem-requeue' that checks if golem-queue.md has < 20 pending tasks and auto-generates new ones (port the auto_requeue logic from effectors/golem-daemon). 2) @hatchet.task with on_crons=['*/15 * * * *'] named 'golem-health' that runs effectors/gemmule-health --daemon and logs the result. Register both in the worker. Write tests. Commit."`

#### Metrics — task stats and Prometheus endpoint
- [!!] `golem [t-2e6bc8] --provider zhipu --max-turns 40 "Read the Hatchet SDK metrics API. Create effectors/hatchet-golem/stats.py that: 1) Calls h.metrics.get_task_metrics() and h.metrics.get_queue_metrics() 2) Prints a summary: tasks completed/failed/pending per provider, avg duration, queue depth 3) Optionally outputs as JSON (--json flag) 4) Add a 'golem-metrics' @hatchet.task with on_crons=['0 * * * *'] that logs hourly stats to ~/.local/share/vivesca/hatchet-metrics.jsonl. Write tests. Commit."`

#### Event-driven dispatch — git push triggers task pickup
- [ ] `golem [t-5f4e68] --provider zhipu --max-turns 40 "Read effectors/hatchet-golem/dispatch.py. Add an event-driven mode: create a @hatchet.task named 'golem-queue-changed' triggered by on_events=['queue:updated']. When triggered, it reads golem-queue.md and dispatches any new pending tasks. Then create a git post-commit hook at ~/germline/.git/hooks/post-commit that calls 'python3 -c \"from hatchet_sdk import Hatchet; h=Hatchet(); h.event.push('queue:updated', {})\"' when golem-queue.md changes. This replaces polling with event-driven dispatch. Write tests. Commit."`

#### Durable tasks — survive worker restarts
- [ ] `golem [t-d274eb] --provider zhipu --max-turns 40 "Read the Hatchet SDK durable_task API. Convert the golem-zhipu task in effectors/hatchet-golem/worker.py to use @hatchet.durable_task instead of @hatchet.task. This means if the worker restarts mid-task, Hatchet will resume from the last checkpoint. Add context.save_state() calls before and after the subprocess.run. Write tests showing checkpoint/resume behavior. Commit."`

#### Logs — centralized task logging
- [ ] `golem [t-8b0c43] --provider zhipu --max-turns 30 "Read the Hatchet SDK logs API. In effectors/hatchet-golem/worker.py, add context.log() calls inside _run_golem: log the command being run, the exit code, and a snippet of stdout/stderr. Then create effectors/hatchet-golem/logs.py that queries h.logs.list() to show recent task logs with filtering by provider and status. Add --tail flag for live following. Write tests. Commit."`

---

### Python rewrites of Rust CLIs (eliminate cargo from Docker build)

All tools: single Python file at ~/bin/<name>, #!/usr/bin/env python3, use requests or urllib, argparse with subcommands matching the Rust CLI exactly. chmod +x after creation. Test each command. Use env vars for API keys (no hardcoded secrets).

#### Tier 1 — daily use

- [ ] `golem [t-110132] --provider zhipu --max-turns 30 "Build ~/bin/noesis as a Python CLI wrapping the Perplexity API. Env: PERPLEXITY_API_KEY. Subcommands: search (sonar, ~0.006), ask (sonar-pro, ~0.01), research (sonar-deep-research, ~0.40), reason (sonar-reasoning-pro, ~0.01), log (show usage from ~/.local/share/noesis/log.jsonl). Flags: --raw (print raw JSON), --no-log (skip logging). POST to https://api.perplexity.ai/chat/completions. Log each query as JSONL with timestamp, model, cost estimate, query. Print extracted text answer + numbered source URLs. Test with: noesis search 'what is the weather in Hong Kong'. chmod +x ~/bin/noesis."`

- [ ] `golem [t-7264a7] --provider zhipu --max-turns 30 "Build ~/bin/caelum as a Python CLI. Fetches HK Observatory weather from https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=en (current forecast) and https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en (current temp/humidity). No args needed — just run 'caelum' and print one line: temp range, condition summary. Use urllib.request (no deps). Test it. chmod +x."`

- [ ] `golem [t-ba1380] --provider zhipu --max-turns 30 "Build ~/bin/consilium as a Python CLI for multi-model deliberation. Env: uses ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY. Takes a question as positional arg. Modes: --quick (parallel query to 3+ models, print each answer), --council (blind answers -> debate -> judge synthesizes), --redteam (adversarial stress test). Use requests to call each API. Models: Claude via Anthropic API, GPT-4o via OpenAI API, Gemini via Google AI API. Print each model's response labeled. Default mode: --quick. Test with: consilium --quick 'what is 2+2'. chmod +x."`

- [ ] `golem [t-816e83] --provider zhipu --max-turns 30 "Build ~/bin/stips as a Python CLI for OpenRouter credits. Env: OPENROUTER_API_KEY. Subcommands: credits (GET https://openrouter.ai/api/v1/auth/key — print balance), usage (GET https://openrouter.ai/api/v1/activity — print recent usage), key (print masked key). Use requests. Test with: stips credits. chmod +x."`

#### Tier 2 — weekly use

- [ ] `golem [t-0a3b79] --provider zhipu --max-turns 30 "Build ~/bin/fasti as a Python CLI wrapping Google Calendar API. Env: GOOGLE_API_KEY. Subcommands: list [date] (list events for a date, default today), move <event-id> <new-datetime>, delete <event-id>. Use the Google Calendar REST API with API key auth. For OAuth operations that need write access, use a service account or stored refresh token at ~/.config/fasti/credentials.json. Print events as: time | title | location. Test with: fasti list. chmod +x."`

- [ ] `golem [t-2895d5] --provider zhipu --max-turns 30 "Build ~/bin/grapho as a Python CLI for managing MEMORY.md. The file is at ~/epigenome/marks/MEMORY.md (or ~/.claude/projects/-home-terry/memory/MEMORY.md via symlink). Subcommands: status (show line count, budget usage — budget is 60 lines), add (interactive: prompt for title, file, description — append entry to MEMORY.md and create the memory file), demote <title> (move entry from MEMORY.md to ~/epigenome/chromatin/immunity/memory-overflow.md), promote <title> (reverse), review (list overflow entries), solution <name> (scaffold ~/docs/solutions/<name>.md). Flags: --format human|json. Test with: grapho status. chmod +x."`

- [ ] `golem [t-267c1c] --provider zhipu --max-turns 30 "Build ~/bin/pondus as a Python CLI for AI model benchmark aggregation. Subcommands: rank (fetch and merge rankings from multiple benchmark sources — Chatbot Arena at https://lmarena.ai, LiveBench, MMLU — print sorted table), check <model> (show one model across sources), compare <modelA> <modelB> (head-to-head), sources (list all sources and cache status), refresh (clear cache at ~/.cache/pondus/), recommend <task-type> (suggest models for coding/reasoning/creative). Cache results for 24h in ~/.cache/pondus/. Flags: --format json|table|markdown. Use requests + simple HTML parsing. Test with: pondus sources. chmod +x."`

- [ ] `golem [t-b1e7c2] --provider zhipu --max-turns 30 "Build ~/bin/sarcio as a Python CLI for managing a digital garden. Posts live at ~/notes/Writing/Blog/Published/. Subcommands: new <title> (create a new draft .md file with frontmatter: title, date, tags, status=draft), list (list all posts with status), publish <filename> (set status=published in frontmatter, add published_date), revise <filename> (open in EDITOR), open <filename> (open in EDITOR), index (regenerate index.md listing all published posts). Use pathlib and yaml (PyYAML or frontmatter parsing). Test with: sarcio list. chmod +x."`

#### Tier 3 — specialized

- [ ] `golem [t-dbfdc1] --provider zhipu --max-turns 30 "Build ~/bin/keryx as a Python CLI wrapping wacli (WhatsApp CLI at ~/germline/effectors/wacli-ro). Subcommands: read <name> [--n N] (resolve contact name to JID, call wacli-ro read, merge dual-JID conversations), send <name> <message> [--execute] (print or execute wacli send command), chats [--n N] (list recent chats via wacli-ro chats), sync start|stop|status (manage wacli sync daemon). Contact resolution: maintain ~/.config/keryx/contacts.json mapping names to JIDs. Use subprocess to call wacli-ro. Test with: keryx chats. chmod +x."`

- [ ] `golem [t-6e540c] --provider zhipu --max-turns 30 "Build ~/bin/moneo as a Python CLI for Due app reminders. Due stores data in ~/Library/Group Containers/ on Mac but on Linux we use a synced JSON file at ~/.config/moneo/reminders.json. Subcommands: ls (list all reminders sorted by date), add <title> --date <datetime> [--repeat <interval>] (add reminder), rm <title> (delete by title match), edit <index> --title/--date (edit fields), log (show completion history from ~/.config/moneo/completions.jsonl). Print reminders as: date | title | repeat. Test with: moneo ls (should show empty or create sample data). chmod +x."`

- [ ] `golem [t-d54f38] --provider zhipu --max-turns 30 "Build ~/bin/anam as a Python CLI for searching AI chat history. Scans ~/.claude/projects/ for session JSONL files. Subcommands: (default) [date] (scan sessions for a date — default today — show prompts with timestamps), search <pattern> (grep across all session files for a regex pattern). Flags: --full (show all, not just last 50), --json (output as JSON), --tool claude|codex|opencode (filter by tool). Use glob + json. Test with: anam today. chmod +x."`

- [ ] `golem [t-e53737] --provider zhipu --max-turns 30 "Build ~/bin/auceps as a Python CLI wrapping the bird CLI (X/Twitter). Subcommands: (default) <input> (auto-route: if URL -> fetch tweet, if @handle -> fetch timeline, else -> search), thread <url> (follow quote-tweet chains), bird <args> (passthrough to bird CLI), post <text> (post via bird). Flags: --vault (output as Obsidian markdown), --lustro (output as lustro JSON), -n/--limit N (default 20). Use subprocess to call bird. Test with: auceps --help. chmod +x."`

### Hatchet dogfooding — advanced features

#### Webhooks — trigger from GitHub push
- [ ] `golem [t-013aa4] --provider zhipu --max-turns 40 "Read Hatchet webhooks API. Create a webhook endpoint that GitHub can call on push to vivesca repo. When triggered, dispatch new pending tasks from golem-queue.md. Steps: 1) Use h.webhooks.create() to register a webhook 2) Create effectors/hatchet-golem/webhook.py that handles the GitHub payload 3) Update .github/workflows/gemmule-wake.yml to also POST to the Hatchet webhook after waking gemmule. This replaces polling — tasks dispatch on push. Write tests. Commit."`

#### Worker labels + sticky sessions — provider affinity
- [ ] `golem [t-c7a3b1] --provider zhipu --max-turns 40 "Read Hatchet worker labels and sticky session docs. Modify effectors/hatchet-golem/worker.py to: 1) Register workers with labels like {provider: 'zhipu', region: 'cn'} 2) Use desired_worker_labels on tasks so zhipu tasks prefer zhipu-labeled workers 3) Add sticky=StickyStrategy.SOFT so repeated tasks from the same queue entry stick to the same worker (warm cache). Write tests. Commit."`

#### Priority queuing — high-priority tasks first
- [ ] `golem [t-8d9c37] --provider zhipu --max-turns 30 "Read Hatchet priority docs. Modify effectors/hatchet-golem/dispatch.py to: 1) Parse [!!] (high-priority) tasks and set default_priority=3 2) Parse [ ] (normal) tasks and set default_priority=1 3) This means Capco prep and fix tasks run before test-writing tasks. Write tests. Commit."`

#### Listener — real-time task completion stream
- [ ] `golem [t-3cb616] --provider zhipu --max-turns 40 "Read Hatchet listener API (h.listener.stream, h.listener.on). Create effectors/hatchet-golem/monitor.py that: 1) Streams task completion events in real-time 2) On success: runs git add + auto-commit (port from golem-daemon's auto_commit) 3) On failure: logs to ~/.local/share/vivesca/hatchet-failures.log 4) Prints a live dashboard: '[OK] t-abc123 zhipu 45s | [FAIL] t-def456 infini 2s | Running: 8 zhipu, 3 infini'. Write tests. Commit."`

#### Backoff — exponential retry for rate limits
- [ ] `golem [t-cd496a] --provider zhipu --max-turns 30 "Modify the golem tasks in effectors/hatchet-golem/worker.py. Add backoff_factor=2.0 and backoff_max_seconds=600 to each @hatchet.task decorator. This means: first retry after execution_timeout, second after 2x, third after 4x, capped at 10 min. Much better than the daemon's simple 1-retry. Write tests. Commit."`

#### Filters — route tasks by content
- [ ] `golem [t-dcf063] --provider zhipu --max-turns 40 "Read Hatchet filters API. Create filters that auto-route tasks: 1) Tasks containing 'consulting' or 'Capco' get priority=3 2) Tasks containing 'test' get priority=1 3) Tasks containing 'fix' or 'broken' get priority=2. Use h.filters.create() to set these up. Modify dispatch.py to attach additional_metadata={'category': 'consulting|test|fix|other'} to each run. Write tests. Commit."`

#### Multi-worker scaling — separate workers per provider
- [ ] `golem [t-491dc5] --provider zhipu --max-turns 40 "Refactor effectors/hatchet-golem/worker.py into per-provider workers. Create worker-zhipu.py, worker-infini.py, worker-volcano.py, worker-gemini.py — each registers only its own task. Then create effectors/hatchet-golem/start-workers.sh that launches all 4 in parallel with supervisor-style restart. This enables independent scaling: run 2 zhipu workers during peak. Write tests. Commit."`

#### Prometheus + Grafana observability
- [ ] `golem [t-bea486] --provider zhipu --max-turns 40 "Add a Prometheus + Grafana stack to effectors/hatchet-golem/docker-compose.yml. 1) Add prometheus container scraping Hatchet metrics via h.metrics.scrape_tenant_prometheus_metrics() endpoint 2) Add grafana container with a pre-built dashboard showing: tasks/min by provider, failure rate, queue depth, avg duration 3) Grafana on port 3000. Write a README section. Commit."`

### Consulting IP — Hatchet vs Temporal for banking clients

#### Hatchet vs Temporal comparison card for financial services
- [!!] `golem --provider zhipu --max-turns 50 "Write a consulting insight card comparing Hatchet and Temporal for AI agent orchestration in financial services. Structure: 1) Executive summary (2 sentences) 2) Problem statement — banks deploying AI agents need orchestration beyond simple task queues 3) Head-to-head comparison table: setup complexity, Python SDK maturity, concurrency model, rate limiting, observability, enterprise adoption, self-hosting, cost, AI-native features 4) When to recommend Temporal: regulated environments needing audit trails, existing Java/Go teams, complex multi-step compliance workflows 5) When to recommend Hatchet: AI-first teams, rapid prototyping, per-provider rate limiting, simpler ops 6) Hands-on experience section: 'We run both in production — Hatchet dispatches 30+ concurrent AI coding agents across 5 LLM providers with built-in rate limiting and concurrency control. Temporal provides durable execution for long-running compliance workflows.' 7) Key risks: Hatchet maturity (18 months old), Temporal operational complexity. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hatchet-vs-temporal-banking.md. 800+ words. Commit."`

#### AI agent orchestration patterns for enterprise
- [!!] `golem --provider zhipu --max-turns 50 "Write a consulting brief on AI agent orchestration patterns for enterprise banking. Cover: 1) The problem — banks running multiple AI agents (coding assistants, document processors, compliance checkers) need infrastructure beyond cron jobs 2) Pattern 1: Task queue (Celery/BullMQ) — simple but no durability 3) Pattern 2: Workflow engine (Temporal/Cadence) — durable but complex 4) Pattern 3: AI-native orchestrator (Hatchet) — built for LLM workloads 5) Pattern 4: Custom daemon — what most teams start with, why they outgrow it 6) Decision framework: when to use which 7) Reference architecture for a bank running 50+ AI agents 8) Our experience: migrated from custom daemon to Hatchet in one session, 2x reduction in code, built-in rate limiting replaced manual cooldown. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-agent-orchestration-patterns.md. 1000+ words. Commit."`

#### Hatchet quick-start guide for technical audience
- [ ] `golem --provider zhipu --max-turns 40 "Write a technical quick-start guide for Hatchet aimed at a bank's platform engineering team. Include: 1) What Hatchet is (one paragraph) 2) docker-compose setup (exact YAML for postgres + rabbitmq + engine + dashboard) 3) Python worker example — a simple task that calls an LLM API 4) Concurrency control — per-model rate limiting 5) Monitoring — dashboard + metrics API 6) Security considerations for banking (self-hosted, data sovereignty, auth tokens) 7) Comparison with what they're probably using (Airflow/Celery). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hatchet-quickstart-banking.md. Commit."`
