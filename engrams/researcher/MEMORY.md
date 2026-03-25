# Researcher Agent Memory

## Obsidian Vault Rename & Wikilink Update Tools (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/obsidian-vault-rename-wikilink-tools-2026.md`
- Best headless CLI: notesmd-cli (Go, yakitrak) — confirmed headless, move updates "all links in vault"
- Best Rust library: turbovault-batch (Epistates/turbovault) — MoveNote + UpdateLinks, parser claims full wikilink syntax
- Official Obsidian CLI (v1.12.4): best link fidelity but REQUIRES app running (will auto-launch)
- NOT useful: obsidian-metadata (frontmatter only), obsidiantools (analysis only), Foam (VS Code only)
- Edge case (aliases/headings/display text): only turbovault-parser explicitly claims full syntax; notesmd-cli unverified

## Leaked/Published System Prompts — Structural Patterns (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/leaked-system-prompts-structural-patterns-2026.md`
- Coverage: Cursor, Claude Code (110+ conditional strings), Cline, v0, Bolt, Lovable, Devin, Manus, Windsurf, ChatGPT/GPT-5
- Sources: x1xhlol repo (36 tools, 30K+ lines), Piebald-AI CC prompts (v2.1.78), jujumilk3 dated snapshots
- Top steal-worthy patterns: constraint-first architecture, one-action-per-turn loop, custom XML output tags, explicit mode separation (Plan/Act), modular conditional loading, security monitor pre-execution layer, CAPS for non-negotiable rules, example-driven behavioral spec, anti-verbosity as explicit rule
- Windsurf "mother's cancer" prompt: confirmed R&D only, NOT production — common misinformation to flag
- Best analysis source: simonwillison.net + Piebald-AI/claude-code-system-prompts

## Open-Source IDE & Coding Agents — Technical Patterns (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/open-source-ide-coding-agents-2026.md`
- Covers: Cline, Roo Code, Continue, Bolt.new/diy, Lovable, v0, Sweep, SWE-agent, mini-SWE-agent, Goose
- Cline: PromptRegistry with model-family fallback; Memory Bank (community convention > product feature); `/newtask` clean-context handoff
- Roo Code: LIFO task stack (not just prompt engineering); summary-only upward propagation; role-based modes prevent cross-mode contamination
- Continue: Rules-as-CI-agents = same markdown rule file enforced in IDE + CI pipeline; Continue Hub marketplace for team rules sharing
- Bolt.new: Streaming artifact execution (parse + execute during LLM stream, before response completes); serialised ActionRunner promise chain
- Lovable: Discussion-default mode (requires action verbs to enter execution); constraint repetition as behavioral guardrail; debug-tools-before-code ordering
- v0: Mandatory `<Thinking>` tags before every CodeProject; stable CodeProject ID; QuickEdit (surgical edits not full regen); 90+ item feature flag list
- Sweep: 10-15k token planning window (peak quality, avoids LLM "lost in middle"); bipartite AST graph + TF-IDF dual search; (file, instructions) pairs for planning
- SWE-agent: ACI as discipline — design interfaces for LM agents not humans; linter-in-edit-loop = synchronous syntax feedback; summary-mode search outputs
- mini-SWE-agent: 100 lines, bash only, 74% SWE-bench verified — "capability over scaffolding" thesis
- Goose: MCP-native from day one (no proprietary format); error-as-tool-response (not exception); context revision WITHIN loop (step 5 of 6)

## MCP Ecosystem Patterns — Servers, Design, Security, Performance (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/mcp-ecosystem-patterns-2026.md`
- 7,300+ servers on Smithery; top by usage: Sequential Thinking, wcgw, GitHub, Brave Search
- 4 tool design patterns: Semantic Search / Workflow Bundling / Code Mode / Progressive Discovery
- Transport rule: stdio=local, Streamable HTTP=remote (SSE deprecated Mar 2025)
- Spec versions: 2025-03-26 (Streamable HTTP), 2025-06-18 (OAuth 2.1 + ResourceLink), 2025-11-25 (Tasks, URL elicitation, CIMD)
- Claude Code ToolSearch v2.1.7: 95% context reduction; `serverInstructions` = what it matches on
- Security: CVE-2025-6514 (mcp-remote RCE); tool poisoning via registry; credential gold standard = OS keychain at execution time only
- Composition: FastMCP mount/namespace; Gateway pattern (auth+routing+audit); Aggregators (Pipedream 2,500 APIs)
- Performance: connection pool = 80% of gains; tool definitions 50–1,000 tokens each; Cursor hard limit 40 tools

## Claude Code Power User Patterns (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/claude-code-power-user-patterns-2026.md`
- Hook enforcement: PreToolUse = only blocking hook; Stop hook exit 2 = force continuation; UV single-file scripts = best impl pattern
- CLAUDE.md: <200 lines, ancestor+descendant hierarchy, 70%/85%/90% context thresholds
- Top frameworks: SuperClaude (30 cmds, 16 personas), BMAD (agile multi-agent), Continuous-Claude (ledger/handoff), OpusPlan (hybrid routing)
- Git worktree = canonical parallel agent isolation; incident.io runs 7 concurrent sessions
- Session Memory (Feb 2026): continuous background summaries; "Compound, don't compact" philosophy
- Cost: OpusPlan 5x reduction; Haiku subagents 10-20x cheaper; lazy MCP = 85% token savings
- Internals: Claude Code uses conditional assembly of 110+ prompt fragments, not monolithic

## Context Engineering & Agent Meta-Techniques (Mar 2025–Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/context-engineering-agent-meta-techniques-2026.md`
- Core term: Karpathy Jun 2025 — "delicate art and science of filling context window with right info for next step." LLM = CPU, context = RAM.
- Four-category framework: Write / Select / Compress / Isolate (LangChain/Karpathy taxonomy)
- KV-cache hit rate = #1 production metric (Manus): 10x cost difference cached vs uncached. Stable prefixes + append-only context required.
- File system as external memory (Manus, Devin): drop content, keep paths — enables restoration. Unlimited effective context.
- todo.md attention hack (Manus): continuously rewrite current objectives to avoid lost-in-the-middle over 50+ tool calls.
- Error retention: leave failed actions in context — models update beliefs implicitly, reduce repeated mistakes.
- Self-correction limits: cannot self-correct reasoning WITHOUT external signal (execution, retrieval). Fresh-context review helps for style/format only.
- Planning: ReAct (baseline), Plan-then-Execute (predictable), CodeAct (+20% ICML 2024), ReWOO (parallel), ToT (superseded by internal reasoning).
- Production 2025 pattern: deterministic backbone + scoped agent at decision points + observability + HITL checkpoints.
- Eval: pass@k (not @1), progress rate (partial credit), cost-of-pass. TheAgentCompany SOTA: 30.3%. Tau-bench GPT-4o <50%.
- Key sources: manus.im/blog, karpathy.bearblog.dev, anthropic.com/research/building-effective-agents, anthropic.com/engineering/writing-tools-for-agents

## Multi-Agent Framework Technical Patterns — All Major Frameworks (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/multiagent-framework-patterns-2026.md`
- ADK: 8 patterns (Sequential, Coordinator, Parallel Fan-Out, Hierarchical, Generator-Critic, Iterative Refinement, HITL, Composite). State = `session.state` shared whiteboard. Three comm modes: passive state write, LLM transfer, AgentTool.
- Magentic-One: Outer loop (Task Ledger + replanning) + Inner loop (Progress Ledger + subtask assignment). Error recovery = adaptive replanning after N stalled steps.
- LangGraph: Checkpoints after every node. `interrupt()` pattern for HITL — CRITICAL: node re-executes from beginning on resume (double-execution). Pre-interrupt ops must be idempotent.
- CrewAI Flows: Decorator-based event model (`@start`, `@listen`, `@router`). Pydantic state. Router mismatch = silent skip (gotcha). `crew.kickoff()` embeds Crews in Flow steps.
- OpenAI Agents SDK: Handoffs = one-way tool-based delegation. Three guardrail tiers (input/output/tool). Tool guardrails don't apply to handoffs. `nest_handoff_history` beta collapses transcript.
- Claude Agent SDK: `resume=session_id` for cross-session continuity. Hooks at lifecycle points. Computer-access model (bash + files). Code-as-output pattern preferred.
- Cross-cutting: ReAct (flexible/costly) vs ReWOO (parallel/brittle) vs CodeAct (novel problems/sandboxed). Hybrid: ReWOO → CodeAct → ReAct fallback = production standard.
- Observability: 89% orgs have some; Arize Phoenix (OTel, framework-agnostic), LangSmith (best LangGraph). Agent-as-judge > LLM-as-judge for process evaluation (0.3% vs 31% human disagreement).
- Production state (Nov 2025): 57% in production; quality #1 blocker (32%); latency #2 (20%).

## AI Governance for Agents — Risk & Regulatory Research (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/ai-governance-agents-2026.md`
- GARP RAI exam: 5 modules (Tools, Risks, Responsible AI, Data/Model Governance). No standalone agentic module — surfaces in Modules 3+5. 80q/4h/100-130h prep.
- SR 11-7 gaps for agents: static assumption mismatch, third-party concentration, explainability thresholds. Path: targeted refinement + continuous monitoring, not replacement.
- Agent autonomy levels (Knight Columbia): L1=Operator, L2=Collaborator, L3=Consultant, L4=Approver, L5=Observer. FS consensus: L4 max; L3 for routine.
- Top threat taxonomy sources: OWASP Top 10 for Agentic Apps (Dec 2025), MAESTRO 7-layer (CSA Feb 2025), MITRE ATLAS 14 new agentic techniques (Oct 2025).
- Prompt injection = #1 agentic vulnerability (OWASP); present in 73% of production deployments audited in 2025.
- Audit trail standard: OpenTelemetry GenAI Semantic Conventions v1.37+ (gen_ai.request.model, token counts, tool calls). EU AI Act requires "automatic logging" — agent action traces are in scope.
- Agent governance frameworks: NIST AI RMF (4 functions: Govern/Map/Measure/Manage), ISO 42001 (38 controls, 9 areas, Dec 2023), BIS 10-action framework (Jan 2025), GaaS runtime proxy (arxiv:2508.18765).
- IIF-EY 2025 survey: 54% G-SIBs piloting agents; 100% planning deployment; data quality #1 barrier; primary spend still in predictive AI.
- AI Agent Index 2025 (arxiv:2602.17753): 25/30 deployed agents disclose no internal safety testing; only 4 publish agent system cards. Enterprise platforms mostly "optional guardrail modules."
- Anthropic RSP v3.0 (Feb 24 2026): ASL-3 activated May 2025; removes prior commitment to pause training if safety controls insufficient.
- Key WebFetch gotchas: BIS/IIF PDFs are binary. garp.org article pages work. opentelemetry.io/blog works. knightcolumbia.org works. iapp.org works. arxiv HTML works.

## AI Coding Agent Engineering Patterns — Cross-Agent (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/ai-coding-agent-patterns-2026.md`
- Covers: Devin, Claude Code, OpenHands, OpenAI Codex, Cursor/Windsurf, Aider
- Top steal: SWE-grep (Windsurf/Cognition) — RL-trained retrieval subagent, 8 parallel tool calls, frees main agent context
- Aider unified diff: 20% → 61% success rate 3x laziness reduction. Remove line numbers, function-level diffs, 9-layer fallback patching
- Aider repo map: PageRank on NetworkX MultiDiGraph with chat-context-aware edge weights, binary search token budgeting, 3-layer cache
- Cursor 2.0: git worktree isolation for parallel agents; dual-model plan/build pipeline; Background Agents → Ubuntu VMs → auto-PRs
- OpenHands: event-sourced state (append-only EventLog). Condenser abstract interface, 2x cost reduction, linear vs quadratic scaling
- Claude Code: TAOR loop; ToolSearch lazy MCP loading; Hooks outside LLM loop (zero tokens); CLAUDE.md re-injected post-compaction
- Devin: compound AI Planner+Coder+Critic; bot-agnostic PR autofix; interactive plan approval; parallel isolated cloud IDEs
- Key sources: anthropic.com/engineering, platform.claude.com/docs/en/agent-sdk, arxiv.org/html/2511.03690v1, cognition.ai/blog/swe-grep, aider.chat/docs

## Claude Agent Teams & Subagents — Patterns (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/claude-agent-patterns-2026.md`
- Agent Teams: Feb 5 2026, experimental, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, v2.1.32+. Ghostty = in-process only (no split panes)
- Subagents: YAML frontmatter + Markdown body. `.claude/agents/` (project) or `~/.claude/agents/` (user). Cannot spawn subagents. Do NOT inherit: parent history, skills, system prompt. DO inherit: CLAUDE.md, MCP, permissions
- `Task` tool renamed to `Agent` in v2.1.63 — check both for compatibility
- +90.2% performance: Opus 4 lead + Sonnet 4 subagents vs single-agent Opus 4 (Anthropic internal eval). Multi-agent ~15x token cost vs chat
- Model hierarchy: Opus = lead/judgment, Sonnet = standard workers, Haiku = high-frequency/lightweight (90% Sonnet capability, 3x cheaper)
- Top anti-patterns: over-parallelizing, vague dispatch (subagents can't ask), lead doing work instead of delegating, same-file parallel edits
- AGENTS.md = cross-tool standard; CLAUDE.md = Claude-specific. Both coexist.
- Best sources: code.claude.com/docs/en/agent-teams, platform.claude.com/docs/en/agent-sdk/subagents, anthropic.com/engineering/multi-agent-research-system, addyosmani.com/blog/claude-code-agent-teams

## Agentic Coding Testing & QA Best Practices (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/agentic-coding-testing-qa-2026.md`
- Testing IS the differentiator between vibe coding and agentic engineering (Karpathy, Osmani, Willison all converge)
- Red/Green TDD: write tests first, confirm they FAIL, then implement — shorthand "use red/green TDD" works in all major models
- "First run the tests" prompt pattern (Willison) for existing codebases — forces agent to discover test infra
- Context-isolated subagent TDD: separate Test Writer / Implementer / Refactorer agents — prevents cross-phase contamination
- Pre-commit automation gates: formatting + linting + tests all block completion without human reviewing every line
- Trust-but-verify = branch isolation + diff review + CI/CD (not full code review)
- 80% problem: agents produce conceptual errors (hallucinated conditions, missing auth checks) not just syntax bugs
- Security risk: 45% of AI code has OWASP Top-10 vulns; 61% functionally correct but only 10.5% secure (arxiv:2512.03262)
- CLI tools: golden path + smoke tests + type checking are the practical QA floor
- Key sources: Willison guides, Osmani agentic-engineering blog + 80% substack, Tweag handbook, nizar.se/agentic-tdd

## Multi-Agent AI in Financial Services (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/multiagent-ai-financial-services-2026.md`
- Confirmed production: GS+Anthropic (accounting/KYC agents, Feb 2026), JPMorgan "Ask David" (supervisor+specialist pattern), HSBC (600+ use cases, Mistral partnership), Capco IB credit memo agent (50% time reduction)
- FS-unique constraint: regulatory accountability non-delegable; four-eyes = agent gate + human gate (not two agents); books-and-records obligations make audit trail mandatory not optional; SR 11-7 MRM applies to every decisioning agent
- SR 11-7 gaps under agentic AI: dynamic validation (periodic cycles miss autonomous recalibration), third-party concentration risk (shared LLM vendor = correlated systemic risk), explainability thresholds undefined
- Dominant production architecture: bounded autonomy (co-pilot + constrained execution), NOT fully autonomous; centralized orchestrator topology (not swarm) for compliance workflows
- MRM failure modes unique to multi-agent: cascading hallucinations, monoculture collapse, conformity bias in review chains
- Key sources: garp.org SR-11-7 analysis, Deloitte agentic banking pieces, PwC validation framework, KPMG AI model risk, arxiv:2508.05687, arxiv:2603.13942

## Multi-Agent Orchestration Patterns for Quality (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/multiagent-orchestration-quality-2026.md`
- Core verdict: model diversity >> agent count; 2 diverse models > 16 homogeneous (arxiv:2602.03794)
- MAD (debate) fails to beat self-consistency at matched compute EXCEPT for judge/evaluation use cases (NeurIPS 2025, arxiv:2510.12697)
- GAN-style refinement works for creative tasks + grounded external feedback; fails on pure reasoning
- Best-of-N diminishing returns are immediate (N=4 worse than N=2 in agent setting, arxiv:2508.02694)
- Topology > count: centralized +80.8% on parallelizable tasks; sequential reasoning degrades -39-70% with ANY multi-agent (arxiv:2512.08296)
- Capability saturation at ~45%: above that threshold, coordination yields negative returns
- Hard ceiling at 3–4 agents under fixed compute (communication overhead eats reasoning budget)
- Judge design: panel of small models > single large judge; different model family from generator; binary/3-point scales; CoT+rubric; adaptive stopping saves rounds
- Framework state: LangGraph (stateful production), CrewAI (linear), AutoGen (maintenance mode), OpenAI Agents SDK (handoffs), Google ADK (8 patterns)

## Personal AI & Life OS Patterns — Comprehensive (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/personal-ai-life-os-patterns-2026.md`
- File-based memory (CLAUDE.md/MEMORY.md) is proven + sufficient. Vector/graph better but operational overhead.
- n8n = best low-code automation layer: 542+ personal productivity templates, Telegram-as-interface, self-hostable, AI-native.
- Obsidian Smart Connections = table-stakes PKM plugin. AKM (heartbeat monitoring + HITL write) = frontier.
- Briefing + nudge = highest-leverage automation. LaunchAgent (Claude Code) or n8n cron → Telegram push.
- Miessler PAI v2.4 = most documented open-source reference implementation. Claude Code-native, versioned.
- PAIMM: 9 tiers, Chatbot → Agent → Assistant. Most power users at AG2. AS1+ (named proactive companion) is rare.
- Anti-patterns: automation sprawl, CrewAI for persistent state, LangGraph for personal pipelines, voice for reasoning.
- HITL requirement confirmed across all documented real systems. Full autonomy in personal context = propagating errors.

## Life OS / Personal AI Agent Landscape (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/life-os-ai-agent-landscape-2026.md`
- Gemini CLI: closest Claude Code alternative — same skills format (directly reusable), hooks system, GEMINI.md. Free 1000 req/day. Locked to Gemini models only. Skills still in preview.
- Goose (Block, 30K stars): model-agnostic, MCP-native, Recipes for workflows, Linux Foundation. No hooks/LaunchAgent equivalent. Coding-first but general capable.
- OpenCode (95K stars): 75+ providers, TUI, model-agnostic. No hooks or lifecycle automation.
- Khoj (33K stars, AGPL): best "second brain" platform — scheduler, mobile app, Obsidian plugin, model-agnostic, self-hostable. Not a CLI orchestrator; no hooks.
- OpenFang (v0.1.0, Mar 2026, Rust): most ambitious — Hands (scheduled agents), 40 channel adapters, SQLite+vector memory, MCP+A2A, 27 LLM providers. Too immature (v0.1.0) for production.
- Agent Zero (13.5K stars): Docker-based universal assistant, self-improving, persistent memory. Complex setup.
- CrewAI state: lost between runs — NOT useful for persistent personal OS.
- MCP ecosystem: mature enough that multiple hosts exist (Claude Desktop, Cursor, Zed, Goose, OpenCode). No host matches Claude Code's hooks/lifecycle depth.
- Claude Code moat: hooks + MEMORY.md + LaunchAgent scheduling + skills — no single tool replicates all four.
- Source gotchas: openfang.sh WebFetch works; github.com/khoj-ai/khoj WebFetch works; geminicli.com/docs works.

## AI Regulation in Financial Services — Jurisdiction Matrix (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/ai-regulation-financial-services-2026.md`
Tiering frameworks deep-dive: `/Users/terry/.claude/agent-memory/researcher/ai-risk-tiering-frameworks-2026.md`
- EU AI Act: high-risk compliance deadline Aug 2 2026 (credit scoring explicitly named Annex III); €35M/7% penalties; EBA factsheet Nov 2025 says no immediate guideline changes.
- UK PRA SS1/23 (eff. May 2024): NOW in implementation-scrutiny phase — Oct 2025 CRO roundtable 21 firms. FCA: no AI-specific rules; Consumer Duty + SM&CR apply. No AI-specific fines yet.
- HKMA: Aug 2024 GenAI circular (opt-out, monitoring); Sep 2024 AI/AML circular (feasibility studies due Mar 2025); AI2 strategy in Fintech 2030 (Nov 2025); GenAI Sandbox++ (Mar 2026). Guidance not hard law.
- MAS: FEAT (2018) + Veritas (2019) → new AIRM Guidelines consultation closed Jan 2026; final guidelines + 12-month transition → compliance ~late 2026/2027. First binding-level MAS AI expectations.
- US: DEREGULATING — Trump EO Jan 2025 rescinded Biden order; CFPB rolled back disparate impact; SR 11-7 (2011) remains backbone. States filling gap (MA $2.5M settlement).
- BIS/FSB/OECD: no binding standards; monitoring + convergence only. FSB Oct 2025 report on AI monitoring.
- HSBC pressure ranking: (1) UK PRA — active now, (2) EU AI Act — Aug 2026 hard deadline, (3) HK/MAS — relationship supervision + incoming guidelines.
- Source notes: finreg.aoshearman.com (EU), freshfields riskandcompliance (UK), stephensonharwood.com (SG), hkma.gov.hk press releases work. EBA/FSB/BIS PDFs are binary — use law firm summaries.

## Persona & Role Prompting in Multi-Agent LLMs (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/persona-role-prompting-multiagent-research.md`
- Output: `/Users/terry/code/vivesca-terry/chromatin/Persona vs Procedure in Multi-Agent Systems - Research.md`
- **Core verdict:** Vanilla persona prompting = null/negative single-agent effect (Zheng EMNLP 2024, 162 roles, 9 models). In multi-agent: introduces conformity, in-group bias, persona collapse — actively undermines diversity goal.
- **Exception:** Dynamic capability-aware role assignment (Zhang et al. arxiv:2601.17152) beats uniform by +74.8% — only when roles match *measured* agent capability, not human-declared labels.
- **Model diversity** (not persona diversity) is the well-evidenced uncorrelated-error mechanism: 2 diverse models = 16 homogeneous (arxiv:2602.03794).
- **Key gap:** Persona diversity × model diversity interaction untested. No CrewAI ablation study. No compliance/domain-expert persona study.
- Source notes: arxiv HTML pages work; ACL anthology HTML works; PDFs are binary.

## AI Model Releases — Q1 2026 (Jan–Mar)
Full detail: `/Users/terry/.claude/agent-memory/researcher/ai-model-releases-early-2026.md`
- OpenAI: GPT-5.3-Codex (Feb 5), GPT-5.4 / 5.4 Thinking / 5.4 Pro (Mar 5). o-series retired. 1M token context. Native computer use in 5.4.
- GPT-5.4 pricing: $2.50/$15 (standard), $30/$180 (Pro) per M tokens.
- Google: Gemini 3 (Nov 2025 base), Deep Think Feb 12 2026 update hit 84.6% ARC-AGI-2. Gemini 3.1 Pro (Feb 19), 3.1 Flash-Lite (Mar 3, $0.25/$1.50 per M).
- DeepMind Aletheia (Feb 2026): autonomous math research agent, solved 6/10 FirstProof problems, authored paper without human help.
- Anthropic: Opus 4.6 (Feb 5), Sonnet 4.6 (Feb 17), Cowork preview (Jan).
- Paradigm shift: test-time scaling now dominant. Three scaling laws: pretraining / post-training / test-time.
- Source gotcha: openai.com and blog.google both 403 on WebFetch. Use simonwillison.net, VentureBeat, MarkTechPost as proxies.

## Chinese AI Agent Ecosystem — Tools, Frameworks, Enterprise (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/chinese-ai-agent-ecosystem-2026.md`
- Coding agents: Tongyi Lingma (30.67% SWE-bench Pass@3, MCTS repo exploration), Baidu Comate (multimodal IDE, 43% internal code), Qwen3-Coder (69.6% SWE-bench, Agent RL with 20K parallel envs)
- DeepSeek agents: V3.2 natively fuses thinking+tool-use; "Thinking in Tool-Use" pattern (reason before call, verify, self-correct); deployed in Chinese banks at scale
- Qwen-Agent: co-designed with Qwen3, encapsulates tool-calling templates — tighter than Western LLM/framework separation
- MetaGPT/MGX: SOP-encoding as architecture ("Code=SOP(Team)"); AFlow (ICLR 2025 oral, #2 agent category); OpenManus built in 3h, 16K stars in 2 days
- AgentScope 1.0: group-wise tool management (paradox-of-choice fix), dual stateful/stateless MCP clients, StateModule for save/restore hierarchies, auto-FastAPI deployment
- Kimi K2.5: 100 parallel sub-agents via PARL (novel RL technique that rewards parallelization, prevents serial collapse)
- Enterprise messaging: DingTalk Agent OS (Dec 2025, full AI OS re-architecture + hardware), Feishu official MCP server, Tencent QClaw (WeChat+QQ OpenClaw bundle, Mar 2026)
- Chinese FS: ICBC "工银智涌" (200+ use cases, 1B+ calls/year), DeepSeek locally deployed across state banks, no SR 11-7 equivalent (algorithm filing + PBoC framework instead)
- Manus: acquired by Meta Dec 2025 for ~$2B; 7 context engineering techniques (KV-cache, logit masking, file-system memory, recitation attention hack, error preservation, restorable compression, diversity injection)
- Source gotchas: eu.36kr.com/en works; technologyreview.com returns CSS only; blog.csdn.net times out; arxiv.org/html works

## OpenClaw / Claw Ecosystem Landscape (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/openclaw-claw-ecosystem-2026.md`
- OpenClaw: ~280K stars, Peter Steinberger, TypeScript, messaging-native. Clawdbot → Moltbot → OpenClaw Jan 2026. Creator joined OpenAI Feb 2026.
- Security: ClawHavoc (12% malicious skills), ClawJacked (WebSocket brute-force), 7 CVEs. Fixed in v2026.2.25.
- Key alternatives: NanoClaw (22K, 700-line TypeScript, containers, Docker deal Mar 2026), Nanobot (27K, 4K-line Python, HKUDS), ZeroClaw (26K, Rust, 3.4MB), PicoClaw (13K, Go, Sipeed), Moltis (2K, Rust, enterprise observability), IronClaw/NullClaw/MicroClaw (niche).
- NemoClaw: NVIDIA enterprise play, unreleased, expected GTC keynote Mar 17 2026.
- Non-claw competitors: LangGraph/CrewAI solve different problem (pipelines, not messaging-native agents).

## Human Memory Science for AI Agents (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/human-memory-science-agents-2026.md`
- Output: `/Users/terry/docs/solutions/human-memory-science-for-agents.md`
- Key gaps confirmed: no production system implements RIF, context-at-encoding, prospective memory, pre-retrieval FOK, reconstruction vs retrieval, or schema-deviation storage.
- Best bridge papers: arxiv:2512.23343 (unified survey), arxiv:2504.15965 (forgetting → AI), arxiv:2502.06975 (episodic gap).
- HTML arxiv pages work for WebFetch; PDF versions return binary garbage.
- ACT-R = best formal model (activation math); SOAR = best symbolic episodic/semantic split; Generative Agents = best consolidation; HippoRAG = best spreading activation implementation.

## AINews / Cora / Source Analytics Research (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/ainews-cora-source-analytics-2026.md`
- AINews pipeline: social-first (Discord/Reddit/Twitter), multi-stage summarization ending in "summaries of summaries" via Gemini 3.0 Pro. Frontend is open source; aggregation pipeline is private/closed.
- "Synx" name: no connection to smol.ai confirmed — likely a confusion.
- Cora by Every.to: email inbox manager, NOT an RSS/news digest tool. No source quality analytics.
- Source quality scoring per-feed: NO commercial product does this as of Mar 2026. Genuine gap.
- Custom pipeline advantages over AINews: structured schema, gap analysis, quality gate, source analytics, domain specificity.

## LangGraph & LangChain Current State (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/langgraph-state-2026.md`
- LangGraph v1.1.2 (Mar 12 2026), LangChain 1.0 GA Oct 2025. No breaking changes pledge until 2.0.
- LangGraph does NOT require full `langchain` — requires `langchain-core` only. Standalone is real.
- LangGraph Platform renamed to LangSmith Deployment Oct 2025. $39/seat/month Plus, enterprise custom.
- LangSmith: optional, free 5K traces/month Developer tier. Not required to run LangGraph.
- Security: CVE-2025-64439 (RCE in checkpoint, fixed in v3.0.0) + CVE-2025-68664 (LangChain Core). Patch critical for enterprise.
- Enterprise FS confirmed users: BlackRock (Aladdin, $11T), JPMorgan ("Ask David", 95% research time cut), Captide (investment research).
- Competition 2026: CrewAI (fastest linear workflows), Pydantic AI (type-safe, V1 Sept 2025), Mastra (TypeScript), AutoGen (maintenance mode). LangGraph wins on complex stateful + observability.
- Full decision tree in the detail file above.

## LangGraph vs Plain Python for Batch Pipelines (Mar 2026) — DECISION CLOSED
Full detail: `/Users/terry/.claude/agent-memory/researcher/langgraph-vs-plain-python-2026.md`
- **Decision made and implemented (2026-03-20): thalamus v2 built with plain Python — no LangGraph.** 92 tests passing.
- Research verdict: LangGraph does not earn its keep for cron-triggered batch pipelines — state container, routing, retry loops are ~20 lines of plain Python each.
- Reuse this verdict for any future pipeline evaluation question. Do not re-research; decision is closed.

## AI Agent Memory Benchmarks — Literature Survey (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/agent-memory-benchmarks-literature-2026.md`
- **No independent academic paper compares ≥5 production backends side-by-side.** MemoryAgentBench (ICLR 2026, arxiv:2507.05257) is closest — covers Mem0 + Cognee + MemGPT but omits Zep, Graphiti, Letta, LangMem entirely.
- **No real/in-situ workload study exists.** All benchmarks are synthetic (LoCoMo, LongMemEval, MemoryAgentBench). No longitudinal or experience-report paper found.
- **Vendor benchmark war:** Mem0, Zep, Letta, Cognee each claim SOTA — all use different baselines, all contested.
- **A 10-backend independent survey would be clearly novel.** Demand exists; no arbiter does.
- **Key independent benchmarks:** MemoryAgentBench (arxiv:2507.05257), AMA-Bench (arxiv:2602.22769), LongMemEval (ICLR 2025), LoCoMo (Snap Research 2024).
- **Key vendor papers:** Mem0 (arxiv:2504.19413), Zep (arxiv:2501.13956).

## Graphiti / Cognee / Letta Practical Setup Research (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/graphiti-cognee-letta-setup-2026.md`
- **Graphiti:** `graphiti-core` v0.28.2 (Mar 11 2026). Kuzu via `pip install graphiti-core[kuzu]` — embedded, no server. Sentence-transformers via `[sentence-transformers]` extra. Ollama LLM works via `OpenAIGenericClient` (NOT `OpenAIClient`). Official MCP is in monorepo `mcp_server/` — no standalone PyPI; use community `montesmakes.graphiti-memory`.
- **Cognee:** `cognee` v0.5.4 (Mar 10 2026). Default local stack = SQLite + LanceDB + Kuzu — Neo4j NOT required. Fully local possible with Ollama + `[ollama]` + `[baml]` extras. MCP: `cognee-mcp` (in monorepo, run from source).
- **Letta:** `letta` v0.16.6 (Mar 4 2026). Server-first model — NOT a drop-in library. `pip install letta` + `letta server` (SQLite, port 8283). Ollama via `OLLAMA_BASE_URL` env var. No official MCP server. Client SDK: `pip install letta-client`. Memory lives in agent "blocks", not standalone store.

## "Life AI" / Personal Productivity AI Landscape Research (Mar 2026)
- **Best sources for product status:** fastcompany.com (Dot launch), techcrunch.com (acquisitions), cybernews.com (independent reviews), gmelius.com (Lindy honest review), skywork.ai (Mem/Limitless deep dives), screenpi.pe (ScreenPipe official, works well).
- **Critical events:** Limitless (ex-Rewind) acquired by Meta Dec 2025, Rewind Mac app shut down Dec 2025. Largest "personal memory" product gone from market.
- **Key products map:** Dot (memory/companion, iOS, $12/mo, ex-Apple design team, $3.7M funded) | Mem 2.0 (knowledge base, relaunched Oct 2025) | Lindy (workflow automation, $299/mo, 234+ integrations) | Motion (AI calendar scheduling, ~$34/mo) | Superhuman ($40/mo, email speed) | ScreenPipe (open source, local screen memory, MCP server) | Reor (local PKM, Obsidian-like, Ollama-based) | Notion 3.0 (walled-garden agent, Feb 2026 3.3 with custom agents).
- **Verdict on "Claude Code for life":** No product comes close to a well-configured Claude Code + Obsidian + MCP + skills setup for a developer-willing user. Dedicated tools win on onboarding friction only. The gap closes for non-technical users where the setup cost matters.
- **Key limitation patterns:** Notion = walled garden, no live cross-app data. Lindy = expensive ($300/mo), inconsistent on complex multi-step. Motion = great for solo, weak on mobile. Mem = note capture only, no real actions. Dot = companion/memory only, no workflow execution. ScreenPipe = capture only, no action execution.
- **Misinformation pattern:** "saves X hours/week" claims from Motion, Lindy, Superhuman are all vendor-sourced or self-reported. No independent audits found.
- Full synthesis: saved in researcher chat (Mar 2026).

## AI Agent Memory Landscape Research (Mar 2026)
- **Best sources:** arxiv.org (papers accessible), blog.getzep.com (WebFetch works), dev.to comparison articles (WebFetch works), AWS blog machine-learning pages (JS-gated, returns CSS only — use WebSearch summaries), medium.com (403 on WebFetch — use WebSearch snippets), serenitiesai.com (timeout). docs.mem0.ai pages (WebFetch works). loze.hashnode.dev (403 on WebFetch).
- **Vendor benchmarks are all contested** — Mem0, Zep, Letta, Cognee each claim to beat each other. Treat all as directional only.
- **Key star counts (Mar 2026):** Mem0 ~41K, Graphiti (Zep) ~20K, LangMem ~2K, Cognee ~3K, Letta/MemGPT ~13K (at Sep 2024 stealth exit).
- **Key funding:** Mem0 $24M (Series A Oct 2025, Basis Set lead); Letta $10M seed (Sep 2024, Felicis); Cognee €7.5M seed (Feb 2026, Pebblebed).
- **Mem0 latest release:** v1.0.5 (Mar 3 2026) — telemetry fix. Stable v1.x series, incremental.
- **AWS exclusive:** Mem0 is exclusive memory provider for AWS Strands Agent SDK — largest institutional validation in the space.
- **OpenAI memory (Apr 2025):** Consumer ChatGPT only — NOT in the API. This is a structural demand driver for third-party solutions.
- **CRITICAL GOTCHA — OpenMemory MCP "local" is misleading:** Official OpenMemory MCP server (Mem0's Docker product) still calls OpenAI API for embeddings even when "self-hosted." Data storage is local; embedding call is not. For true data privacy: use `tensakulabs/mem0-mcp` (community project) which uses Qdrant + Neo4j + Ollama embeddings — zero cloud keys.
- **Kuzu as graph backend:** Graphiti supports Kuzu (embedded, no separate server, like SQLite for graphs) in addition to Neo4j. Much lighter footprint for local deployments — single file, ~500MB RAM vs Neo4j's 4GB minimum.
- **MCP integration (both major tools):** Mem0 has official MCP server (cloud) + community local fork. Graphiti MCP 1.0 (Nov 2025, Apache 2.0) is fully self-hostable. Both work with Claude Code via MCP.
- **Misinformation pattern:** "90% token reduction" / "26% accuracy improvement" — always check baseline used. All vs full-context-window stuffing, not vs each other.
- **Recommendation for local+consulting+daily-use:** Mem0 OSS (tensakulabs fork) + Qdrant + Ollama for general memory; add Graphiti for temporal/compliance-tracking use cases. Skip LangMem (in-memory default trap), Letta (runtime not module), Cognee (too young for daily driver).
- Full synthesis: `/Users/terry/docs/solutions/ai-agent-memory-landscape-2026.md`

## HKMA GenAI Sandbox++ Research (Mar 2026)
- **Official press release:** hkma.gov.hk/eng/news-and-media/press-releases/2026/03/20260305-3/ — WebFetch works, returns clean summary. Authoritative.
- **Best secondary sources:** theasianbanker.com (WebFetch works, clean detail), leaprate.com (WebFetch works), marketing-interactive.com (WebFetch works, quantitative results), fintechnews.hk (WebFetch partial — JS-heavy but returns some text).
- **fundstech.com returns 403** on WebFetch. charltonslaw.com returns JS/CSS only. hsfkramer.com returns 403.
- **Cohort 1 participant names confirmed source:** finews.asia article — WebFetch works well, full bank list.
- **Key quantitative results (Cohort 1, confirmed Oct 2025 Symposium):** STR prep -30–80%; doc processing 1 day → 5 min; risk assessment -60%; 86% user satisfaction; >70% credit assessment useful.
- **Cohort 1 banks (10):** HSBC, Bank of China (HK), StanChart, China CITIC Bank Intl, CCB (Asia), Citibank (HK), Dah Sing, Hang Seng, Livi Bank, Societe Generale.
- **Cohort 1 tech partners (4):** Aereve, Alibaba Cloud, Baidu, FORMS HK.
- **Hang Seng Bank fraud automation PDF:** hangseng.com/content/dam/hase/pdf/hkma_genai_sandbox_2025_fraud_investigation.pdf — direct PDF link (may need to download).
- **Application contact from Cohort 1:** GenAI_sandbox@hkma.gov.hk — likely applies for Sandbox++ too until new contact confirmed.
- Full brief: /tmp/hkma-sandbox-plus-brief.md

## RegTech / Regulatory Gap Analysis Research (Mar 2026)
- **Best vendor sources:** cube.global (WebFetch mostly JS-gated, use WebSearch), finreg-e.com (WebFetch works on article pages, not homepage), ascentregtech.com (WebFetch works on product pages), corlytics.com (JS-gated).
- **Key vendors:** CUBE Global (broadest coverage, 180+ jurisdictions, acquired 4CRisk for AI gap analysis Aug 2025), Corlytics+Clausematch (end-to-end chain, acquired Deloitte RegTech + ING SPARQ), AscentAI (US/UK focused, rebranded Mar 2025), FinregE (UK, NLP-powered), Compliance.ai (US).
- **APAC coverage gap confirmed:** All leading platforms are UK/US-built. None demonstrate HK-specific depth or HKMA circular expertise. CUBE lists MAS as covered; no HK-native materials found anywhere.
- **Best secondary sources:** synpulse.com (WebFetch works, HK+SG regulatory outlook), nasdaq.com/articles/fintech (APAC RegTech trends), unit21.ai/blog (RegTech barriers), ioni.ai/post (AI gap analysis step-by-step).
- **IBM think articles:** WebFetch works well for compliance/AI topics — detailed GenAI use case coverage.
- **Common misinformation:** CUBE "50x faster than manual" = vendor claim, no independent validation. RegTech "market size" figures vary wildly by report ($15B vs $35B) due to different scope definitions.
- Full research: `/tmp/lacuna-competitive-research.md`

## Manus AI Architecture & Landscape (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/manus-ai-architecture-2026.md`
- Stack: Claude 3.5/3.7 + Qwen wrapper. Ubuntu 22.04 sandbox per task. CodeAct (Python) as action format. One tool per loop iteration.
- Context engineering: KV-cache hit rate = #1 metric; file system as external memory; todo.md attention hack; leave failures in context; logit masking not dynamic tool removal.
- Wide Research (Jul 2025): 100+ parallel Manus instances, each with own VM + fresh context. Orchestrator decomposes then aggregates.
- Manus 1.5: 4x faster, +15% quality. "Unlimited context" = file-based externalization.
- Security: system prompt trivially leaked Mar 2025; VS Code server kill chain via `deploy_expose_port` (Embrace The Red, Jun 2025).
- Meta acquisition: Dec 2025, ~$2B, $100M ARR, WhatsApp/Instagram integration roadmap.
- OSS clones: OpenManus (52K stars, MetaGPT team, ReAct pattern), Suna (Kortix, FastAPI+Next.js, Apache 2.0), agenticSeek (fully local, Ollama).
- Best source: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

## HK Consulting / Banking Comp Research (Mar 2026)
- **Best sources for HK salary data:** Morgan McKinley (`morganmckinley.com/hk/salary-guide/data/<role>/hong-kong-sar`) — WebFetch works, returns clean monthly HKD ranges. Robert Half (`roberthalf.com/hk/en/insights/salary-guide/technology`) — WebFetch works, returns annual HKD with percentiles. Glassdoor 403s on WebFetch — use WebSearch summaries instead.
- **Glassdoor HK data quality issue:** Annual salary figures for mid-senior roles often appear to be USD mislabelled as HKD (e.g., Capco PC "HK$200K/year" is clearly USD). The monthly pay view and Managing Principal data are internally consistent and more reliable. Cross-check: monthly × 12 = annual to detect mislabelling.
- **Capco HK comp ladder (2025):** Senior Consultant HK$617-798K total (Glassdoor); Managing Principal HK$1.25-1.7M (Glassdoor, 7 submissions); Principal Consultant ~HK$850K-1.3M (interpolated). Bonus culture contested (3.4/5 PC satisfaction). **No equity post-Wipro** — Partners get title + salary only, ~USD $600K total (US figure).
- **Capco career ladder:** Consultant → Senior → Principal → Managing Principal → (Exec Dir) → Partner. Revenue accountability starts at Principal. "Principal School" exists at S→PC transition. ~2-3yr per level for high performers.
- **HK bank Head of Data / AGM comp (2025-2026):** Robert Half Head of Data HK$1.2-1.8M/yr (50th pct: HK$1.6M). Morgan McKinley "Head of" permanent HK$80-150K/month, contract HK$90-190K/month. PayScale AGM HK$835K average = discard (all-industry, skews low).
- **AI specialisation premium:** 20-40% over generalist consulting (global studies); within consulting firms, premium accrues via billing rate + bonus, not base salary bands. HK day rates: general senior consultant HK$3-6K/day; AI strategy/FS HK$10-18K/day (estimated, low-medium confidence — no authoritative HK AI day-rate survey exists).
- **McKinsey EM HK (Jan 2026):** HK$1.1-1.9M total comp (Glassdoor, 25 submissions, credible). Best MBB anchor for HK principal-equivalent comp.
- **Deloitte Manager HK:** HK$54-64K/month base (Glassdoor monthly view, Feb 2026 — use monthly view, not annual, for Deloitte HK data).

## Capco APAC People Research (Mar 2026)
- **Best primary sources:** capco.com/about-us/newsroom-and-media (press releases, WebFetch works), consultancy.asia (WebFetch works, good biographical detail), finextra.com (press release syndication), fundselectorasia.com, waterstechnology.com (podcast/profiles).
- **LinkedIn returns 999** on WebFetch — use search result snippets + theorg.com + zoominfo.com + rocketreach.co instead for individual profiles.
- **theorg.com/org/capco/org-chart/<name>** — works well for title confirmation; sometimes sparse on detail.
- **Key APAC people confirmed (March 2026):** James Arnett (APAC Managing Partner, HK), Paul Sommerin (APAC Head of Digital & Technology, HK), Edwin Hui (APAC Data Lead, HK), Bertie Haskins (Head of Data APAC & ME, HK), Subodh Ojha (AI Practice Lead, HK), Rezwan Shafique (Partner, Wealth/CapMkts, HK), John McBain (Partner, HK), Darren Pigg (Partner, APAC Insurance Lead, HK), Dr Shelley Zhou (APAC ESG Lead, HK).
- **Thought leader content:** capco.com/intelligence/ — WebFetch works, bylines extractable. Key APAC AI pieces: "Building Data Leadership in APAC" (Bertie Haskins), "APAC Capital Markets Transformation Trends" (Malhotra et al., May 2025), "APAC Banking & Payments Trends 2025" (Chulayuth Lochotinan).

## Claude Effort Level & Extended Thinking API (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/claude-effort-thinking-api-2026.md`
- `effort` is a CEILING, not a floor. At `high`: model "almost always thinks." At `medium`/`low`: may skip thinking for simple tasks. Model complies — it cannot override effort.
- `budget_tokens` deprecated on Opus 4.6 + Sonnet 4.6. Replace with `thinking: {type: "adaptive"}` + `output_config: {effort: "..."}`.
- Claude Code `effortLevel` setting maps directly to `output_config.effort` at the API level + adaptive thinking mode.
- Opus 4.6 defaults to `medium` effort for Max/Team (NOT high). Sonnet 4.6 defaults to `high`.
- `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` reverts to old fixed `MAX_THINKING_TOKENS` budget.
- Sources: platform.claude.com/docs/en/build-with-claude/effort, platform.claude.com/docs/en/build-with-claude/adaptive-thinking, code.claude.com/docs/en/model-config

## Token Efficiency & Multi-Agent Anti-Patterns (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/token-efficiency-multiagent-2026.md`
Research output: `/tmp/research_efficiency.md`
- Saturation at 4 agents; 17x error amplification in "bag of agents" (unstructured topology)
- Sequential tasks ≥45% single-agent accuracy: multi-agent REDUCES performance 39-70% (Google Dec 2025)
- Task sweet spot: 5-15 min/task, 5-6 tasks/teammate; too small = overhead wins; too large = context rot
- Observation masking beats LLM summarisation: 52% cost reduction, 10-turn window, wins 4/5 conditions (JetBrains Dec 2025)
- File conflicts: two agents on same file = zero benefit. File ownership must be declared before spawn.
- Handoff state must be written (progress files), not assumed from conversation history
- Quality control: Sentinel (hard gate) + Healer (iterative loop) + LLM-as-judge (94% accuracy with few-shot)
- Self-review is unreliable: models 64.5% more likely to catch errors in external than own output
- Source notes: anthropic.com/engineering works; code.claude.com/docs works (full content); towardsdatascience.com JS-gated (metadata only); orq.ai JS/Framer-gated (no content)
- **Org structure:** Matrix — by geography (HK hub, SG hub, India, Thailand) AND by capability practice (Strategy/Consulting, Digital & Technology, Data Intelligence, Transformation, plus industry verticals: Banking, CapMkts, Wealth, Insurance, ESG).

## Capco AI Methodology Research (Mar 2026)
- **capco.com/intelligence/* individual article pages** — WebFetch works well on article pages; returns authors, date, framework components cleanly. Use direct article URLs, not the intelligence index page.
- **capco.com/about-us/solution-partners** — WebFetch works; lists full tech ecosystem (Google Cloud, OpenAI, Celonis, Automation Anywhere, MuleSoft, Pyramid Analytics, Aptus.AI etc.).
- **capco.com/about-us/newsroom-and-media/** — WebFetch works for press releases; good for partnership announcements.
- **Key confirmed frameworks (Mar 2026):** Confidence-Driven Agentic AI (3-layer: Decision Model/Context/Action Rules), AI Governance Accelerators (4-component: roles, practices/tools, regulation, responsible AI principles), NIST-tiered risk approach for AI.
- **Key AI author: Chinmoy Bhatiya** — most prolific on agentic AI and governance; appears US/global-facing not APAC. APAC AI = Bertie Haskins (Head of Data APAC).
- **Capco's only confirmed AI platform partner: OpenAI** (Mar 2025, Beta Services Partner Program). Google Cloud is a solution partner but no AI-specific deal. No confirmed Anthropic/Azure/AWS AI partnerships.
- **No confirmed Capco-HSBC engagement** in any public source. HSBC's own AI partners are Mistral AI (confirmed 2025) and internal teams. The connection exists via proximity (both FS FS-focused) but is not public.
- **HK-specific Capco content:** Wealth management survey (74% HK affluents comfortable with AI), "Building Data Leadership in APAC" (Bertie Haskins, Dec 2025) with HKMA cross-sector AI guidelines reference. Full synthesis: `/Users/terry/code/vivesca-terry/chromatin/Capco AI Methodology Research.md`

## HK Salaries Tax / Employment Transition Research (Mar 2026)
- **gov.hk/en/residents/taxes/salaries/salariestax/chargeable/termination.htm** — authoritative, WebFetch works; covers taxable vs non-taxable termination payments clearly.
- **gov.hk/en/residents/taxes/salaries/salariestax/chargeable/backpay.htm** — relating-back provision details; WebFetch works.
- **taxsummaries.pwc.com/hong-kong-sar/individual/income-determination** — good cross-reference for HK termination rules; WebFetch works.
- **clic.org.hk** — excellent plain-English legal explainers; WebFetch works on most pages.
- **hkwj-taxlaw.hk** — reliable HK tax law commentary; WebFetch works.
- **ird.gov.hk PDF files** — return binary/compressed; use search result summaries instead.
- **Key settled facts (cross-referenced 3+ sources):** (1) PILON taxable since April 1, 2012, no exception. (2) PILON accrues when agreement becomes unconditional OR employment terminates, whichever earlier — this determines tax year. (3) MPF: PILON is NOT relevant income — no employer or employee MPF contribution. (4) Relating-back provision applies to gratuities/terminal awards only, NOT PILON. (5) Statutory severance/long service payments (EO formula) are non-taxable. (6) IR56F filed by employer (not employee) at least 1 month before cessation date. (7) Progressive rates: 2/6/10/14/17%; standard rate cap 15%; aggregates all income across all employers in same tax year.
- **Misinformation to watch:** Some sources conflate "termination payment" generically — PILON and severance are in different categories with different tax treatment. MPF offset abolition (May 2025) only affects severance/long service, not PILON.

## Consulting Proposal & SOW Research (Mar 2026)
- **Best structural source:** slideworks.io/resources/how-to-write-consulting-proposals-like-mckinsey — WebFetch works; full SCR section order extracted.
- **Best SOW source:** nmsconsulting.com/consulting-sow-template/ — WebFetch works; change control, exit criteria, KPIs.
- **AI contract clauses:** stack.expert/blog/ai-consulting-contracts-essential-legal-framework — JS-gated (Framer); returns CSS only. Use WebSearch summaries instead.
- **wednesday.is/writing-articles/ai-consulting-contract-and-pricing-models** — WebFetch works; good T&M vs fixed-price guidance.
- **hiscox.com/blog/rookie-consulting-mistakes** — returns 403 on WebFetch. Use WebSearch result summaries.
- **Capco methodology:** capco.com/intelligence/* mostly JS-gated. capco.com/about-us/success-stories — WebFetch works well; extracted 30 case studies in full.
- **Glassdoor salary pages:** return 403 on WebFetch — use WebSearch result summaries; salary data embedded in search snippets.
- **Key practitioner finding:** "Never price without a paid discovery phase" — the most consistent principle across all sources. Phase 0 (2–4 weeks, fixed small fee) is the protective gate before any fixed-price AI commitment.
- **Capped T&M (NTE)** = safest AI pricing hybrid. T&M flexibility + hard budget ceiling. Requires Change Order to exceed cap.
- **Dangerous clauses ranking:** (1) "Client satisfaction" acceptance standard, (2) Unlimited revisions, (3) Absolute AI performance guarantees, (4) All-IP assignment including methods.
- **Scope creep patterns specific to AI:** new use cases mid-flight, performance targets shifted post-build, data quality remediation claimed as consultant's problem, regulatory changes post-SOW.

## AI Consulting in APAC FS Market Research (Mar 2026)
- **beaumont-capitalmarkets.co.uk** — WebFetch works; good HK regulatory overview (HKMA/SFC frameworks, PDPO).
- **capco.com/intelligence/* pages** — Mostly JS-gated; WebFetch returns CSS/tracking code. Use search result summaries + WebFetch on specific capco.com news pages.
- **hkma.gov.hk press release pages** — WebFetch works (not PDF links). Use press release URL, not PDF link.
- **pwchk.com HTML pages** — WebFetch works for structure but body JS-gated; extract via search result summaries for content.
- **consultancy.asia/consulting-industry/fees-rates** — WebFetch works but returns only high-level proxies (annual rev per consultant). No day rate breakdowns.
- **roberthalf.com/hk salary guide** — WebFetch works but data is traditional FS roles only; no AI-specialist salary breakdowns as of 2026.
- **sleek.com HK consultant rates** — page is pure JS/Elementor; WebFetch returns nothing useful.
- **Reliable for FS AI market data:** precedenceresearch.com, futuremarketinsights.com (market sizing), mckinsey.com/insights (works sometimes, often timeout), deloitte.com/global (works), ey.com/insights (works).
- **Key 2025-2026 facts:** APAC AI consulting CAGR ~35.6% (fastest globally); FS = 22.3% of global AI consulting spend; 62% of AI pilots never reach production; MAS AIRG published Nov 2025; HKMA Fintech 2030/AI2 Strategy announced Nov 2025; Capco-OpenAI partnership Nov 2025; Accenture USD 5.9B AI deal bookings FY25.
- **HK consulting day rates:** No published data. Proxy: Big 4 annual rev/consultant USD 300-400K → ~HKD 15-31K/day. FS boutique senior principal/MD: HKD 15-25K/day estimated.

## AI Tooling Landscape Research (Mar 2026)
- **Best WebSearch queries:** Use specific model names + "benchmarks 2026", "pricing per million tokens", "enterprise adoption 2025" — surfaces artificialanalysis.ai, shakudo.io, and platform-official pages well.
- **artificialanalysis.ai/leaderboards/models** — most reliable neutral benchmark aggregator; Intelligence Index scores cross-provider. WebFetch works on summary data.
- **platform.claude.com/docs/en/about-claude/pricing** — always check official for Claude pricing (WebFetch works). Third-party summaries frequently wrong on Opus pricing.
- **ai.google.dev/gemini-api/docs/pricing** — Gemini official pricing; WebFetch works.
- **Menlo Ventures 2025 State of Generative AI** — reliable enterprise adoption figures ($37B spend 2025, $11.5B 2024). WebFetch works on menlovc.com.
- **Deloitte 2026 State of AI in Enterprise** — governance/maturity stats; summary via WebSearch result summary.
- **braintrust.dev/articles/best-llmops-platforms-2025** — strong comparison of eval tools; WebFetch works.
- **Misinformation patterns:** Benchmark scores vary significantly between standard vs thinking/extended-compute modes (e.g., Claude GPQA 74.1% standard vs 89.9% thinking). Always clarify eval configuration. GPT-5.x pricing evolves rapidly — verify before quoting.
- **Key 2025 landscape facts:** LangChain 47M+ PyPI downloads; Cursor $29.3B valuation $1B ARR; GitHub Copilot 20M users 90% Fortune 100; Claude Agent SDK renamed from Claude Code SDK Sep 2025; MCP donated to Linux Foundation Dec 2025 (AAIF).
- Full landscape synthesis: `/tmp/ai-tooling-landscape-2026.md`

## ClawHub / OpenClaw Skills Research (Mar 2026)
- **clawhub.ai** = fully JS-rendered (React/Vite + Convex) — WebFetch returns minified JS. Cannot browse skills.
- **clawhub.biz** — same issue; returns homepage structure only, not skill data.
- **www.clawhub-skills.com** — serves default 24 skills regardless of `?q=` or `?category=` params (client-side React filtering). Not useful for category browsing via WebFetch.
- **clawhub.ai/api/v1/skills?q=...** — returns same 49-skill default page regardless of params. Not a real REST API endpoint — SPA data.
- **Productive sources:** `raw.githubusercontent.com/VoltAgent/awesome-openclaw-skills/main/README.md` (category counts), `playbooks.com/skills/openclaw/skills/<skillname>` (individual skill detail, WebFetch works well), `lobehub.com/skills/<slug>` (skill descriptions), `github.com/freakyflow/garminskill` (full skill source), `github.com/omarshahine/HomeClaw` (HomeKit MCP/Claude Code plugin).
- **OpenClaw vs Claude Code:** These are OpenClaw/Clawdbot SKILL.md files — NOT Claude Code skills natively. Architecture is identical (SKILL.md markdown). All skills are adaptable to Claude Code with minor edits (remove OpenClaw-specific install commands).
- **Key skill categories (playbooks.com counts):** Health & Fitness 188 skills, Smart Home 100, Finance 148, Calendar 92, Crypto 767, Notes & PKM 290.
- **Security note:** ~341 malicious skills found in ClawHub (Feb 2026 "ClawHavoc" incident). Security-sensitive skills (finance, credential access) need code review before adapting.
- **Best search strategy:** WebSearch for `clawhub openclaw "<specific term>" skill` surfaces playbooks.com, lobehub.com, and GitHub direct links that WebFetch can then extract. Don't try to browse clawhub.ai/biz directly.

## Due App (dueapp.com) Automation Research (Mar 2026)
- **Official URL scheme docs:** https://www.dueapp.com/developer.html — WebFetch works (extracted full parameter table)
- **Zendesk support articles:** dueapp.zendesk.com returns 403 on WebFetch — use WebSearch result summaries instead
- **MacStories article (modern Shortcuts):** JS-gated — returns CSS only, no article text. Use WebSearch result summaries.
- **automators.fm threads:** WebFetch returns errors. Use WebSearch result summaries.
- **No CLI or API.** No programmatic interface beyond URL scheme and Shortcuts actions. "Phocus" is Hasselblad software, not Due's developer name.
- **URL scheme always shows editor UI** — `/add` opens the add-reminder view. Providing `title` parameter pre-fills title and suppresses keyboard; but the editor screen still opens. No `autosave` or silent-add parameter documented or found in any community source.
- **Native Shortcuts actions (v20.5+) are the headless path:** "Create Reminder" and "Create Repeating Reminder" run without opening Due at all. Confirmed by support article summary and MacStories. This is the only silent-add path.
- **CloudKit sync:** Due uses CloudKit/Core Data internally. No programmatic trigger documented. Sync happens automatically when app data changes — no external hook.

## LLM Agent Tool Count & Memory Limits (Mar 2026)
- **Degradation curve (empirical, RAG-MCP / vllm-semantic-router):** ~50 tools = 84-95% accuracy; ~200 tools = 41-83%; ~740 tools = 0-20%. Baseline drops from 78% at 10 tools to 13.62% at 100+ tools (82% collapse).
- **Lost-in-the-middle effect confirmed for tools:** Position bias observed; middle-list tools 22-52% accuracy vs 31-32% at start/end.
- **Anthropic Tool Search Tool (advanced tool use post):** 10+ tools = recommended trigger. Context: 5-server / 58-tool MCP setup consumes ~55K tokens before conversation. Opus 4 improved 49%→74%, Opus 4.5 improved 79.5%→88.1% with tool search enabled. 85% context reduction.
- **Anthropic official Skills API limit:** Max **8 Skills per API request** (hard cap). Guidance: "limit active Skills simultaneously to maintain reliable recall accuracy." No hard number given beyond the 8 cap — advises empirical eval.
- **Anthropic Claude Code SKILL.md loading architecture (confirmed Mar 2026):** THREE-LEVEL loading: (1) Metadata only (~100 tokens/skill) always in system prompt at startup; (2) SKILL.md body loaded on-demand via bash when triggered; (3) Supporting files loaded as needed. Descriptions have `disable-model-invocation: true` to exclude even from Level 1. Official docs: code.claude.com/docs/en/skills and platform.claude.com/docs/en/agents-and-tools/agent-skills/overview.
- **Claude Code skills character budget (confirmed empirically + now documented):** Default = 2% of context window (fallback 16,000 chars). At 63 skills with avg 263-char descriptions: only 42/63 shown ("Showing 42 of 63 skills due to token limits"). ~109 chars overhead per skill. Override: `SLASH_COMMAND_TOOL_CHAR_BUDGET=30000 claude`. Capacity: ~42 skills at 263-char avg, ~67 skills at 130-char avg, ~75 skills at 100-char avg. Skills exceeded budget = silently invisible to model, cannot be invoked even manually.
- **Claude Code skills vs enterprise Skills API — they are different things:** Claude Code = filesystem-based SKILL.md files, no API upload, no code execution container required, discovered from `~/.claude/skills/` and `.claude/skills/`. Enterprise Skills API = uploaded via `/v1/skills` API, runs in VM/code execution container, requires 3 beta headers, workspace-scoped, has pre-built PDF/PPTX/Excel/Word skills. Shared architecture (SKILL.md format, progressive disclosure) but different deployment and runtime.
- **No hard "N skills" limit for Claude Code** — the constraint is the character budget on descriptions (~16K chars default), not a count. Disable `disable-model-invocation: true` on rarely-needed skills to exclude them from budget consumption. `user-invocable: false` keeps description in context; only `disable-model-invocation: true` removes it.
- **MCP server practitioner cap:** 2-3 active MCP servers max for optimal startup. Each server loads full schema at session start. Playwright MCP alone = 22% of 200K context window.
- **Hard limits by platform:** Cursor = 40 MCP tools max; GitHub Copilot = 128 MCP tools max; OpenAI = 128 tools max; Microsoft Copilot Studio = 128 tools max.
- **Practitioner sweet spot:** 25-30 tools before significant performance degradation (no citation, practitioner rule of thumb). Start with 10-20 tool databases; use semantic/RAG retrieval beyond that.
- **"150 instructions reliably"** — practitioner community claim for CLAUDE.md/system prompt rules. No academic citation found.
- **Key sources for Claude Code skills:** code.claude.com/docs/en/skills (authoritative, WebFetch works), platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (authoritative, WebFetch works), platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (authoritative), github.com/anthropics/claude-code/issues/13099 (empirical budget research), gist.github.com/alexey-pelykh/faa3c304f731d6a962efc5fa2a43abe1 (detailed measurements), blog.fsck.com/2025/12/17/claude-code-skills-not-triggering/ (15K char limit reference).
- **Common misinformation:** "5x improvement" or "12x" figures from tool-search posts conflate different metrics. Use specific Anthropic numbers: 49%→74% (Opus 4), 79.5%→88.1% (Opus 4.5). Also: the enterprise "8 Skills API limit" does NOT apply to Claude Code filesystem skills — different system entirely.

## Claude Sonnet 4.6 vs Opus 4.6 Benchmarks (Mar 2026)
Full synthesis in local guide: `~/docs/solutions/claude-model-guide.md` (updated Mar 2, 2026)
Key source access patterns:
- **platform.claude.com/docs/en/about-claude/pricing** — official pricing table; WebFetch works; authoritative. Use this, not third-party summaries.
- **anthropic.com/claude-sonnet-4-6-system-card** — redirects to PDF (binary); cannot extract. Use search result summaries.
- **anthropic.com/news/claude-sonnet-4-6 and /claude-opus-4-6** — JS-gated; WebFetch returns sparse content. Use websearch result summaries.
- **artificialanalysis.ai/models/claude-sonnet-4-6** — WebFetch works, returns Intelligence Index score and speed/latency metrics.
- **artificialanalysis.ai/articles/claude-sonnet-4-6-gdpval** — WebFetch works; gives token consumption comparison (Sonnet 280M vs Opus 160M on GDPval-AA).
- **vellum.ai/blog/claude-opus-4-6-benchmarks** — WebFetch works; good cross-referenced table with ARC-AGI-2 = 68.8% (not 75.2% — that was an error in some coverage).
- **digitalapplied.com/blog/*** — WebFetch works; good benchmark tables. But reports GPQA as 74.1% (standard eval mode).
- **theneuron.ai and officechai.com** — WebFetch works; officechai.com reports GPQA as 89.9% (thinking mode). Both correct; different eval configs.
- **venturebeat.com** — returns 429 on busy periods; skip.
- **lmcouncil.ai/benchmarks** — JS-heavy; returns no data via WebFetch. Scores not accessible.
- **datastudios.org** — Wix-based; WebFetch returns JS/CSS not article text.

Key misinformation patterns:
- **"$15/$75 for Opus 4.6"** is WRONG — that was Opus 4.1/Opus 4. Opus 4.6 is $5/$25 (confirmed platform.claude.com).
- **"5x cheaper" for Sonnet vs Opus** is only valid if comparing to Opus 4.1. Sonnet 4.6 vs Opus 4.6 is 1.67x, not 5x.
- **GPQA Diamond discrepancy (74.1% vs 89.9%)** — both are real. 74.1% = standard mode; 89.9% = adaptive thinking max effort. Gap vs Opus collapses from 17pp to 1.4pp in thinking mode.
- **ARC-AGI-2 for Opus 4.6**: Some sources say 75.2% (error). Confirmed 68.8% via vellum.ai cross-referencing system card.

## HSBC AI Governance Research (Mar 2026)
Full synthesis in chat. Key source access patterns:
- **hsbc.com PDF files (principles doc, annual report, ESG review):** Return binary/compressed PDF — WebFetch cannot extract text. Use search result summaries instead.
- **scribd.com, klover.ai, aidataanalytics.network:** All return 403/error on WebFetch.
- **hsbc.com/news-and-views and /who-we-are/hsbc-and-digital pages:** WebFetch works but returns sparse content (JS-gated main body). Use WebSearch result summaries.
- **HKMA PDFs (hkma.gov.hk/media/eng):** Return binary — cannot extract. Use press release pages instead.
- **pymnts.com, techjournal.uk, agile-me.com, siia.net:** WebFetch works and returns good content.
- **Best single source for governance detail:** pymnts.com (hub-and-spoke model, Albrecht quotes), agile-me.com (four-pillar GMOC structure), techjournal.uk (Sosulski quotes on proportionality).
- **The 7 principles are confirmed via search summaries** — exact verbatim text not extractable (PDF-only).
- **Doug Robertson:** Title confirmed (Group Head of Responsible AI, AI Management & Strategy). No public speeches/papers found — LinkedIn only.
- **No public regulatory submissions found** — HSBC has not published consultation responses to HKMA or UK AI consultations in a discoverable way.

## Firecrawl Claude Code Plugin (Mar 2026)
- **Official status:** Listed in `anthropics/claude-plugins-official` as an EXTERNAL plugin. Install: `/plugin install firecrawl@claude-plugins-official` in Claude Code. Also installable via MCP directly: `claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-YOUR_KEY -- npx -y firecrawl-mcp`
- **Tools (14 total, from raw GitHub README):** firecrawl_scrape, firecrawl_batch_scrape, firecrawl_check_batch_status, firecrawl_map, firecrawl_search, firecrawl_crawl, firecrawl_check_crawl_status, firecrawl_extract, firecrawl_agent, firecrawl_agent_status, firecrawl_browser_create, firecrawl_browser_execute, firecrawl_browser_list, firecrawl_browser_delete
- **Credential:** One Firecrawl API key (fc-...) from firecrawl.dev/app/api-keys
- **Pricing:** 500 free credits (one-time, ~500 page scrapes). Hobby $16/mo (3K credits), Standard $83/mo (100K credits). No free monthly replenishment.
- **VS WebFetch:** WebFetch = Claude built-in, no API key, no credits, free always, but fails on JS-heavy/bot-protected sites and returns raw content. Firecrawl = handles JS rendering + anti-bot + proxy rotation, returns clean LLM-ready markdown, supports crawling entire sites, costs credits.
- **Key advantage over WebFetch/defuddle:** JS-rendering (SPAs), anti-bot bypass, batch/crawl at scale, structured JSON extraction, autonomous agent mode. Not worth it for simple static pages — WebFetch handles those fine.
- **Reliable sources:** raw.githubusercontent.com/firecrawl/firecrawl-mcp-server/main/README.md (authoritative tool list), firecrawl.dev/pricing (pricing), docs.firecrawl.dev/developer-guides/mcp-setup-guides/claude-code (install steps), github.com/anthropics/claude-plugins-official (official status confirmed)
- **Misinformation pattern:** Firecrawl blog claims it's "in Anthropic's official marketplace" — technically true (external_plugins dir) but NOT in the internal/Anthropic-built plugins list. It's a vetted third-party plugin.

## Human Memory Research for AI Architecture (Mar 2026)
Full reference: `human-memory-ai-architecture.md`
- **CLS:** Consolidation = generalization filter, not indiscriminate. Prediction error drives encoding; schema-consistent info consolidates fastest.
- **Sleep:** Top-down instruction > emotional salience (Frontiers 2025). Awake replay tags memories before sleep. Brief waking rest ~ sleep for declarative memory.
- **Forgetting:** Engram competition (Trends Neurosci 2025) — memories suppressed, not erased. Adaptive function = suppress obsolete. Intentional forgetting requires activation first.
- **Prospective memory:** If-then implementation intentions d=0.45-0.51 over plain to-do lists. Reminder anticipation reduces encoding effort — bigger failure when reminder unavailable.
- **Context-dependent memory:** Encoding variability benefits recognition when retrieval context uncertain. Memories shift from perceptual to semantic cues rapidly (dynamic cueing, PMC 2025).
- **Reliable PMC sources; Cell.com/Nature.com 303-redirect — use PMC or search summaries.**

## Midjourney Web API (as of Feb 2026)
- **No official public API.** Enterprise API was announced as "under investigation" (Typeform at midjourney.typeform.com/to/NwpTH4oS). Restricted to enterprise; no public access as of Feb 2026. Prediction market (Manifold) sat at 5% for a 2025 public release.
- **ALL open-source reverse-engineering projects target Discord, not midjourney.com.** Every major GitHub repo (erictik/midjourney-api, George-iam, yachty66, novicezk/midjourney-proxy, trueai-org/midjourney-proxy) calls `discord.com/api/v9/interactions` — not any midjourney.com endpoint.
- **Auth for Discord-based approaches:** Discord user bearer token (captured from browser DevTools Network tab → "interactions" request → Authorization header). Parameters needed: authorization, channel_id, guild_id, application_id, session_id, version, id.
- **Apify Midjourney Automation actor:** Uses exported cookie from midjourney.com (Cookie-Editor extension) — one of the few approaches that targets the web interface directly, but it's browser automation (Playwright/Puppeteer), not a clean REST API call.
- **CelestialRipple/Midjourney-Web-API:** Exposes POST `/api/send_and_receive` + GET `/upscale` but internally uses captured Discord interaction headers — still Discord under the hood.
- **midjourney.com web app:** Launched alpha 2024, full release 2025. Auth is Discord OAuth / Google SSO. Session managed via `__Secure-next-auth` cookie (Next.js auth). No public documentation of internal REST endpoints.
- **No GraphQL endpoint publicly documented.** No REST endpoint for `/api/imagine` on midjourney.com confirmed in any source.
- **Reliable sources for this topic:** github.com/topics/midjourney-api, trueai-org/midjourney-proxy README.en.md, yachty66 raw source code, manifold.markets prediction market, aibase.com enterprise API news

## AI Benchmark Data Access (Feb 2026)
Full reference: `ai-benchmark-data-access.md`
- **API (only one):** Artificial Analysis — `GET https://artificialanalysis.ai/api/v2/data/llms/models` (free key, 1K req/day)
- **HuggingFace datasets:** SWE-bench (`princeton-nlp/SWE-bench*`), SWE-rebench tasks (`nebius/SWE-rebench-leaderboard`), LiveBench (`livebench/*`), Terminal-Bench (`sabhay/terminal-bench-2-leaderboard`, `ia03/terminal-bench`)
- **GitHub YAML:** Aider at `Aider-AI/aider/aider/website/_data/*.yml`
- **SWE-bench leaderboard scores JSON:** `SWE-bench/swe-bench.github.io` → `data/leaderboards.json`
- **Scrape-only:** SEAL (Scale AI) — private eval data by design
- **LM Arena ELO scores:** No official export; use community `nakasyou/lmarena-history` (daily GH Actions)
- **Key caveat:** HF datasets give task corpora, not leaderboard scores, for SWE-rebench and Terminal-Bench

## HK Physiotherapy for Spine/Back (Feb 2026)
- **LIHKG blocks WebFetch** (JS-heavy, Cloudflare). Forum threads often share specific physio names via PM only — not publicly indexed.
- **Baby Kingdom threads:** Same pattern — specific names shared via private message, not public post.
- **Top-rated.online:** Has aggregated Google reviews for HK clinics; direct WebFetch returns 403.
- **happyhongkonger.com/best-physiotherapists-hong-kong/** — best English "best of" list; WebFetch works; covers 17 clinics with A/B ratings.
- **sassyhongkong.com/physiotherapy-physiotherapist-hong-kong-health-wellness/** — expat-skewed but solid clinic directory; WebFetch works.
- **togetherphysio.com/comment and /back** — clinic's own testimonials page; Wix-based, reviews load via JS, not accessible via WebFetch.
- **GooDoctor physio section:** Shows "no data" on direct fetch — use search result summaries instead.
- **Prohealth Asia team page (prohealthasia-hk.com/team):** WebFetch works; lists all therapist names by location.
- **hksstc.com.hk/physiotherapist/:** WebFetch works; gives David Tai's full credentials.
- Key methodology: Chinese-language search surfaces clinic SEO pages, not forum discussions. Forum names are shared via PM. Best approach for "who locals travel to see" = search specific therapist names from clinic sites + cross-reference top-rated.online/GooDoctor review aggregators.

## ESF Kindergarten Admissions (as of Feb 2026)
- **join-us.esf.edu.hk** — ESF admissions portal (JS-heavy; WebFetch returns CSS/structure not content — use WebSearch result summaries instead)
- **oas.esf.edu.hk/welcome** — actual OAS login (email + OTP); kindergarten option inside
- **whichschooladvisor.com/hong-kong/school-news/applying-to-esf-schools-in-hong-kong-2026-guide** — best third-party synthesis; WebFetch works; confirms HK$500 fee
- **topschoolsadmissions.com/blog/esf-k1-year1-year7-applications-faqs** — good FAQs; WebFetch works
- **esf.edu.hk/kindergarten-debenture-application/** — debenture steps; WebFetch works; confirms cheque + HK$50K deposit
- **esf.edu.hk/contact-us/** — confirmed admissions contacts; WebFetch works
- **Fee misinformation:** AI search summaries reported HK$1,000 and HK$2,800 — both wrong for kindergarten. K1 fee is **HK$500**, confirmed by two independent sources. HK$2,800 = primary/secondary. HK$1,000 = unverified/outdated.
- **Payment confirmed:** Credit card via PayPal in the OAS system.
- **Kornhill/Quarry Bay School Kindergarten:** Official name is "ESF Quarry Bay School Kindergarten". 100 K1 places. Connected to ESF QBS → guaranteed primary place there → SIS for secondary. New campus, opening Aug 2026.
- **Late application (post-Sep 2025):** Same OAS portal, rolling waitlist by priority category + date. No hard cutoff.
- **Debenture is entirely separate:** Own form + HK$50K cheque deposit to ESF Centre. NOT part of the online application. Priority Play Visit only (doesn't guarantee place alone).

## HK International School — VEO/VSA Pathway (Feb 24, 2026)
Full research in `~/code/vivesca-terry/chromatin/Theo - International School Research.md` (VSA Deep Dive section).
- **victoria.edu.hk/zh-hk/school-placement/** — official VEO placement data; WebFetch works; lists all destination schools with numbers
- **vsa.edu.hk/admissions/** subpages — WebFetch works on how-to-apply and school-fees; Admissions Policy page (en/Admissions_Policy.aspx) returns 403
- **schooland.hk/kg/victoria** — campus enrollment table; WebFetch works; no K3-specific breakdown
- **edu-kingdom.com/forum.php?mod=viewthread&tid=XXXXXX** — parent threads; WebFetch works with &archiver=1 suffix for older threads
- **gostudy.hk** — good synthesis articles; WebFetch works
- **sakura-membership.com** — debenture explainers; WebFetch works
- **champion-debenture.com** — debenture broker; page loads but prices sparse (contact-only)
- **Misinformation risk:** The "28%" VEO→VSA acceptance rate is third-party inferred (gostudy.hk), not officially stated. VEO publishes absolute numbers only (694/4yrs = ~174/yr). Treat as estimate.
- **Rejection silence:** edu-kingdom has almost no VSA rejection stories from VEO families. Data gap — not evidence of high success rates.
- **"Priority" language is contested:** Official policy says priority; one school tour report says tiebreaker only. Critical to verify directly with VSA.
- **VSA debenture secondary market price:** Individual HK$3M, Corporate HK$4M (reference, broker-sourced). Capital levy amount not publicly disclosed by VSA.

## UK BNO Visa Rules (as of Feb 2026)
Full details researched Feb 24, 2026. Key reliable sources:
- gov.uk/british-national-overseas-bno-visa — official, WebFetch works on overview page but subpages often 403; use search result summaries
- davidsonmorris.com/bno-visa/ — best comprehensive synthesis; WebFetch often times out; use WebSearch result summaries
- sincereimmigration.com — good for 180-day calculation details
- hongkongwatch.org — reliable NGO advocacy source for political risk
- visahq.com/news/ — tracks HK-specific UK immigration news
- vanessaganguin.com/news/ — good for earned settlement consultation details
- Parliament Hansard — authoritative for ministerial statements

### Key verified facts
- **No deadline to apply.** The scheme has no fixed end date. The 5-year ILR pathway was reconfirmed by Home Secretary Nov 20, 2025.
- **Feb 9, 2026 expansion:** Adult children of BNO holders who were under 18 on Jul 1, 1997 can now apply independently (triggered by Jimmy Lai sentencing).
- **Application fee:** £193 (2.5yr) or £268 (5yr) per person. Can apply from HK.
- **IHS (healthcare surcharge):** £1,035/year adults → £2,587.50 (2.5yr) or £5,175 (5yr). Children under 18: £776/year → £1,940 (2.5yr) or £3,880 (5yr). Rates set Feb 2024.
- **Residency:** 180 days max outside UK in ANY rolling 12-month window within 5-year qualifying period (not an average). Can return to HK if under limit.
- **ILR current requirements:** 5 years continuous residence, B1 English, Life in the UK test, £3,029/person fee.
- **Proposed changes (consultation closed Feb 12, 2026):** B2 English (up from B1), possible £12,570/year income threshold. Implementation expected ~April 2026. BNO holders NOT exempt from these changes, but retain 5-year ILR route (vs 10-year for general applicants).
- **Work rights:** Full — all applicants (main + dependants). Cannot work as professional sportsperson only.
- **Financial requirement to apply:** No fixed threshold. Must show 6 months self-sufficiency (approx £2K-£9.2K depending on family size). Exempt if already 12+ months in UK.
- **Citizenship:** After ILR, eligible after 1 further year.
- **Misinformation risk:** Some sources say BNO holders are "fully exempt" from earned settlement — this is WRONG. They are not exempt; they get the 5-year path as their special carve-out, vs 10-year default. The B2/income changes still apply to them.
- **Political risk:** The scheme has no end date but Parliament debates continue. Labour government reconfirmed it Nov 2025. The consultation outcome (B2/income) releases March 2026, takes effect April 2026.

## HK Brokerage for Irish UCITS ETFs on LSE (Feb 2026)
- **Saxo HK: DEAD.** Stopped new clients Sep 30, 2024; no new positions from Nov 1, 2024. Eliminated from all HK broker comparisons going forward.
- **Tiger Brokers HK:** Does NOT offer LSE trading. Markets: HK, US, A-shares, SG, AU, JP, CA only. No plans confirmed.
- **Futu/moomoo HK:** Does NOT offer LSE retail trading. Markets: HK, US, A-shares, SG, AU, JP, CA. LSE membership is institutional/clearing only.
- **HSBC HK:** LSE theoretically available to Premier/Premier Elite customers via phone/hotline only — not standard retail digital platform. Commission ~0.5% minimum GBP30. Very high for passive investing. Not recommended.
- **Standard Chartered HK:** LSE NOT available. US, HK, A-shares only.
- **IBKR HK** — the dominant choice for LSE ETF access:
  - SFC licensed; $0 account minimum; $0 inactivity fee (individual accounts, confirmed on official page Feb 2026)
  - LSE Fixed commission: 0.05% min £3/order (SmartRouting); 0.10% min £4 (Direct Routing)
  - LSE Tiered commission: 0.05% min £1/order + exchange fees (£0.10 for ETFs) + clearing (£0.06)
  - For buy-and-hold: Fixed plan better for orders >~£3,000; Tiered better for very small orders (£1 min)
  - FX conversion: 0.002% (0.2 bps) with $2 USD minimum via manual conversion; auto-conversion adds ~0.03% to rate
  - Fractional shares: US + eligible European ETFs (market cap >$5B, ADV >$5M). VWRA eligibility not confirmed — check platform directly. Recurring investment feature available if fractional is supported.
  - Irish UCITS ETFs on LSE: **NO UK stamp duty** (SDRT exempt for non-UK incorporated securities — confirmed by UK gov regulation)
  - Estate/succession: NO transfer-on-death for non-US residents. Requires probate — email estateprocessing@interactivebrokers.com with death cert. HK probate grants generally issued in 6 weeks for estates >HKD400K.
  - Investor protection: SFC regulated + HK ICF (HKD500K for HKEX-traded products) + US SIPC via IBLLC ($500K/$250K cash) + Lloyd's excess to $30M
- **Key research methodology:** Verify Saxo HK status first in any HK brokerage comparison — it's eliminated but still appears in outdated rankings. Tiger/Futu LSE access is a common misconception (their marketing says "UK stocks" but it's not available at retail level for HK accounts, or it's Singapore only).
- **Sources:** interactivebrokers.com.hk (official fee pages), financemagnates.com (Saxo closure), home.saxo/en-hk/campaigns/closure (confirmation), bogleheads.org (UCITS tax structure), UK gov SDRT regulation

## WeChat RSS API Research (Feb 2026)
Full reference: `~/docs/solutions/wechat-rss-api-technical-reference.md`
- **Two distinct API families:** i.weread.qq.com (WeRead app API, used by wewe-rss) vs mp.weixin.qq.com (MP operator portal, used by we-mp-rss/wechat_spider)
- **WeRead source lookup:** raw.githubusercontent.com/cooderl/wewe-rss/main/apps/server/src/trpc/trpc.service.ts — best single code file for proxy endpoint + error code structure
- **obsidian-weread-plugin weread-api.md** — best doc for book-level i.weread.qq.com endpoints
- **cuiqingcai.com/4652.html** — best doc for mp.weixin.qq.com/cgi-bin/appmsg (fakeid/token approach); WebFetch works on retry
- **GitHub CSDN 521 errors:** blog.csdn.net URLs regularly 521 — don't waste retries; check cnblogs.com or zhihu.com alternatives
- **wewe-rss archived Jan 19, 2026 (read-only)** — all issue data still accessible
- **Methodolgy note:** The proxy domain (weread.111965.xyz) shields the actual i.weread.qq.com endpoints — to get real URLs, read trpc.service.ts AND trace what the proxy forwards to (requires source code of proxy itself, which is not public)

## AI Company Blog RSS Feeds (Mar 2026)
Full synthesis returned to user. Key verified RSS URLs and source patterns:
- **LangChain blog:** moved to blog.langchain.com (was blog.langchain.dev — 308 redirect). RSS: `https://blog.langchain.com/feed` — valid, confirmed live (Feb 2026 posts visible).
- **Hugging Face blog:** `https://huggingface.co/blog/feed.xml` — valid RSS 2.0, 500+ entries, posts multiple times/week.
- **Google DeepMind blog:** `https://deepmind.google/blog/feed/basic` — valid RSS, posts weekly (March 2026 entries confirmed). Via redirect from deepmind.com/blog/feed/basic.
- **AWS ML Blog:** `https://aws.amazon.com/blogs/machine-learning/feed/` — valid, 3-5 posts/day, very high volume.
- **Microsoft Research Blog:** `https://www.microsoft.com/en-us/research/blog/feed/` — valid, biweekly posts.
- **Databricks blog:** `https://www.databricks.com/feed` — valid, 3+ posts/day (high volume).
- **LlamaIndex blog:** `https://www.llamaindex.ai/blog` — no RSS found (JS-rendered). Bi-weekly newsletter format.
- **Anthropic:** No native RSS. Community-generated feeds via github.com/Olshansk/rss-feeds (news, engineering, research separately).
- **OpenAI:** `https://openai.com/feed.xml` — 403 on direct fetch. Community fallback: `https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_openai_research.xml`.
- **Perplexity blog:** `https://www.perplexity.ai/hub` — 403 on WebFetch. No confirmed RSS found.
- **Weaviate blog:** `https://weaviate.io/blog` — 1-2 posts/week. No RSS found via WebFetch.
- **Pinecone blog:** `https://www.pinecone.io/blog/` — weekly. No RSS found.
- **Qdrant blog:** `https://qdrant.tech/blog/` — 2-4 posts/week. No RSS found.
- **Cohere blog:** `https://cohere.com/blog` — JS-gated, content not accessible. Monthly cadence inferred from search results.
- **Mistral AI news:** `https://mistral.ai/news` — monthly product + some engineering posts. No RSS found.
- **Groq blog:** `https://groq.com/blog` — 1-3 posts/week. No RSS found.
- **Anthropic Alignment Science:** `https://alignment.anthropic.com/` — 2-4 posts/month, safety research focus. No RSS confirmed.
- **For blogs without native RSS:** Use openrss.org or rss.app to generate feeds from blog URLs.
- **Olshansk/rss-feeds GitHub repo** is the best source for Anthropic/OpenAI/xAI feeds (auto-generated daily from GH Actions).

## Wechat2RSS (wechat2rss.xlab.app) — Feb 2026
- **Service URL:** https://wechat2rss.xlab.app — main site + docs
- **Docs that WebFetch successfully:** /deploy/ (pricing), /deploy/deploy (Docker steps), /deploy/config (all vars), /deploy/guide (usage), /deploy/api (feed URL + endpoints)
- **Two modes:** (1) Free hosted public list — 300+ accounts at /list/all, no login needed; (2) Self-hosted paid license — full-featured Docker deployment, your own WeChat login
- **Pricing (self-hosted):** Trial ¥10/7 days, Monthly ¥15/month, Annual ¥150/year. Pre-Oct 2024 users: ¥10/month or ¥100/year discounted renewal.
- **Activation:** Pay via WeChat QR code on /deploy/ page, note your email in payment memo. Code emailed within 24h. Three env vars required: LIC_EMAIL (lowercase), LIC_CODE, RSS_HOST.
- **Feed URL format:** `/feed/:id.xml` (XML) or `/feed/:id.json` (JSON Feed). Aggregated: `/feed/all.xml?k=TOKEN`.
- **Adding accounts:** Two methods: (1) `/add/:id` with public account biz ID; (2) `/addurl?url=https://...` auto-parses from article URL. To get biz ID: open article in browser → F12 → `atob(biz)`. Also: open WeChat article → share → "Read in WeChat Reading" to get WeChat Reading login for account scanner.
- **RSS_TOKEN:** Service password; passed as `?k=TOKEN` in all API/subscription URLs.
- **Self-hosted privacy advantage:** No credentials sent outside your server + WeChat servers. Competitor services transmit login data externally.

## NVIDIA China GPU Export Controls (as of Feb 23, 2026)

### Reliable sources for this topic
- gamersnexus.net/gpus-news/timeline-gpu-export-controls-nvidia-gpu-bans-ai-gpu-black-market: best single-page chronological timeline (current through Aug 2025)
- tomshardware.com: best English-language GPU spec coverage; WebFetch sometimes 403s, use search results instead
- datacenterdynamics.com: good data centre industry angle; 403 on WebFetch
- scmp.com: original B30A source (Aug 19, 2025 report); WebFetch works with summarisation
- merics.org: reliable China tech market analysis
- cfr.org: authoritative policy analysis on chip controls
- mayerbrown.com/en/insights/publications/: clean WebFetch, good BIS rule summaries
- techcrunch.com: reliable breaking news on export control announcements

### Key verified facts (Feb 2026)
- **B30A status:** Real engineering project, NOT officially confirmed. All specs from SCMP Aug 2025 via 2 unnamed insiders. Jensen Huang acknowledged it Aug 22, 2025 ("up to the US government"). No approval announced. Specs NOT finalised as of the report.
- **B30A reported specs (unverified):** 144 GB HBM3e, ~4.0 TB/s bandwidth, ~7 PFLOPS dense FP4; single-die Blackwell; ~7.6x H20 in FP8; ~half B300; 2.2x Huawei Ascend 910C TPP
- **H20 ban/reversal:** Apr 9-16, 2025 — new licence requirement; NVIDIA took $5.5B charge. Jul 14, 2025 — licences approved, H20 sales resumed. Aug 2025 — 15% revenue to US government agreed.
- **AI Diffusion Rule:** Biden published Jan 15, 2025; Trump rescinded May 7, 2025. 2022/2023 China-specific controls remain in force regardless.
- **H200 approved Dec 8, 2025:** Trump announced; 25% revenue condition; case-by-case BIS licences. BIS rule formalised Jan 15, 2026. As of Feb 4, 2026, H200 shipments stalled in US security review (State Dept pushing for tighter conditions). Chinese customs reportedly told not to admit H200s.
- **B30A vs H200 strategic question:** H200 approval makes B30A's regulatory path less urgent for NVIDIA. Both products potentially compete for same Chinese hyperscaler budgets.
- **Huawei context:** Ascend 910C shipping from May 2025, ~60% of H100 performance per DeepSeek benchmarks. Ramping to 600K units in 2025 but yield-constrained. B30A approval would still be a 2.2x performance advantage over 910C.

### Misinformation patterns
- "12x faster than H20" figures in secondary sources conflate FP4 vs FP8 or are unverified — use ~7.6x (FP8 normalised)
- All B30A specs ultimately trace to one SCMP report from two unnamed sources — do not treat as verified hardware specs
- The Biden AI Diffusion Rule and the 2022/2023 China controls are separate instruments — rescinding the Diffusion Rule did NOT loosen the older China controls

## Open-Source Research Agent Architectures

### GPT-Researcher (assafelovic/gpt-researcher) — Feb 2026 code review
- raw.githubusercontent.com/assafelovic/gpt-researcher/master/gpt_researcher/: best access path for actual source files
- deepwiki.com/assafelovic/gpt-researcher/1-overview: good architecture summary (but use raw GitHub for actual code)
- Key confirmed patterns (code-verified):
  - Planner uses `strategic_llm` (o3/o4-mini), seeded with one real search before generating sub-queries
  - Sub-query parallelism: `asyncio.gather()` with no semaphore at standard level; semaphore only in deep_research
  - Source provenance: LangChain Document metadata `{source: url, title: title}` → preserved through EmbeddingsFilter → formatted as `Source: <url>\nTitle:\nContent:` block in context string
  - Statistical deduplication: NOT implemented. README claims it; code does not have it.
  - Deep research tree: breadth=3, depth=2 defaults; each depth level halves breadth (`max(2, breadth//2)`); spawns fresh GPTResearcher per node
  - Context budget: 25,000-word cap; trimmed by reverse iteration (keeps most recent)
  - MCP cache pattern: "fast" mode runs MCP once on root query, reuses result for all sub-queries
- Misinformation risk: "cross-source reliability scoring" is a marketing claim, not implemented in code. Always verify claims against raw source files.
- Methodology that worked: fetch raw.githubusercontent.com URLs directly — WebFetch returns full source, not the summarized GitHub HTML view

### Australian Skilled Migration (189/190 visas) — Feb 2026 research
- immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/skilled-independent-189/points-table: official points table (JS-heavy, WebFetch returns empty — use third-party synthesis)
- anzscosearch.com/mltssl/: best for checking MLTSSL membership by ANZSCO code (WebFetch works)
- smartvisaguide.com/occupations/<code>: tracks actual visa grant data and eligible visa subclasses per occupation (authoritative)
- ahclawyers.com: good for round snapshot analysis and CSOL changes
- krisahn.com.au: tier system explanation
- visasidekick.com.au: allocation and invitation round tracking
- acs.org.au/msa/: ACS assessment requirements (WebFetch works)
- Key facts verified Feb 2026:
  - **MLTSSL vs CSOL split:** CSOL (Dec 7, 2024) governs 482/186 only. MLTSSL still governs 189/190/491. These are separate lists.
  - **224115 Data Scientist:** CSOL only — NOT on MLTSSL → NOT eligible for subclass 189. Confirmed by smartvisaguide.com/occupations/224115.
  - **224114 Data Analyst:** Same — CSOL only, not MLTSSL.
  - **Data Scientist 189 pathway:** Must use ICT MLTSSL code — 261111 (ICT Business Analyst), 261112 (Systems Analyst), or 261313 (Software Engineer). ACS assesses all three.
  - **ICT on MLTSSL (Tier 4, 0.5% multiplier):** 261111, 261112, 261211, 261311, 261312, 261313, 261399, 262112, 263111, 263311, 263312
  - **Nov 2025 round cutoffs:** 261111 = 70–100 pts; 261112 = 70–95 pts; 261313 = 85–100 pts
  - **Points minimum:** 65 to lodge EOI; realistic floor for ICT 189 is 85–90 pts
  - **ACS fee:** AUD $1,498. Processing 4–6 weeks. ICT major degree = 2 yrs exp (last 10) required.
  - **190 state best bets (no job offer, ICT):** NSW, Victoria, South Australia. ACT if you have local residency. WA requires job offer. Tasmania is health/education focused.
- Misinformation risk: avie.com.au incorrectly lists 224115 as 189-eligible. Always verify occupation list membership at smartvisaguide.com/occupations/<code> or anzscosearch.com/mltssl/.
- anzscosearch.com/points-test/ has English points wrong (shows Competent = 10 pts). Correct is 0 pts.

## Bluetooth Speaker Quiet Floor Research (Mar 2026)
- **DXOMARK is the only lab that specifically tests "Bedtime" use case** for speakers — most other reviewers don't measure minimum volume at all
- **Bose SoundLink Flex: confirmed BAD** for bedtime — DXOMARK explicitly says "first volume steps do not ensure full intelligibility" and "not recommended for bedtime." Volume sub-score 57/141.
- **Sony SRS-XB100: confirmed problematic** — Reddit quote: "its quietest volume still sounds like someone is actually with you." No EQ app. Min volume too loud for bedroom.
- **Bose SoundLink Micro (Gen 1 & 2):** No lab data on minimum volume. Reddit suggests "great at moderate levels" but no quiet-floor test. Gen 2 = HK$1,099 (Bose HK official). Distorts above 50% — so works best in lower half of volume range.
- **JBL Go 4:** HK$320–399 (authorized). No specific quiet-floor data in reviews. Max 83.3 dB. 5-band EQ in app helps.
- **Tribit Stormbox Micro 2:** Ranked #1 small speaker by speakerranking.com for sound quality. HK$389 (YOHO). No quiet-floor lab data but reviews note "adequate" low-volume control.
- **Soundcore Select 4 Go / Mini 3 Pro:** Reddit recommends Select 4 Go for close-proximity low-volume listening over XB100. No lab quiet-floor data.
- **Software workaround:** Android "Disable Absolute Volume" in Developer Options decouples phone and speaker volume — enables finer granular control at minimum.
- **Methodology note:** Most review sites don't test minimum volume. DXOMARK does. Forum threads (MetaFilter, Reddit via redditrecs.com) give anecdotal user reports. price.com.hk reliable for HK pricing.
- **Key gap:** No head-to-head minimum dB comparison found. This metric is genuinely underreported.

## Reliable Source Domains by Topic

### AI Cost-Per-Task vs Per-Token (as of Feb 22, 2026)
- artificialanalysis.ai/articles/sonnet-4-6-everything-you-need-to-know: primary source for Sonnet 4.6 token inflation data
- artificialanalysis.ai/articles/claude-sonnet-4-6-gdpval: GDPval-AA benchmark — confirms 280M vs 58M token figure (4.8x)
- swe-rebench.com: best source for cost-per-SWE-bench-problem with actual dollar amounts per model
- hal.cs.princeton.edu/swebench_verified_mini: HAL leaderboard — cost per 50-task suite with token counts
- aider.chat/docs/leaderboards/: Aider polyglot benchmark — cost per benchmark run across models
- adam.holter.com/ai-costs-in-2025-cheaper-tokens-pricier-workflows: best synthesis of token deflation + workflow inflation paradox
- bvp.com/atlas/the-ai-pricing-and-monetization-playbook: Bessemer — token/task/outcome pricing framework with gross margin data
- deloitte.com/us/en/insights/topics/emerging-technologies/ai-tokens-how-to-navigate-spend-dynamics.html: enterprise cost governance framework
- Key verified facts (Feb 2026):
  - Sonnet 4.6 on GDPval-AA: 280M tokens vs Sonnet 4.5's 58M = **4.8x inflation** (source: AA GDPval article)
  - Opus 4.6 non-reasoning: 11M output tokens vs median 3.9M (2.8x verbose); adaptive max: 58M vs median 12M (4.8x verbose)
  - MiniMax M2.5: 56M vs median 15M; M2.1: 58M vs 15M; M2: 70M vs 15M (all verbose)
  - AA Intelligence Index run costs: Sonnet 4.6 $2,088; Opus 4.6 $2,486; Sonnet 4.5 ~$733 (Sonnet 4.6 = 3x more expensive to run than 4.5)
  - SWE-rebench cost/problem: Claude Code $3.50 (52.9% resolve), Claude Opus 4.6 $0.93 (51.7%), GPT-5.2 xhigh $1.28 (51.7%), MiniMax M2.5 $0.09 (39.6%)
  - SWE-rebench Chinese models (Feb 2026, 48-problem dynamic set): GLM-5 $0.45/prob 42.1% → $1.07/resolved | GLM-4.7 $0.27/prob 41.3% → $0.65/resolved | Qwen3-Coder-Next $0.49/prob 40.0% → $1.23/resolved | DeepSeek-V3.2 $0.15/prob 37.5% → $0.40/resolved | DeepSeek-R1-0528 $0.41/prob 21.7% → $1.89/resolved | MiniMax M2.5 $0.09/prob 39.6% → $0.23/resolved
  - Qwen 3.5 (397B MoE, Feb 16 2026): NOT yet on SWE-rebench; SWE-bench Verified self-reported 76.4%; API ~$0.11/1M in, output price not confirmed; Qwen3-Coder-Next is a separate older coding-specialist model
  - GLM-5 pricing: $1.00/1M in, $3.20/1M out (docs.z.ai); AA Intelligence Index score 50
  - DeepSeek-V3.2 pricing: $0.28/1M in (cache miss), $0.42/1M out (api-docs.deepseek.com)
  - DeepSeek-R1-0528 SWE-rebench: 21.7% resolve rate — low because R1 RL training skews toward math/algorithmic, not real-world SWE tasks
  - Qwen3-Coder-Next vs Qwen 3.5: DIFFERENT models. Qwen3-Coder-Next is coding-specialist on Qwen3-Next-80B-A3B base; Qwen 3.5 is the general-purpose Feb 2026 flagship (397B MoE)
  - HAL SWE-bench mini: Sonnet 4.5 High $12.89/problem (72% accuracy); Claude Opus 4.1 $44.27/problem (61%); Gemini 2.0 Flash $0.09 (24%)
  - Aider benchmark costs: o3-pro $146.32; GPT-4.5-preview $183.18; Gemini 2.5 Pro $49.88; Claude Opus 4 $65.75; DeepSeek-V3.2 Chat $0.88
  - Adam Holter: GPT-5 high reasoning $823/task vs GPT-5 Nano $67/task for equivalent work
  - Grok 4 ($3/$15/M) costs "effectively 3x Sonnet with thinking enabled, 15x Sonnet without" due to reasoning token volume
  - Token price range: GPT-5 Mini $0.25/$2/M; Gemini 2.5 Flash-Lite $0.10/$0.40/M; DeepSeek R1 $0.57/$1.90/M
- Misinformation risk: Token-list prices are NEVER sufficient for comparing agentic task costs. Verbosity and reasoning token inflation routinely cause 3x-15x cost multipliers not reflected in per-token rates.
- Key enterprise framework: Deloitte advocates token FinOps with real-time monitoring, business unit chargebacks, and ROI thresholds per project. Traditional TCO models explicitly flagged as insufficient.
- Bessemer gross margin insight: AI companies run 50-60% gross margins vs 80-90% for SaaS — reason per-token pricing is structurally fragile.

### AI Frontier Models Landscape (as of Feb 22, 2026)
- llm-stats.com/llm-updates: best single page for chronological model releases with dates
- artificialanalysis.ai/models/<model-slug>: authoritative for intelligence index, speed, price rankings — WebFetch works cleanly
- arena.ai/leaderboard: live Elo scores; lmarena.ai redirects here (301)
- llm-stats.com/models/<slug>: good pricing/context/benchmark summaries; WebFetch works
- the-decoder.com: reliable English-language coverage of Chinese model releases
- openai.com/index/ pages: 403 on direct WebFetch — use search results summaries instead
- Key findings Feb 2026: Gemini 3.1 Pro = #1 on Artificial Analysis Intelligence Index (score 57). Claude Opus 4.6 = #1 on arena.ai text leaderboard Elo (~1506). Best value: Sonnet 4.6 ($3/$15) or Gemini 3.1 Pro ($2/$12). Biggest open-source story: GLM-5 (MIT, 744B MoE) + Qwen 3.5 (397B MoE, Apache 2.0).
- Misinformation risk: Alibaba benchmark claims for Qwen 3.5 are self-reported — CNBC could not independently verify. Always flag vendor-reported benchmarks vs third-party (Arena Elo, Artificial Analysis).
- Leaderboard scores are NOT stable: different sources report different Elo scores for the same model depending on snapshot date and whether "thinking" variants are included separately.

### OpenAI Codex CLI (as of Feb 2026)
- developers.openai.com/codex/: official docs hub — all feature pages WebFetch cleanly
- github.com/openai/codex: source + discussions; Rust rewrite is now canonical (Node.js deprecated)
- developers.openai.com/codex/changelog/: authoritative for release history
- simonwillison.net/2025/Dec/12/openai-skills/: best analysis of skills format adoption
- Key findings documented in response to Terry Feb 22 2026 — see below for architecture facts
- **Tool primitives:** `read_file`, `apply_patch`, shell exec — NOT a rich multi-tool set. One primary tool = shell command executor (Unix philosophy). Web search built-in (cached index by default, or live mode).
- **Hooks:** Only `notify` hook officially shipped — fires on `agent-turn-complete`, receives JSON payload via stdin. No pre-tool / post-tool hooks. PR #11067 (Feb 8, 2026) proposing full hooks system (PreToolUse, PostToolUse, AfterAgent, SessionStart) was REJECTED — OpenAI said "no longer accepting unsolicited code contributions; all contributions by invitation only." Maintainer stated they are "actively working on designing a hooks system" internally. Significant community demand (447 upvotes on issue #2109 as of Mar 2026). Only `agent-turn-complete` event supported; `agent-turn-start` requested but not shipped (#8455).
- **Instruction file:** `AGENTS.md` — global at `~/.codex/AGENTS.md`, project-scoped (walks repo root → CWD). Also `AGENTS.override.md` for strict overrides. Configurable fallback filenames. 32 KiB combined limit. Injected as user-role messages before prompt.
- **Skills:** SKILL.md format (YAML front matter: name, description + instructions). Lives at `.agents/skills/` (repo), `~/.agents/skills/` (user), `/etc/codex/skills` (admin). Explicit (`$skill-name`) or implicit (Codex picks based on task match). Same format as Claude Code skills — Simon Willison notes it's "quietly adopted" not formally announced.
- **MCP:** Full MCP client support — STDIO and streamable HTTP servers. Config in `~/.codex/config.toml`. Tool allow/denylists per server. Codex can also run AS an MCP server (`codex mcp-server`).
- **Models:** Defaults to `gpt-5.3-codex`. Supports any Chat Completions or Responses API provider. OSS/local via `--oss` flag (Ollama, LM Studio). Custom providers in config.toml with `base_url` + `env_key`. Non-OpenAI providers work but Codex is optimized for OpenAI.
- **Multi-agent:** Experimental. Parallel subagents spawned automatically or on request. Roles defined in `[agents]` section of config.toml (model, reasoning effort, role-specific config file). Built-in roles: default, worker, explorer. Subagents inherit sandbox policy, run non-interactive.
- **General purpose:** NOT positioned as general assistant. Coding-focused by design. Can do non-coding tasks via shell + MCP but has no built-in email/calendar/messaging tools.
- **Architecture vs Claude Code:** Codex = Unix shell-first (one tool: shell executor). Claude Code = purpose-built tools (Read, Write, Bash, WebSearch, etc.). Claude Code hooks are richer (pre/post tool). Claude Code's CLAUDE.md ≈ Codex's AGENTS.md. Claude Code's `/commands` ≈ Codex's slash commands + skills.
- **Misinformation risk:** Some comparison articles claim Codex has "no non-OpenAI model support" — FALSE, it does via custom providers. Don't trust single-source comparisons on this topic.

### OpenCode (sst/opencode) Hook System (as of Mar 2026)
- **Two-tier hook system:** (1) TypeScript/JS plugin hooks (full-featured, primary); (2) config-based shell hooks (experimental, limited).
- **Plugin hooks** (`.opencode/plugins/*.ts`): require `@opencode-ai/plugin` package. Key hook types: `tool.execute.before` (blocks/modifies, Claude PreToolUse equivalent), `tool.execute.after` (observe only), `session.created`, `session.idle` (post-turn, Claude PostTurn equivalent), `session.compacted`, `experimental.chat.system.transform` (inject system prompt). Shell commands invoked via Bun `$` template literal inside plugin code.
- **Config-based hooks** (`opencode.jsonc` under `experimental.hook`): `file_edited` and `session_completed` only. Each takes `command: [...]` array. No pre-tool event. Simpler but very limited.
- **NOT shell-script hooks**: Unlike Claude Code (plain shell commands in settings.json), OpenCode plugins must be TypeScript/JavaScript. Shell scripts can be *called from* plugins via Bun's `$` API.
- **Known limitations (open issues as of Mar 2026):** MCP tool calls don't trigger plugin hooks (#2319); subagent tool calls bypass `tool.execute.before` (#5894 — security risk if relying on hooks for policy enforcement).
- **Best sources:** opencode.ai/docs/plugins/, github.com/sst/opencode/issues/1473 (origin issue, closed via plugin system), gist.github.com/johnlindquist/0adf1032b4e84942f3e1050aba3c5e4a (community plugin guide)

### Specialty Coffee Equipment Research
- orea.uk: official Orea brand site — product specs, geometry philosophy, filter types (WebFetch works). Designer name NOT publicly credited; company presents as collective
- slowpoursupply.co: excellent for WBC winning recipes, equipment analysis, specialty drippers
- sprudge.com: authoritative championship coverage; 2025 WBC George Peng (SOLO) vs 2024 Martin Wölfl (Orea V4)
- thebasicbarista.com: large retailer with detailed product descriptions, comparative specs
- sibarist.coffee: premium filter paper vendor; publishes champion packs with dripper combos
- Key finding: **Orea V4** = modular flat-bottom APEX (hybrid geometry), 4 interchangeable bottoms, USD $67–70, HK$535. 20%+ of 2024 WBC competitors used it; highest-scoring cups in 2024/2025 WBC. NOT beginner-friendly (steep learning curve, little margin for error).
- Key finding: **SOLO Mazelab** = fixed 40° sloped bottom, PCTG plastic (low thermal mass), USD $44–48. Designed by Jackie Tran (CZ Brewers Cup 2024). 2025 WBC champion George Jinyang Peng used it over Orea V4 — signifies shift toward temperature-control methodology.
- Key finding: **Orea V4 Narrow vs Wide** — Narrow emphasizes brightness/intensity (≤28g), Wide emphasizes balance/body (≤36g). Both at same price.
- Key finding: **Orea V4 bottoms** — Fast (unclogable, fine grind), Classic (balanced, forgiving), Open, APEX (hybrid). Negotiator tool needed for flat-paper brewing (additional cost).
- Misinformation risk: Marketing "4 brewers in 1" oversells ease; actually requires significant parameter tuning and understanding of interaction between bottom choice, grind, pour stage, and filter type.
- Common complaints: Kalita wave papers can stall/over-extract; Orea's own TYPE G flat filters slightly thick; minimal room for pouring error; learning curve high.
- Chinese user feedback scarce (one Threads post found Feb 2026); no comprehensive Mandarin review corpus yet.

### Mechanical Keyboard Hardware Research
- qwertykeys.com: official vendor + brand site for Qwertykeys/Neo series; WebFetch works but price display may show local currency as "$" (verify USD via third-party vendors like divinikey.com or swagkeys.com)
- markerchun.com: designer's own project pages — best source for design intent, specs table, acoustic philosophy
- alexotos.com: reliable independent reviewer; fetches cleanly; gives price ranges and honest cons
- divinikey.com, swagkeys.com: US vendors with clean USD pricing; WebFetch works well
- deltakeyco.com: EU vendor (prices in EUR despite "$" symbol display); WebFetch returns currency confusion
- Key finding: Neo65Cu is a Qwertykeys product designed by markerchun; case material is aluminum top + brass OR copper bottom (Cu in name = copper-option bottom, not full copper)
- Key finding: "Cu" series price range $110-$140 USD bare kit (brass vs copper bottom); $165-$220 built/reviewed configurations
- Misinformation risk: Qwertykeys product page may show "$4,000" — likely a currency display bug (HKD or TWD). Real USD price is ~$110-140.

### 40% Keyboard Research (Travel-Focused) — Feb 2026
- keybumps.com/articles/best-40-percent-mechanical-keyboards.html: good overview but missing weights for some boards
- keeb-finder.com/keyboards/filter/40: comprehensive listing; WebFetch 403s but search result summaries reliable; prices sometimes in non-USD (check vendor page)
- epomaker.com product pages: WebFetch works but renders JS-heavy — specs often incomplete; cross-check with xda-developers or notebookcheck reviews
- aphnetworks.com/reviews/: reliable multi-page reviews with tested battery life; need to fetch page /4 for score
- notebookcheck.net: best for real-world battery testing; tested TH40 Bluetooth drain rate
- green-keys.info: Japanese reviewer, good depth, but WebFetch returns CSS-only (content blocked)
- mechanicalkeyboards.com: prices display in non-USD for some regions (showed "$11,900" for $129 board — currency bug)
- Misinformation patterns: retailer weights often include shipping box (kbdfans.com showed 1,260g for Agar Mini when keyboard-only is ~1,089g for aluminum). Always flag if weight source is product page vs reviewed unit.
- Key verified specs (Feb 2026):
  - TH40: 440-500g (sources vary by 60g; official says 440g, reviewers say ~500g), 258x97x35mm, $72-80, ABS, gasket, QMK/VIA, 3000mAh, tri-mode
  - Luma40: 410g, 240x87x20.8mm, $98-116, CNC aluminum, tray-mount, VIA, 1450mAh, tri-mode, 47-key ortholinear low-profile
  - Vortex Core Plus: 552g, 269x92x15mm, $129, CNC aluminum, 50-key low-profile, AAA batteries (NOT rechargeable), tri-mode (BT+2.4GHz+wired), VIA 3.0, Gateron LP only
  - Keychron Q9: ~1050g, 326x94x20mm, $59-151, 6063 aluminum, double-gasket, QMK/VIA, wired-only
  - KBDFans Agar Mini: ~1089g (aluminum), $163-278, gasket, QMK (wired)/ZMK (wireless), 300mAh, dual-mode wireless version available — NOT travel-friendly weight
  - Zan40 (Niuniu/zFrontier): $154-179, aluminum, VIAL, tri-mode available, weight unconfirmed
  - NIUNIU @40: $89-109, aluminum, ~550g, 236x85x30mm, VIAL, tri-mode, low-profile
- TH40 known issues: Bluetooth reconnect bug (firmware update needed, deletes settings); clips break on disassembly; VIA needs manual JSON upload + V2 mode enable; missing apostrophe/quotation mark in default layer config; macro editing in VIA errors out
- Vortex Core Plus critical travel caveat: uses 2x AAA alkaline batteries (not rechargeable) — requires carrying spare batteries on trips

### Keyboard Layout Learning (Colemak-DH)
- dreymar.colemak.org/training.html: canonical training advice — specific tool recommendations and methodology (WebFetch works cleanly)
- colemakmods.github.io/mod-dh/learn.html: switching difficulty index and DH-specific caveats (WebFetch works)
- colemakmods.github.io/mod-dh/: canonical Colemak-DH project site
- forum.colemak.com/forum/6-experiences/: best repository of first-person transition accounts
- colemak.academy/: dedicated trainer for Colemak/Colemak-DH (free, no login needed)
- monkeytype.com + keybr.com: the community's two default training tools; both support Colemak-DH
- vale.rocks/posts/typing-systems: good cold turkey timeline (4.8 → 83 WPM documented)
- filiphalas.com/my-journey-zsa-voyager-miryoku-colemak-dh: realistic programmer transition with Vim caveats
- sbulav.github.io/typing/switch-to-colemak/: structured approach, keybr → monkeytype progression, Vim pitfalls
- blog.beerriot.com/2024/10/19/learning-colemak-dh/: most recent first-person account (Oct 2024), good on sleep/muscle-memory insight
- Key verified facts:
  - Colemak-DH difficulty index = 29 (vs Colemak 28, Dvorak 68) — modest difference from vanilla Colemak
  - Colemak-DH moves D and H out of centre column; DH vs Colemak is a nearly identical learning path
  - Community consensus: start with DH directly, not vanilla Colemak — no reason to switch twice
  - Cold turkey: gets you to fluency faster (weeks not months) but painful; Tarmak adds stability (each step ~1-2 weeks)
  - Tarmak has a DH-specific progression: 4 steps, each moving 3-4 keys
  - ZXCV shortcuts: Colemak-DH Angle mod moves V one position — minor issue, workaround is Extend layer or OS-level rebind
  - Vim: three camps — (1) no remap (stay physical), (2) langmap neio for hjkl, (3) noremap QWERTY-equivalents. Most programmers end up in camp 1 or 2
  - Practice schedule consensus: 15-20 min/day beats long sessions; daily consistency > volume; sleep is a documented accelerant

## Google Takeout / Browser Auth Automation (Feb 2026)
- corbado.com/blog/device-bound-session-credentials-dbsc: best DBSC explainer (technical, accurate, covers TPM requirement)
- developer.chrome.com/blog/remote-debugging-port: Chrome 136+ blocks `--remote-debugging-port` on DEFAULT profile; need `--user-data-dir` to separate debug profile
- github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1054: key thread — Google detects UCD as of Chrome 110+; SeleniumBase needed for newer Chrome
- rebrowser.net/blog/undetected-chromedriver*: ~30% success vs advanced systems; recommends Nodriver/dedicated APIs for production
- blog.castle.io/from-puppeteer-stealth-to-nodriver*: anti-detect evolution; modern tools move toward OS-level input (no CDP)
- raf.dev/blog/chrome-debugging-profile-mcp/: clearest guide for `--user-data-dir` debug profile setup for automation
- Key facts verified:
  - Google Takeout download URLs: 7-day window but per-download passkey re-auth triggered by server-side signed URL, not cookie age
  - DBSC: Origin Trial Oct 2025–Feb 2026 (Windows/TPM only). Short-lived cookies (5-10 min). Stolen cookies can't be refreshed without bound private key. NOT yet enforced on Takeout in Feb 2026 (still experimental/beta)
  - No public Google Takeout API. Internal `takeout-pa.googleapis.com` exists but cannot be enabled in Cloud Console — reverse-engineered only
  - Chrome 136+: `--remote-debugging-port` requires `--user-data-dir` pointing to non-default dir
  - Practical winner: CDP attach to dedicated debug Chrome profile (user logs in once to debug-profile Chrome, Rust connects via chromiumoxide's connectOverCDP equivalent)
  - Rust CDP libraries: chromiumoxide (mattsse, main), spider_chrome (fork, higher concurrency), chaser-oxide (stealth fork, experimental)
  - undetected-chromedriver / playwright-stealth: ~30% success vs Google's systems; "This browser may not be secure" error common; NOT reliable for Google auth in 2025
- Misinformation patterns: Secondary sources often say "just use stealth mode" without testing Google specifically. Google's bot detection is tier-1 hardened; Cloudflare-bypass tools do not generalise to Google auth.
  - WPM timeline (community aggregate, starting from ~80 WPM QWERTY):
    - Week 1-2: 10-40 WPM (painful)
    - Month 1: 40-60 WPM
    - Month 2-3: 60-80 WPM (back to pre-switch speed)
    - Month 6+: 80-100+ WPM
  - Common pitfalls: (1) switching back to QWERTY under pressure, (2) training on <200-word lists, (3) not deleting whole word on error, (4) skipping accuracy discipline (aim 96%+), (5) attempting alt-fingering before 50 WPM
  - Programming: symbols layer (AltGr key) is the community standard — keeps brackets on home-adjacent keys
  - Misinformation pattern: "Colemak-DH is much harder than vanilla Colemak" — the difficulty index difference is only 1 point

### WeChat Public Account RSS Tools (as of Feb 23, 2026)
- github.com/rachelos/we-mp-rss: best actively maintained self-hosted option (last release v1.4.8 Dec 2025, 2.2k stars). Mechanism: simulates mp.weixin.qq.com web platform requests using fakeid+token from operator's own WeChat MP account. Token expires and needs periodic renewal.
- wechat2rss.xlab.app: longest-running SaaS (ran free ~3 years). Curated list of 300+ free accounts; self-hosted version ¥200/year, supports 400+ subscriptions per account, 6h avg latency. Mechanism undisclosed publicly.
- werss.app: SaaS, paid, "manually collected" articles, 1 min–28 hour latency, WeChat login auth. Stability history: acknowledged 2023 instability. Free trial 3 days; VIP1 ~¥100/yr, VIP2 ~¥180/yr.
- jintiankansha.me (今天看啥): SaaS, curated content, paid VIP for full RSS, ad-free, custom count. Free tier: 2 accounts. Covers Bilibili/Zhihu too, not just WeChat.
- github.com/cooderl/wewe-rss: ARCHIVED Jan 19, 2026. Was based on WeChat Reading API; rate-limited to 50 req/account/day by Tencent before archival. 8.8k stars. Do NOT recommend for new setups.
- github.com/feeddd/feeds: CLOSED Jul 5, 2023. Was crowd-sourced via Android Hamibot automation. 2.1k stars.
- github.com/hellodword/wechat-feeds: ARCHIVED/STOPPED. Was GitHub-hosted static feeds for 6200+ accounts. Dead.
- RSSHub /wechat/mp/msgalbum/ route: narrow use case only — works only for accounts that publish tagged article albums. Not general-purpose.
- EFB (ehForwarderBot/efb-wechat-slave): bridges WeChat to Telegram. Last release Jan 2022, depends on web WeChat (blocked for most accounts since 2017). Effectively dead.
- Huginn: self-hosted automation that can scrape Sogou WeChat search. Works but manual setup, Sogou links expire quickly, requires proxy.
- Key mechanisms taxonomy: (1) WeChat Reading API [wewe-rss, archived], (2) WeChat MP platform web API with operator token [we-mp-rss, wechat2rss], (3) Manual/crowd-sourced curation [feeddd-dead, werss], (4) WeChat web protocol [EFB-dead], (5) Sogou search scraping [Huginn-hacky], (6) Article album tags [RSSHub-narrow]
- Misinformation risk: Many blog posts still recommend wewe-rss as if it's active — it was archived Jan 2026. Always check GitHub for archive notice.
- Search methodology: Chinese-language V2EX threads and Zhihu 知乎 articles surface the most current community knowledge. GitHub topics/wechat-rss is sparse (only 3 repos).

### AI Governance Regulation (Banking / HK)
- hkma.gov.hk/eng/regulatory-resources/regulatory-guides/by-subject-current/fintech/: canonical HKMA fintech/AI guidance index
- brdr.hkma.gov.hk: HKMA Banking Regulatory Document Repository — direct PDF access for circulars
- bis.org/bcbs/bcbs_work.htm: BCBS work programme (annual updates)
- bis.org/bcbs/publ/d605.htm: BCBS third-party risk principles (finalised Dec 8, 2025)
- iapp.org/news/: reliable for EU AI Act deadline tracking (confirmed Commission missed Feb 2 deadline)
- mas.gov.sg/publications/consultations/: MAS consultation papers (AI risk mgmt CP Nov 2025, closed Jan 31 2026)
- committees.parliament.uk: UK Treasury Committee AI in FS report published Jan 20, 2026
- artificialintelligenceact.eu/implementation-timeline/: EU AI Act milestone tracker (JS-heavy — use WebSearch instead)
- Key finding: HKMA GenAI Sandbox Cohort 2 announced Oct 2025, trials began early 2026; HSBC participating (4 use cases)
- Key finding: HKMA cloud practice guide issued Jan 8, 2026 — 8 domains (expanded from 4), under Fintech 2030
- Key finding: EU Digital Omnibus (proposed Nov 19, 2025) would delay high-risk AI Act obligations by up to 16 months (Aug 2027 / Aug 2028 effective dates)
- Key finding: Commission missed Feb 2, 2026 deadline for Article 6 high-risk classification guidance; expected Mar/Apr 2026

### Professional Certifications (IAPP, GARP, etc.)
- iapp.org/certify/ and store.iapp.org: canonical for AIGP exam details, fees, BOK
- garp.org/rai/fees-payments: canonical for GARP RAI fees and exam dates (WebFetch works)
- privacybootcamp.com: reliable commentary on IAPP cert changes (BOK updates, CPE policy)
- trainingcamp.com/articles/: good practitioner-facing cost/salary synthesis
- mindgard.ai/blog/: reliable cert comparison articles
- LinkedIn pulse articles from actual candidates: best source for real study hours + difficulty
- IAPP does NOT publish pass rates — community consensus is the only source
- GARP RAI exam windows: April and October only (not year-round); AIGP is year-round on-demand via Pearson VUE
- Key finding: AIGP BOK updated to v2.1 effective Feb 2, 2026 — always check for current version

### Group Deliberation / Decision Science
- PubMed/PMC: peer-reviewed, good for meta-analyses
- Wiley Online Library: social psychology journals (EJSP, JASP)
- AoM journals (journals.aom.org): management/OB research
- AIImpacts.org: good synthesis of forecasting/GJP research
- composable-models.github.io: LLM debate original paper (Du et al. 2023)
- arxiv.org: LLM/AI debate preprints (check 2024-2025 vintage)

### Structured Analytic Techniques
- rand.org: authoritative on SATs (RR1408 is key report)
- cia.gov/resources/csi: primary source for Tradecraft Primer
- pherson.org: Heuer & Pherson practitioner materials

## Key Research Findings (Group Deliberation for AI Design)

See: group-deliberation-research.md for full synthesis

### macOS Productivity Software
- rectangleapp.com: official source for Rectangle/Rectangle Pro features & pricing
- github.com/nikitabobko/AeroSpace: canonical source for AeroSpace status
- macworld.com, howtogeek.com: reliable for macOS software comparisons
- icemenubar.app / github.com/jordanbaird/Ice: Ice = menu bar manager, NOT a window manager

### Kaneko Optical (金子眼鏡) HK Research
- kaneko-optical.co.jp/en/brand_kaneko: canonical series overview (KC, KV); WebFetch works
- kaneko-optical.co.jp/en/brand_shokunin: craftsman series (恒眸作 Koh Boh-Saku etc.); WebFetch works
- twenty20vision.shop: Shopify store, WebFetch works — confirmed HKD prices (KC75 = HK$3,280)
- shop.kind.co.jp: second-hand Japanese optical, good for used KV-116 specs
- glasses.beprice.jp: second-hand, has KV-116 spec data; WebFetch works for some pages
- puyi.com/hk_en: 403 on WebFetch; use WebSearch for product names then direct search
- thenewblackoptical.com: JS-heavy product pages, WebFetch returns nav only; use site: search
- thewarehouse.com.hk: JS-heavy homepage, WebFetch returns empty; use WebSearch
- HK stockists confirmed: Kaneko own stores (Pedder Arcade Central + K11 Musea TST), The New Black Optical (multiple locations), Twenty20 (twenty20vision.shop), Puyi Optical, Red Dot Optic (Hysan Place CWB), The Warehouse Optic
- Key finding: Kaneko DOES make browline/sarmount frames — mainly in KV Vintage series and Koh Boh-Saku craftsman line
- KV browline models confirmed: KV-95, KV-116, KV-130, KV-131 (sarmount style with celluoid brow + metal lower)
- KV-116 specs: 49□21-145, browline/sarmount, black or clear/brown colors, ~¥48,400 new
- KV-130: larger sarmount, 54□21-155 (too big at 54mm)
- KV-131: larger sarmount, 54□21-155 (too big)
- Koh Boh-Saku sarmount: celluloid + samplatina, T-254 / T-261 models, ~¥42,000-46,000
- KV series uses adjustable clings (クリングス可動式) nose pads on combination frames — confirmed on KV-18
- Price range in HK: ~HK$3,000-4,500 for standard KC/KV series frames (no lenses); craftsman series higher
- SPA series: NOT found in any source — may not exist or may be misremembered

### EPOMAKER TH40 40% Keyboard — Feb 2026 research
- epomaker.com/products/epomaker-th40: official spec page (WebFetch works; shows 800g which is SHIPPING WEIGHT not keyboard weight)
- xda-developers.com/epomaker-th40-review/: 8.5/10, best balanced English review (WebFetch works)
- notebookcheck.net: two separate TH40 articles — hands-on review AND "fixing the TH40" followup (very useful for issues)
- aphnetworks.com/reviews/epomaker-th40: harshest review (6.0/10); most detailed on VIA issues and usability limits
- moorereppion.com/th40/: good independent owner perspective; confirmed missing Delete key and hyphen issues
- smzdm.com post a8p690wq: Chinese owner review exists but page returns JS-only on WebFetch — skip
- notebookcheck-cn.com: Chinese summary review, fetches cleanly
- Key weight discrepancy: official site shows 800g (shipping weight including packaging). Actual keyboard weight: 440g / 0.44kg per XDA and NotebookCheck reviews. DO NOT quote 800g as keyboard weight.
- VIA setup is NOT plug-and-play: must manually download JSON from epomaker.com/blogs/via-json/, enable V2 definitions in VIA, then import. This is a real friction point confirmed by multiple independent sources.
- Flamingo vs Wisteria distinction matters: Flamingo (linear) = criticised as notchy/cheap by NotebookCheck. Wisteria (linear) = better received. This is a checkout decision that affects experience significantly.
- QK40 does not appear to be a real/widely-known product — searches return nothing. User may have been thinking of a different board.

### Silent/Quiet Mechanical Keyboards for Office — Feb 2026 research
- keeb-finder.com/keyboards/filter/silent-switches: best aggregator for filtering by silent switches, price, layout
- milktooth.com/comparisons/: authoritative switch-vs-switch comparisons with actuation force data (WebFetch works cleanly)
- quietest.org/quietest-keyboard-switches/: dB measurements for switches — has actual numbers (28-30 dB range)
- lumekeebs.com/blogs/blog/: solid switch comparison articles; Shopify-rendered blog posts often return JS-only on WebFetch
- switchandclick.com: good for keyboard recommendations but info can be dated (2022-era Keychron K6 recs)
- clickandthock.com: Wix-built site — WebFetch returns code not article content; use search summaries only
- varmilo.com product pages: JS-heavy, WebFetch returns nothing; use keeb-finder.com or mechkeys.com for specs
- keychron.com product pages: WebFetch works and returns useful pricing/switch data
- wobkey.com/pages/*: WebFetch works for reviews
- Key verified facts (Feb 2026):
  - **Keychron Q2 Pro** (65%, full aluminum, gasket, double-gasket, wireless): $149.99 barebone / $167.99 assembled. Ships with K Pro Red/Brown/Banana — NOT silent. BUT hotswap = swap in any MX silent switch. Known issues: stock is NOT silent (needs mods), keycap quality criticised.
  - **Keychron V2 Max** (65%, plastic top/ABS, gasket, wireless): $94.99–$114.99. Shipped with Gateron Jupiter (not silent). Hotswap. Budget entry to the Keychron ecosystem.
  - **Wobkey Rainy75 Pro** (75% layout, aluminum, FR4 plate, 5-layer foam, wireless): $139. Ships with Kailh Cocoa linear. Well-damped "raindrop" sound — not specifically silent switches, but very well damped acoustics. Issues: linear-only stock, wireless toggle awkward (under Caps Lock), some QC switch doubling reports.
  - **NuPhy Air75 V3** (75% layout, low-profile, wireless, hotswap): $139. Silent Blush switch option available. Knob is wobbly and pops off. Best low-profile silent for office. Not a standard-profile keyboard.
  - **NuPhy Node75** (75% layout, standard-profile, gasket, wireless): $99.95. Blush Max silent switch option available. "Almost silent" with linear switches. Good value. Touch bar is unique feature.
  - **Varmilo Minilo VXT67** (65%, hotswap, wireless tri-mode): ~$94–130 depending on variant. Kailh Prestige Silent switch option available. Silicone pad between plate and PCB. EC switch variant (original Minilo VXB67) is NOT hotswap — avoid for this use case.
- Silent switch rankings (dB, multi-source):
  - ZealPC Zilent V2 67g: 28 dB — quietest but ~$1.20/switch (premium)
  - Cherry MX Silent Red: 29 dB — widely available, pre-lubed, reliable
  - TTC Bluish White V2 Silent: 29 dB tactile, 42g actuation, PC top housing (crisper sound), $5.35/10
  - Gateron Silent Ink Black: 29 dB linear, 70g — heavier feel
  - Gazzew U4: silent tactile, 45–62g, deep/bass-heavy sound, $6.50/10 — best for those who want feedback
  - Kailh BOX Silent Pink: 30 dB linear, 35g — lightest option
  - Keychron Silent K Pro: no dB figure from independent sources; Keychron-branded, factory pre-lubed, MX 3-pin
- Misinformation risk: Many "quiet keyboard" roundups recommend Keychron K6 with Gateron Red — standard Gateron Red is NOT silent (just linear). Always check if silent dampeners are present.
- Methodology: keeb-finder.com filter is best starting point. milktooth.com comparisons for switch data. keychron.com WebFetch for pricing.

### HK Eyewear Chains — Birthday & Corporate Discounts

#### OWNDAYS Birthday Discount
- Official Taiwan announcement (owndays.com/tw/zh_tw/information/332) confirms 8折 (20% off) birthday discount for registered members
- Validity: whole birthday month (整個生日月) — coupon issued at start of birth month
- Eligibility: must be a registered member BEFORE your birthday month; no specific tier requirement mentioned
- Coupon is personal-use only (本人使用限定) — confirmed by Dcard dispute thread
- HK-specific page is JS-rendered; cannot WebFetch. Terms likely mirror TW/SG
- OWNDAYS SG membership page (WebFetch) does NOT mention birthday discount — it's handled via the app/email, not the website
- No published corporate/company discount program. OWNDAYS HK is operated by Bluebell Group JV — no public B2B portal
- Corporate inquiries: hr.hk@owndays.com (found via job listing search, not official promo)

#### JINS HK Birthday/Corporate Discounts
- JINS HK app (App Store listing confirmed) offers member-exclusive coupons — app description mentions coupons but NOT a specific birthday discount
- JINS HK website jinsmember page and memberday page are both JS-heavy — WebFetch returns only tracking code
- No evidence of a birthday-month discount for JINS HK (as of Feb 2026) — contrast with Taiwan JINS which runs birthday promos
- JINS HK has a "App Member Day" (會員感謝日) promotion — separate from birthday; not well-documented publicly
- No corporate discount program found for JINS HK

### HK Eyewear Chains (OWNDAYS / JINS / Zoff)
- Mall tenant pages (cityplaza.com, moko.com.hk, newtownplaza.com.hk, langhamplace.com.hk, leetungavenue.com.hk, uptownplaza.com.hk) return static HTML with shop number + hours — BEST source for individual branch details
- owndays.com/hk store locator is fully JS-rendered — WebFetch returns nothing. Workaround: fetch individual shop pages at owndays.com/hk/zh_hk/shops/50XX
- jins.com.hk/en/findastore/ is also JS-rendered — use mall pages + hongkong-map.com + zaubee.com instead
- wanderlog.com returns Google review aggregates with hours + address — works for OWNDAYS branches
- OWNDAYS HK: ~21 branches (2025), covers all major districts. Official store numbering: 50XX series
- JINS HK: ~9 branches as of Jan 2024 InvestHK report; aiming to double. First store: apm Kwun Tong (Sep 2018)
- AI search result summaries mix up OWNDAYS and JINS branch lists — always cross-verify per-brand from mall pages

### US Estate Tax for Non-Resident Aliens (HK Residents) — Feb 2026

**Key sources:**
- irs.gov/businesses/small-businesses-self-employed/estate-tax-for-nonresidents-not-citizens: IRS canonical page — WebFetch works cleanly
- law.cornell.edu/cfr/text/26/20.2102-1: CFR §20.2102-1, unified credit for NRA estates ($13,000 credit = ~$60,000 exemption)
- irc.bloombergtax.com/public/uscode/doc/irc/section_2105: IRC §2105 full text — lists all property excluded from NRA gross estate
- thetaxadviser.com/issues/2025/apr/estate-tax-considerations-for-non-us-persons: cites key IRC sections (2101, 2103, 2104, 2106)
- buzzacott.hk/insights/key-tax-considerations-for-non-us-persons: HK-specific; cash in broker portfolio IS US situs, cash in US bank is NOT
- hk-lawyer.org/content/often-overlooked-us-tax-and-reporting-issues: HK lawyer publication on estate admin
- mossadams.com/articles/2025/10/us-gift-and-estate-taxes-for-non-us-persons: comprehensive NRA situs analysis
- creativeplanning.com/international/insights/estate-planning/nonresident-alien-us-estate-tax-trap: good NRA trap summary
- nomoneylah.com/2025/07/23/invest-in-sp500-index: IBKR + CSPX/VUAA guide for non-US residents

**Verified facts:**
- NRA exemption: $60,000 (unified credit of $13,000 per §20.2102-1, unchanged since 1976, not inflation-indexed)
- One Big Beautiful Bill (2025) raised US citizen exemption to $15M (2026) — NRA $60K unchanged
- Max rate: 40% on US-situs assets above $60K (same graduated schedule as US citizens via IRC §2101, effectively flat 40% above exemption)
- US-HK estate tax treaty: NONE. HK abolished estate duty in 2006, so it has no estate tax treaties.
- Filing threshold: Form 706-NA required when US-situs assets exceed $60,000 at death. Due 9 months post-death (extendable).
- Enforcement mechanism: US brokers (including Schwab HK, IBKR) will NOT release assets to beneficiaries without IRS Form 5173 (Federal Transfer Certificate). This is the primary enforcement lever — not IRS proactive audit.
- IRS can pursue beneficiaries directly under transferee liability provisions if estate tax unpaid.

**US-situs property (IS subject to estate tax):**
- Stock in any US-incorporated corporation (IRC §2104) — regardless of where certificate held or account located
- US-domiciled ETFs (VTI, VOO, QQQ etc.) — incorporated as US corporations
- Cash held within a US brokerage portfolio/investment account
- US real estate and tangible property in the US
- US LLC interests
- US person debt obligations (with major exception — see below)

**NOT US-situs property (exempt from estate tax):**
- Ireland-domiciled ETFs (VWRA, CSPX, VUAA, IWDA) — foreign corporations, not US-incorporated
- Qualifying portfolio debt (IRC §2105(b)(3)) — registered bonds where interest qualifies for portfolio interest exception under §871(h)(1). Includes most publicly-traded US corporate bonds and Treasuries issued after July 18, 1984.
- Cash deposits at US commercial banks (checking, savings, CDs, time deposits)
- Foreign branch deposits of US banks
- Life insurance proceeds
- Works of art on loan for public exhibition

**Note on broker cash:** Cash within a US brokerage investment account IS US situs. Cash in a US bank account is NOT. This is a critical distinction — money market funds held at a US broker are US-incorporated and count as US situs.

**Ireland ETF workaround — legal basis:**
- An ETF's situs = the country of incorporation/domicile, NOT where underlying stocks are
- Ireland-domiciled ETFs (listed on LSE, Euronext Amsterdam, SIX) are Irish-incorporated → not US situs → immune from US estate tax
- Additional benefit: US-Ireland tax treaty reduces withholding on US dividends within fund from 30% to 15% at fund level (vs 30% for HK residents holding US ETFs directly)
- Ireland levies no withholding tax on distributions to non-Irish residents
- KIDs/PRIIPs restrictions apply only to EU/UK retail clients — HK residents at IBKR are NOT subject to these restrictions and CAN buy LSE-listed UCITS ETFs

**Broker options for HK residents to buy Ireland UCITS ETFs:**
- Interactive Brokers HK (interactivebrokers.com.hk): primary recommendation — access to 150+ markets including LSE; HK residents can open; no PRIIPs restriction
- Saxo Bank HK: CLOSED Sept 30, 2024 — not available. Transferred clients to Singapore entity.
- Charles Schwab International: HK residents can open; designed for US-listed stocks but WARNING — US ETFs = US situs
- Key ETFs: CSPX (iShares S&P 500 UCITS, LSE, 0.07%), VUAA (Vanguard S&P 500 UCITS, LSE, 0.07%), VWRA (Vanguard FTSE All-World UCITS Acc, LSE, 0.22%), IWDA (iShares MSCI World UCITS, LSE, 0.20%)

**Enforcement practical reality:**
- IRS does NOT proactively identify NRA decedents with US brokerage accounts
- Practical enforcement = transfer certificate requirement: US brokers freeze assets until Form 5173 issued by IRS
- If estate tax owed but 706-NA not filed, IRS can pursue beneficiaries directly (transferee liability)
- Ongoing income tax withholding (FDAP at 30%) is enforced at source by brokers — estate tax is not
- Misinformation risk: "no enforcement" is overconfident — the broker freeze mechanism is real and traps heirs

### HK Menswear / Local Retail
- ubeauty.com.hk, popbee.com: good for Korean brand HK store openings with prices in HKD
- harpersbazaar.com.hk, esquirehk.com: HK fashion editorial, often JS-heavy so WebFetch rarely returns body text
- shopsinhk.com: reliable for store locations and opening hours
- salvo-store.com: direct source for Salvo Wan Chai, verified price data in HKD
- d-mop.com: main multi-brand select shop in HK for contemporary/European menswear
- ka-pok.com: kapok select shop, 11 HK locations, stocks Norse Projects, ONS, Common Projects
- cotwohk.com: cotwo at 523 Lockhart Rd, Causeway Bay — Japanese brands (NEIGHBORHOOD, WTAPS, BEAMS, KAPITAL)
- hoods at 10 Ice House St, Central: Japanese streetwear (NEIGHBORHOOD, WTAPS) — confirmed open

### Blink Shell / iOS Terminal
- github.com/blinksh/blink: canonical issues/discussions
- github.com/Alhadis/OSC8-Adoption: authoritative list of OSC 8 support by terminal
- docs.blink.sh/basics/tips-and-tricks: keyboard config examples for Emacs/Meta
- docs.blink.sh/basics/customize: modifier key remapping, custom presses, SmartKeys
- Key finding: Blink's native URL scan DOES NOT work inside tmux. openurl command also breaks in tmux. OSC 8 not confirmed supported in Blink. Best workaround: tmux copy-mode + keyboard binding to pipe URL to `openurl` or OSC 52 clipboard.
- **Alt/Meta key with tmux in Blink (iPad + external keyboard):**
  - **Config > Keyboard > ⌥ Option:** Toggle "Same for both sides" OFF to use left Option as Meta (right as normal Alt). OR set "Press send" = None + "As modifier" = ESC. Both send proper `^[` (ESC) prefix for Meta bindings.
  - **Status:** Issue #262 (Alt combinations not working) was reported in 2018 as unfixed (mapping Alt→Esc worked as workaround; issue remains open as of Feb 2026). Intermittent reports suggest partial support.
  - **Config > Keyboard > Custom Presses:** Add custom bindings to override iPadOS interception (e.g., Ctrl-Space to prevent emoji menu). This pattern can workaround system conflicts.
  - **Backtick (Alt+`):** No specific documented support. Backtick works as tmux prefix key, but Alt+Backtick combos untested. Safe assumption: use simpler modifier combos.
  - **Reliable modifier combos (iPad + external keyboard):** Ctrl+key, Shift+key, Cmd+key all work. Meta+key (Alt as ESC prefix) works via config but is NOT 100% reliable — expect occasional drops.
  - **Known conflict:** Caps Lock remapped to Control has state desync issue when switching apps. Between presses there's a delay; rapid Ctrl sequences may fail. Single-delay workaround: be deliberate about modifier timing.
  - **Hardware keyboard caveat:** Third-party Bluetooth keyboards (GBoard) don't transmit Shift down-events properly. Shift+arrow tmux resizing works on iPad native keyboard + Magic Keyboard. Test with actual hardware before binding critical sequences to Shift+modifier.
  - **iOS keyboard limitation:** Native iPad keyboard in Blink v13.2+ supports Shift+arrow/modifier combos. GBoard/third-party keyboards do NOT.
  - **Practical guidance:** For tmux on iPad via Blink: avoid Alt/Meta heavy bindings; prefer Ctrl+prefix or remap tmux to single-key prefixes (e.g., backtick). Test all custom keybinds on actual target hardware before committing.

### Textual TUI Framework
- textual.textualize.io/widgets/: best entry point for widget docs (API pages at /api/ sometimes 404)
- github.com/Textualize/textual/blob/main/src/textual/widgets/: source of truth when docs are thin
- willmcgugan.github.io: Will McGugan's blog has deep dives on streaming Markdown internals
- textual v4 (Jul 2025) added native streaming Markdown — check version before recommending patterns
- Key finding: Textual API /api/ pages 403/404 frequently — fall back to GitHub source directly

### HK Public Transport APIs
- data.gov.hk dataset pages return clean endpoint tables (WebFetch works well)
- Official spec PDFs (data.etabus.gov.hk, citybus.com.hk) are binary-compressed — WebFetch cannot parse them. Use dataset HTML pages instead.
- Live API endpoints are open/keyless — can WebFetch them directly to verify response structure
- KMB base: https://data.etabus.gov.hk/v1/transport/kmb/
- CTB base: https://rt.data.gov.hk/v2/transport/citybus/
- NWFB merged into CTB as of July 2023 — company_id "NWFB" removed
- No documented rate limits on either API (data.gov.hk T&Cs are silent on this)
- **HK Tramways ETA API (unofficial, no auth required):**
  - ETA endpoint: `http://www.hktramways.com/nextTram/geteat.php?stop_code={STOP_CODE}`
  - Returns XML; fields include `eat` (ETA), `is_arrived` (bool), `is_last_tram` (bool), `tram_id`, `dest_stop_code`
  - Stop list: `http://hktramways.com/js/googleMap.js` — parse stopsArrayEB / stopsArrayWB for [code, nameEN, nameTC, nameZH, lat, lng]
  - Emergency messages: `http://www.hktramways.com/nextTram/getmessage.php?stop_code={STOP_CODE}`
  - NOT on data.gov.hk — no official open-data registration; unofficially public since ~2014
  - WebFetch cannot parse ETA response (XML causes sizeCalculation error) — must use raw HTTP client
  - Eastbound codes use pattern: SKT, 101E, 99E, 97E, ... (odd decreasing) then named codes near terminus
  - Westbound codes use pattern: SKT, 02W, 04W, 06W, ... (even increasing)
  - Kornhill area stop codes (WB): 08W=Holy Cross Path, 10W=Tai Hong Street, 12W=Tai Koo Shing Road, 14W=Kornhill

### iOS Safari PWA (as of 2025)
- firt.dev/notes/pwa-ios/: best maintained compatibility table, updated regularly
- webkit.org/blog/14403/updates-to-storage-policy/: authoritative on storage quotas (Safari 17+)
- bugs.webkit.org: canonical for confirmed bug status (e.g., bug 211018 service worker freeze — fixed in iOS 14)
- magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide: good practical summary
- Key findings:
  - `standalone` is the ONLY supported display mode on iOS (no `minimal-ui`, `fullscreen`)
  - No `beforeinstallprompt` event — users must manually use Share > Add to Home Screen
  - Storage quota: NOT a fixed 50MB cap — Safari 17+ grants same quota as browser (up to 60% disk); 50MB figure is outdated
  - 7-day eviction: applies when PWA is not accessed — least-recently-used policy, not a hard timer
  - Storage is ISOLATED between Safari browser and home screen PWA (different origins/contexts)
  - Background: app is suspended immediately when backgrounded; setInterval/setTimeout stop; no Background Sync
  - Workaround for background: use `visibilitychange` event to trigger fetch when app becomes visible again
  - EU incident (Feb 2024): Apple briefly removed PWA standalone in EU, reversed within 2 weeks (iOS 17.4 shipped with full PWA support)
  - `apple-mobile-web-app-capable` meta tag: deprecated but still works; web app manifest is preferred
  - `apple-touch-startup-image` still required for splash screens (manifest `background_color` not used)
  - `viewport-fit=cover` + `env(safe-area-inset-*)` CSS required for notch/Dynamic Island handling
  - Manifest fields NOT supported: `orientation`, `dir`, `lang`, `related_applications`, `shortcuts`, `display_override`, `share_target`
  - Service worker cache update: call `reg.update()` on load; add `self.skipWaiting()` in SW; provide manual refresh button

### Vercel Serverless Functions
- vercel.com/docs/functions: canonical — use WebFetch directly, returns clean markdown
- vercel.com/docs/functions/limitations: definitive limits table (memory, duration, invocations)
- vercel.com/docs/limits: general platform limits including invocation quotas
- vercel.com/docs/regions: region codes — hkg1 = Hong Kong, hnd1 = Tokyo
- vercel.com/kb/guide/how-to-enable-cors: CORS pattern with modern Web API
- Key finding: The old `export default function handler(req, res)` Node.js pattern still works but is deprecated. Current pattern is Web API `fetch(request: Request): Response`. Vercel docs show both.
- Key finding: Edge Runtime is being de-emphasized — Vercel docs now warn "We recommend migrating FROM edge to Node.js for improved performance and reliability" (as of 2025).
- Key finding: Fluid Compute enabled by default for new projects as of April 23, 2025. Reduces cold starts significantly.
- Hobby free tier: 1M invocations/month, 4 CPU-hrs active compute, 360 GB-hrs provisioned memory, 100 GB bandwidth.
- HK region: hkg1 (ap-east-1) exists. Hobby plan can select any single region in vercel.json.

### Analog Clock / Watchface UI Design
- marco.org: exceptional first-principles critique of Apple Watch Infograph legibility (2018 but timeless)
- community.facer.io: practitioner forum — good for realistic hand-ratio discussions
- docs.zepp.com/docs/watchface/specification/: Zepp OS spec — most concrete numerical values for watchface design
- clockoclock.app: good dark mode clock design guide with specific hex values
- shannonethomas.com/2016/10/03/watchos-redesign.html: watchOS grid-based redesign proposal, useful hierarchy critique
- developer.apple.com/design/human-interface-guidelines/complications: JS-heavy, WebFetch fails — use WebSearch to extract what's reported from it
- Key findings: see analog-clock-design.md

### iOS App Icon Visual Treatment / Pillow Generation
- developer.apple.com/videos/play/wwdc2025/220/: WWDC25 canonical source on iOS 26 Liquid Glass icon design
- praeclarum.org/2025/09/12/app-icons.html: developer's practical notes on iOS 26 layered icon format
- mjtsai.com/blog/2025/06/23/icon-composer-notes/: best practitioner gotchas on Icon Composer backward compat issues
- www.graphic.com/tutorials/create-a-clock-app-icon: only source with CONCRETE numeric values (inner glow 50% Overlay, highlight 80%/25pt blur, drop shadows 2-15%)
- applypixels.com/blog/the-hunt-for-the-squircle: confirms Apple squircle math was never publicly released
- Key findings:
  - Pre-iOS 7 gloss = 3 layers: gradient overlay (light top) + white ellipse top-40-45% (semi-transparent) + squircle mask. Exact alphas never disclosed.
  - iOS 7–17: completely flat, no system overlay. Submit flat square, OS rounds corners only.
  - iOS 18: flat + dark/tinted variants required. Dark mode icons use subtle top-to-bottom gradient on glyphs.
  - iOS 26: Liquid Glass — GPU-rendered dynamically, NOT bakeable in Pillow. System auto-applies to flat PNGs but result is "mediocre". Proper approach: Icon Composer + layered .icon format.
  - Liquid Glass backward compat BROKEN: Icon Composer outputs look bad on iOS 18. Two separate icon sets or flat PNG compromise.
  - Apple squircle corner radius ≈ 22% of icon width (224px on 1024px). Not a true superellipse — continuous bezier curve never released.
  - Clock app icon is ANIMATED (live time since iOS 7) — cannot replicate the "polish" statically.
  - Pillow best practice: squircle mask via rounded_rectangle(radius=224 on 1024) + radial vignette layer + soft specular ellipse (top, 10-15% opacity, heavy blur) + inner glow (50% Overlay) + stacked drop shadows (2-15% each)
  - developer.apple.com/design/human-interface-guidelines/app-icons: JS-heavy, WebFetch returns noscript fallback only

### Claude Code Skills / Extensions Ecosystem
- hesreallyhim/awesome-claude-code: canonical curated list (main hub, most comprehensive)
- travisvn/awesome-claude-skills + ComposioHQ/awesome-claude-skills: secondary awesome lists
- awesomeclaude.ai: visual directory aggregator
- claudecodeplugins.io: marketplace (jeremylongshore ecosystem, CCPI package manager)
- github.com/topics/claude-code-plugin + github.com/topics/awesome-claude-code: GitHub topic pages
- Key finding: "skills" (`.claude/skills/`) and "commands" (`.claude/commands/`) are converging — skills are now the preferred format; commands still work but skills support more features (subagent invocation, supporting files).
- Star count anomaly: search results returned inflated/synthetic star counts (e.g., "55k stars for Claude Code", "53.9k for obra/superpowers") — verify on actual GitHub pages before quoting.

### Claude Code Skills/Hooks — Novel Patterns from GitHub (Feb 2026)

**From obra/superpowers (v4.1.1, Jan 23 2026):**
- **Composable Skills Framework**: discrete, triggerable skills activate based on context. Not suggestions — mandatory workflows enforced at invocation.
- **Subagent Delegation Pattern**: "fresh subagent per task with two-stage review" (spec compliance, then code quality). Quality gates embedded in skill invocation.
- **Specification-First Design**: brainstorming skill requires "design in sections for validation" before code generation. Evidence-driven over ad-hoc.

**From disler/claude-code-hooks-mastery (10 commits, Jul 2025):**
- **Intelligent Fallback Chaining**: multi-provider TTS (ElevenLabs > OpenAI > pyttsx3) with explicit routing order. Applies to any multi-backend scenario.
- **Tool-Level Access Control via Hooks**: separate Builder (all tools) from Validator (read-only). Roles enforced through hook-gate tool access, not just permissions.
- **Context Injection via UserPromptSubmit**: dynamically inject git status, recent issues, project metadata BEFORE Claude processes prompt. Better than static system prompts.
- **PostToolUse Transcript Transformation**: JSONL → readable JSON via hooks. Enables downstream analytics/audit compliance.

**From trailofbits/skills (82 commits, last update timing unclear):**
- **Security-Domain Modular Architecture**: skills organized by practice area (smart contracts, code auditing, malware, reverse engineering). Practitioner can install only relevant tooling.
- **Skill-as-Adapter Pattern**: wrap established tools (CodeQL, Semgrep, YARA, Burp) rather than reimplementing. Lower barrier to adoption.
- **Meta-Skill Pattern**: "semgrep-rule-variant-creator" auto-generates rule variants across languages with test-driven validation. Generalizes beyond security.

**From OthmanAdi/planning-with-files (v2.15.1, session catchup fix):**
- **Three-File Planning System**: task_plan.md (phases + checkboxes) + findings.md (research) + progress.md (session logs). Filesystem-as-extended-memory principle.
- **Attention Manipulation via Hooks**: re-read plans before major decisions. Prevents goal drift + hidden errors. Works because hook runs before Claude decision point.
- **Error Persistence**: failures logged in plan files prevent repetition. Session history in filesystem survives context window resets.

**From parcadei/Continuous-Claude-v3 (117 commits, created Dec 23 2025, 3.5k stars):**
- **Handoff Over Compaction**: YAML-formatted state transfers preserve nuanced decisions better than raw conversation replay. Reduces token loss during handoffs.
- **Multi-Layer Code Abstraction (TLDR)**: 95% token reduction via semantic indexing — AST → call graphs → control flow → data flow → PDGs. Claude understands structure without reading full files.
- **Continuity Ledgers**: persistent ledgers track decisions, file claims (prevent simultaneous edits), session state across restarts. Prevents lost context + edit conflicts.
- **Isolated Agent Contexts**: specialized sub-agents (scout, oracle, kraken) operate in bounded windows — prevents context pollution from parallel work.
- **Philosophy: Compound, Don't Compact**: extract learnings when sessions end → begin fresh with full clarity, not degraded history.

**Summary of Cherry-Pick Patterns:**
1. **Composability > Monoliths**: skills should be discrete, invoked conditionally, with validation gates (obra, trailofbits).
2. **Hooks for System Design**: UserPromptSubmit for context, PostToolUse for output shape, PreToolUse for gates. Not just logging — enforcement points.
3. **Filesystem as Extended Memory**: never rely on context window alone; task_plan.md + findings.md as persistent state that survives reset (planning-with-files).
4. **Semantic Compression > Raw Replay**: TLDR/PDG abstraction reduces tokens; handoffs preserve nuance better than compaction (Continuous-Claude-v3).
5. **Role-Based Tool Gating**: separate roles (Builder vs Validator) via hook-level access control, not just permissions (disler).

### Specialty Coffee Equipment (OREA, April, and landscape)
- beanbelthk.com: best HK retailer for OREA + NextLevel Pulsar + specialty kit — HKD prices, WebFetch works
- orea.uk: official site, good for specs; shop.orea.uk is JS-heavy (Shopify) — use WebSearch for prices
- usa-shop.orea.uk: USD prices; 404s on some product URLs — use search results instead
- aprilcoffeeroasters.com: official April brewer source, WebFetch works for price/specs
- thebasicbarista.com: reviews — JS-heavy, WebFetch returns nav only; use WebSearch excerpts
- vvcafe.com: Taiwan retailer, ships to HK, prices in TWD (~1680 TWD for V4)
- home-barista.com: community forum — 403 on WebFetch; use WebSearch for excerpt content
- coffeeadastra.com (Jonathan Gagne): deep technical brewer analysis — WebFetch works, very high quality
- dailycoffeenews.com: good launch/product news; WebFetch works well
- coffeegeek.com: 2024 best manual brewer awards — WebFetch returns mostly markup, use WebSearch excerpts
- nextlevelbrewer.com: official Pulsar site; beanbelthk.com stocks Pulsar at HK$560
- weberworkshops.com: Weber Bird brewer, $360 USD, premium/niche
- Key product facts (verified HKD prices at Bean Belt HK, Feb 2026):
  - OREA V4: HK$535 | OREA Z1: HK$535 (Z1-only) or HK$655 (+50 filters) | NextLevel Pulsar: HK$560
  - Weber Bird: ~$360 USD (no HK retailer confirmed) | Timemore B75: ~$50-60 USD widely available
  - Cafec Deep 27: widely available, ~$30-40 USD
- OREA Z1 is OREA's new (2025) zero-bypass brewer, NOT modular like V4. Uses Sibarist FAST filters (proprietary, required). For 1 cup only. Fast: avg 2:41.
- NextLevel Pulsar: CoffeeGeek Best Manual Brewer 2024. Designed by astrophysicist Jonathan Gagne. $65 USD. Valve-controlled no-bypass + dispersion cap. No gooseneck required. Endorsed by Scott Rao. Cleanup is the main complaint.
- Weber Bird: $360 USD, reverse-direction vacuum brewer, French press form factor, borosilicate/brass. Sold out in 10 min at launch. Premium niche — not a beginner buy.
- Sibarist: Spanish filter paper brand (not a brewer). FAST filters = 27-40% faster than V60. Used by 2024 World Brewers Cup champion Martin Wolfl with OREA. Also makes Dual Chamber and B3 variants.
- Melodrip: a pour dispersal tool (not a brewer itself). Makes any pour gentler/less agitation. Also makes COLUM mini dripper (zero-bypass cone, stainless + glass, Indiegogo origin, niche).
- Cafec Deep 27: very narrow cone (27° angle), Japan. Proprietary Abaca paper only. Fast flow, small footprint, good sweetness — less forgiving than flat bed.
- Origami: beautiful Japanese cone dripper (Mino porcelain), accepts V60 and Kalita filters. Not technically innovative but visually stunning. New: AIR model (lighter AS resin) and ReWork (recycled porcelain).
- Community consensus 2025: OREA V4 is the highest performer per dollar. Pulsar is the best dedicated no-bypass brewer for those who want maximum extraction control. V60 remains the community bracket winner for overall versatility.

### Taobao Specialty Coffee (China to HK)
- Douban 咖啡组 and V2EX threads are the richest community sources for roaster recs
- qianjiecoffee.com has SSL issues — WebFetch fails; use WebSearch with site-specific queries instead
- Zhihu threads 403 on WebFetch; rely on WebSearch AI summaries from zhihu results
- Taobao direct-to-HK shipping: SF Express option removed Sep 2024. Current: Cainiao 直運標準 or 集運標準, ~3-10 working days, ¥99 minimum for free shipping (as of late 2024)
- Key community-consensus roasters: M2M, Fisher (啡舍), 前街, BOB, 乔治队长, Outman, 炬点
- Prices for specialty pour-over beans: roughly ¥50-100 per 200g for mid-tier; ¥80-200+ per 200g for high-end single origins
- Most mainland roasters do NOT list HK shipping explicitly — buyer uses Taobao's Cainiao consolidation

### Claude Model Specs & Comparisons (as of Feb 2026)
- anthropic.com/news/claude-sonnet-4-6 and anthropic.com/news/claude-opus-4-6: canonical announcement pages (WebFetch works for Sonnet page; Opus page may 429)
- platform.claude.com/docs/en/about-claude/pricing: canonical pricing (WebFetch 403 — use search results instead)
- platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6: model IDs and release notes (WebFetch 403)
- vellum.ai/blog/: reliable benchmark comparisons, WebFetch works well
- digitalapplied.com/blog/: clean benchmark summaries, WebFetch works
- latent.space/p/ainews-*: best practitioner-focused caveats (token usage anomalies, regressions); WebFetch works
- thezvi.substack.com: good for behavioral observations and safety flags; WebFetch works
- venturebeat.com/technology/: 429 errors on repeated fetches; use search excerpts instead

**Key verified facts (Feb 2026):**
- Sonnet 4.6 released Feb 17, 2026; Opus 4.6 released Feb 5, 2026
- Sonnet 4.6 pricing: $3/$15 per million input/output tokens (standard ≤200K)
- Opus 4.6 pricing: $5/$25 per million input/output tokens (standard ≤200K)
- Long context (>200K, either model): 2x input / 1.5x output premium — Sonnet $6/$22.50, Opus $10/$37.50 per million
- 1M context window: beta, tier-4 API orgs only; applies to both Sonnet 4.6 and Opus 4.6
- Sonnet 4.6 benchmarks: SWE-bench 79.6%, OSWorld 72.5%, ARC-AGI-2 58.3%, GDPval-AA 1633 Elo, GPQA Diamond 74.1%
- Opus 4.6 benchmarks: SWE-bench 80.8%, OSWorld 72.7%, ARC-AGI-2 68.8%, GDPval-AA 1606 Elo, GPQA Diamond 91.3%, Terminal-Bench 2.0 65.4%
- Opus 4.6 MRCR v2 (long context recall): 93% at 256K, 76% at 1M tokens; Sonnet 4.5 scored only 18.5% at 1M (Sonnet 4.6 score not yet published)
- CRITICAL TOKEN CAVEAT: Sonnet 4.6 used 4.8x more tokens than Sonnet 4.5 on GDPval-AA (280M vs 58M). Despite same listed price, actual cost-per-task can exceed Opus in agentic workflows.
- Opus 4.6 unique feature: "Agent Teams" — parallel sub-agent coordination in Claude Code
- Context compaction (auto-summarize): available on both models; enables effectively unlimited conversation length even within standard window

### Canadian Express Entry CRS (Feb 2026 research)
- canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/check-score/crs-criteria.html: official full scoring table (WebFetch works cleanly)
- canadavisa.com/express-entry-invitations-to-apply-issued.html: comprehensive draw history (WebFetch works)
- immigration.ca/express-entry-draws-2025/: 2025 draws (WebFetch works)
- cicnews.com/2026/01/2025-express-entry-year-in-review: CRS policy changes summary
- ielts.ca/take-ielts/ielts-for-canadian-immigration/ielts-to-clb/: official IELTS→CLB table (WebFetch works cleanly)
- sepimmigration.ca/post/permanent-residence-canada-hongkong/: HK Stream A/B summary
- Key verified facts (Feb 2026):
  - NOC 21211 (Data Scientist) REMOVED from STEM category Feb 2025. Also removed: 21231, 21232, 21233, 21230, 21211, 21223. No STEM draws occurred in all of 2025.
  - Job offer points (50/200 CRS) eliminated as of March 25, 2025.
  - No general all-program draws since April 2024. CEC draws running at 508-547 cutoff (Q4 2025 – Q1 2026).
  - CEC draws: 508-547 CRS. French category: 379-481. Healthcare category: 462-510.
  - IELTS 6.0 all skills = CLB 7 (16/17 CRS pts per ability). IELTS 6.5 all = CLB 8 (22/23). IELTS 7.0 reading/writing/speaking + 8.0 listening = CLB 9 (29/31).
  - HK Stream B: 12 months Canadian work experience, no education requirement, in Canada when applying, deadline Aug 31 2026.
  - HK PR applicant open work permit: valid 3 years, must have held work/study permit in prior 3 years, deadline May 2029.
  - WES ECA fee: ~CAD $256 base + HST + delivery. Processing ~35 working days. Valid 5 years.
  - 5 designated ECA bodies: WES, CES-UofT, ICAS, IQAS, ICES-BCIT. WES is most used.
- Misinformation risk: Several sites still list job offer CRS points as active — they were removed March 25, 2025.
- Misinformation risk: Some sites claim STEM draws ongoing or expected — there were ZERO STEM draws in all of 2025, and 2026 STEM draw prospects are dim (not a priority per IRCC levels plan).

### AI News Date Verification (January 2026 events)
- Verified reliable sources for Jan 2026 AI events: cnbc.com/2026/, techcrunch.com/2026/, blogs.nvidia.com, x.ai/news, newsroom.accenture.com, mas.gov.sg, whitehouse.gov/presidential-actions/
- Key date-verification finding: "anniversary coverage" contamination is real — always check URL year (2026/ vs 2025/) not just article title
- Boston Dynamics Atlas at Hyundai Savannah: public DEMONSTRATION was Jan 5, 2026 (60 Minutes). Active field testing articles appear Jan 16-21. Claim of "Jan 4" is WRONG.
- Arcee Trinity Large: Arcee blog post Jan 27, TechCrunch coverage Jan 28, HuggingFace/formal launch Jan 29. Claim of "Jan 28" is defensible as media date.
- Trump AI EO: signed Dec 11, 2025. NOT January 2026. AI Litigation Task Force became operative Jan 10, 2026. Characterizing it as "operative January 2026" is misleading — the EO itself is a December 2025 event.
- Baseten $300M Series E: BusinessWire press release dated Jan 23, 2026; Bloomberg reported Jan 20. Claim of "Jan 23" confirmed.
- MAS AI Risk Guidelines: consultation OPENED Nov 13, 2025; CLOSED Jan 31, 2026. Claim of "closing Jan 31" is correct.

### AI Banking Regulation (2025 Calendar Year — Global Timeline)
- EU AI Act: Feb 2 2025 = prohibited practices ban; Aug 2 2025 = GPAI obligations + penalty regime live; Aug 2 2026 = high-risk (credit scoring) compliance deadline
- EBA factsheet on AI Act banking implications: published Nov 21, 2025. Credit scoring = high-risk. No new EBA guidelines needed immediately.
- EC must issue high-risk classification guidelines by Feb 2 2026
- HKMA GenAI Sandbox Cohort 1: announced Dec 2024, trials ran Jan–mid 2025, 15 use cases from 10 banks
- HKMA AI/ML AML circular: banks submitted feasibility studies by end-Mar 2025; 48 AIs responded
- HKMA GenAI Sandbox Cohort 2: launched Apr 28, 2025 (FiNETech5), 27 use cases from 20 banks
- HKMA GenAI Symposium / Cohort 1 results report: Oct 31, 2025. Key findings: 30-80% reduction in STR prep time, doc processing from 1 day to ~5 mins
- HKMA GenAI Sandbox Cohort 2 selection announced: Oct 15, 2025
- HKMA AML AI dedicated team circular: Nov 19, 2025 (supporting AI in AML/CFT monitoring)
- HKMA Fintech 2030 launched: Nov 3, 2025 (HK FinTech Week). DART pillars. AI2 strategy. Responsible AI Toolkit (no specific launch date given). GenAI Sandbox++ announced for 2026.
- Project Noor (HKMA + BISIH + FCA): XAI tool for financial supervisors, announced Oct 2025, ongoing
- MAS AI Risk Management Guidelines: consultation paper issued Nov 13 2025, closed Jan 31 2026, not yet finalized. 12-month transition period after finalization.
- Trump Jan 20 2025: revoked Biden AI EO (EO 14110). Jan 23 2025: new EO "Removing Barriers to American Leadership in AI"
- Trump Dec 11 2025: new EO "Ensuring a National Policy Framework for AI" — preempt state AI laws
- US: No new banking-specific AI regulation from OCC/Fed/FDIC in 2025. GAO report on AI oversight in financial services: May 2025. SR 11-7 not updated.
- Colorado AI Act (SB 24-205): enacted Jun 22 2025, effective Jun 30 2026 (delayed from Jan 1 2026)
- UK FCA: Principles-based approach, no AI-specific regulation. Sep 9 2025: launched "AI and the FCA: our approach" webpage + FS25/5 feedback statement on AI Live Testing. Dec 3 2025: AI Live Testing formally launched (first cohort: NatWest, Monzo, Santander, Lloyds/Scottish Widows, etc.)
- IOSCO AI Consultation Report on AI in capital markets: published Mar 2025, consultation closed Apr 11 2025
- FSB AI monitoring report: Oct 10, 2025. Third-party concentration risk identified as top vulnerability.
- BIS/Basel: Jun 2025 publication on AI supply chain (BIS Papers no. 154); Basel Committee 2025-26 work programme includes "digitalisation of finance" as priority
- Reliable sources for EU AI Act: artificialintelligenceact.eu, eba.europa.eu, trilateralresearch.com, dlapiper.com AI Outlook, hdsr.mitpress.mit.edu (academic)

### AI in Banking — 2025 Production Deployments (Key Verified Facts)
- JPMorgan LLM Suite: launched summer 2024, hit 200K users in 8 months (verified: JPMorgan official site, CNBC Sep 2025, Tearsheet Sep 2025). Named American Banker 2025 Innovation of Year. $2B AI value projection from COO late 2025 (raised from $1.5B May 2025). 450+ use cases in production.
- Goldman Sachs: GS AI Assistant firmwide mid-2025 after 10K pilot. GitHub Copilot on 12,000 developer desktops. Devin AI coding agents: announced July 11, 2025 (CNBC). Hundreds of Devin instances live, scaling to thousands. Projected 3-4x productivity vs prior tools.
- Morgan Stanley: AI@ MS Debrief (meeting notes, Zoom integration) in production. AskResearchGPT launched Oct 2024, expanded 2025. 98%+ advisor team adoption. Advisors respond 10x faster to client inquiries with AskResearchGPT. ~40K of 80K employees using OpenAI tools.
- BNY Mellon: Eliza platform — 117 AI solutions in production by Q3 2025 (75% jump in that quarter). 96% employee adoption in H1 2025. Contract Review Agent: 75% reduction in review time (4 hrs → 1 hr). Jan 2026: 20K "Empowered Builders", 130+ Digital Employees.
- Lloyds: £50M AI value in 2025 (announced Jan 29, 2026 PR). Athena (20K users, 66% search time cut). GitHub Copilot (5K engineers, 50% legacy code conversion improvement). AI HR Assistant (90% first-contact resolution). 50+ GenAI solutions deployed.
- Barclays: BarxBot in production (FX quotes 75% faster). Microsoft Copilot rollout: 50K by end-2025, targeting 100K by early 2026. GenAI call assistant live in Barclays UK. £700M cost efficiency in 2025 (beat £500M goal). £2B cumulative target by 2026.
- Citi: Citi Squad automated 220K code reviews in Q1 2025 (from Q1 earnings). Citi Assist + Stylus deployed to ~150K employees. Stylus Workspaces upgraded to agentic AI Sep 22, 2025 (pilot 5K users). 182K employees have access. Uses Google Gemini + Anthropic Claude.
- HSBC: 600+ AI use cases. 20K+ developers using coding assistant (15% efficiency gain). Fraud/AML: 2-4x more detection, 60% fewer false positives. Mistral AI multi-year partnership announced Dec 1, 2025. Harvey AI legal deal Jan 20, 2026.
- DBS: SGD 750M AI economic value in 2024 (verified in 2024 Annual Report, double 2023). 1,500+ models, 370+ use cases. Targeting >SGD 1B in 2025. Named Global Finance World's Best AI Bank 2025. iCoach, hyper-personalized nudges (45M/month to 5M customers) in production.
- Standard Chartered: SC GPT launched across 41 markets Mar 27, 2025. 70,000+ employees. 200K prompts in first weeks. Use cases: credit ops, financial crime, ops efficiency, front-office insights. Won Dataiku AI safety award 2025.
- OCBC: 300+ AI use cases, 30+ GenAI. HOLMES AI for relationship managers. AI surveillance flagged 30% more suspicious transactions vs 2023. Named Best AI for Customer Personalisation (Asian Banker 2025).
- Agentic shift timing: MIT/Insights 2025 survey — 16% already deployed agentic AI, 52% in pilots as of 2025. BNY Mellon was earliest to use "agentic" language (Eliza 2024). Citi agentic Stylus Sep 2025. JPMorgan announced agentic phase at Sep 2025 CNBC profile.
- Citi 6.5M prompts figure is UNVERIFIED — not traceable to earnings or press releases. Do not use. Verified is 220K code reviews (Q1 earnings).
- bankautomationnews.com: reliable for Citi quarterly AI metrics from earnings calls

### Speech-to-Text / Transcription APIs (Feb 2026)
- deepgram.com/learn/: Deepgram's own benchmarks — useful but self-serving; cross-reference with artificialanalysis.ai
- deepgram.com/pricing: canonical Deepgram pricing (WebFetch via search results works; direct WebFetch to pricing page may redirect)
- groq.com/pricing: canonical Groq STT pricing — WebFetch works cleanly
- costgoat.com/pricing/openai-transcription: reliable aggregated OpenAI transcription pricing table (Feb 2026 verified)
- brasstranscripts.com/blog/: independent pricing/comparison blog — reliable for assembled pricing tables, not marketing
- assemblyai.com/pricing: WebFetch works but returns JS-heavy content; direct fetch gave clean pricing data Feb 2026
- platform.openai.com/docs/pricing: 403 on WebFetch — use costgoat.com aggregator instead
- gladia.io/pricing: WebFetch works cleanly — confirmed $0.61/hr async self-serve, 10 free hrs/month
- rev.ai/pricing: WebFetch works — Reverb $0.20/hr, Reverb Turbo $0.10/hr, Whisper Fusion $0.30/hr
- speechmatics.com/pricing: WebFetch works — $0.24/hr Pro tier, 480 min free/month
- Key verified pricing (all per-minute, batch, Feb 2026):
  - Groq Whisper-large-v3-turbo: $0.000667/min ($0.04/hr) — cheapest managed option
  - Groq Whisper-large-v3: $0.00185/min ($0.111/hr)
  - Whisper self-hosted (SaladCloud RTX 3060): ~$0.000083/min ($0.005/hr) — ~200 hrs audio/$ for long files
  - Rev.ai Reverb Turbo: $0.00167/min ($0.10/hr)
  - Rev.ai Reverb: $0.00333/min ($0.20/hr)
  - AssemblyAI Universal-2: $0.0025/min ($0.15/hr)
  - AssemblyAI Universal-3 Pro: $0.0035/min ($0.21/hr) — adds keyterms for +$0.00083/min ($0.05/hr)
  - OpenAI gpt-4o-mini-transcribe: $0.003/min ($0.18/hr)
  - Deepgram Nova-3 (batch): $0.0043/min ($0.258/hr) + $0.0013/min keyterm add-on → $0.0056/min all-in
  - OpenAI whisper-1 / gpt-4o-transcribe: $0.006/min ($0.36/hr)
  - Azure Speech (standard batch): $0.006/min ($0.36/hr)
  - Speechmatics Pro: $0.004/min ($0.24/hr) — custom dict included, 480 min free/month
  - Gladia async self-serve: $0.0102/min ($0.612/hr) — 10 hrs free/month; revamped custom vocab (unlimited words, intensity 0-1, pronunciation)
  - Google Cloud STT v2 standard: $0.024/min; Enhanced: $0.036/min
  - AWS Transcribe: $0.024/min (custom vocab included, no extra cost)
- Key accuracy (WER, lower is better, real-world data):
  - Deepgram Nova-3: 5.26% WER batch, 6.84% WER streaming (April 2025)
  - AssemblyAI Universal-2: ~14.5% streaming WER; Universal-3 Pro significantly better
  - OpenAI gpt-4o-transcribe: ~8.9% WER (Deepgram self-reported benchmark — treat as approximate)
  - Whisper large-v3: ~10-12% WER on real-world data; WORSE on real-world noisy audio than clean benchmarks
- CRITICAL: Whisper-large-v3 hallucination problem confirmed. WER 53.4 on noisy real-world data in one study (vs 12.7 for v2). Hallucinates 4x more than v2. Proper nouns 11% relative error increase.
- Groq Whisper: same model weights as OpenAI Whisper (whisper-large-v3), just faster inference. Same accuracy + hallucination issues.
- Custom vocabulary feature comparison (critical for Sanskrit/Buddhist terms):
  - Speechmatics: 1000 words/job, sounds_like phonetics, batch supported — included in base price
  - AssemblyAI: Universal up to 200 keyterms; Slam-1 up to 1000 keyterms; +$0.05/hr add-on
  - Deepgram Nova-3: up to 100 terms (500 token limit); +$0.0013/min; 625% uplift case study
  - Rev.ai: up to 6000 phrases/job for English; included in base price
  - Gladia: unlimited words (revamped Feb 2026); intensity control (0-1); pronunciation; included in base price
  - Google STT v2: phrase boost (0-20 boost value) + custom classes; available for batch; pricey base
  - AWS Transcribe: custom vocabulary (word lists); included; batch supported
  - Azure Speech: custom lexicon (PLS format, phoneme-level); batch supported; +$0.0075/min for custom batch
  - OpenAI Whisper/gpt-4o-transcribe: NO vocabulary injection feature at all
  - Groq Whisper: NO vocabulary injection feature
- Batch recommendation for meditation/dharma content (10-60 min, Sanskrit/Pali vocabulary):
  - Best value overall: Speechmatics ($0.004/min, 1000-word dict with sounds_like, 480 min free)
  - Best accuracy + vocabulary control: Deepgram Nova-3 ($0.0056/min all-in, 625% uplift on keyterms)
  - Best budget if spending time on phonetics: self-hosted Whisper + custom dict on top (WhisperX)
  - Avoid: Gladia (expensive), Google/AWS (expensive), OpenAI/Groq Whisper (no vocab injection + hallucinations)

### Speechmatics Batch API — Advanced Features (Feb 2026)
- Word-level timestamps: INCLUDED BY DEFAULT in JSON output — no special config needed
- Confidence scores: INCLUDED BY DEFAULT in alternatives[].confidence (0.0-1.0)
- Speaker diarization: set diarization="speaker" in transcription_config; adds "speaker" field (S1, S2...) to every word
- operating_point: "enhanced" uses larger model, ~20-40% slower but more accurate; default is "standard"
- Custom vocab sounds_like: accepts multiple phonetic English spellings per entry; max 1000 words/job; entries >6 words silently dropped
- Webhook (notification_config): up to 3 URLs, contents can be "transcript"/"data"/"jobinfo", method POST or PUT; much preferred over polling for production
- Rate limits: 10 new jobs/sec (POST), 50 polls/sec (GET), max 20K concurrent jobs
- Data retention: 7 days only — download transcripts promptly
- Polling alternative: asyncio + httpx with asyncio.Semaphore(10) respects 10/sec submit limit; poll interval 5s safe for N<250 files
- Format 2.9 is current JSON schema (as of Jun 2025)
- docs.speechmatics.com/speech-to-text/batch/limits: definitive rate limit source (WebFetch works)
- docs.speechmatics.com/features/custom-dictionary: custom vocab docs (WebFetch works, returns clean content)
- docs.speechmatics.com/speech-to-text/batch/notifications: webhook/notification_config docs (WebFetch works)

### Audio Preprocessing for STT (Feb 2026)
- ffmpeg chain for quiet/ambient recordings: `highpass=f=80,afftdn=nf=-25,loudnorm,volume=1.5`
  - highpass=f=80: removes sub-80Hz rumble (HVAC, room) — always safe
  - afftdn=nf=-25: FFT adaptive denoising, no external model needed
  - loudnorm: EBU R128 normalisation — most reliable single improvement for quiet/variable-volume speech
  - volume=1.5: restores energy lost during denoising
- Silence trimming: ffmpeg silenceremove filter or pydub; -50dB threshold, 0.5s start silence
- Always downsample to 16kHz mono before submission (`-ar 16000 -ac 1`) — reduces file size and matches STT native format
- Demucs (htdemucs model): best for heavy background noise/music; extracts vocals stem; slower (10x real-time CPU), occasional quality loss on quiet/breathy speech — A/B test first
- Traditional spectral subtraction denoisers (noisereduce library) can HURT accuracy — distorts frequency representation the model expects
- No published quantified WER improvement exists for the ffmpeg chain on meditation audio specifically (community qualitative reports only)
- pyvideotrans.com/blog/ffmpeg-nosie: best source for ffmpeg chain with STT context (WebFetch works)
- github.com/openai/whisper/discussions/2125: community consensus on preprocessing (Demucs recommended over traditional denoisers)

### Whisper Fine-Tuning for Domain Vocabulary (Feb 2026)
- CRITICAL: fine-tuning Whisper creates a separate self-hosted model — it does NOT improve your Speechmatics pipeline. Two different architectural paths.
- Minimum data: ~8 hrs for meaningful improvement (HF blog: 31.5% absolute WER reduction on language task). For English jargon only: 2-4 hrs plausible.
- Use existing Speechmatics transcripts as training labels — pair audio files with corrected .txt transcripts; load with librosa at sr=16000
- Model choice: whisper-small (T4 GPU, 5-10 hrs training); whisper-medium (A10G, 10-20 hrs); whisper-large-v3 (A100, impractical for personal projects)
- Training cost: ~$5-15 for a run on RunPod or Modal
- WER improvement on jargon: ~5-15% relative (not the 31.5% absolute from the language-specific HF demo — that's for a new language)
- huggingface.co/blog/fine-tune-whisper: canonical HF tutorial with full code (WebFetch works, returns full content)
- modal.com/docs/examples/fine_tune_asr: jargon fine-tuning example with 7K samples (WebFetch works)

### LLM Post-Correction Prompting for Dharma Transcripts (Feb 2026)
- Single structured JSON call beats 3 separate calls (summary + concepts + classification) — lower latency and cost
- Haiku cost for 60-min transcript (~12K tokens): ~$0.004-0.006 per enrichment call
- Tradition classification signals: Theravada (Pali terms, jhana, Southeast Asian teachers), Vajrayana (Rinpoche, rigpa, dzogchen, mahamudra, ngondro), Zen (koans, zazen, roshi, sesshin), Advaita (self-inquiry, Ramana, Nisargadatta), Secular (MBSR, Kabat-Zinn)
- Haiku pitfalls on meditation content: (1) "corrects" Pali terms to English homophones in summaries — prevent with explicit "use Pali/Sanskrit spelling" instruction; (2) summary length drift — enforce max word count; (3) Secular teachers misclassified as Theravada — add tradition_evidence field
- For terminology correction pass: specify exact error→correction pairs explicitly; don't ask Haiku to freely correct (hallucination risk)

### AI in Banking (2026 — for consulting/advisory context)
- bankingdive.com: JS-heavy — WebFetch returns no body text; use WebSearch instead
- lloydsbankinggroup.com press releases: sometimes return error 1007 — try PDF version URL directly
- mckinsey.com: WebFetch times out frequently; use WebSearch for McKinsey report summaries instead
- grcreport.com: reliable for HKMA supervisory priority summaries; WebFetch works
- amlintelligence.com: good practitioner AML publication, WebFetch works, Jan 2026 article confirmed
- artificiallawyer.com: reliable for bank legal AI deals with verified dates
- Accenture banking trends 2026 report: PDF at accenture.com/content/dam/... is direct download; the HTML page WebFetchable
- Key verified Jan 2026 events: HSBC-Harvey AI deal (Jan 20), Lloyds £100M AI announcement (Jan 29), BNY Mellon 20K agent deployment article (Jan 16), AML Intelligence 5-trends article (Jan 8)
- MAS AI Risk Guidelines status: consultation CLOSED Jan 31, 2026 — NOT yet finalized. 12-month transition period after finalization.
- HKMA key 2026 dates: operational resilience deadline May 31 2026; GenAI consumer protection listed as 2026 priority; Responsible AI Toolkit under Fintech 2030 strategy
- SR 11-7 (US model risk): NOT updated in Jan 2026 — ABA called for update but none issued
- DBS: 800+ AI models, 350 use cases; proprietary ADA/ALAN platforms; Harvard Business School case study published
- Goldman Sachs: GS AI Assistant launched firm-wide Jan 2025 (NOT Jan 2026 — rollout to 10K employees was Jan 2025); Devin autonomous coding deployed 2026
- BNY Mellon Eliza 2.0: 20,000 "Empowered Builders", 130+ Digital Employees; 5% unit cost reduction in custody trades confirmed Jan 2026
- Lloyds: £50M AI value in 2025 (confirmed), targeting £100M in 2026; announcement dated Jan 29, 2026

### China AI Ecosystem (2025)
- artificialanalysis.ai/downloads/china-report/: quarterly China AI state-of-play reports, very useful
- carnegieendowment.org: good policy analysis on China AI governance
- globaltimes.cn: useful for Chinese bank DeepSeek adoption news (state media, so promotional bias)
- thefinanser.com/2025: good synthesis of China bank AI leapfrog narrative
- Key facts verified:
  - DeepSeek R1 launch: Jan 20, 2025 (same day as Kimi K1.5)
  - DeepSeek V3 compute cost: $5.576M (GPU pre-training only — total CapEx >$1.3B per SemiAnalysis)
  - Qwen3 launch: April 29, 2025 (Alibaba); Qwen3-235B flagship
  - Kimi K2: July 2025 (1T param MoE, open sourced); K2 Thinking: November 2025
  - Baidu Ernie open-sourced from June 30, 2025 (strategic shift post-DeepSeek)
  - ByteDance Doubao API: ¥0.0008/1K tokens — effectively free; triggered price war
  - China AI price war: started mid-2024 with DeepSeek lowering to ¥1/M tokens, race to near-zero by mid-2025, reversed Q3 2025 (DeepSeek +50% in Sep 2025)
  - Chinese banks (ICBC, CCB): heavily deploying domestic models (DeepSeek + proprietary); not Western models
  - China gov AI investment 2025: ¥345B total (39% of total), ¥89B for 15 new AI research centers

### Apple PhotoKit (macOS/iOS, Swift) — Feb 2026

- github.com/LimitPoint/LivePhoto: best single-file reference for Live Photo creation with full Swift source (WebFetch works on raw file)
- github.com/LimitPoint/LivePhoto/blob/master/README.md: technical constraint reference (WebFetch works)
- developer.apple.com/forums: JS-heavy — WebFetch returns forum config not thread content; use WebSearch excerpts
- developer.apple.com/videos/play/wwdc2022/10132/: WWDC22 change history session (WebFetch works)
- ikyle.me/blog/2025/querying-the-ios-photo-library: good 2025 album/folder creation code examples (WebFetch works)

**Live Photo creation constraints (verified across 3 sources):**
- Both JPEG and MOV must share a UUID string called the asset identifier
- JPEG: embed in `kCGImagePropertyMakerAppleDictionary` with key `"17"` = assetIdentifier
- MOV: two metadata items required: `com.apple.quicktime.content.identifier` = assetIdentifier (top-level) + timed metadata track `com.apple.quicktime.still-image-time` = 0xFF (int8)
- `PHAssetCreationRequest.forAsset()` → `addResource(with: .photo, ...)` + `addResource(with: .pairedVideo, ...)`
- NO filename matching required — pairing is 100% via the UUID in the metadata
- NO documented duration constraints — but timed metadata track timing controls where the "still image moment" is
- If importing a pre-made JPEG+MOV pair, you must write the UUID metadata into BOTH files BEFORE calling PHAssetCreationRequest

**Album and folder creation:**
- Album: `PHAssetCollectionChangeRequest.creationRequestForAssetCollection(withTitle:)` inside `performChanges`
- Folder: `PHCollectionListChangeRequest.creationRequestForCollectionList(withTitle:)` inside `performChanges`
- Add album to folder: `PHCollectionListChangeRequest(for: folder)?.addChildCollections(albums as NSFastEnumeration)`
- Nested folders (folder inside folder): API supports it (`PHCollectionList` is itself a `PHCollection`), BUT in practice, apps crash or silently ignore deeply nested structures. One level of folder > albums is the safe limit.
- Cross-`performChanges` reference: capture `placeholderForCreatedAssetCollection.localIdentifier` in block 1, then fetch and add in block 2 (can't cross-reference within same block for parent-child relationship)

**Batch import stability:**
- Root cause of crashes: memory pressure → system kills `photolibraryd` → `assetsd` XPC connection breaks → error "Connection to assetsd was interrupted"
- iOS 26 / future: `PHPhotosError.limitExceeded` code added — but undocumented which APIs trigger it
- Recommended pattern: serial `performChanges` calls with `DispatchSemaphore` timeout (5s), retry on timeout, never batch thousands in a single change block
- `performChangesAndWait` is synchronous but does NOT help with daemon crashes
- Memory pressure is the trigger — avoid holding large image buffers during import; release after each `performChanges`

**Duplicate detection — no native API:**
- PhotoKit has NO built-in duplicate prevention. Importing the same file twice creates two assets.
- Pattern 1: Save `localIdentifier` from `placeholderForCreatedAsset` to your own database; check before importing
- Pattern 2: Fetch all assets, compare by `creationDate` + `PHAssetResource.assetResources(for:)[0].originalFilename` — note: `originalFilename` lookup takes 7-15ms per asset, slow at scale
- Pattern 3: WWDC22 persistent change tokens — use `PHPhotoLibrary.shared().fetchPersistentChanges(since: token)` to track inserted identifiers across app launches; persist `changeToken` to disk
- No hash/perceptual hash dedup in PhotoKit — must implement yourself if needed

### Capco AI Thought Leadership
- capco.com/intelligence/capco-intelligence/: WebFetch works, returns clean markdown
- Detailed report index: capco-thought-leadership.md
- Key report cluster: agentic-ai (Jun 11), agentic-ai-in-action (Apr 30), agentic-ai-transforming-payments (Jun 30), confidence-driven-agent-ai (Aug 25), all 2025
- New Frontier Old Habits (Jan 9, 2026): Forbes/Probert/Forooghian — killer quote "AI rewards focus, not frenzy"
- Journal 60 GenAI: flagship publication, 16 papers, includes Sundararajan (NYU) on board governance
- Capco-OpenAI partnership: announced Nov 17, 2025
- PDF .ashx downloads on capco.com: WebFetch fails — use WebSearch for content

### Consulting Firm AI Investment Announcements (2023 baseline, 2025 execution)
- CRITICAL: Big 4 "big AI announcements" were mostly 2023, not 2025. Don't misdate these.
  - Accenture $3B over 3 years: announced June 13, 2023
  - EY $1.4B + EY.ai platform: announced September 21, 2023
  - PwC US $1B over 3 years: announced April 26, 2023
  - KPMG $4.2B over 3 years: announced 2023 (extends through 2026)
  - BCG-Anthropic: Sep 14, 2023; BCG-OpenAI: March 2023
  - Bain-OpenAI expanded: October 2024
  - Deloitte Zora AI: announced Nvidia GTC 2025 (March 2025)
  - Oliver Wyman Quotient: June 27, 2024
  - Capco-OpenAI partnership: November 17, 2025
  - Accenture acquires Faculty (UK AI firm): announced January 6, 2026
- newsroom.accenture.com: canonical for Accenture press releases
- businesswire.com: reliable for Capco press releases

### AI Lab & Consulting Firm Blogs (RSS Feed Inventory)

**AI Lab Blogs (Highest Credibility):**
- deepmind.google/blog/: Google DeepMind research announcements; NO official RSS feed (email newsletter only). ~2-3 posts/week.
- ai.meta.com/blog/: Meta AI (FAIR) model releases + research summaries; NO official RSS feed discovered (community requested RSSHub route github.com/DIYgod/RSSHub #16938). ~1-2 posts/week. JS-rendered.
- blogs.nvidia.com/: NVIDIA main blog (product/marketing focus). RSS: https://feeds.feedburner.com/nvidiablog (verified RSS 2.0). ~3-5 posts/week.
- developer.nvidia.com/blog/: NVIDIA Technical Blog (developer tutorials, CUDA, optimization). RSS: https://developer.nvidia.com/blog/feed (verified Atom 1.0). ~3-5 posts/week.

**Consulting Firm AI Blogs (Market Analysis, Lower Credibility):**
- mckinsey.com/capabilities/tech-and-ai/our-insights: Tech & AI Insights. RSS: https://www.mckinsey.com/insights/rss (verified RSS 2.0, contains ALL McKinsey insights not just AI). ~50 items per 2-week cycle.
- bcg.com/capabilities/artificial-intelligence/insights: BCG AI Insights. NO official RSS feed (newsletter only, community RSS generators unreliable). ~1-2 posts/week.
- deloitte.com/us/en/insights.html: Deloitte Insights hub. NO official RSS feed (MyDeloitte newsletter only). Podcast RSS available at deloitteuniversitypress.libsyn.com/rss (limited scope). ~1-3 AI articles/week.

**Regulator (Authoritative but Low Frequency):**
- mas.gov.sg/publications: MAS publications hub. AI-specific docs: AI Model Risk Management (Dec 2024), Consultation Paper on AI Risk Management (Jan 2025), FEAT Principles (2018). NO RSS feed; updates via press releases + PDF downloads. Quarterly regulatory cycle.

**RSS Feed Pattern Finding:** Lab blogs either have NO RSS feeds (DeepMind, Meta) or share feeds that are JS-heavy (requires right-click inspect to find). McKinsey has a general feed that is NOT AI-specific. NVIDIA has two feeds, split by audience (marketing vs technical). Consulting firms deliberately don't RSS-syndicate (email lock-in strategy).

### Cognitive Task-Switching / Multitasking Research
- pubmed.ncbi.nlm.nih.gov: canonical for peer-reviewed switch-cost studies
- pmc.ncbi.nlm.nih.gov/articles/PMC8428299/: state-of-the-art multitasking review (2021, still current)
- blog.ninlabs.com/blog/programmer-interrupted/: Parnin (GT) programmer interruption study — empirical, 86 programmers, 10K sessions
- pubsonline.informs.org/doi/10.1287/orsc.2017.1184: Leroy & Glomb 2018 "Tasks Interrupted" — ready-to-resume plan, Org Science
- confresearchr.org/icse-2024 + kjl.name/papers/icse24.pdf: ICSE 2024 "Breaking the Flow" developer interruption study
- blog.oberien.de/2023/11/05/23-minutes-15-seconds.html: CRITICAL debunk — "23 min 15 sec" claim not in any Mark paper; came from oral interviews only
- CRITICAL MISINFORMATION PATTERNS: (1) "23 minutes 15 seconds" — not in Mark's paper, interview claim only; (2) "40% productivity loss" — Rubinstein et al. 2001 measured millisecond reaction-time costs, not 40% on real work; the % figure is a popularisation; (3) "23 min to recover" conflated with "25 min to return after sidetracked" (Mark 2005 = different stat); (4) "$450B annual cost" figures are unfounded estimates
- Key verified facts: Rubinstein et al. (2001, J Exp Psych) = millisecond switch costs for rule-switching; Rogers & Monsell (1995) = 200ms+ costs for predictable switches; Parnin (2013) = 10-15 min for developers to resume code editing; Leroy (2009, OBHDP) = attention residue is real, unfinished tasks with time pressure cause most residue; Leroy & Glomb (2018, Org Science) = ready-to-resume plan reduces residue significantly; Srna, Schrift, Zauberman (2018, Psych Science) = *illusion* of multitasking (not actual) boosts effort/engagement on simple aligned tasks only
- Steel-man conditions: (a) automatised/procedural tasks = near-zero switching cost; (b) trained, predictable switching can improve; (c) scheduling similar tasks in batches; (d) perceiving task as "multitasking" increases engagement on simple aligned tasks (Srna 2018)

### Cal Newport (2025-2026 Research)
- calnewport.com/archive/: best for full archive listing by month — WebFetch returns clean markdown titles+dates
- calnewport.com/blog/: homepage shows ~8 most recent posts with abstracts
- thedeeplife.com/podcasts/episodes/: podcast episodes; most episode pages load OK via WebFetch
- podcastnotes.org/category/deep-questions-podcast/: independent episode notes (partial transcripts)
- bigthink.com: picks up Newport essays; WebFetch works cleanly
- Cal Newport has NO new book announced as of Feb 2026 — Slow Productivity (Mar 2024) is most recent
- "The Deep Life" is a concept/podcast brand, not a new book title (as of Feb 2026)
- Deep Life Stack v2.0 was updated Nov 2023: Discipline → Values → Control → Vision (4 layers)
- Key new concepts 2025-2026: "long thinking" (analog notebook + extended focus), "additive vs extractive technologies", "vibe reporting" (AI hype coverage critique), "digital deskilling" (AI agent management eroding professional skills)
- Newport's AI stance 2026: skeptic of hype/agents, pragmatist on current capabilities; natural language interfaces = genuine "killer app"; time blocking/slow productivity frameworks unchanged

### Kindle Cloud Reader Text Extraction (as of Feb 2026)
- blog.pixelmelt.dev/kindle-web-drm/: BEST technical source — reverse-engineered KCR's SVG glyph obfuscation (Oct 15, 2025, updated Jan 13, 2026)
- shkspr.mobi/blog/2025/10/improving-pixelmelts-kindle-web-deobfuscator/: improvement using full-page Tesseract 5 OCR (code NOT published due to licence issue)
- github.com/transitive-bullshit/kindle-ai-export: Playwright + gpt-4.1-mini screenshots → text; last updated Oct 2024; requires WebGL-capable browser (fails in VM)
- readwise.io/bookcision: extracts Kindle HIGHLIGHTS only (not full text); still maintained (transferred to Readwise 2023)
- docs.readwise.io/readwise/docs/importing-highlights/kindle: Readwise uses browser extension scraping notebook page; highlights only, not full text
- marc.merlins.org/perso/public/post_2023-05-14_You-Cannot-Cut-and-Paste-From-Kindle-Cloud-Reader-Anymore.html: confirms rendering change to server-side images (~2023)
- Key architectural facts (verified Oct 2025):
  - KCR serves TAR archives containing JSON page data with glyph ID mappings + SVG definitions — NOT plain text
  - Glyphs are randomized per-request: 'T' might be glyph 24, alphabet reshuffled every time — makes direct decode impossible
  - Old DOM scraping (2020 gist by MTco) is dead — text is no longer in the DOM at all
  - Highlighting is done with empty DIVs at server-provided pixel coordinates
  - Three extraction tiers confirmed working as of 2025:
    1. HIGHLIGHTS ONLY (legal, no DRM): Readwise browser extension / Bookcision bookmarklet → scrapes read.amazon.com/kp/notebook
    2. FULL TEXT via vision LLM (technically OCR-adjacent, requires auth, not DRM circumvention): kindle-ai-export (Playwright + gpt-4.1-mini screenshots). Works if you own the book. Accuracy "near perfect" in testing. Fails on VMs (WebGL required).
    3. FULL TEXT via SVG deobfuscation (technically complex, crosses DRM reverse-engineering boundary): PixelMelt approach — render SVG glyphs, SSIM-match to TTF characters, 361/361 glyphs matched; or Tesseract 5 on full page reconstructions. No packaged tool published. Legal status uncertain.
  - DeDRM (Calibre plugin): broken for Mac users without e-ink device as of early 2025. Amazon ended USB transfer in Feb 2025. Downgraded Kindle for PC 2.4.0 + DeDRM 10.0.9 still works for pre-Apr 2025 books on Windows.
  - Kindle for Mac DRM: only works with a physical Kindle e-ink device in the loop (to extract serial-number-based key). No Mac-only method confirmed working in 2025.
  - No official Amazon API for full book text — only unofficial highlights access via authenticated notebook page scraping.
  - ReaderTools / KindleOptimizer Chrome extensions: last updated 2019; status uncertain for 2024-2025 KCR.

### tmux Status Bar Design Research
- github.com/rothgar/awesome-tmux: canonical curated list of tmux themes/plugins
- github.com/vaaleyard/tmux-dotbar: good minimal example (dot separator pattern); WebFetch returns clean content
- github.com/niksingh710/minimal-tmux-status: TPM plugin, prefix-indicator focused; WebFetch works
- waylonwalker.com/tmux-status-bar/: good pattern reference; redirected/may need WebFetch retry
- stephango.com/flexoki: canonical Flexoki palette; WebFetch returns exact hex values
- github.com/kaikramer/dotfiles: good iceberg-based example with clean variable-defined colors
- CRITICAL: `#F` in format strings = tmux alias for `#{window_flags}` — uppercase hex colors break. Use lowercase hex OR avoid hex in format strings entirely.
- CRITICAL: Inline color codes in window-status-format/window-status-current-format can break mouse click detection. Correct pattern: set colors via `set -g window-status-style` and `set -g window-status-current-style` SEPARATELY, keep format strings clean (no `#[fg=...]` embeds).
- CORRECT separation pattern (confirmed via tmux issue #1909 + best practice):
  ```
  set -g window-status-style        "fg=colour242,bg=default"
  set -g window-status-current-style "fg=colour251,bold,bg=default"
  set -g window-status-format        " #I:#W "
  set -g window-status-current-format " #I:#W "
  ```
- Flexoki Dark hex values (verified from stephango.com/flexoki, Feb 2026):
  - black: #100f0f | base-950: #1c1b1a | base-900: #282726 | base-850: #343331 | base-800: #403e3c
  - tx (primary): #f2f0e5 | tx-2 (muted): #b7b5ac | tx-3 (faint): #6f6e69
  - red-400: #d14d41 | orange-400: #da702c | yellow-400: #d0a215 | green-400: #879a39
  - cyan-400: #3aa99f | blue-400: #4385be | purple-400: #8b7ec8 | magenta-400: #ce5d97
- For iOS/Blink compatibility: avoid Nerd Font icons (may not render). Use ASCII-safe separators only.
- Pattern for variable-defined colors (from kaikramer dotfiles): define COL_X variables, reference in style options. Cleaner than colour numbers and avoids magic numbers.
- tmux-powerkit claims Flexoki theme support but requires TPM — overkill for a 2-window setup.
- No standalone Flexoki tmux theme found without a plugin system (as of Feb 2026) — must hand-roll.

### Anthropic API Proxy / Claude Code Alternative Backends (Feb 2026)
- Three distinct approaches: (A) local proxy that translates Anthropic→OpenAI, (B) direct Anthropic-compatible endpoints from providers, (C) enterprise gateway (LiteLLM)
- Official Claude Code env vars: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` (overrides API key header)
- Official Claude Code docs on LLM gateways: code.claude.com/docs/en/llm-gateway (WebFetch works cleanly)
- **Direct Anthropic-compatible endpoints (no proxy needed):**
  - Moonshot Kimi: `https://api.moonshot.ai/anthropic/` (confirmed, set ANTHROPIC_BASE_URL directly)
  - DeepSeek: `https://api.deepseek.com/anthropic` (confirmed, official docs at api-docs.deepseek.com/guides/anthropic_api)
  - GLM/Z.AI: `https://api.z.ai/api/anthropic` (community-confirmed via GitHub gists)
- **Key proxy projects (by maturity):**
  - **LiteLLM** (github.com/BerriAI/litellm): enterprise-grade, 100+ providers, Anthropic `/v1/messages` endpoint — OFFICIALLY mentioned in Claude Code docs. Best for teams.
  - **1rgs/claude-code-proxy** (3.1K stars, Python): translates to OpenAI or Gemini; env vars `PREFERRED_PROVIDER`, `BIG_MODEL`, `SMALL_MODEL`. Port 8082.
  - **openbridge** (fakerybakery/claude-code-kimi-groq, 381 stars): pip-installable; targets Kimi K2/GLM-4.5/Qwen3-Coder; `pip install openbridge` + `ANTHROPIC_BASE_URL=http://localhost:8323/`
  - **CCProxy** (orchestre-dev/ccproxy, MIT): supports Anthropic/OpenAI/Gemini/DeepSeek/OpenRouter; install script; config at `~/.ccproxy/config.json`; port 3456
  - **claude-code-mux** (9j/claude-code-mux, 469 stars, Rust): ARCHIVED Feb 18 2026 — read-only. Was 18+ providers with priority routing. Do not recommend for new use.
  - **anthropic-proxy-rs** (m0n0x41d, 25 stars, Rust): translates to OpenAI-compatible via `UPSTREAM_BASE_URL`; lightweight single binary
  - **maxnowack/anthropic-proxy** (Node, OpenRouter-specific): simple single-purpose proxy
  - **gemini-api-proxy** (IT-BAER, 10 stars): exposes free Gemini Code Assist as Anthropic `/v1/messages` — uses undocumented Google APIs, ToS risk
- **Model name mapping in Claude Code:** use `CLAUDE_CODE_*_MODEL` env vars (or `claude_model_config` in settings.json) to map Claude model names to custom proxy model names
- **Key gateway requirement:** proxy must forward `anthropic-beta` and `anthropic-version` headers; failure causes reduced functionality
- **Caveats:**
  - claude-code-mux archived — don't recommend
  - gemini-api-proxy uses undocumented Google APIs — ToS risk
  - Blog post (fsck.com) warns: many GitHub proxy setups are "sketchy" — review before piping curl to bash
  - Tool-use/thinking features may degrade with models that don't support them natively

### WeChat Public Account RSS Bridges (Self-Hosting, as of Feb 2026)

**wechat2rss (ttttmr/Wechat2RSS):**
- github.com/ttttmr/Wechat2RSS: canonical repo (active, 1.2k stars, no formal releases — Docker image is the deliverable)
- wechat2rss.xlab.app/deploy/: official deploy docs; wechat2rss.xlab.app/deploy/active: activation info
- Mechanism: WeChat Reading API (not direct WeChat scraping) — requires WeChat Reading account + QR scan
- PAID self-hosted: ¥15/month or ¥150/year. License keys (LIC_EMAIL + LIC_CODE) required to run container.
- Docker image: `ttttmr/wechat2rss:latest` (amd64 + arm64). Single container, data persisted at `/wechat2rss` volume. No database needed.
- Env vars: `LIC_EMAIL`, `LIC_CODE`, `RSS_HOST` (full URL), `RSS_HTTPS` (default "1"), `TZ`
- No free tier for self-hosted. Free public service at wechat2rss.xlab.app covers 300+ accounts.
- Platform support: Docker on any VPS/Mac Mini. Railway (one-click). Zeabur (requires paid plan). NOT HuggingFace.
- Railway free tier is dead (¥5/month minimum now) — this is why user's Railway instance 404d.
- Risk: account enters "风控中" if scraped too aggressively; accounts that are "frequently used" less likely to trigger.
- Activation codes are single-instance (one container only); self-service reset at wechat2rss.xlab.app/deploy/active.

**wewe-rss (cooderl/wewe-rss):**
- github.com/cooderl/wewe-rss: ARCHIVED Jan 19, 2026 (read-only). 8.8k stars, 1.5k forks.
- Mechanism: WeChat Reading API (same approach as wechat2rss) — needs WeChat Reading account + QR scan
- FREE and open source (Apache 2.0) — no license keys
- Docker: `cooderl/wewe-rss-sqlite:latest` (SQLite, simpler) or `cooderl/wewe-rss:latest` (MySQL)
- SQLite run: `docker run -d -p 4000:4000 -e DATABASE_TYPE=sqlite -v $(pwd)/data:/app/data cooderl/wewe-rss-sqlite:latest`
- Env vars: `DATABASE_URL` or `DATABASE_TYPE=sqlite`, `AUTH_CODE`, `SERVER_ORIGIN_URL`, `CRON_EXPRESSION`, `FEED_MODE=fulltext`, `MAX_REQUEST_PER_MINUTE` (default 60)
- HuggingFace free tier: WORKS as host but sleeps after 48h inactivity → feeds stop updating. Data may wipe on restart (no persistent storage on free tier). That's why user's Space is dead.
- HuggingFace fix: either wake the space regularly OR upgrade to paid persistent storage tier.
- Known issues: auth sessions drop frequently (reported May 2025, unresolved). Manual re-login required every few days for some users. Rate limit tightened Apr 2025: 50 requests/account/day, 300/IP/24h.
- Relay risk: some requests route through weread.111965.xyz (developer claims no data retention, but third-party dependency)
- Still deployable from archived code — Docker image still on ghcr.io — but no future fixes for WeChat API changes.

**we-mp-rss (rachelos/we-mp-rss):**
- github.com/rachelos/we-mp-rss: ACTIVELY MAINTAINED (Dec 2025 release, 2.2k stars, Python/FastAPI + Vue3)
- Different mechanism: scrapes WeChat content (possibly via PC WeChat), QR code auth
- Docker: `docker run -d -p 8001:8001 -v ./data:/app/data ghcr.io/rachelos/we-mp-rss:latest`
- Features: export to MD/PDF/DOCX, webhook, API interface
- V2EX community reports mixed results (封号 risk, similar to wewe-rss)

**Platform recommendation for 2026:**
- Mac Mini local: all three work (Docker, arm64 supported). Best option for stability.
- VPS (cheap): any work. Wechat2rss on Sealos costs ~¥11-15/month (but wechat2rss itself costs ¥15/month too).
- HuggingFace free: wewe-rss WORKS but sleeps after 48h — need to keep alive with a cron ping (uptimerobot etc.)
- Railway: no longer free — minimum $5/month. 404 issues are the dead free tier.
- Render free tier: worth trying for wewe-rss (SQLite variant) as Railway alternative

**Common gotchas:**
- Chinese search ("微信公众号RSS自建") surfaces more recent community reports than English
- Both tools use WeChat Reading as the backend, not direct WeChat API — same underlying risk
- V2EX/Zhihu community consensus (2025): neither tool is perfectly stable; wewe-rss slightly more popular historically but now archived

### macOS Docker Runtimes (Apple Silicon, Feb 2026)
- docs.orbstack.dev: official OrbStack docs — comparison pages exist but use checkmarks not numbers; go to /benchmarks for metrics (but may be self-serving)
- fsck.sh/en/blog/docker-desktop-alternatives-2025/: best independent comparison, WebFetch works cleanly
- github.com/abiosoft/colima: Colima canonical repo; issues tracker has real RAM/startup reports
- github.com/apple/container: Apple container CLI — v0.9.0 (Feb 3, 2026), requires macOS 26 (Tahoe) for full support
- code.saghul.net/2025/02/migrating-from-docker-desktop-to-colima-2025-update/: good 2025 Colima migration notes
- repoflow.io/blog/apple-containers-vs-docker-desktop-vs-orbstack: best benchmark numbers (CPU, memory, startup times)

**Key verified facts (Feb 2026):**
- OrbStack: idle CPU ~0.1%, idle RAM under 1GB (community), 180mW vs Docker Desktop 726mW power draw. Free for personal non-commercial use (revenue <$10K/yr). Commercial license $8/month or $96/year. Has "Start at Login" GUI toggle — works on Sequoia, some reported bugs on beta macOS. Containers with `--restart always` survive reboots IF OrbStack engine auto-starts. Known issue: dirty shutdown on macOS reboot can corrupt DB-backed containers (GitHub issue #1897, open as of 2025). macOS-only, Apple Silicon native.
- Colima: idle RAM ~400MB on M1 (multiple sources). No native auto-start — requires manual launchd plist OR `brew services start colima` (which has known breakage in Feb 2025 — brew services starts but colima doesn't). Most reliable autostart: custom launchd plist. Free (MIT). CLI-only, no GUI. Recommend `--vm-type=vz --mount-type=virtiofs` for Apple Silicon performance. UDP unsupported (2025).
- Docker Desktop: idle RAM 2GB+, up to 6GB with one container. Slowest startup. Free only for individuals/small orgs (<250 employees AND <$10M revenue). Most reliable auto-start (system integration). Heaviest option.
- Podman: daemonless architecture, no persistent background process. Autostart bugs documented (GitHub issues #4647, #2781). macOS support via Podman Machine (Apple Virtualization Framework on M-series). Free (Apache 2.0). Less mature on macOS. Not recommended for "set and forget" Mac deployments.
- Lima: Colima is built on Lima. Direct Lima usage = more config, same fundamentals. No balloon memory device — memory not returned to OS until VM stops. Same autostart pain as Colima.
- Apple Container CLI: v0.9.0, Feb 2026. Requires macOS 26 (Tahoe) for full support — some features on Sequoia 15.5+ with limitations. Apple Silicon ONLY. Not yet stable (pre-1.0, minor versions may break). CPU/memory performance matches or beats OrbStack in benchmarks. Container startup: 0.9s vs OrbStack 0.23s (Apple Container is SLOWER to start individual containers due to per-container VM). Open source (Swift). `brew install --cask container`.
- **For "just run one container reliably": OrbStack is the practical winner for minimal config. Colima is the best free alternative but needs launchd wrangling.**
- **Critical OrbStack gotcha for long-running containers:** `--restart=unless-stopped` combined with OrbStack auto-start works for reboots, BUT clean shutdown of macOS may corrupt DB-backed containers if containers aren't stopped first (issue #1897). Mitigation: add a launchd shutdown hook or accept the risk for SQLite (less severe than Postgres/MySQL).
- Apple Container CLI is NOT production-ready for "set and forget" as of Feb 2026 — pre-1.0, macOS 26 required, no stable auto-start docs.

### Google Photos to iCloud Migration Tools (Feb 2026)

**Key finding: The gap is real but partial.** The extraction and metadata-fix layers are well-covered; the automated import + verification + disk-space batching layer is missing or barely handled.

**Official tool:**
- Apple/Google Data Transfer Project (DTP): web-based, direct Google→iCloud cloud transfer. Handles metadata (name, description, location, file type). Albums land in single "Import from Google" album (no album structure preserved). No verification. Not for Workspace/Family/Education accounts. No disk space concern (cloud-to-cloud). Source: support.apple.com/en-us/120924

**Best open-source tool for the full pipeline:**
- **osxphotos** (RhetTbull, 3.3k stars, Python): from v0.67.0 (Dec 2023) supports Google Takeout JSON sidecar import. Key flags: `--walk --sidecar --skip-dups --dup-albums --sidecar-ignore-date --report takeout_import.csv`. Auto-finds Google Takeout's JSON naming scheme. Generates CSV report. Does NOT handle disk space awareness or true batching. Community consensus: import in batches of ~500 manually; Photos.app crashes after sustained large imports. Source: github.com/RhetTbull/osxphotos

**Metadata-only tools (don't import, just fix files):**
- **GooglePhotosTakeoutHelper / gpth** (TheLastGimbus, 5.5k stars, Dart): organises Takeout into chronological folder, moves files. No iCloud import. Recommends separate exiftool step for EXIF restoration. No disk awareness. Last release Sep 2023.
- **Xentraxx/GooglePhotosTakeoutHelper** (fork, 127 stars): adds ZIP processing, EXIF GPS/timestamp writing, 6 album strategies. Still metadata-only, no import.
- **jnwarp gist**: minimal Python script — fixes DateTimeOriginal on JPEGs, renames by timestamp. Hardcoded to US Eastern TZ. No batching, verification, or disk space.
- **google-photos-metadata-fix** (holmes-software), **google-takeout-metadata-restorer** (pfilbin90), **Greegko/google-metadata-matcher**: all metadata-fix-only, varying stars and age.

**Takeout→Apple Photos import tools (partial pipeline, limited):**
- **akhudek/google-photos-to-apple-photos** (25 stars, Python, 2022): imports + recreates albums + deduplication. No metadata fix. No disk space. Crashes after many sequential imports (known limitation, requires restart).
- **AndreYonadam/google-takeout-to-apple-photos** (18 stars, Swift, 2020): reads JSON sidecar for location/date, imports to Photos.app, basic dedup. No batching, no disk space. Likely broken (pre-osxphotos era).
- **citelao/google_photos_takeout_to_apple_photos** (4 stars, TypeScript): uses exiftool + AppleScript. Handles live photo pairing. Random-sample verification. Author says results are "decent but extremely unreliable."
- **dnlbnls/google-takeout-photos-process-to-icloud** (1 star, PowerShell, Mar 2024): Windows only. Uses ExifTool + FFmpeg + iOS Files app import. Manual batch of 500 advised. No verification. Disk space not addressed. Windows-only.

**Not yet built (Apple Photos target):**
- **PhotoMigrator** (jaimetur): cloud-to-cloud migration across Immich, Synology, Nextcloud. Apple Photos listed as "roadmap" — not yet available.

**Common failure pattern across all tools:**
- Photos.app crashes or returns "Unknown Error" after sustained batch imports (~300-500+ photos in one session). No tool handles this automatically. Community workaround: manual year-by-year batching.
- No tool combines: disk space pre-check → Takeout extraction → metadata fix → batched import → verification report.

**Paid options:**
- AnyTrans (iMobie): iOS device manager with batch iCloud photo management. Not specifically designed for Google Takeout. Mixed reviews (some reports of failure to transfer). Not transparent about disk space handling.
- MultCloud, CloudsLinker: cloud-to-cloud only; don't touch local files or metadata.

**Sources:**
- support.apple.com/en-us/120924 (official Apple DTP tool)
- github.com/RhetTbull/osxphotos (osxphotos)
- github.com/TheLastGimbus/GooglePhotosTakeoutHelper
- github.com/akhudek/google-photos-to-apple-photos
- github.com/citelao/google_photos_takeout_to_apple_photos
- github.com/dnlbnls/google-takeout-photos-process-to-icloud
- talk.macpowerusers.com/t/importing-photos-into-photos-app-from-google-takeout/35813

## AI Governance Certifications for Financial Services (Feb 2026)
Full synthesis in researcher response, Feb 25 2026.

### Reliable sources
- garp.org/rai/fees-payments: authoritative fee page (WebFetch works cleanly); April 2026 standard = $750 non-member
- isaca.org/credentialing/aaia: official AAIA page (WebFetch works); $459 member / $599 non-member
- isaca.org/credentialing/aaia/aaia-exam-content-outline: full domain breakdown (WebFetch works)
- iapp.org/certify/aigp: official AIGP page; $649 member / $799 non-member; BOK v2.1 effective Feb 2026
- assets.contentstack.io/...AIGP_BOK_2.1.0_FINAL.pdf: BOK v2.1 PDF — returns binary, not readable via WebFetch
- privacybootcamp.com/Resources/Article/aigp-body-of-knowledge-2026: best readable AIGP 2026 domain summary
- smatica.com/product/iso-iec-42001-lead-auditor-self-study-*: PECB self-study prices ($889 Lead Auditor, ~$1,798 Lead Implementer e-learning via live-online)
- davidharper.substack.com/p/garps-risk-and-ai-rai-certificate: best critical GARP RAI assessment (WebFetch works)
- mindgard.ai/blog/best-ai-risk-management-certifications: good overview table (WebFetch works)
- isqi.org/A4Q-AI-Compliance-EU-AI-Act/AI-C.425: A4Q EU AI Act cert; $176.70; (WebFetch works)
- dqsglobal.com/en/learn/hk/: HK-specific provider for ISO 42001 courses — 403 on WebFetch

### Key verified facts
- AAIA prerequisite: must hold CIA, CPA, CISA, or equivalent (active). Terry qualifies via CIA + CPA. Exam $459 members.
- AAIA domains: AI Governance & Risk (33%), AI Operations (46%), AI Auditing Tools & Techniques (21%). Notably does NOT explicitly reference SR 11-7 or banking regs — is audit-methodology focused.
- IAPP AIGP v2.1 (Feb 2026): 4 domains. Explicitly covers EU AI Act, NIST AI RMF, ISO 42001, ISO 42005. No prerequisites. $649 members / $799 non-members.
- GARP RAI: 80 questions, 4 hrs, 100-130 hrs study. Module 5 covers model governance with financial sector lens. April/Oct windows. Standard (April 2026): $625 FRM holders, $650 members, $750 non-members. Exam fee includes digital study access.
- PECB ISO 42001 Lead Auditor: self-study = $889 (SMATICA); e-learning live = $1,798; includes exam voucher + lifetime material access. Lead Implementer e-learning: ~$1,798.
- A4Q EU AI Act: $176.70, 40 MCQ, 60 min, no prerequisites, 2-year validity. Good for orientation not depth.
- CRISC 2025 update: Domain 2 now includes LLM/AI risk. Good for IS risk mgmt context but not AI governance specific.
- NIST AI RMF Architect (CertifiedInfoSec): ~$4,495 including training — expensive for what it is; not widely recognised.

### Methodology notes
- PECB direct pages (pecb.com) are JS-heavy — WebFetch returns navigation only; use authorised resellers (SMATICA, reconn.io) for pricing
- MAS consultation paper page (mas.gov.sg) returns CSS/JS not content — WebFetch fails; use search result summaries
- HKMA sources thin on specific certification requirements — no published list of endorsed credentials

### Misinformation patterns
- NIST AI RMF has no official NIST-branded certification — all "NIST AI RMF" certs are third-party training programs
- "EU AI Act certification" is a fragmented market — ISO 42001 is the closest to a formal standard; most EU AI Act courses are training only
- GARP RAI does not explicitly cover SR 11-7 in curriculum titles, but Module 5 addresses model governance in banking context per expert review

## Search Methodology That Worked

- Search authentic dissent + Nemeth's name surfaces her specific papers well
- "hidden profile paradigm Stasser Titus" is the canonical search for information-sharing failures
- For LLM debate: search arxiv directly + ICLR/EMNLP/ACL anthology
- RAND PDF often 403s — use the HTML summary page instead (rand.org/pubs/...)
- For HK store research: Chinese search surfaces price data and store opening news faster than English; ubeauty.com.hk and popbee.com are best for HKD price points
- Most HK fashion brand/shop sites are JS-heavy — WebFetch returns Shopify config, not content. Use WebSearch with site-specific queries instead of WebFetch for product/price data.
- AI blog RSS discovery: try common patterns (site:/feed, /rss, /atom.xml) + GitHub issue trackers (RSSHub feature requests) + Feeder/Feedspot aggregators. Official RSS is minority case for major blogs.

## Embodied AI & Humanoid Robotics (Mar 2026)
Full detail: `/Users/terry/.claude/agent-memory/researcher/embodied-ai-humanoid-robotics-2026.md`
- **Leading companies (Mar 2026):** Figure 03 (BotQ, 12K/yr), Tesla Optimus Gen 3 (data-only, no useful work per Musk Q4 2025), Boston Dynamics Atlas electric (Hyundai/DeepMind, all 2026 units committed), Agility Digit (most credible deployment: Toyota Canada 7 units RaaS), 1X NEO ($20K, teleop hybrid), Unitree G1 ($13.5K).
- **Figure/BMW reality check:** BMW confirmed 1 robot doing 1 task. CEO's "fleet running end-to-end" was false. Cross-checked via Fortune April 2025. Treat all founder-led robotics deployment claims skeptically.
- **Tesla Optimus reality check:** Musk confirmed Jan 28 2026 — deployed units not doing useful work, data collection only.
- **AI integration:** VLA (Vision-Language-Action) models are the dominant paradigm. Key: Physical Intelligence π0 (open-source, Feb 2026), Gemini Robotics (DeepMind, Mar 2026), Figure Helix, Unitree UnifoLM-VLA-0.
- **Data flywheel:** Formalized at arxiv:2511.19647. Real examples: π0.6 with Weave Robotics (50% less human intervention). Still mostly simulation + teleop — not wide field accumulation yet.
- **Timelines (Bain + Goldman + Morgan Stanley):** 3yr = semi-structured industrial. 5yr = service environments. 10yr = open-world. Goldman base: 250K units/yr by 2030. Biggest bottleneck: battery (2hr vs 8hr shift); fine motor dexterity second.
- **Source reliability:** fortune.com (WebFetch works), bain.com/insights (WebFetch works), figure.ai/news (works), deepmind.google/blog (works), humanoidsdaily.com (secondary, ok).
