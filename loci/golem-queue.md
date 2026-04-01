# Golem Task Queue

CC writes fully-specified entries. Daemon executes mindlessly.
All providers 89-97% capable — spread tasks across all 5 for quota pacing.

## Pending

### North Star 2: Career — Capco Week 1 readiness (build, not prose)

- [ ] `golem [t-cap01] --provider zhipu --max-turns 40 "Build ~/germline/effectors/capco-brief. Python CLI. Subcommands: capco-brief stakeholders (reads ~/epigenome/chromatin/Capco Transition.md and any Capco*.md files, extracts all named people with roles into a quick-reference table), capco-brief calendar (reads fasti output for next 5 days, groups by client vs internal), capco-brief checklist (reads ~/docs/pulse/capco-day1-*.md, outputs unchecked items as actionable list). Output markdown to stdout. Add --help. chmod +x. Commit."`
- [ ] `golem [t-cap02] --provider infini --max-turns 40 "Build ~/germline/effectors/card-search. Python CLI that searches ~/epigenome/chromatin/euchromatin/consulting/cards/*.md by keyword. Usage: card-search 'model risk' → shows matching cards with title + first 3 lines. card-search --full 'bias' → shows full card content. card-search --list → shows all cards with titles. Uses simple grep, no dependencies. Useful for quick recall during client calls. chmod +x. Commit."`
- [ ] `golem [t-cap03] --provider volcano --max-turns 40 "Read all files in ~/epigenome/chromatin/euchromatin/consulting/cards/. Audit each for: 1) length >300 words 2) has all 5 sections (problem, why it matters, approach, considerations, Capco angle) 3) no placeholder text 4) factually plausible regulatory references. Write audit results to ~/germline/loci/copia/card-audit-report.md. List cards that pass, cards that need fixes (with specific issues), and missing topic gaps for banking AI consulting. Commit."`

### High priority — daemon + automation

- [x] `golem [t-8851fe] [t-qp01] --provider codex --max-turns 40 "Read effectors/golem-daemon. In the dispatcher loop where tasks are picked from the queue, change task pickup so that when a task's tagged provider is in cooldown, the task becomes available to any non-frozen provider. Do NOT rewrite the queue line — keep the original provider tag for stats, but dispatch to whoever is free. When a provider is NOT in cooldown, respect the original provider affinity. This is cross-provider task migration. Read the existing cooldown logic first to understand the data structures. Write tests that: 1) mock a provider in cooldown state 2) verify its pending tasks get dispatched to another provider 3) verify tasks for non-frozen providers still respect affinity. Run uv run pytest on new tests. Commit."`
- [x] `golem [t-gog01] --provider zhipu --max-turns 40 "Rewrite gog (Gmail CLI) as a Python effector at ~/germline/effectors/gog. The original was a Rust binary. Read the gog references in membrane/receptors/stilus/SKILL.md and membrane/receptors/epistula/SKILL.md to understand the interface. Subcommands needed: gog gmail read [--full] [--unread] [--from X] [--after DATE], gog gmail send --to X --subject X --body X, gog gmail reply --id X --body X, gog gmail archive --id X, gog gmail search --query X. Use Google Gmail API via google-api-python-client + oauth2client. Store OAuth credentials at ~/.config/gog/credentials.json, token at ~/.config/gog/token.json. Print results as: date | from | subject | snippet. Add --help. chmod +x. Write subprocess tests at assays/test_gog.py. Commit."`
- [x] `golem [t-porta01] --provider zhipu --max-turns 40 "Rewrite porta (web auth gateway) as a Python effector at ~/germline/effectors/porta. Read the porta references in membrane/receptors/ to understand the interface — grep -r porta membrane/receptors/. Core function: manage browser cookies/auth state for headless automation. Subcommands: porta status (show active sessions), porta login <service> (interactive OAuth/cookie capture), porta export --service X (export cookies for curl/requests), porta clear --service X. Store sessions at ~/.config/porta/sessions/. Use browser_cookie3 or similar for cookie extraction. Add --help. chmod +x. Write subprocess tests at assays/test_porta.py. Commit."`
- [x] `golem [t-72bfe7] [t-auto01] --provider codex --max-turns 40 "Soma (Linux/Fly.io) has no scheduled automation — the 22 LaunchAgents at ~/officina/launchd/ are macOS .plist files that don't work on Linux. Create a crontab from the plist definitions. Steps: 1) Read all .plist files in ~/officina/launchd/ 2) Extract the schedule (StartCalendarInterval or StartInterval) and the command (ProgramArguments) from each 3) Convert to cron syntax 4) Write to a file at ~/officina/soma-crontab.txt 5) Install with crontab ~/officina/soma-crontab.txt. Before installing, print the generated crontab for review. Skip any agents that depend on macOS-only tools (launchctl, osascript, security find-generic-password). Commit the crontab file."`

### Test infrastructure — fixture fix

- [ ] `golem [t-fix-tmp] --provider zhipu --max-turns 25 "Multiple tests fail because /tmp/pytest-vivesca does not exist. Find all test files that reference this path: grep -r 'pytest-vivesca' assays/. Either 1) add a conftest.py fixture that creates /tmp/pytest-vivesca as a tmpdir before tests run and cleans up after, or 2) replace hardcoded /tmp/pytest-vivesca with tmp_path (pytest built-in fixture) in each test file. Option 2 is preferred — it's the pytest-native approach. Run uv run pytest on affected files after fixing. Commit."`

### Test infrastructure (dedup'd — one of each)

- [x] `golem [t-a27bf7] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-1a5413] --provider codex --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-2ef0fd] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`

### Effector health (dedup'd)

- [x] `golem [t-b8fb38] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-2d020a] --provider zhipu --max-turns 30 "Health check: taste-score, queue-gen, quorum, launchagent-health, circadian-probe.py, immunosurveillance, vesicle, receptor-health, phagocytosis.py, golem-validate. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-19745a] --provider gemini --max-turns 30 "Health check: chat_history.py, channel, search-guard, oura-weekly-digest.py, legatum-verify, cn-route, find, lacuna, chemoreception.py, regulatory-scan. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`

### Codebase quality

- [x] `golem [t-c864f1] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f031c4] --provider codex --max-turns 30 "Find ALL files in ~/germline/ containing hardcoded macOS home paths. Replace with Path.home() (Python) or $HOME (shell). Verify nothing breaks. Commit."`

### Test coverage — targeted modules

- [x] `golem [t-6ddb89] --provider codex --max-turns 40 "Write tests for /home/terry/germline/metabolon/organelles/phenotype_translate.py (560 lines). Read the module first. Mock external calls. Write to assays/test_organelles_phenotype_translate.py. Target 80%+ line coverage. Run uv run pytest assays/test_organelles_phenotype_translate.py -v. Fix all failures. Commit."`
- [x] `golem [t-8a7c3b] --provider gemini --max-turns 25 "Write tests for /home/terry/germline/metabolon/enzymes/kinesin.py (63 lines). Read the module first. Mock external calls. Write to assays/test_enzymes_kinesin.py. Aim for 100% coverage given small size. Run uv run pytest assays/test_enzymes_kinesin.py -v. Fix all failures. Commit."`

### Effector tests (dedup'd — one per effector)

- [x] `golem [t-47b27f] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-435845] --provider infini --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-df9840] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-aa755e] --provider codex --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [!] `golem [t-9a3712] --provider gemini --max-turns 30 "Write tests for effectors/cibus.py. Read the script first. Test via subprocess.run — NEVER import. Write to assays/test_cibus.py. Run uv run pytest on the new file. Fix failures. Commit." (retry)`

### Consulting IP — Capco readiness

- [x] `golem [t-5cc21a] --provider zhipu --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-6f9244] --provider volcano --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-b9f28c] --provider infini --max-turns 30 "Write a consulting insight card: Cross-border AI regulation comparison — HK vs SG vs UK vs EU. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/cross-border-ai-regulation.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-4ce3b5] --provider codex --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [!] `golem [t-7c35d2] --provider gemini --max-turns 30 "Write a consulting insight card: AI talent strategy for banks — building vs buying AI capability. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-talent-strategy.md. Structure: problem, three talent models, skills taxonomy for banking AI, retention strategies, upskilling pathways, Capco angle. 600-900 words. Commit." (retry)`
- [x] `golem [t-cdb8cf] --provider zhipu --max-turns 30 "Write a consulting insight card: AI center of excellence setup guide for banks — from 0 to operating in 90 days. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-coe-setup-guide.md. Structure: problem, 90-day roadmap (week-by-week), governance structure, team composition, success metrics, common pitfalls, Capco angle. 700-1000 words. Commit."`
- [x] `golem [t-211b2c] --provider codex --max-turns 40 "Write a comprehensive briefing on Hong Kong financial regulation for AI/technology: HKMA, SFC, IA key circulars and expectations around AI adoption in banking, insurance, securities. Include HKMA's Supervisory Policy Manual modules on technology risk (TM-E-1, OR-1). Write to ~/epigenome/chromatin/euchromatin/consulting/cards/hk-ai-regulatory-landscape.md. 500+ words. Commit."`
- [x] `golem [t-cf8a10] --provider volcano --max-turns 30 "Write a conversation guide: First meeting with a Capco managing director — building credibility as an AI/technology specialist. Write to ~/epigenome/chromatin/euchromatin/consulting/playbooks/first-meeting-md.md. Structure: 5 talking points that demonstrate depth without overselling, 3 questions to ask about current engagements, how to position AI expertise as complementary to Capco's FS domain, things to avoid, how to offer immediate value. 500-700 words. Commit."`

### Daemon improvements

- [x] `golem [t-9dffa6] --provider codex --max-turns 30 "Read effectors/golem-daemon, specifically auto_commit(). Add retry logic: if git push fails (network error), retry 3 times with 30s backoff. If all retries fail, log error but don't crash daemon. Also add: if git pull fails at startup, continue with local state rather than crashing. Write tests. Commit."`
- [!] `golem [t-d69304] --provider gemini --max-turns 35 "Read effectors/golem-daemon. Add a 'top' subcommand that shows currently running golems: task_id, provider, elapsed_time, prompt snippet. Read RUNNING_FILE for task state. Write tests. Commit." (retry)`
- [x] `golem [t-f1adb3] --provider zhipu --max-turns 40 "Read effectors/golem (the shell script). Infini provider (deepseek-v3.2 at cloud.infini-ai.com) has intermittent exit=2 failures with 0s duration. Debug: 1) Check INFINI_API_KEY is correctly formatted 2) Test the endpoint directly with curl 3) Check if rate limiting or quota exhaustion is the cause 4) Read daemon logs for infini-specific error patterns. Write findings and fix. Commit."`

### Random test fixes (dedup'd)

- [x] `golem [t-f5d33f] --provider infini --max-turns 35 "Run uv run pytest -q --tb=no 2>&1 | grep '^FAILED' | shuf | head -10. For each: run pytest on that file, read traceback, fix. Iterate until green. Commit."`

## Killed (CC triage 2026-04-01)

Removed 22 tasks:
- **Duplicates (11):** pytest collection fix x2, golem-dash x2, effector --help x1, pytest --co x1, update-coding-tools test x2, random test fix x3
- **Dead path — ~/bin/ removed (4):** stips, fasti, sarcio, moneo — these already exist as skills
- **Speculative infra (3):** Temporal Docker setup, Hatchet webhook, supervisor config — against "simplify don't engineer"
- **Low-value (1):** standup-log CLI
- **Already done (1):** epigenome marks git tracking
- **Path-dependent (2):** perplexity.sh test (dup), backup-due.sh test (dup of existing)

### Auto-requeue (14 tasks @ 22:53)
- [x] `golem [t-c44a51] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-13455f] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-0716e0] --provider infini --max-turns 30 "Health check: start-chrome-debug.sh, weekly-gather, log-summary, search-guard, cg, rename-plists, soma-activate, browse, golem-health, launchagent-health. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-069533] --provider volcano --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7342c4] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-7f7df6] --provider infini --max-turns 30 "Write tests for effectors/plan-exec.deprecated. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fe5984] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-699a66] --provider zhipu --max-turns 30 "Write tests for effectors/qmd-reindex.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-2b1f59] --provider infini --max-turns 25 "Find subprocess.run calls without timeout in effectors/. Add timeout=300. Commit."`
- [x] `golem [t-bb4c2d] --provider volcano --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-5545cd] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-26b2e5] --provider infini --max-turns 30 "Write a consulting insight card: AI vendor due diligence questionnaire for banks. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-vendor-due-diligence.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-0c0303] --provider volcano --max-turns 30 "Write a consulting insight card: AI model risk management framework for banks — write a consulting brief with problem, approach, key considerations. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-model-risk-framework.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-212582] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 22:53)
- [x] `golem [t-ccf324] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-55b0b3] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit." (retry)`
- [x] `golem [t-a30d32] --provider infini --max-turns 30 "Health check: coaching-stats, update-compound-engineering, golem-cost, golem-validate, plan-exec, evident-brief, tmux-url-select.sh, legatum, cytokinesis, exocytosis.py. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-b8c4b6] --provider volcano --max-turns 30 "Write tests for effectors/update-coding-tools.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-303f28] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-33be17] --provider infini --max-turns 30 "Write tests for effectors/auto-update-compound-engineering.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ae4a14] --provider volcano --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-c984c9] --provider zhipu --max-turns 30 "Write tests for effectors/hetzner-bootstrap.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-0d8a5d] --provider infini --max-turns 25 "Check all assays/test_*.py can be collected by pytest --co. Fix any that error. Commit."`
- [x] `golem [t-d613b7] --provider volcano --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-d3bc19] --provider zhipu --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-69718c] --provider infini --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-89678a] --provider volcano --max-turns 30 "Write a consulting insight card: Data governance for AI/ML training data in banking. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/data-governance-ai.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-202510] --provider zhipu --max-turns 35 "Read effectors/golem-daemon. Add cmd_stats — show pass/fail/retry counts, avg duration by provider, tasks completed today. Usage: golem-daemon stats. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 23:03)
- [x] `golem [t-cc421a] --provider zhipu --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-0e6d69] --provider infini --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-d16ffe] --provider volcano --max-turns 30 "Health check: goose-worker, quorum, plan-exec.deprecated, safe_rm.py, respirometry, test-spec-gen, weekly-gather, centrosome, engram, coverage-map. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-956754] --provider zhipu --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-827b8c] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-16f797] --provider volcano --max-turns 30 "Write tests for effectors/start-chrome-debug.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-90e019] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-cdf585] --provider infini --max-turns 30 "Write tests for effectors/golem-orchestrator. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-a3cb3a] --provider volcano --max-turns 25 "Scan assays/ for hardcoded macOS home paths. Replace with Path.home(). Commit."`
- [x] `golem [t-5cdbed] --provider zhipu --max-turns 25 "Find test files with SyntaxError. Fix syntax. Commit."`
- [x] `golem [t-63cb0b] --provider infini --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-9dc45d] --provider volcano --max-turns 30 "Write a consulting insight card: AI bias testing framework for credit decisioning. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-bias-testing.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-1117e1] --provider zhipu --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-15808f] --provider infini --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 03:33)
- [x] `golem [t-6ca158] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-c5b96e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-d66010] --provider infini --max-turns 30 "Health check: generate-solutions-index.py, rename-kindle-asins.py, council, cn-route, phagocytosis.py, compound-engineering-status, find, oci-arm-retry, oura-weekly-digest.py, diapedesis. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-1e71a0] --provider volcano --max-turns 30 "Write tests for effectors/tmux-osc52.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-ba350e] --provider zhipu --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-6ba64a] --provider infini --max-turns 30 "Write tests for effectors/backup-due.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-fc9db2] --provider volcano --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-85d2a1] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-env.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-b9efbf] --provider infini --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-18cfad] --provider volcano --max-turns 25 "Check all effectors respond to --help without crashing. Fix crashers. Commit."`
- [x] `golem [t-712da6] --provider zhipu --max-turns 25 "Scan effectors/ for hardcoded paths. Fix with Path.home() or $HOME. Commit."`
- [x] `golem [t-417ee9] --provider infini --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-000294] --provider volcano --max-turns 30 "Write a consulting insight card: GenAI policy template for bank employees. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/genai-policy-template.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-adcd2d] --provider zhipu --max-turns 35 "Read effectors/golem-review (if exists). Enhance to also check consulting content quality (>200 words, proper structure). Write tests. Run uv run pytest. Commit."`

### Auto-requeue (14 tasks @ 03:36)
- [x] `golem [t-18dafe] --provider volcano --max-turns 40 "Run uv run pytest --co -q 2>&1 | grep ERROR. Fix ALL collection errors. Common: hardcoded paths, bad imports, syntax. Run --co again until 0 errors. Commit."`
- [x] `golem [t-b41e8e] --provider zhipu --max-turns 50 "Run uv run pytest -q --tb=no --continue-on-collection-errors 2>&1 | grep FAILED | sed 's/::.*//g' | sort | uniq -c | sort -rn | head -5. For each of the top 5 failing test files: run pytest on it, read traceback, fix. Iterate until green. Commit."`
- [x] `golem [t-598907] --provider infini --max-turns 30 "Health check: chromatin-decay-report.py, rotate-logs.py, safe_rm.py, wacli-ro, regulatory-capture, launchagent-health, safe_search.py, golem-cost, chat_history.py, golem-orchestrator. For each: run --help, ast.parse if Python, check shebang. Fix broken ones. Commit."`
- [x] `golem [t-91d0aa] --provider volcano --max-turns 30 "Write tests for effectors/perplexity.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-81792c] --provider zhipu --max-turns 30 "Write tests for effectors/pharos-health.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-083829] --provider infini --max-turns 30 "Write tests for effectors/update-compound-engineering-skills.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-268fda] --provider volcano --max-turns 30 "Write tests for effectors/chromatin-backup.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-211cc5] --provider zhipu --max-turns 30 "Write tests for effectors/agent-sync.sh. Effectors are scripts — use exec or subprocess.run. NEVER import. Run uv run pytest. Fix failures. Commit."`
- [x] `golem [t-76aaa3] --provider infini --max-turns 25 "Find Python files missing shebang in effectors/. Add #!/usr/bin/env python3. Commit."`
- [x] `golem [t-f19634] --provider volcano --max-turns 25 "Scan assays/ for hardcoded $HOME paths. Replace with Path.home(). Commit."`
- [x] `golem [t-6886a8] --provider zhipu --max-turns 25 "Find unused imports in metabolon/**/*.py. Remove them. Commit."`
- [x] `golem [t-f4e863] --provider infini --max-turns 30 "Write a consulting insight card: Responsible AI governance checklist for financial institutions. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/responsible-ai-checklist.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-8ffdb9] --provider volcano --max-turns 30 "Write a consulting insight card: AI incident response playbook for financial services. Write to ~/epigenome/chromatin/euchromatin/consulting/cards/ai-incident-response.md. Structure: problem (2 sentences), why it matters (3 bullets), approach (numbered steps), considerations, Capco angle. 500-800 words."`
- [x] `golem [t-9de427] --provider zhipu --max-turns 35 "Read effectors/golem-dash (if exists). Improve to show real-time task progress, ETA to drain. Write tests. Run uv run pytest. Commit."`

### Vivesca improvements (build)

- [ ] `golem [t-vi01] --provider volcano --max-turns 40 "The golem-daemon mark_failed() retries rate-limited tasks but doesn't track HOW MANY times a task has been retried. Add a retry counter: when re-queuing a task, append [retry:N] to the queue line. In parse_queue(), extract this counter. After 5 retries, mark as permanently failed [!!] instead of re-queuing. Update stats to show retry distribution. Write tests. Commit."`
- [ ] `golem [t-vi02] --provider infini --max-turns 40 "Build ~/germline/effectors/golem-report. Python CLI that reads golem.jsonl and golem-queue.md, generates a markdown report: tasks completed today, by provider, success rate, avg duration, rate-limit events, top 3 longest tasks, top 3 most-retried. Output to stdout. Add --date flag for historical reports. Commit."`
- [ ] `golem [t-vi03] --provider codex --max-turns 40 "The Temporal worker at ~/germline/effectors/temporal-golem/worker.py spawns golem subprocesses but doesn't log results to golem.jsonl like the daemon does. Add JSONL logging: after each activity completes, append {timestamp, task, provider, exit_code, duration_s, success, rate_limited} to ~/.local/share/vivesca/golem.jsonl. Match the daemon's format exactly — read golem-daemon's logging to see the schema. Commit."`
- [ ] `golem [t-vi04] --provider gemini --max-turns 40 "golem-orchestrator dispatch has a 300s timeout that's too short for large batches. Fix: 1) Make dispatch.py exit immediately after submitting the workflow (don't wait for completion — Temporal tracks that). 2) Add golem-orchestrator results <workflow-id> command that queries Temporal for workflow result. 3) Update dispatch to print the workflow ID so user can check later. Commit."`
- [ ] `golem [t-vi05] --provider zhipu --max-turns 40 "Build ~/germline/effectors/golem-dash. Python CLI, reads golem.jsonl in real-time (tail -f style). Shows live updating table: per-provider active/completed/failed/rate-limited counts, rolling success rate, estimated time to queue drain. Use rich library for terminal UI. Commit."`
- [ ] `golem --provider infini --max-turns 50 "Write assays/test_auto_update_compound_engineering.sh.py for effectors/auto-update-compound-engineering.sh. Run uv run pytest assays/test_auto_update_compound_engineering.sh.py -v --tb=short."`
- [ ] `golem --provider zhipu --max-turns 50 "Write assays/test_circadian_probe.conf.py for effectors/circadian-probe.conf. Run uv run pytest assays/test_circadian_probe.conf.py -v --tb=short."`
- [ ] `golem --provider volcano --max-turns 50 "Write assays/test_com.vivesca.soma_pull.plist.py for effectors/com.vivesca.soma-pull.plist. Run uv run pytest assays/test_com.vivesca.soma_pull.plist.py -v --tb=short."`
- [ ] `golem --provider infini --max-turns 50 "Write assays/test_exocytosis.conf.py for effectors/exocytosis.conf. Run uv run pytest assays/test_exocytosis.conf.py -v --tb=short."`
- [ ] `golem --provider zhipu --max-turns 50 "Write assays/test_fasti.py for effectors/fasti. Run uv run pytest assays/test_fasti.py -v --tb=short."`
- [ ] `golem --provider infini --max-turns 50 "Write assays/test_pharos_env.sh.py for effectors/pharos-env.sh. Run uv run pytest assays/test_pharos_env.sh.py -v --tb=short."`
- [ ] `golem --provider zhipu --max-turns 50 "Write assays/test_pharos_health.sh.py for effectors/pharos-health.sh. Run uv run pytest assays/test_pharos_health.sh.py -v --tb=short."`
- [ ] `golem --provider volcano --max-turns 50 "Write assays/test_pharos_sync.sh.py for effectors/pharos-sync.sh. Run uv run pytest assays/test_pharos_sync.sh.py -v --tb=short."`
- [ ] `golem --provider infini --max-turns 50 "Write assays/test_plan_exec.deprecated.py for effectors/plan-exec.deprecated. Run uv run pytest assays/test_plan_exec.deprecated.py -v --tb=short."`
- [ ] `golem --provider zhipu --max-turns 50 "Write assays/test_qmd_reindex.sh.py for effectors/qmd-reindex.sh. Run uv run pytest assays/test_qmd_reindex.sh.py -v --tb=short."`
- [ ] `golem --provider infini --max-turns 50 "Write assays/test_regulatory_scrape.py for effectors/regulatory-scrape. Run uv run pytest assays/test_regulatory_scrape.py -v --tb=short."`
