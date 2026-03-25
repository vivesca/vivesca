---
name: Open-Source IDE & Coding Agents — Technical Patterns (Mar 2026)
description: Deep research on Cline, Roo Code, Continue, Bolt.new/diy, Lovable, v0, Sweep, SWE-agent, Goose — architecture, context management, tool use, novel patterns, leaked prompts
type: reference
---

## Research coverage period
March 2025 – March 2026. Compiled March 2026.

## Agents covered
Cline (formerly Claude Dev), Roo Code (Cline fork), Continue, Bolt.new/bolt.diy, Lovable, v0 (Vercel), Sweep, SWE-agent (Princeton), Goose (Block/Square).

NOT covered here (separate memory file): Devin, Claude Code, OpenHands, Cursor, Windsurf, Aider, OpenAI Codex.

---

## Cline (VS Code)

**Architecture:** VS Code extension with Plan/Act mode separation. PromptRegistry singleton manages model-specific variants via family fallback (e.g., "claude-4" → "claude"). TemplateEngine uses `{{PLACEHOLDER}}` syntax for runtime injection. Components (agent role, MCP integration, tool instructions, act_vs_plan) are modular and can be enabled/disabled per model variant.

**Agent loop:** Plan mode = exploratory (read many files, build context, produce plan). Act mode = execution (tools active, commands run). Modes are distinct system prompt configurations, not just state flags.

**Context management:**
- Memory Bank: markdown files at repo level (projectbrief.md, productContext.md, activeContext.md, systemPatterns.md, techContext.md, progress.md). A community-created instruction set — not a built-in feature, but so widely adopted it's effectively standard.
- `/newtask` tool: packages plan + decisions + relevant files + next steps into a fresh context window. Clean handoff mechanism between phases.
- Focus Chain: todo list generated at task start, reinjected on a cadence to prevent context drift.
- Auto Compact: summarises bloated history. `/smol` for manual in-place compression.
- Context Window Progress Bar (visual): formula `maxAllowedSize = Math.max(contextWindow - 40_000, contextWindow * 0.8)`. Makes invisible limits visible.
- Checkpoints: file snapshots. Message editing + restore lets users rewind conversations AND workspace state.

**Tool use:** File editing, terminal, browser (via MCP), MCP servers for everything else. Deep Planning mode front-loads clean context before implementation. Agentic exploration (read files dynamically) preferred over RAG vector search — founders say this "works much better" and RAG "distracts the model."

**System prompt:** Publicly disclosed. Source on GitHub: `cline/cline/src/core/prompts/system-prompt`. XS variant for small context models. Plan mode prompt variant optimized per model family.

**Novel patterns:**
- PromptRegistry with model-family fallback is a clean way to maintain model-specific tuning without prompt duplication.
- Memory Bank as a community-developed convention (not product feature) that became de facto standard — implies user-space context patterns can be more important than built-in mechanisms.
- `/newtask` as clean-context handoff tool is generalizable.

---

## Roo Code (Cline fork)

**Architecture:** Three-layer: Extension Host (Node.js) + Webview UI (React) + External Services. Monorepo with pnpm + Turborepo. Extension Host and Webview communicate via VS Code `postMessage` API with discriminated union types + monotonic sequence counters (preventing stale updates).

**Boomerang Tasks / Orchestrator mode:**
- Stack-based task execution: `ClineProvider` maintains a LIFO stack (`clineStack`) of active AI tasks with parent-child relationships.
- When orchestrator spawns subtask: parent PAUSES, subtask runs in isolation with its own conversation history.
- Context flows DOWN via explicit instructions at subtask creation. Only the completion SUMMARY flows UP to parent.
- Orchestrator mode intentionally lacks file-read/execute capabilities — prevents context pollution from implementation details.
- Built-in modes: Orchestrator, Architect (plan only, no code edits), Code, Debug, Ask. User-customizable modes.

**Multi-diff editing:** Experimental strategy applies multiple diff edits simultaneously rather than one at a time. Diff-based (not full file rewrite) to save tokens.

**Context management:**
- @mentions: `@file`, `@folder`, `@problems`, `@git-changes`, `@terminal`, `@url` for explicit context inclusion.
- Semantic indexing: CodeIndexManager with Qdrant vector database for code search.
- Context condensation: auto-summarises when approaching model context limits.
- Dual storage: `.roo-code/tasks/` (cross-instance safe) + VS Code GlobalState (backward compat). Write-through debounced updates.

**Novel patterns:**
- LIFO task stack = explicit orchestrator/worker separation implemented as a data structure, not just prompt engineering.
- Summary-only context propagation upward = context budget preserved at orchestrator level.
- Role-based mode system (Architect = read-only, Code = write) prevents accidental cross-mode contamination.

---

## Continue

**Architecture:** Three-process messaging architecture: core (logic), extension (IDE integration), gui (React/Redux UI). All TypeScript. Communication via defined message protocols in `core/protocol`.

**Pivot (2025):** Repositioned from "AI code assistant" to "quality control for your software factory" — source-controlled AI checks, enforceable in CI. Rules system is the core primitive now.

**Rules system:**
- `.continue/rules/` markdown files in repo. Version-controlled, shareable.
- Rules run as full AI agents on every PR — flag only what they're told to catch, suggest one-click fixes.
- Continue Hub: public/private marketplace for rules. Org-scoped sharing. Slug format `owner/item-name`.
- CI enforcement: GitHub Actions workflow sends PR diff + rules to LLM → parses response → posts review comments on PR.

**Context providers (@mentions):**
- `@file`, `@codebase`, `@url`, `@terminal`, `@problems`, etc.
- HTTP provider interface: POST to URL, returns `{name, description, content}` ContextItems.
- MCP servers are now the recommended extension mechanism (custom provider API deprecated).
- `@codebase` deprecated in favour of agent-mode tools that explore the codebase dynamically.

**Agent mode:** Equips model with file exploration + search tools. Agent decides what context to fetch (same philosophy as Cline).

**Novel patterns:**
- Rules-as-CI-agents is architecturally novel: the same natural-language rule file runs in the IDE for the developer AND in CI for the team. Single source of truth.
- Continue Hub as a rule marketplace enables team-level AI behavior standardisation without custom engineering.
- The pivot from "individual assistant" to "team quality enforcement" is a distinct product position worth noting.

---

## Bolt.new / Bolt.diy

**Architecture:** Three-tier: frontend (Remix), AI provider layer (LLM API), WebContainer runtime (in-browser Node.js via `@webcontainer/api`). bolt.diy = official open-source fork supporting 19+ LLM providers.

**WebContainer:**
- In-browser Node.js sandbox. Virtual filesystem at `/home/project` (in-memory).
- Custom "BoltShell" executes npm/build scripts. Auto port-forwarding for dev server previews.
- Constraints: no native binaries, no pip/git (uses isomorphic-git instead). Persistent across session.

**Agent loop (streaming-first):**
1. User message + file context → `/api/chat`
2. Server-side context optimization (history summarisation, relevant file selection)
3. LLM streams response via SSE
4. Client-side `EnhancedStreamingMessageParser` detects structured XML artifacts IN REAL TIME during stream
5. Actions queue into global `ActionRunner` pipeline
6. `ActionRunner` executes sequentially in WebContainer

Key: actions execute BEFORE the full LLM response completes (parse during stream, execute immediately).

**ActionRunner:**
- Global promise chain: `#globalExecutionQueue = globalExecutionQueue.then(() => callback())` — serialises all operations.
- File-level locks prevent race conditions. Locked files show visual indicator.
- Each artifact gets its own ActionRunner instance.

**Artifact format (XML-like):**
```
<boltArtifact>
  <boltAction type="file" filePath="...">content</boltAction>
  <boltAction type="shell">npm install</boltAction>
  <boltAction type="start">npm run dev</boltAction>
</boltArtifact>
```

**State management:** Nanostores for domain stores (files, editor, terminal, previews) coordinated via WorkbenchStore.

**Novel patterns:**
- Streaming artifact execution (parse + execute before response completes) = responsive UX that appears instantaneous.
- Serialised global execution queue prevents race conditions without complex locking.
- Server-side context optimization before LLM call (not just client-side) reduces token waste.
- Output-format-as-action-spec (XML artifacts) is cleaner than tool calls for streaming scenarios.

---

## Lovable

**Architecture:** React/Vite/Tailwind/TypeScript frontend. No direct backend execution (no Python/Node) — Supabase-only for backend functionality. Live preview iframe alongside chat window.

**Agent mode (GA July 2025, default for all new users):**
- Sequential workflow: interpret → explore codebase → uncover missing context → make changes → auto-fix issues → wrap up with summary.
- New action tools: codebase search, on-demand file reading, log/network inspection, web search, image generation.
- Reports "90% reduction in build error rates" after switch to iterative agentic approach.
- 91% reduction in "unwanted changes" (single-source attribution).

**System prompt (leaked, confirmed):**
- Discussion-default: treats all input as planning unless explicit action verbs ("implement", "create") appear.
- Context management hierarchy: check "useful-context" section → current-code blocks → search/read additional files. Never read files already in context.
- Batch tool calls: "invoke all relevant tools simultaneously" — parallel where possible.
- Design-system-first: all styling from centralized tokens (index.css, tailwind.config.ts). "NEVER write ad hoc styles in components."
- Constraint repetition as guardrail: key rules stated multiple times across sections for reinforcement.
- Conciseness requirement: responses under 2 lines unless detail requested.
- Debugging: "Use debugging tools FIRST before examining or modifying code" — logs/network before code analysis.

**UX patterns:**
- Visual Edits: click-to-modify elements without prompts (reduces prompt writing).
- Select & Edit: click element + describe change.
- Real-time preview iframe updates as code changes.

**Novel patterns:**
- "Discussion-default" mode prevents premature execution — must see action verbs to shift into build mode.
- Constraint repetition as behavioral reinforcement (explicit technique for LLM prompt reliability).
- Debugging-tools-first ordering in system prompt = agents check observable state before modifying code.

---

## v0 (Vercel)

**Architecture:** UI generation agent. Tech stack locked: Next.js 14+ App Router, React 18+, TypeScript, Tailwind CSS, shadcn/ui, Lucide React icons. No Pages Router, no custom CSS, no ORMs unless requested.

**System prompt (leaked Nov 2024, multiple versions on GitHub):**
- Vercel CTO confirmed authenticity, stated "the prompt without the models, evals, and UX is of limited value."

**CodeProject structure:**
- Single CodeProject block per response, consistent project ID across edits.
- Files in kebab-case. Predefined stable file set (layouts, components, hooks) — not regenerated on every response.
- File-level operations: `<DeleteFile>`, `<MoveFile>` for precise modifications.

**QuickEdit mechanism:**
- "v0 DOES NOT need to rewrite all files for every change" — edit only relevant files.
- Surgical modifications: identify target sections, preserve surrounding context, apply focused changes.

**Thinking tags:**
- Mandatory `<Thinking>` tags BEFORE generating any CodeProject.
- Plans: project structure, styling, images/media, formatting, frameworks/libraries, caveats.
- Chain-of-thought before code output.

**Post-response suggestions:** 3–5 ranked follow-up actions ranked by "ease and relevance."

**Feature flag system:** Prompt includes a 90+ item feature flag list — context-sensitive behaviour without prompt duplication.

**Refusal pattern:** Single hardcoded `REFUSAL_MESSAGE` string — prevents variation/hedging in harmful content responses.

**Novel patterns:**
- Mandatory `<Thinking>` before every CodeProject = enforced planning, not optional CoT.
- Feature flag list as a context-sensitivity mechanism at prompt level — enables same model to behave differently across product tiers.
- Ranked post-response suggestions = outcome-oriented UX (moves user forward, not just answers query).
- Stable CodeProject ID across edits = addressable, consistent artifact model (not conversation-drift-prone).

---

## Sweep

**Architecture:** GitHub App → issue trigger → search/plan/code pipeline → PR creation. No IDE. Also JetBrains plugin (separate architecture).

**Search/plan/code pipeline:**
1. Issue received
2. Embedding search + lexical TF-IDF search to identify relevant files
3. AST bipartite graph: files ↔ code entities (functions, classes, methods). Removes zero-in-degree nodes (external imports) to reduce noise — reduces edges from ~680 to ~102.
4. Planning at 10-15k context window (GPT-4 "lost-in-the-middle" degrades after 20k)
5. Decision: prune irrelevant files, expand promising directories
6. Code generation per file
7. PR creation

**Context window strategy (key insight):** Quality peaks at 10-15k tokens. Sweep makes planning decisions at that threshold, not at max context. After planning, prunes context and expands new targets — iterative search tree through the codebase.

**Long file handling:** Files >1,500 lines → Concrete Syntax Trees to extract relevant function/class spans only.

**Dual search:** Lexical (TF-IDF with n-grams, handles camelCase/snake_case/PascalCase) + semantic (embeddings). Lexical catches identifiers that vector search misses.

**Failure handling:** "Restart the whole process is the most pragmatic way" for failed agents. No complex recovery — linear execution, easier to restart. ~80% of failures from non-prompt issues (tool errors, environment).

**Novel patterns:**
- 10-15k planning window as explicit design constraint (not just "use more context" = use better context).
- Bipartite graph + zero-in-degree pruning = noise reduction without expensive full-repo indexing.
- Dual search (TF-IDF n-grams + embeddings) catches identifier patterns that pure vector search misses.
- Plan decomposes to (file, instructions) pairs — file-level granularity, not function-level, avoids over-specification.

---

## SWE-Agent (Princeton) + mini-SWE-agent

**Architecture:** GitHub issue → LM agent with custom ACI (Agent-Computer Interface) → patch + PR. NeurIPS 2024.

**ACI — the core contribution:**
The key insight: LM agents are a NEW category of end user with different needs than humans. Existing CLIs/UIs are designed for humans. Custom ACI designed for LM agents = 12.5% pass@1 on SWE-bench (vs << 5% for raw shell access).

**Custom tools built:**
- `find_file`, `search_file`, `search_dir` — output SUMMARIES not raw results (avoids context flooding).
- File viewer with windowing: shows file in configurable-size windows with line numbers. Allows scrolling. Prevents "show entire 10,000-line file" problem.
- File editor with LINTER INTEGRATION: after every edit, linter runs and syntax errors are returned to agent in same feedback loop. Agent sees "Edit introduced 2 syntax errors: line 45..." immediately.
- `open`, `goto <line>`: navigation within files.
- History processor: keeps context concise by summarising/trimming old tool outputs.

**Key behavioral insight (from paper):** Agents naturally converge to: (1) reproduce issue → (2) localise to specific lines → (3) edit-execute loop. Interface should be designed around this pattern, not general-purpose CLI.

**mini-SWE-agent (2025):**
- 100 lines of Python. No custom tools. Bash only.
- 74% on SWE-bench verified (with capable models like Claude Opus 4.x).
- Stateless: every action via `subprocess.run` — completely independent. No persistent shell session.
- No tool-calling interface needed — any model works.
- Insight: specialized scaffolding matters less than model capability. With sufficiently capable models, bash ≥ custom ACI.

**Trivial sandboxing:** Swap `subprocess.run` with `docker exec`. No state to manage.

**Novel patterns:**
- ACI as a design discipline: custom interfaces for LM agents, not adapted human interfaces. Generalises beyond coding.
- Linter integration in edit tool = synchronous error feedback loop (agent doesn't wait for test run to discover syntax errors).
- Summary-mode search outputs: `search_dir` returns "found N matches in K files" + top excerpts, not raw grep dump.
- mini-swe-agent's "capability over scaffolding" thesis: a single bash tool + capable model outperforms elaborate tooling + weaker models.

---

## Goose (Block/Square)

**Architecture:** Rust + TypeScript. Three components: Interface (CLI or desktop app) → Agent (core logic) → Extensions (MCP servers). Agent runs the interactive loop, Extensions provide tools via MCP.

**Agent loop:**
1. Human request
2. LLM receives full tools list
3. Model produces JSON tool calls
4. Goose executes tool calls via extensions
5. Results returned to model
6. Context revision (irrelevant content removed)
7. Final response

Errors are returned to model as tool responses (not thrown) — agent can self-correct.

**Context management:**
- Auto-compaction at 80% token limit (both CLI and Desktop).
- Strategies: summarize (default), truncate, clear, prompt.
- "Find and replace instead of rewriting large files" as explicit efficiency principle.
- Algorithm removes "old or irrelevant content" from context during revision step.

**MCP-first philosophy:**
- All extensions are MCP servers. 3,000+ MCP servers available.
- Goose = MCP host. Extensions = MCP servers. Unified protocol, no proprietary tool format.
- Contributed to Linux Foundation Agentic AI Foundation (Dec 2025) alongside Anthropic MCP + OpenAI AGENTS.md.

**Recipes system (evolving):**
- Currently: YAML/text files with prompts for reusable workflows.
- Roadmap: full agentic automation flows with sub-recipe composition.
- Break complex automations into sub-recipes for maintainability.
- Session sharing issue (identified Aug 2025): single shared Agent for all sessions causes interference via shared ExtensionManager. Proposal for per-session agents pending.

**Multi-model:** Supports 25+ LLM providers. Multi-model configuration for cost/performance optimization.

**Novel patterns:**
- MCP-native from day one: no proprietary tool format = ecosystem portability (agents can move between Goose, Claude Desktop, Cursor, Zed with same extensions).
- Error-as-tool-response (not exception) = agent can recover without special error handling paths.
- Context revision step WITHIN loop (step 5 before final response) = proactive context trimming, not just emergency compaction.

---

## Cross-cutting steal-worthy patterns

### 1. Summary-output tools (SWE-agent, Sweep)
Search tools should return summaries/counts + top results, NOT raw dump. Prevents context flooding. Generalises to any retrieval tool.

### 2. Linter-in-edit-loop (SWE-agent)
Synchronous syntax validation after every edit returned as part of tool output. Agent gets error feedback in same turn as edit, not after test run.

### 3. Discussion-default, action-verb activation (Lovable)
Default to planning/discussion mode. Require explicit action verbs to enter execution mode. Prevents premature code generation from ambiguous prompts.

### 4. Mandatory `<Thinking>` before generation (v0)
Force a planning step before ANY code artifact. Chain-of-thought is not optional — it's enforced by prompt structure.

### 5. 10-15k planning window (Sweep)
Make major decisions when context is 10-15k tokens, not at max. Quality degrades above 20k (LLM "lost in middle"). Prune + re-expand iteratively rather than dump everything in.

### 6. Stateless execution (mini-SWE-agent)
`subprocess.run` per action = trivially sandboxable, trivially parallelisable, no shared state bugs. Accept the statelessness cost (no persistent env) for the simplicity gain.

### 7. Context boundary at orchestrator level (Roo Code Boomerang)
Orchestrator receives only completion summaries from workers. LIFO stack with context isolation. Prevents orchestrator context from inflating with implementation details.

### 8. Streaming artifact execution (Bolt.new)
Parse structured artifacts during LLM stream → execute immediately. User sees results before response completes. Dramatically improves perceived responsiveness.

### 9. Rules-as-CI-agents (Continue)
Same rule file = IDE hint for developer + CI enforcement for team. Single source of truth for coding standards that works at both individual and organisation scale.

### 10. Constraint repetition as behavioral guardrail (Lovable)
Key restrictions stated multiple times in different sections. Explicit technique to improve LLM compliance with hard constraints in long prompts.

---

## Source quality notes
- `cline.bot/blog` and `docs.cline.bot`: official, high technical detail
- `latent.space/p/cline`: founder interview, good architectural insight
- `deepwiki.com/stackblitz-labs/bolt.diy`: high-quality auto-generated from source, reliable
- `deepwiki.com/RooCodeInc/Roo-Code`: same, reliable for internal architecture
- `gist.github.com/hiddenest/992eb025dc342983503e8edb83ad3b7b`: v0 system prompt gist (Jun 2025 version)
- `github.com/x1xhlol/system-prompts-and-models-of-ai-tools`: comprehensive leaked prompts repo (Lovable, v0, Devin, etc.)
- `github.com/sweepai/sweep/blob/main/docs/pages/blogs/ai-code-planning.mdx`: Sweep's own technical blog in repo
- `e2b.dev/blog/sweep-founders-share-learnings-from-building-an-ai-coding-assistant`: Sweep founder retrospective
- `arxiv.org/abs/2405.15793`: SWE-agent NeurIPS 2024 paper (abstract level accessible)
- `github.com/SWE-agent/mini-swe-agent`: mini-swe-agent README, very clear
- `block.github.io/goose/docs/goose-architecture/`: Goose official architecture docs
