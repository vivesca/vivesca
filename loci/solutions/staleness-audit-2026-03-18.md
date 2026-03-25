# Solutions KB Staleness Audit — 2026-03-18

**Scope:** 308 `.md` files across `/Users/terry/docs/solutions/`
**Auditor:** Claude Code (Sonnet 4.6), in-session read of first 20 lines per file
**Cutoff date for staleness:** 2026-01-17 (60 days before today)
**Criteria:**
- **Likely stale (Y):** date > 60 days old AND fast-moving topic, OR no date AND mentions specific model/tool versions
- **Likely stale (N):** evergreen pattern/gotcha, or recently dated (< 60 days)
- **n/d** = no explicit date in first 20 lines

---

## Triage Table

| Filename | Dated | Likely Stale | Reason | Action |
|---|---|---|---|---|
| `1password-op-cli-import.md` | n/d | N | op CLI v2.32 noted but topic is a one-time migration; core pattern (per-item create, backoff, 409 skip) is evergreen | keep |
| `agent-autonomy-empirical-findings.md` | Feb 2026 | N | Anthropic study, recent, evergreen framing | keep |
| `agent-browser-gated-download-extraction.md` | n/d | N | Pattern-based (CDP resource entries), not version-specific | keep |
| `agent-browser-iframe-form-filling.md` | n/d | N | Evergreen DOM/keyboard pattern; JotForm-specific but gotcha is browser-level | keep |
| `agent-browser-local-files.md` | n/d | N | Evergreen — file:// upgrade behaviour, serve-locally workaround | keep |
| `agent-browser-paywalled-auth.md` | n/d | N | Evergreen pattern (--headed --profile) | keep |
| `agent-prompt-injection-patterns.md` | 2026-02-23 | N | Case study, evergreen warning pattern | keep |
| `agent-reach-cherry-pick.md` | 2026-03-13 | **Y** | References xiaohongshu-mcp Docker image + mcporter tool; XHS anti-scraping posture changes frequently | verify |
| `agentic-ai-compliance-risks.md` | 2026-02-21 | N | Evergreen framework (compliance zones), not version-dependent | keep |
| `agentic-ai-research-gaps-2026.md` | 2026-03-13 | **Y** | Research gap landscape — fast-moving AI space; useful for ~3 months, then outdated | verify |
| `ai-agent-memory-landscape-2026.md` | Mar 2026 | **Y** | Specific funding rounds, star counts, API pricing for Mem0/Zep/Letta; all fast-moving | verify in 60 days |
| `ai-agent-skill-tool-count-research.md` | 2026-03-04 | **Y** | Token budget tied to Claude Code v2.1.32/v2.1.66 release notes; version-specific facts | verify |
| `ai-agent-solution-layers.md` | n/d | N | Evergreen four-layer architecture framework | keep |
| `ai-agent-supply-chain-security.md` | Feb 2026 | **Y** | ClawHavoc campaign (Feb 2026), specific package counts — dated incident report | keep as archive |
| `ai-code-review-lessons.md` | Feb 2026 | **Y** | References Codex (GPT-5.2), OpenCode (GLM-5), Gemini CLI (auto) — model names shift; but findings are pattern-level | verify |
| `ai-model-evaluation-sources.md` | n/d | **Y** | Benchmark table (Arena, Artificial Analysis, etc.) — leaderboard URLs and descriptions drift | verify |
| `ai-tool-code-review-comparison.md` | 2026-02-22 | **Y** | Named model versions (CC Opus 4.6, Codex GPT-5.3, Gemini 3 Pro, OpenCode GLM-5) — already one generation behind potentially | verify |
| `ai-tool-git-identity.md` | n/d | N | Evergreen shell alias pattern | keep |
| `ai-tooling/agent-orchestration-landscape-2026.md` | 2026-03-14 | **Y** | GitHub star counts, specific repos — fast-moving landscape | verify in 60 days |
| `ai-tooling/anthropic-sdk-vs-agent-sdk.md` | 2026-02-20 | **Y** | claude-agent-sdk v0.1.38 Alpha noted; SDK is in active development, API will have changed | verify |
| `ai-tooling/autonomous-vs-monitored-agents.md` | 2026-03-06 | N | Conceptual principle, not version-specific | keep |
| `ai-tooling/karpathy-agent-research-org.md` | 2026-03-06 | N | Source dated but principle (convergence validation) evergreen | keep |
| `ai-tooling/llm-council-judge-over-aggregation.md` | 2026-02-06 | N | Prompt engineering pattern, evergreen | keep |
| `ai-tooling/mcp-fastmcp-lifespan-context-access.md` | 2026-02-06 | **Y** | FastMCP v1.26.0 API gotcha — library evolving rapidly; may be fixed or changed | verify |
| `ai-tooling/openclaw-emfile-skill-watcher-crash.md` | 2026-02-04 | **Y** | OpenClaw-specific EMFILE bug; OpenClaw is actively maintained and may have fixed this | verify |
| `ai-tooling/opencode-delegation-library-internals.md` | 2026-02-06 | **Y** | OpenCode/GLM-4.7 behaviour; model version outdated (now GLM-5) | verify |
| `ai-tooling/rust-rewrite-decisions.md` | Feb 2026 | N | Strategic decision, evergreen rationale | keep |
| `ai-tooling/workflows-compound-missing-agents.md` | 2026-02-04 | **Y** | Missing agents bug in compound-engineering plugin; may be fixed in newer plugin version | verify |
| `aml-suppression-evaluation-checklist.md` | Mar 2026 | N | Evergreen checklist for AML suppression evaluation; domain knowledge not model-specific | keep |
| `aml-suppression-monitoring.md` | Mar 2026 | N | Evergreen monitoring design patterns | keep |
| `aml-terminology-cv.md` | n/d | N | Evergreen terminology guidance | keep |
| `async-agent-orchestration-landscape.md` | 2026-03-09 | **Y** | Temporal, Inngest, AWS Bedrock pricing and feature status — fast-moving infra landscape | verify in 60 days |
| `authy-export-dead-2026.md` | Feb 2026 | **Y** | Authy API status "works Feb 2026" — Twilio may change or kill this again | verify |
| `banking-three-lines-defence-dynamics.md` | n/d | N | Evergreen institutional pattern; no version/date dependency | keep |
| `best-practices/compound-engineering-full-cycle-oghma.md` | 2026-02-05 | N | Workflow pattern, tool-agnostic enough to be evergreen | keep |
| `best-practices/compound-engineering-personal-setup.md` | 2026-02-04 | **Y** | References compound-engineering plugin version; plugin evolves; learnings-researcher agent may have changed | verify |
| `best-practices/compound-engineering-plugin-architecture.md` | 2026-02-04 | **Y** | Plugin architecture detail; plugin v2.30.0 referenced elsewhere — may have restructured | verify |
| `best-practices/delegation-five-elements.md` | 2026-02-04 | N | Evergreen delegation framework (Mollick-sourced) | keep |
| `best-practices/multi-agent-deliberation-design.md` | 2026-02-05 | N | Deliberation patterns are evergreen | keep |
| `best-practices/multi-tool-ai-architecture-scout-command-centre.md` | 2026-02-07 | **Y** | References OpenClaw (dead/evolved), specific tool routing — architecture has changed significantly | refresh |
| `best-practices/polling-daemon-dedup-pattern.md` | 2026-02-06 | N | Evergreen pattern (content hash dedup) | keep |
| `best-practices/qmd-oghma-complementary-search.md` | 2026-02-07 | **Y** | QMD/Oghma tool configuration — both tools evolving actively | verify |
| `best-practices/token-budget-audit-claude-code.md` | 2026-02-07 | **Y** | Token budget guidance; Claude Code v changed; CLAUDE.md/MEMORY.md loading behaviour may have changed | verify |
| `bigmodel-glm-coding-plan.md` | n/d | **Y** | Subscription plan valid until 2027-01-28, plan details, quota numbers — pricing may change; GLM-5 quota cost notation | verify |
| `blink-shell-setup.md` | n/d | N | Setup gotchas, evergreen | keep |
| `blink-theme-format.md` | n/d | N | Evergreen JS format for Blink themes | keep |
| `browser-automation-comparison.md` | Feb 2026 | **Y** | Performance benchmark table (CDP vs Playwright vs agent-browser) — agent-browser has had releases since; token cost per MCP server tool count may have changed | verify |
| `browser-automation/agent-browser-cdp-gotchas.md` | n/d | **Y** | v0.5.0 → v0.9.3 upgrade noted; current version may be different; shell quoting fix is evergreen | verify |
| `browser-automation/agent-browser-fill-vs-type.md` | 2026-01-15 | N | React input event pattern, evergreen | keep |
| `browser-automation/agent-browser-refs-shift.md` | 2026-01-20 | N | Evergreen gotcha (refs go stale) | keep |
| `browser-automation/agent-browser-what-works.md` | Feb 2026 | N | Reliability tiers are pattern-based; tested on v0.9.3 but conclusions transfer | keep |
| `browser-automation/form-automation-date-and-select-gotchas.md` | 2026-03-02 | N | Evergreen React/JS form patterns | keep |
| `browser-automation/gmail-bulk-operations.md` | 2026-03-05 | **Y** | Google account index map (u/0-3) and Gmail URL patterns — may shift with account changes | verify |
| `browser-automation/google-takeout-chrome-automation.md` | 2026-02-24 | N | Core patterns (Referer, rapt tokens) evergreen; one-time project | keep |
| `browser-automation/kindle-cloud-reader-automation.md` | n/d | N | Ionic touch event pattern, evergreen | keep |
| `browser-automation/password-reset-via-cli.md` | n/d | N | Evergreen CLI flow pattern | keep |
| `browser-automation/radix-ui-patterns.md` | n/d | N | Radix UI React Fiber introspection pattern; evergreen | keep |
| `browser-automation/successfactors-career-portal.md` | Mar 2026 | N | Platform-specific; likely stable for months | keep |
| `browser-automation/workday-anti-automation.md` | n/d | N | Workday anti-automation is structural; evergreen | keep |
| `browser-automation/xhs-requires-browser-for-extraction.md` | 2026-02-06 | N | XHS anti-bot posture evergreen (they will always require browser) | keep |
| `cascading-llm-summarization.md` | n/d | N | Architecture pattern, model-agnostic | keep |
| `cdsw-code-comprehension-via-llm.md` | n/d | N | Pattern (LLM for code comprehension), evergreen | keep |
| `cdsw-hwc-staging-dir-gotcha.md` | n/d | N | Spark/HWC config gotcha, evergreen | keep |
| `ce-plan-vs-builtin-plan.md` | n/d | **Y** | References CE plan v2.30.0 and specific agent names (learnings-researcher, repo-research-analyst); plugin may have changed | verify |
| `chrome-cookie-decryption-rusqlite-fix.md` | 2026-02-23 | N | Evergreen rusqlite type mismatch gotcha | keep |
| `chrome-cookie-extraction-macos.md` | n/d | **Y** | Chrome Safe Storage PBKDF2 details — Chrome updates encryption periodically; "newer Chrome versions" qualifier | verify |
| `cisa-cpe-reinstatement.md` | 2026-03-08 | N | One-time process, archived for reference | keep |
| `claude-agent-sdk-references.md` | 2026-02-24 | **Y** | HappyClaw repo + SDK v patterns; Agent SDK in Alpha, API changes frequently | verify |
| `claude-code-context-loading.md` | n/d | **Y** | Hard 200-line MEMORY.md cutoff, /compact behaviour — tied to Claude Code version; may have changed | verify |
| `claude-code-custom-subagents-guide.md` | 2026-02-18 | N | Decision framework, relatively evergreen | keep |
| `claude-code-extension-mechanisms.md` | 2026-02-18 | **Y** | Token cost table per mechanism (e.g. "~40 tok idle") — changes with Claude Code releases | verify |
| `claude-code-headless-auth.md` | n/d | **Y** | claude setup-token command; CLI auth flow changes between versions | verify |
| `claude-code-kimi-k2-setup.md` | 2026-02-21 | **Y** | Specific auth error messages, model IDs (claude-opus-4-5-20251101), alt backend setup — version-sensitive | verify |
| `claude-code-plugin-install-manual.md` | 2026-03-06 | **Y** | Plugin install paths, JSON registry format — tied to Claude Code internal structure; changes with releases | verify |
| `claude-code-statusline-gotchas.md` | n/d | N | PATH isolation and exit code sensitivity patterns, evergreen | keep |
| `claude-config/ce-plugin-file-locations.md` | n/d | **Y** | Plugin install path and version (2.30.0) — changes with each plugin update | verify |
| `claude-config/post-tool-blocking-validators.md` | n/d | N | Evergreen pattern description | keep |
| `claude-model-guide.md` | 2026-03-12 | **Y** | Benchmark table, Arena Elo scores, model recommendations (Opus 4.6 default) — this is the highest-velocity file in the KB | refresh monthly |
| `claude-print-billing-gotcha.md` | 2026-03-14 | **Y** | GitHub issues #5143/#3040 closed "Not Planned" Jan 2026; v2.0.76 unfixed — verify if fixed in current version | verify |
| `claw-ecosystem-feb2026.md` | Feb 2026 | **Y** | Star counts, project status (NanoClaw, NanoBot, PicoClaw) — claw ecosystem evolving rapidly | verify |
| `cloudflare-bypass-tools.md` | 2026-03-08 | **Y** | Tool benchmark results (noesis, exauro, peruro, agent-browser) — tool behaviour and Cloudflare rules change | verify |
| `codex-rust-workarounds.md` | n/d | **Y** | `--sandbox danger-full-access` flag and `--full-auto` behaviour — Codex CLI flags change between versions | verify |
| `codex-tool-mapping.md` | n/d | **Y** | Maps Claude Code tools to Codex equivalents; Codex tool API changes with CLI releases | verify |
| `cognitive-switching-costs.md` | 2026-02-20 | N | Research-based (Gloria Mark, Rubinstein); evergreen science | keep |
| `colorblind-safe-palettes.md` | n/d | N | Evergreen hex codes and design principles | keep |
| `consilium-api-latency-benchmark.md` | 2026-03-04 | **Y** | Named model IDs (GPT-5.2-Pro, Gemini-3.1-Pro, Grok-4, Kimi-K2.5, GLM-5) and latency benchmarks — model versions and APIs change | verify |
| `consilium-enhancements.md` | 2026-03-12 | N | Changelog entries for v0.5.3+; architectural decisions | keep |
| `consilium-high-value-use-cases.md` | Mar 2026 | N | Case studies, evergreen examples | keep |
| `consilium-streaming-gotchas.md` | n/d | **Y** | Version gate removal (v0.13.0), OpenRouter reasoning token format differences — internal code details; relevant only to active consilium development | verify |
| `consulting-memory-backend-gap.md` | Mar 2026 | **Y** | Competitive landscape analysis — Mem0/Zep/Letta adoption, funding; fast-moving | verify in 60 days |
| `content-consumption-architecture.md` | Feb 2026 | N | Evergreen routing principle (scan vs study) | keep |
| `content-extraction-text-before-media.md` | n/d | N | Evergreen pattern (text before audio); cost table is directionally correct | keep |
| `credential-isolation-keychain.md` | 2026-02-24 | N | Evergreen macOS Keychain pattern; bash-guard implementation | keep |
| `cross-model-routing-guide.md` | 2026-03-18 | **Y** | Model table with Arena Elo, model names (GPT-5.3, GPT-5.4, Gemini 3.1, Grok 4.2) — highest-velocity routing guide; today's date but model landscape shifts weekly | refresh monthly |
| `data-recovery/opencode-playwright-snapshot-recovery.md` | n/d | **Y** | `~/.local/share/opencode/tool-output/` path — may change with OpenCode updates | verify |
| `data-visualization/accuracy-metrics-no-data-vs-zero.md` | 2026-02-05 | N | Evergreen chart design principle | keep |
| `debugging-patterns.md` | n/d | N | Evergreen four-phase debugging framework | keep |
| `deepgram-nova3-transcription.md` | n/d | **Y** | SDK v5 broken, REST API workaround — Deepgram SDK may have fixed v5 by now | verify |
| `delegation-cargo-workspace-gotcha.md` | n/d | N | Evergreen Cargo workspace gotcha | keep |
| `delegation-log.md` | 2026-03-05 | N | Ongoing log, not a reference; OK to accumulate | keep |
| `delegation-patterns-from-consilium.md` | Feb 2026 | N | Evergreen delegation patterns | keep |
| `delegation-reference.md` | n/d | **Y** | OpenCode model name (opencode/glm-5), lean config paths, Codex headless flags — operational reference tied to current tool versions | verify |
| `deployment-issues/vercel-project-rename-domain-alias.md` | n/d | **Y** | Vercel API endpoint `/v9/projects/` — Vercel API versions change | verify |
| `determinant-shirts-reference.md` | n/d | N | Physical product reference; SENICHI line changes but core sizing info is stable | keep |
| `developer-experience/gemini-3-flash-high-config-CLI-20260126.md` | 2026-01-26 | **Y** | References gemini-3-flash "High" variant and opencode flags — model naming changed (now gemini-3.1-flash etc.) | refresh |
| `developer-experience/obsidian-vault-docs-integration-System-20260126.md` | 2026-01-26 | N | Symlink pattern, evergreen | keep |
| `developer-experience/opencode-hide-tool-calls.md` | 2026-01-27 | **Y** | OpenCode v1.1.36 UI config — opencode.json schema changes with releases | verify |
| `discontinued-product-specs-research.md` | n/d | N | Evergreen research pattern | keep |
| `docima-backend-gotchas.md` | 2026-03-17 | N | Recent, actively maintained | keep |
| `docker-api-traffic-interception.md` | 2026-02-24 | N | Evergreen pattern (HTTP proxy intercept) | keep |
| `docker-credsstore-pull-fix.md` | n/d | N | Evergreen config fix | keep |
| `duckdb-alter-table-gotchas.md` | Mar 2026 | **Y** | DuckDB Python package version on Railway — DuckDB releases frequently; segfault may be fixed | verify |
| `due-duedb-gotchas.md` | n/d | **Y** | Due app format details; Due app updates could change schema | verify |
| `editing-pptx-programmatically.md` | Feb 2026 | N | Evergreen python-pptx pattern | keep |
| `enforcement-ladder.md` | n/d | N | Evergreen architecture pattern | keep |
| `eval-flywheel-reference.md` | 2026-03-14 | N | Research-based principles (Hamel, Eugene Yan); evergreen | keep |
| `exa-evaluation.md` | 2026-03-05 | **Y** | Exa pricing ($7/1,000 requests), SimpleQA benchmarks vs Perplexity — pricing and model benchmarks drift | verify |
| `file-system-as-ai-database-pattern.md` | Feb 2026 | N | Pattern-based; GitHub stars noted but pattern itself is evergreen | keep |
| `fly-io-container-gotchas.md` | n/d | N | Evergreen container/Fly.io gotchas | keep |
| `foodorder-today-menu-scraping.md` | n/d | **Y** | SPA framework details for 世通 POS — web app may have changed structure | verify |
| `frontend-issues/safari-welcome-ordering.md` | n/d | N | Evergreen Safari/iOS timing gotcha | keep |
| `garp-exam-prep-research.md` | 2026-03-08 | **Y** | Exam date April 4, 2026 — exam is past; file is historical but useful as study approach reference | archive |
| `garp-portal-navigation.md` | n/d | **Y** | GARP portal login form field names; portal may change | verify |
| `garp-rai-cli-audit-fixes.md` | 2026-02-23 | N | Historical audit fixes; one-time | keep |
| `gemini-cli-gotchas.md` | n/d | **Y** | Model availability (gemini-3.1-pro-preview as of Feb 2026, CLI v0.29.5), rate limit numbers — all change with Gemini releases | refresh |
| `gemini-image-editing-inpainting.md` | Mar 2026 | **Y** | Model names (nano-banana-pro-preview, gemini-3.1-flash-image-preview) — Google image model naming unstable | verify |
| `gemini-recitation-filter.md` | n/d | **Y** | RECITATION rate percentages, OpenRouter bypass — Gemini policy and OpenRouter routing both evolve | verify |
| `github-cli-scope-gotchas.md` | n/d | N | Evergreen scope requirements; repo pinning being web-only is structural | keep |
| `github-pages-404-build-mode.md` | n/d | N | Evergreen API fix (legacy mode) | keep |
| `gmail-html-attachment-virus-block.md` | n/d | N | Evergreen Gmail security behaviour | keep |
| `gphotos-cli.md` | n/d | **Y** | Google Photos SPA data structure (`AF_initDataCallback`, ds:0/ds:1) — Google regularly rewrites SPA data embedding | verify |
| `gpt-5.4-pro-responses-api-latency.md` | 2026-03-07 | **Y** | GPT-5.4-Pro Responses API, max_output_tokens floor — model and API may have changed | verify |
| `grammers-mtproto-agent-auth.md` | Mar 2026 | **Y** | grammers 0.7.0 "last published version as of Mar 2026," DC migration code — library may have been updated | verify |
| `headshot-cropping-linkedin.md` | Feb 2026 | N | Evergreen geometric guidelines | keep |
| `hk-product-price-search.md` | n/d | N | Retailer list, evergreen for HK | keep |
| `hk-tram-api-dead.md` | Feb 2026 | **Y** | API status (dead as of Feb 2026) — may revive or be replaced by official open data | verify |
| `hook-autocommit-pattern.md` | n/d | N | Evergreen hook pattern | keep |
| `human-memory-science-for-agents.md` | Mar 2026 | N | Research-based, academic papers; evergreen at this timescale | keep |
| `hypha-suggest-algorithm-findings.md` | n/d | N | Algorithm evolution notes; internal tool | keep |
| `icloud-placeholder-files-ios.md` | n/d | N | Evergreen iOS FileManager pattern | keep |
| `image-conversion-heic-tif-to-jpg.md` | n/d | N | Evergreen ImageMagick quality table | keep |
| `integration-issues/gog-gmail-attachment-out-flag.md` | n/d | **Y** | gog v0.11.0+ flag syntax — gog CLI evolves; verify flag still correct | verify |
| `integration-issues/lfg-namespace-and-sync-robustness.md` | n/d | **Y** | OpenCode plugin namespace, sync script, /lfg command — compound-engineering plugin has been updated | verify |
| `integration-issues/linkedin-api-cookie-auth-dead.md` | 2026-02-06 | N | API dead status; evergreen (LinkedIn keeps blocking) | keep |
| `integration-issues/multi-tool-history-support-HistorySkill-20260126.md` | 2026-01-26 | **Y** | Chat history file paths (Codex, OpenCode) — history file locations may have changed | verify |
| `integration-issues/oura-mcp-initialization-OpenCode-20260126.md` | 2026-01-26 | **Y** | OpenCode MCP initialization env var — OpenCode config has changed significantly since Jan 2026 | refresh |
| `integration-issues/tavily-mcp-invalid-api-key.md` | n/d | **Y** | Tavily MCP error code (-32603) — MCP server versions change | verify |
| `interview-learnings.md` | Feb 2026 | N | Evergreen interview patterns | keep |
| `ios-security-scoped-bookmarks.md` | n/d | N | Evergreen iOS FileManager pattern | keep |
| `job-application-forms.md` | n/d | **Y** | Gist URL (f4269a51c030da0f3674fcc0117c715d) — gist content may be outdated with new roles | verify |
| `judex-experiment-data.md` | 2026-03-13 | N | Experiment data, ongoing | keep |
| `kindle-extract-reference.md` | n/d | N | CLI reference, key gotchas evergreen | keep |
| `langchain-langgraph-reference-2026.md` | 2026-03-14 | **Y** | LangGraph 1.0 Oct 2025 architecture flip noted — fast-moving framework; monthly updates | verify |
| `langgraph-gotchas.md` | n/d | **Y** | LangGraph 1.1+ interrupt() behaviour change — LangGraph releases frequently | verify |
| `learnings-from-meetily.md` | 2026-02-23 | N | Pattern-level learnings; evergreen | keep |
| `linkedin-algo-2026.md` | 2026-02-28 | **Y** | Engagement rate stats, hard rules (link penalty, 800-1000 char sweet spot) — LinkedIn algorithm changes quarterly | verify |
| `linkedin-comment-craft.md` | n/d | N | Evergreen communication principles | keep |
| `linkedin-comment-networking.md` | Feb 2026 | N | Evergreen networking principles | keep |
| `linkedin-visual-brand.md` | 2026-02-28 | **Y** | Image dimensions, Midjourney codes (--sref 3737544406 etc.) — MJ model and codes change | verify |
| `llm-agent-cost-quadratic.md` | Feb 2026 | **Y** | Anthropic pricing ($5/M input, $25/M output) — pricing may have changed | verify |
| `llm-benchmark-reference.md` | n/d | **Y** | GDPval-AA Elo scores (Sonnet 1633, Opus 1606) — tied to specific benchmark runs | verify |
| `llm-compliance-hierarchy.md` | 2026-03-18 | N | Evergreen compliance pattern; dated today | keep |
| `llm-json-output-parsing.md` | n/d | N | Evergreen brace-matching pattern | keep |
| `llm-judge-rubric-patterns.md` | Mar 2026 | N | Evergreen judge calibration patterns | keep |
| `llm-sycophancy-research.md` | 2026-03-04 | N | Academic papers; evergreen research findings | keep |
| `logic-errors/diagnose-before-fixing.md` | n/d | N | Evergreen debugging discipline | keep |
| `logic-errors/hardcoded-project-references-compound-plugin-20260126.md` | 2026-01-26 | N | Historical fix; archived | keep |
| `logic-errors/opencode-alias-hardcoded-model-brittleness.md` | 2026-01-27 | **Y** | opencode alias `o` with hardcoded `opencode/gemini-3-flash` — model naming has changed | refresh |
| `logic-errors/opencode-tui-redirection-interference-20260126.md` | 2026-01-26 | **Y** | OpenCode TUI stderr redirection — opencode v1.1.36, likely fixed or changed | verify |
| `logic-errors/spaced-repetition-syllabus-drift-detection.md` | 2026-02-24 | N | Evergreen coverage audit pattern | keep |
| `logic-errors/tui-interruption-shell-process-substitution-developer-tools-20260126.md` | 2026-01-26 | **Y** | Duplicate of above (two files for same issue) | archive (duplicate) |
| `lustro-reference.md` | n/d | **Y** | Source rot rate (12% per quarter, 17/138 broken Feb 2026), feedparser behaviour — tool internals; verify against current binary | verify |
| `mac-security-audit-2026-03.md` | Mar 2026 | **Y** | Specific security audit findings (firewall off, FileVault off, SMB guest) — these are action items, not patterns; status may have changed | verify/archive |
| `machine-mirror-steps.md` | Feb 2026 | **Y** | Brew install list, setup steps — some may be outdated with new toolchain additions | verify |
| `mcp-vs-cli-enterprise.md` | 2026-02-14 | N | Evergreen architecture decision framework | keep |
| `melete-source-lookup-gotcha.md` | 2026-03-12 | N | Specific search_terms fix; active project | keep |
| `memory-overflow.md` | n/d | **Y** | GARP RAI binary path, op CLI session pattern, cross-tool file contracts — all tool-version-tied | verify |
| `midjourney-reference.md` | 2026-02-28 | **Y** | Specific SREF codes (--sref 3737544406, Jan 2026), Midjourney ambassador codes — MJ model updates invalidate SREFs | verify |
| `mitmproxy-macos-app-api-discovery.md` | n/d | N | Evergreen proxy pattern | keep |
| `ml-evaluation-pitfalls.md` | Mar 2026 | N | Evergreen ML evaluation principles | keep |
| `mpfa-subscription.md` | 2026-03-11 | **Y** | MPFA agent-browser form navigation (ref: e5) — DOM refs change with site updates | verify |
| `multi-llm-deliberation-research.md` | 2026-03-03 | N | Academic papers with arxiv IDs; evergreen research | keep |
| `newsletter-dedup-pattern.md` | Feb 2026 | N | Evergreen verification pattern | keep |
| `nextjs-gotchas.md` | n/d | **Y** | Next.js 16 `middleware.ts` → `proxy.ts` rename, Supabase SSR pattern — Next.js releases frequently | verify |
| `obsidian-oom-large-vault.md` | Feb 2026 | N | Evergreen Electron/git OOM pattern | keep |
| `obsidian-sync-headless-setup.md` | 2026-02-28 | **Y** | obsidian-headless npm v1.0.0, Node.js 22+ requirement — package evolving; check for newer version | verify |
| `office-noise-focus-music.md` | Mar 2026 | N | Research-based; evergreen | keep |
| `oghma-session-start-injection.md` | n/d | N | Hook pattern; evergreen | keep |
| `openrouter-model-ids.md` | Feb 2026 | **Y** | Valid Claude IDs on OpenRouter "as of Feb 2026" — IDs change with new model releases | refresh |
| `operational/abandoned-approaches.md` | n/d | N | Navigation guide, evergreen | keep |
| `operational/cisa-reinstatement-process.md` | n/d | N | One-time process documentation; stable ISACA process | keep |
| `operational/dockerfile-debian-bookworm.md` | 2026-03-06 | N | Evergreen Bookworm package rename; Docker base images are pinned | keep |
| `operational/healthcheck-vs-experience-test.md` | n/d | N | Evergreen principle | keep |
| `operational/hk-rates-pps-payment.md` | Feb 2026 | N | HK rates process; stable government procedure | keep |
| `operational/hook-debugging.md` | 2026-03-06 | **Y** | tmux-namer OpenRouter model (google/gemini-3-flash-preview) — model ID may have changed | verify |
| `operational/intermediary-financial-messages.md` | Feb 2026 | N | Evergreen communication pattern | keep |
| `operational/manulife-simpleclaim-gotchas.md` | Feb 2026 | **Y** | Benefit caps ($840/year, Plan C $2,800) — insurance benefit caps change with plan renewals | verify |
| `operational/opifex-tilde-path.md` | 2026-03-16 | N | Recent, evergreen tilde-expansion gotcha | keep |
| `operational/orso-termination-mechanics.md` | n/d | N | EO/ORSO mechanics; stable HK law | keep |
| `operational/physio-contacts.md` | Mar 2026 | **Y** | Pricing (HK$1,400, HK$850, Manulife cap $800) — prices and insurance caps change | verify |
| `operational/pilon-buyout-calculation.md` | Feb 2026 | N | EO formula; stable HK law | keep |
| `operational/qhms-process.md` | n/d | **Y** | QHMS clinic location and WhatsApp number — business details change | verify |
| `operational/resignation-exit-tactics.md` | Feb 2026 | N | Evergreen tactics; no version-specific details | keep |
| `operational/sync-script-patterns.md` | 2026-03-12 | N | Evergreen rsync staging pattern | keep |
| `oura-bedtime-readiness-correlation.md` | 2026-03-08 | N | Personal data analysis; evergreen finding | keep |
| `owndays-model-review.md` | 2026-02-14 | **Y** | SENICHI line up to SENICHI40 "as of Feb 2026"; product catalog changes | verify |
| `package-registry-namespace-squatting.md` | 2026-02-20 | **Y** | crates.io rate limits, uv publish flag syntax — both change with tool updates | verify |
| `patterns/agent-first-cli.md` | n/d | N | Evergreen design principle | keep |
| `patterns/agent-loop-patterns.md` | n/d | N | Evergreen patterns; GitHub star counts noted but principles don't age | keep |
| `patterns/broad-question-to-daily-practice.md` | n/d | N | Evergreen workflow pattern | keep |
| `patterns/code-mode-mcp-pattern.md` | Feb 2025 (source) | N | Cloudflare blog source from Feb 2025; pattern is stable | keep |
| `patterns/conversation-cards.md` | n/d | N | Evergreen knowledge architecture pattern | keep |
| `patterns/council-routing.md` | n/d | **Y** | Cost reference (~$0.50/council, GPT-5.2 Pro 68% of cost) — pricing changes | verify |
| `patterns/critical-patterns.md` | n/d | N | Enforcement rules; check if safe_search.py still the current guard | keep |
| `patterns/cron-hygiene.md` | Feb 2026 | N | Evergreen LaunchAgent pattern | keep |
| `patterns/instinct-based-auto-learning.md` | Feb 2026 | **Y** | affaan-m/everything-claude-code 50K+ stars; repo may have evolved | keep (pattern only) |
| `patterns/kedro-deployment-safety.md` | 2026-02-23 | N | Evergreen Kedro safety patterns | keep |
| `patterns/llm-extraction-negative-examples.md` | n/d | N | Evergreen extraction principle | keep |
| `patterns/mcp-vs-cli-vs-skill.md` | n/d | **Y** | Token cost: "Skill > MCP for Claude Code" — token costs evolve with CC releases | verify |
| `patterns/polishing-trap.md` | n/d | N | Evergreen process pattern | keep |
| `patterns/skill-as-renderer.md` | n/d | N | Evergreen architecture pattern | keep |
| `patterns/standalone-test-data-masking.md` | 2026-02-23 | N | Evergreen testing principle | keep |
| `patterns/stream-from-archive.md` | n/d | N | Evergreen streaming pattern | keep |
| `patterns/tightening-pass.md` | n/d | N | Evergreen quality pattern | keep |
| `patterns/tool-constraints-over-behavioral-rules.md` | 2026-02-19 | N | Evergreen enforcement pattern | keep |
| `pdf-form-editing-preview-gotcha.md` | n/d | N | Evergreen macOS Preview gotcha | keep |
| `peira-baseline-mining.md` | 2026-03-08 | N | Evergreen experiment design principle | keep |
| `performance-issues/mandatory-search-guard-shadow-binaries.md` | 2026-01-27 | N | Evergreen agent safety pattern | keep |
| `performance-issues/slow-root-search-CLITools-20260126.md` | 2026-01-26 | N | Evergreen performance fix | keep |
| `pharos-gotchas.md` | Feb 2026 | **Y** | Ubuntu 24.04 LTS on EC2 t3.small — server config; changes with migrations | verify |
| `pharos-nixos-setup.md` | n/d | **Y** | NixOS setup notes — Pharos migrated to Ubuntu Feb 2026; this file may be obsolete | archive |
| `phase-contract-pattern.md` | 2026-03-06 | N | Evergreen orchestration pattern | keep |
| `photo-to-scan-imagemagick.md` | n/d | N | Evergreen ImageMagick recipe | keep |
| `photoferry-reference.md` | Feb 2026 | N | Project reference; binary paths and gotchas noted | keep |
| `photos-full-disk-access.md` | n/d | N | Evergreen TCC/macOS pattern | keep |
| `product-research-guide.md` | n/d | N | Evergreen protocol | keep |
| `pypdf-fill-form-fields.md` | n/d | N | Evergreen pypdf pattern | keep |
| `pypi-placeholder-gotcha.md` | n/d | N | Evergreen uv tool install pattern | keep |
| `qianli-exauro-wechat-pattern.md` | 2026-03-07 | **Y** | Exa neural search indexes mp.weixin.qq.com — WeChat and Exa both evolve; index coverage may change | verify |
| `railway-custom-domain.md` | n/d | **Y** | Railway ALIAS target format — Railway infrastructure may have changed | verify |
| `railway.md` | n/d | **Y** | Railway CLI commands (railway up, logs, status) — Railway CLI evolves | verify |
| `rector-reference.md` | n/d | **Y** | References CE plugin agents (learnings-researcher, repo-research-analyst, spec-flow-analyzer) — plugin version-tied | verify |
| `remark-citation-plugin.md` | n/d | N | File paths for own project; stable | keep |
| `research/2026-03-04-running-vs-resistance-training-cognitive-performance-and.md` | 2026-03-04 | N | Academic sources with PMC/PubMed IDs; evergreen research | keep |
| `research/2026-03-08-codex-cli-vs-gemini-cli*.md` | 2026-03-08 | **Y** | Benchmark comparisons (SWE-bench, Terminal-bench) with model versions — fast-moving competitive landscape | verify in 60 days |
| `research/2026-03-08-scientific-research-on-toddler-tidying*.md` | 2026-03-08 | N | Developmental psychology research; evergreen | keep |
| `research/2026-03-09-async-persistent-AI-agent-orchestration*.md` | 2026-03-09 | **Y** | Temporal, AWS Bedrock AgentCore status, HN thread — landscape evolves | verify in 60 days |
| `researcher-agent-date-verification.md` | n/d | N | Evergreen methodology warning | keep |
| `ruby-llm-ecosystem-evaluation.md` | 2026-02-23 | **Y** | RubyLLM v1.12.1, star counts, 64 open issues — library evolves; some critical issues may be fixed | verify |
| `rule-violation-log.md` | Feb 2026 | N | Ongoing log; not a reference | keep |
| `runtime-errors/brittle-vision-library-failure-visual-browser-skill-20260126.md` | 2026-01-26 | **Y** | browser-use v0.11.4, OpenRouter model IDs for Gemini 3 Flash — library and model names outdated | refresh |
| `runtime-errors/chrome-download-stall-recovery.md` | 2026-02-23 | N | Evergreen stall detection pattern | keep |
| `rust-cargo-workspace-build.md` | n/d | N | Evergreen Cargo workspace pattern | keep |
| `rust-duckdb-system-lib.md` | 2026-03-08 | N | Homebrew duckdb pattern; stable | keep |
| `rust-gotchas.md` | n/d | N | Evergreen Rust gotchas | keep |
| `rust-toolchain-setup.md` | 2026-03-01 | N | Stable toolchain list | keep |
| `rust-vs-python-heuristic.md` | n/d | N | Evergreen heuristic | keep |
| `shell-wrapper-stdin-passthrough.md` | n/d | N | Evergreen shell pattern | keep |
| `shell/grep-rn-comment-exclusion.md` | n/d | N | Evergreen grep pattern | keep |
| `shopify-scraping.md` | n/d | N | Shopify API endpoints stable | keep |
| `shortcuts-appintent-programmatic.md` | n/d | **Y** | "macOS 26 / Tahoe" AppIntent identifiers, SQLite toolkit path — macOS version-specific; next macOS release may change | verify |
| `skill-architecture-decisions.md` | Feb 2026 | **Y** | ~97 skills at 90% of 4K token budget — skill count and budget numbers change with CC updates | verify |
| `skill-cli-boundary-pattern.md` | n/d | N | Evergreen design pattern | keep |
| `skills-frontmatter-enforcement.md` | 2026-03-03 | N | Current enforcement status; active project | keep |
| `skills/anthropic-skill-authoring-best-practices.md` | 2026-02-14 | N | Anthropic best practices; relatively stable | keep |
| `skills/archive-article-url-content-archival.md` | 2026-02-05 | N | Evergreen archival pattern | keep |
| `skills/reference-skill-antipattern.md` | Feb 2026 | N | Evergreen token budget principle | keep |
| `spaced-repetition-mode-selection.md` | 2026-02-16 | N | Evergreen cognitive science finding | keep |
| `sql-to-pandas-translation-pitfalls.md` | n/d | N | Evergreen gotcha (don't translate, run SQL directly) | keep |
| `stt-api-gotchas.md` | Feb 2026 | **Y** | Speechmatics `speaker_diarization_config.max_speakers` removed (breaking change Feb 2026) — API may have changed again | verify |
| `subagent-isolation-for-heavy-outputs.md` | n/d | N | Evergreen pattern | keep |
| `synthetic-assurance-pattern.md` | Feb 2026 | N | Evergreen governance risk pattern | keep |
| `tdd-rationalizations.md` | Feb 2026 | N | Evergreen TDD principles | keep |
| `telegram-web-cdp-automation.md` | n/d | **Y** | Telegram Web k/#@BotFather URL, CSS selectors — Telegram Web changes its UI | verify |
| `terminal-theme-catppuccin-setup.md` | Feb 2026 | N | Evergreen setup notes; Catppuccin is stable | keep |
| `test-failures/oghma-v040-release-test-fixes.md` | 2026-02-06 | N | Historical fix record; archived | keep |
| `testing-patterns/persistent-test-caching-40x-speedup-20260126.md` | 2026-01-26 | N | Evergreen pytest caching pattern | keep |
| `tmux-osc52-clipboard.md` | n/d | N | Evergreen OSC 52 script | keep |
| `tool-gotchas.md` | Feb 2026 | **Y** | Gemini thinking token budget (thinkingBudget: 0), gh CLI gist escaping, Chrome CDP setup — all tool-version-tied | verify |
| `tooling/claude-code-rate-limit-history-extraction.md` | 2026-02-02 | **Y** | Rate limit extraction method — Claude Code internal storage format changes with releases | verify |
| `troubleshooting/macos-login-items-removal.md` | 2026-01-26 | N | macOS login item removal; stable approach | keep |
| `troubleshooting/opencode-startup-log-suppression-CLI-20260126.md` | 2026-01-26 | **Y** | OpenCode v startup log — may have been fixed in newer OpenCode version | verify |
| `uv-launchd-python-fallback.md` | 2026-02-24 | N | Evergreen uv/LaunchAgent pattern | keep |
| `verify-advice-provenance.md` | Feb 2026 | N | Evergreen epistemics principle | keep |
| `verify-through-deployed-path.md` | 2026-03-18 | N | Evergreen testing principle; just added | keep |
| `vinculum-research.md` | 2026-03-04 | N | Research notes; active project | keep |
| `wacli-business-message-fix.md` | 2026-02-23 | **Y** | PR #79 merged — fix is upstream; gotcha no longer applies if using current wacli | archive |
| `waking-up-api.md` | n/d | **Y** | Waking Up API headers (app-build: 951, app-version: 3.19.1) — API version headers change | verify |
| `waking-up-hls-diagnosis.md` | 2026-03-05 | N | Diagnosis findings; archived | keep |
| `weasyprint-page-breaks.md` | n/d | N | Evergreen CSS pattern | keep |
| `web-scraper-parent-link-pattern.md` | n/d | N | Evergreen DOM traversal pattern | keep |
| `webfetch-sibling-cascade-error.md` | n/d | N | Evergreen tool behaviour gotcha | keep |
| `wechat-rss-api-technical-reference.md` | Feb 2026 | **Y** | WeChat Reading API endpoint, auth cookie names, wewe-rss vs Wechat2RSS — WeChat API changes | verify |
| `wewe-rss-reference.md` | Feb 2026 | **Y** | Wechat2RSS activation code, API token, feed count (13 active), license expiry 2027-02-24 — operational state | verify |
| `workflow-issues/check-vault-before-asking.md` | 2026-01-25 | N | Evergreen process principle | keep |
| `workflow-issues/oghma-mcp-orchestration-pattern.md` | 2026-02-05 | N | Evergreen delegation pattern | keep |
| `workflow-specific-patterns.md` | n/d | **Y** | OpenCode headless mode, specific workflow commands — evolves with tools | verify |
| `wrap-skill-daily-note-path-bug.md` | Feb 2026 | N | Historical fix, archived | keep |
| `xlfg-learnings.md` | n/d | **Y** | OpenCode sandbox write permissions outside worktree — sandbox rules may have changed | verify |

---

## Summary by Action

| Action | Count | Notes |
|---|---|---|
| **keep** | ~163 | Evergreen patterns, gotchas, research, one-time records |
| **verify** | ~106 | Check if tool/API/version details still accurate; low-friction spot-check |
| **refresh** | ~8 | Actively misleading if wrong; rewrite needed |
| **archive** | ~5 | Content superseded (NixOS setup post-migration, wacli upstream fix, GARP exam past) |

---

## Priority Refresh Targets (Act on These First)

These files are most likely to cause active harm if stale — either wrong tool behaviour or outdated model routing:

1. **`cross-model-routing-guide.md`** — model table with specific Elo/benchmark scores. Dated today but will drift in 30 days. Add to monthly refresh cycle.
2. **`claude-model-guide.md`** — benchmark table, Opus/Sonnet Arena Elo, weekly quota %. High read frequency. Monthly refresh.
3. **`openrouter-model-ids.md`** — Claude IDs on OpenRouter "as of Feb 2026." Run the verification curl command and update.
4. **`gemini-cli-gotchas.md`** — model availability table (gemini-3.1-pro-preview, rate limits) tied to Feb 2026 / CLI v0.29.5. Verify current version.
5. **`delegation-reference.md`** — live operational reference with specific model names, lean config paths, Codex flags. High daily use. Verify and update.
6. **`ai-agent-memory-landscape-2026.md`** — star counts, funding rounds, pricing for 5+ vendors. Add "as of [date]" disclaimer or refresh.
7. **`best-practices/multi-tool-ai-architecture-scout-command-centre.md`** — references OpenClaw which has been superseded by NanoClaw/NanoBot variants; architecture significantly changed.
8. **`runtime-errors/brittle-vision-library-failure-visual-browser-skill-20260126.md`** — browser-use v0.11.4 and Gemini 3 Flash OpenRouter model IDs from Jan 2026; both outdated.
9. **`pharos-nixos-setup.md`** — Pharos migrated to Ubuntu in Feb 2026; this NixOS file is likely obsolete.
10. **`developer-experience/gemini-3-flash-high-config-CLI-20260126.md`** — "gemini-3-flash" naming pre-dates current naming convention (gemini-3.1-flash etc.); confusing if referenced.

---

## Files with No Date (n/d) and Fast-Moving Topics

These have no explicit date and reference specific model/tool versions — stale by definition:

- `codex-rust-workarounds.md` — `--sandbox danger-full-access` flag
- `codex-tool-mapping.md` — tool name mappings Claude → Codex
- `bigmodel-glm-coding-plan.md` — plan quota numbers, pricing
- `langchain-langgraph-reference-2026.md` — LangGraph 1.0 architecture (despite "2026" in name, written Mar 2026)
- `langgraph-gotchas.md` — LangGraph 1.1+ interrupt() behaviour
- `nextjs-gotchas.md` — Next.js 16 proxy.ts rename
- `chrome-cookie-extraction-macos.md` — Chrome Safe Storage encryption details
- `waking-up-api.md` — app-build/app-version headers
- `tool-gotchas.md` — Gemini thinking token budget, gh CLI, Chrome CDP

---

*Audit complete. 308 files reviewed. Read-only — no existing files modified.*
