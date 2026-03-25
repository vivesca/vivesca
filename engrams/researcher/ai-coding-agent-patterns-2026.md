---
name: AI Coding Agent Engineering Patterns (Mar 2026)
description: Technical implementation patterns from Devin, Claude Code, OpenHands, OpenAI Codex, Cursor/Windsurf, and Aider — March 2025–March 2026 deep research
type: reference
---

## Research coverage period
March 2025 – March 2026. Compiled March 2026 from official blogs, leaked prompts, arxiv papers, GitHub issues, and technical writeups.

## Key cross-cutting patterns (steal-worthy)

### 1. Specialised retrieval subagent (Windsurf/Cognition SWE-grep)
- Context retrieval spends >60% of first agent turn on large repos — delegate it to a separate fast model
- SWE-grep: RL-trained (modified policy gradient + F1 reward prioritising precision), 8 parallel tool calls/turn, max 4 turns, tools restricted to grep/read/glob
- Main agent context stays clean ("context budget" preserved, no "context poisoning")
- Speed: Cerebras inference, 2800 tok/s (mini), 650 tok/s (full) vs Claude Haiku baseline
- Generalises: any agent can delegate retrieval to a cheap/fast subagent

### 2. KV-cache hit rate as primary production metric (Manus, confirmed)
- 10x cost difference: $0.30 vs $3/MTok cached vs uncached (Claude pricing)
- Stable prefixes, append-only contexts, deterministic JSON serialisation, explicit cache breakpoints
- Consequence: do NOT dynamically remove tools — breaks cache prefix. Use logit masking instead.

### 3. File system as external memory (Manus, Anthropic, Claude Code)
- Files = unlimited, persistent, structured memory outside context window
- Drop file contents from context, keep file paths only
- todo.md / task_plan.md / progress.md continuously updated — pushes goals into recent attention window
- Critical for >50-turn tasks: combats "lost in the middle" degradation

### 4. Aider unified diff format — 3x laziness reduction
- SEARCH/REPLACE baseline: 20% success rate (GPT-4 Turbo on 89 tasks)
- Unified diff: 61% success rate — 3x improvement
- Key modifications: remove line numbers (models are bad at them), treat hunks as search-replace not precise offsets, encourage full function-level diffs over surgical lines
- Flexible patching with 9x fallback layers: normalisation, marker recovery, indentation flexibility, sub-hunk chunking, context window variation

### 5. Event-sourced state with deterministic replay (OpenHands)
- Single ConversationState object; append-only EventLog; metadata to base_state.json
- Condenser: abstract interface, condense([Event]) -> [Event]; LLMSummarizingCondenser = 2x cost reduction, ~linear vs quadratic scaling
- Condenser uses KEEP/REWRITE directives referencing message indices — avoids LLM quoting messages verbosely
- Preserves: goals, progress, remaining tasks, critical files, failing tests; drops: old raw outputs

### 6. Interleaved thinking in tool loops (Anthropic Claude)
- Think-Act-Think-Act pattern: reasoning block before each tool call AND after each result
- Reduces error propagation in multi-step chains
- Enables: "does this result actually answer my question, or do I need another tool call?"
- API: interleaved-thinking-2025-05-14 beta header; with adaptive thinking enabled automatically

### 7. Cursor/parallel agents with git worktree isolation
- Up to 8 parallel agents, each in its own git worktree (same repo, different working directory + branch)
- Faster than clones, lower disk, changes isolated until merge
- Background Agents: isolated Ubuntu VMs with internet, auto-create PRs for review
- Two-model pipeline: plan with one model (heavy), build with another (light or background)

### 8. Autofix loop closure (Devin)
- Bot-agnostic PR comment parsing: any bot (linter, CI, security scanner, dependency manager) that comments = fix trigger
- Configuration: user specifies which bots trigger autofix
- Termination: "CI runs clean" state
- Enables: agents that auto-close their own PR review cycles without human retouching

## Devin (Cognition)

**Architecture:** Compound AI — not a single model. Planner (high-reasoning model) + Coder (code-specialised) + Critic (adversarial security/logic review). RL fine-tuned on top of base LLMs.

**Context management:** Auto-indexes repos every ~2 hours into wiki + architecture diagrams. "Devin Search" with Deep Mode for complex exploration. Handles "5M lines of COBOL or 500GB repos" (methodology undisclosed).

**State/memory:** Playbooks (user-defined, stored procedures), Knowledge base (encoded conventions), Wiki (auto-generated per-repo). Parallel sessions each get isolated cloud IDEs.

**Agent loop specifics (Devin 2.0):** Interactive planning before execution — codebase analysis in seconds, preliminary plan shown, user can edit before run. Multiple parallel Devin instances with separate IDEs.

**Failure handling:** "Early loss-cutting" is explicit user guidance — restart fresh vs iterate on stuck agent. Autofix loop: write → review → bots comment → Devin fixes → CI reruns.

**Novel:** PR autofix loop; parallel Devin instances with isolated IDEs; interactive plan approval before execution.

**What's opaque:** Internal model architecture, RL training details, how planner/coder/critic interact at the API level.

## Claude Code (Anthropic)

**Architecture:** TAOR loop (Think-Act-Observe-Repeat). Minimal orchestrator — model decides next steps, not hardcoded logic. Four primitive tools: Read, Write, Execute (Bash), Connect (MCP/WebSearch/WebFetch) + orchestration (Agent/Skill/TodoWrite).

**Context management:**
- Auto-compaction ~50% capacity; CLAUDE.md re-injected after each compaction (unlike conversation history)
- Layered memory loading at startup: org policy → project rules → user preferences → auto-learned patterns
- Subagents: fresh context window, inherit CLAUDE.md + MCP + permissions but NOT parent history; return condensed summary only
- ToolSearch: dynamically loads MCP tools on-demand instead of preloading all schemas (critical for context economy)
- Parallel tool execution: read-only tools concurrent, state-mutating tools sequential

**Interleaved thinking:** Think between every tool call AND after every tool result. Enabled via adaptive thinking or explicit beta header.

**Hooks (deterministic lifecycle, outside LLM loop):**
- UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop, SubagentStart, SubagentStop
- Zero tokens consumed. Can short-circuit (PreToolUse rejection = tool blocked, Claude gets rejection message).
- PreCompact: archive full transcript before summarisation

**State/memory:**
- Session = resumable by session_id. Fork support (branch into different approach without modifying original).
- CLAUDE.md summarisation instructions: free-form section headers, compactor matches on intent
- Effort levels: low/medium/high/max — independent of extended thinking

**Failure handling:** max_turns + max_budget_usd limits with result subtypes (error_max_turns, error_max_budget_usd, error_during_execution). stop_reason field: end_turn, max_tokens, refusal.

**Novel:** Hooks architecture (deterministic enforcement outside LLM); ToolSearch for lazy MCP loading; CLAUDE.md re-injection post-compaction; session fork pattern; SubagentStart/SubagentStop hooks for parallel task tracking.

## OpenHands (formerly OpenDevin)

**Architecture:** Four-package modular design: openhands.sdk (core), openhands.tools (implementations), openhands.workspace (environments), openhands.agent_server (FastAPI + WebSocket). CodeActAgent = primary agent using Python execution as primary action format.

**Agent loop:** Stateless event processor. State = ConversationState (mutable metadata) + EventLog (append-only). Agent processes events step-by-step, emits structured events via callbacks. Events: LLMConvertibleEvent (visible to LLM) vs Internal (state updates, condensation — NOT in LLM context).

**Context management (Condenser system):**
- Abstract interface: condense([Event]) -> [Event]
- LLMSummarizingCondenser: up to 2x cost reduction, linear vs quadratic scaling
- Preserves: goals, progress, remaining tasks, critical files, failing tests
- Drops: old raw tool outputs
- Result stored as CondensationEvent in log; applied before sending history to LLM
- Cache-aware: triggers only at size thresholds to maximise prompt cache hits

**Security layer:**
- SecurityAnalyzer: rates each tool call LOW/MEDIUM/HIGH/UNKNOWN risk
- ConfirmationPolicy: can be updated dynamically mid-session
- SecretRegistry: late-bound credential injection, auto-masking in outputs, supports live rotation

**Multi-agent coordination:** AgentDelegateAction spawns sub-agents as independent conversations. Hierarchical: CodeActAgent → BrowsingAgent delegation.

**Tool system:** Action (Pydantic validated) → ToolExecutor → Observation. MCP tools treated as first-class (MCPToolDefinition + MCPToolExecutor via FastMCP). Distributed: tools cross process/network boundaries via lightweight JSON-serialisable specs.

**Novel:** SecretRegistry with live rotation + auto-masking; CondensationEvent in event log (condensation as a first-class event, not a separate mechanism); event separation (internal vs LLM-visible prevents bookkeeping clutter); non-native tool calling fallback (regex parsing for models without function calling).

## OpenAI Codex

**Architecture:** Cloud-native agent with per-task isolated containers. Model: GPT-5.2-Codex (Dec 2025) — context compaction for long-horizon work, strong multi-file reasoning.

**Agent loop:** Structured prompt (system + developer + user roles). Developer role injects sandbox description and shell tool. Loop: model evaluates → natural language or tool call → if tool call: execute in container, append outputs → repeat until completion or step limit.

**Sandboxing:**
- Platform-native: seccomp + Landlock on Linux; native sandbox on Windows; WSL on Windows for Linux behaviour
- Modes: read-only, workspace-write (default), danger-full-access
- Approval policies: untrusted, on-request, never
- Permission-profile config language: filesystem + network sandbox policy plumbing as separate configurable layers
- Subagents inherit parent sandbox policy (symlinked writable roots, persisted host approvals, project-profile layering)
- Network disabled by default even in cloud (prevents exfiltration, blocks prompt injection from untrusted sources)

**Multi-file changes:** GPT-5.2-Codex specialised for repo-scale reasoning (refactors, migrations). Context compaction handles long-horizon multi-file work.

**State/memory:** No persistent cross-session memory disclosed. Context compaction within session.

**Failure handling:** Step limit triggers stop. Explicit permission denial → Claude-style rejection message to model, attempts different approach.

**Novel:** Permission-profile config language as first-class feature; network-off-by-default as security primitive; subagent sandbox policy inheritance; dual OS sandboxing (seccomp/Landlock vs native Windows).

## Cursor Agent / Windsurf

### Cursor

**Architecture:** Dual-model pipeline. Architect model (heavy, plans changes) + Editor model (lighter, applies edits). Agent mode uses tool calls; agent determines relevance, not exhaustive attachment.

**Context management:**
- .cursor/rules: per-file/pattern scoped rules, version-controlled, merged in priority order (Team → Project → User)
- Hybrid indexing: semantic vector DB built at startup + real-time LSP integration
- CLAUDE.md compatibility: reads project CLAUDE.md directly (shared context across tools)
- IDE state injection: open files, cursor position, recent edits, linter errors, edit history — automatic

**Edit application:** "// ... existing code ..." semantic delimiter instead of line numbers. Edit_file tool call from main model → passed to weaker model for application.

**Parallel execution (2.0):** Up to 8 agents via git worktrees. Background Agents: isolated Ubuntu VMs, auto-PR creation. Plan in foreground, build in background. Plan with multiple agents simultaneously for competing approaches.

**Failure handling:** "Search before acting" philosophy baked into system prompt. `ask_user` action available. Early project-level context via rules and CLAUDE.md reduces planning failures.

**Novel:** Git worktree isolation for true parallel agents (not shared workspace); plan/build model separation; CLAUDE.md cross-tool compatibility.

### Windsurf (Cascade)

**Architecture:** Cascade agent + SWE-grep retrieval subagent. Context assembly pipeline: Rules → Memories → Open files → Fast Context (M-Query retrieval) → Recent IDE actions → trim to window.

**Fast Context / SWE-grep:**
- RL-trained (F1 reward, precision-weighted); 8 parallel tool calls/turn, 3 exploration + 1 answer turns
- 2800+ tokens/sec (mini) via Cerebras
- Reduces retrieval from 20+ seconds to under 1 second
- "Flow window" target: 5 seconds (above which P(breaking flow) rises sharply)

**Context management:**
- M-Query: proprietary retrieval (768-dim vectors, not naive cosine similarity)
- Memories: cross-session persistence for architectural decisions, encoded per project
- Real-time IDE state monitoring: file saves, terminal commands, navigation history
- Rules files (.windsurfrules): persistent project/global instructions

**Novel:** SWE-grep as RL-trained retrieval specialist; "context pollution" framing (retrieval results in main agent = wasted intelligence); 5-second flow window as design constraint; IDE state as implicit context (not just files).

## Aider

**Architecture:** CLI tool. Repo-map + edit-format selection + multi-model routing. Architect model (reasons about changes) + Editor model (applies changes).

**Repo map (graph ranking system):**
- NetworkX MultiDiGraph: nodes = files, edges = cross-file references
- PageRank with personalisation: chat files +100/len(fnames), mentioned identifiers +100, private identifiers 0.1x, referenced in active chat file 50x
- Tree-sitter parsing: .scm query files per language for definitions + references
- Token budgeting: binary search, O(log N), 15% tolerance, converges to optimal subset
- Three-layer cache: TAGS_CACHE (persistent disk, diskcache.Cache, mtime invalidation) + map_cache (in-memory, keyed by chat_fnames+token_budget) + tree_cache (per-file rendering)
- Refresh strategies: always, files, auto (adaptive), manual

**Edit formats:**
- `whole`: full file rewrite (simple, expensive)
- `diff` (SEARCH/REPLACE blocks): semantic boundaries, no line numbers, best for most models
- `udiff` (modified unified diff): removes line numbers, treats hunks as search-replace; 3x laziness reduction vs SEARCH/REPLACE on GPT-4 Turbo (20% → 61% on 89 tasks)
- `editor-diff`: architect model plans, editor model applies — separates intent from syntax
- `diff-fenced`: filepath inside fence (Gemini fix — models that fail at pre-fence filepath placement)
- Flexible patching fallbacks: normalisation → marker recovery → indentation flexibility → sub-hunk chunking → context window variation. Removing flexible patching = 9x more errors.

**Multi-model:** Default `diff` or `editor-diff` per model profile. Sonnet 4.x uses `diff` or `editor-diff`.

**Novel:** PageRank personalisation with chat-context-aware weights is architecturally elegant — the graph ranking adapts to what the user is asking about, not just static structure. Flexible patching as first-class fallback system (not error — expected and planned for).

## Source quality notes
- cognition.ai/blog: official, limited technical disclosure (marketing-oriented)
- anthropic.com/engineering: authoritative, high technical density
- platform.claude.com/docs/en/agent-sdk: official, most technically complete Claude source
- arxiv.org/html/2511.03690v1 (OpenHands SDK paper): peer-reviewed, most complete OpenHands source
- deepwiki.com/Aider-AI/aider: high-quality auto-generated wiki from source code, reliable
- aider.chat/docs: official, Paul Gauthier's own documentation, very technical
- gist.github.com/sshh12: leaked Cursor system prompt (Mar 2025) — reliable for prompting patterns, may be outdated
- developers.openai.com/codex: official but surface-level on implementation
- markaicode.com, cuckoo.network: secondary analysis, cross-reference before citing
