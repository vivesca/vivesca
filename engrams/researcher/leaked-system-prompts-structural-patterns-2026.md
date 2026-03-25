---
name: Leaked/Published System Prompts — Structural Patterns (Mar 2026)
description: Cross-agent analysis of structural patterns from leaked/published system prompts of Cursor, Claude Code, Cline, v0, Bolt, Manus, Lovable, Devin, Windsurf, ChatGPT — March 2025–March 2026
type: reference
---

## Primary source repositories
- x1xhlol/system-prompts-and-models-of-ai-tools (36 tools, 30K+ lines)
- EliFuzz/awesome-system-prompts (versioned, dated leaks)
- Piebald-AI/claude-code-system-prompts (CC v2.1.78, Mar 17 2026, 110+ strings)
- jujumilk3/leaked-system-prompts (dated snapshots per tool)
- elder-plinius/CL4R1T4S (ChatGPT, Gemini, Grok, Claude, Cursor, Devin)

## Per-tool structural notes

### Claude Code (Anthropic, v2.1.78 Mar 2026)
- NOT a monolithic prompt: 110+ conditional strings dynamically assembled
- 5 categories: Agent Prompts (~25), Data Prompts (~30), System Prompts (~80), System Reminders (~40), Tool Descriptions
- Context-conditional loading: environment, config, plan mode, subagent role trigger different strings
- 18 builtin tool descriptions — large, vary by availability
- System Reminders inject real-time: file mods, hook results, memory contents, token usage
- Security monitor (2675 + 2966 tokens) evaluates tool calls against block/allow rules BEFORE execution
- Parallel fork pattern: "reading fork output mid-flight" explicitly prohibited
- Memory: "Dream memory consolidation" + "Session memory update instructions"
- Plan modes: 5-phase enhanced / iterative (with user interviews) / subagent simplified — each different token budget
- Minimalist philosophy hardcoded: avoid over-engineering, prefer editing over creating, skip premature abstractions
- Tool preference hierarchy: Read over cat, Glob over find, Edit over sed
- Security URL allowlisting for WebFetchTool
- Dual-pass bash validation: command prefix extraction + file path impact analysis

### Cursor (March 2025 gist, sshh12)
- 7 sections: Identity, Communication Principles (5 rules), Tool Architecture (12 tools), Tool Calling Discipline, Code Modification Strategy, Search/Info Gathering, Debugging
- Two-model architecture: main agent proposes edits; secondary (weaker) model applies them
- Dynamic context attachment: files open, cursor position, recent views, edit history, linter errors injected automatically
- Semantic edit markers: `// ... existing code ...` around changes (not line numbers) — avoids offset drift
- Hard rule: NEVER output code to USER, use edit tools instead
- Max 3 linter error fix attempts, then ask user
- Self-sufficiency bias: "Bias towards not asking the user for help if you can find the answer yourself"
- NEVER mention tool names to users (abstraction layer between tool names and communication)
- Tool calling: only call available tools, follow schema exactly, "only call tools when necessary"

### Cline (open source, VS Code, ~59K chars / 12K tokens)
- Explicit dual-mode architecture: Plan Mode (strategize/discuss) vs Act Mode (execute)
- 12 tools defined with XML-style invocation syntax: `<read_file><path>...</path></read_file>`
- Sequential confirmation loop: one tool per message, requires user approval before proceeding
- Completion gate: tasks end with `attempt_completion` — forces explicit completion declaration
- MCP integration section: how to create/modify/integrate MCP servers
- File edit distinction: `write_to_file` (create/overwrite) vs `replace_in_file` (targeted edit)
- Tool documentation: header, delimiter, markdown, examples per tool

### Bolt.new (StackBlitz, Oct 2024 leak)
- XML-based hierarchical structure: `<system_constraints>`, `<code_formatting_info>`, `<message_formatting_info>`, `<diff_spec>`, `<artifact_info>`
- `<artifact_info>` contains `<artifact_instructions>` with 14 rules using CAPS emphasis
- Constraint-first architecture: environment limits declared BEFORE execution instructions
- GNU unified diff format for file modifications
- Streaming artifact: parse + execute during LLM stream (before response completes) — ActionRunner promise chain
- Anti-verbosity: "DO NOT be verbose and DO NOT explain anything unless asked", "NEVER use the word 'artifact'"
- Holistic artifact generation: one comprehensive artifact with all steps (not incremental)
- Action ordering is "VERY IMPORTANT": install deps before use, create files before executing
- WebContainer constraint: no native binaries, browser-native code only (JS/WASM)

### Lovable (mid-2025 leak)
- Custom XML output tags: `<lov-code>`, `<lov-thinking>` (optional, shows reasoning), `<lov-write>`, `<lov-error>`, `<lov-success>`
- One `<lov-write>` block per file maximum
- Three operational modes: Discussion (default), Implementation (triggered by action verbs: "create", "add", "code"), Debugging
- Example-driven instruction: `<examples>` sections with `<user_message>`/`<ai_message>` pairs — primary behavioral mechanism
- Ultra-concise output: "Answer concisely with fewer than 2 lines of text (not including tool use)"
- Hard rules: NEVER partial implementations, NEVER non-existent file references, ONE new file per component/hook (50 lines max target)
- Immediate build constraint: "all edits will immediately be built and rendered — NEVER make partial changes"
- Design-system-first: all styles via design tokens in index.css/tailwind.config.ts — direct classes forbidden
- First-interaction special instructions section (separate from main)
- "Not every interaction requires code changes" — discussion-first philosophy

### v0 (Vercel, March 2025 leak, 2200+ lines)
- Specialized identity: UI generation assistant (not general-purpose)
- Two-part structure: Operational Guidelines + Capabilities/Domain Knowledge
- Custom component tags: `<CodeProject id="...">`, `<QuickEdit file="..." />`, `<DeleteFile />`, `<MoveFile />`, `<AddEnvironmentVariables names={[...]} />`
- Inline footnote citations: `[^index]` (general) + `[^vercel_knowledge_base]` (Vercel-specific)
- Do/Don't paired examples with explicit contrast
- Rules use CAPS for emphasis: "v0 MUST use kebab-case", "v0 DOES NOT output SVG for icons"
- Rationale included with restrictions (why, not just what)
- Accessibility mandated as default (WCAG 2.1): semantic HTML, ARIA, keyboard nav, 44px touch targets
- QuickEdit: surgical modifications without full regeneration — preserves design context

### Devin (Cognition, Aug 2025 leak)
- Three explicit modes: Planning (investigation), Standard (execution + iteration), Edit (file-only, post-approval)
- `<think>` scratchpad mandatory before: git ops, mode transitions, task completion declaration, after image analysis
- Communication protocol: speak only when: env issues, deliverables, critical info, permissions needed
- `block_on_user_response` values: BLOCK (unresolvable), DONE (complete), NONE (continue)
- Truthfulness hardcoded: no fake sample data, no mocking when real data inaccessible, never modify tests
- LSP-first for code understanding: use Language Server Protocol over grep/find
- Categorized tool systems: Reasoning, Shell, Editor, Search, LSP, Browser, Deployment, Git, MCP
- Environment issues: `<report_environment_issue>` — report, don't fix autonomously
- Multi-command batching: sequential without waiting for intermediary results
- POP QUIZ backdoor: section that lets instructions override previous (security vulnerability)

### Manus (March 2025 leak)
- Hierarchical document structure (no XML tags): Capabilities + Prompting Guide + Agentic Loop
- 6-step agentic loop: Analyze Events → Select Tools → Wait for Execution → Iterate → Submit Results → Enter Standby
- "Choose only one tool call per iteration, patiently repeat" — single-action-per-loop pattern
- todo.md: continuously updated task checklist — attention-window trick for long tasks
- External memory: write intermediate results to workspace files, not context
- CodeAct paradigm: executable Python code as primary action mechanism (not fixed tool tokens)
- Structured error handling: 3 failures → pivot to alternative approach → escalate
- Section-based governance: `<tool_use_rules>`, `<browser_rules>`, `<writing_rules>`
- "Avoid using pure lists and bullet points format" in outputs

### Windsurf Cascade (Dec 2024 leak)
- "AI Flow paradigm" — operates independently and collaboratively
- Similar structure to Cursor: identity, tool framework, code change guidelines, debugging, communication
- NEVER output code to user unless requested (same as Cursor)
- Single edit per turn maximum
- Production Windsurf: does NOT use the "mother's cancer treatment" motivational prompt (that was R&D/experimental only — confirmed by Windsurf engineer)

### ChatGPT/GPT-5 (2025 leaks)
- Identity block: "You are ChatGPT...Knowledge cutoff: 2024-06...Personality: v2"
- 6 tools: bio (persistent memory, plain text only), canmore (canvas editing), image_gen, python (Jupyter), web (search+URL), deprecated browser
- Memory restrictions: explicit excluded categories list; plain text only (never JSON) for bio tool
- "Do not end with opt-in questions or hedging closers" — anti-hedging directive
- "Ask at most one necessary clarifying question at the start, not the end"
- Search activation rules: 4 specific scenarios that trigger web search (doesn't default to it)
- file_search uses dual queries: precision (exact definitions) + recall (short keywords)
- ALWAYS REWRITE CODE TEXTDOCS using single update with ".*" pattern — prescriptive instruction style
- "Bias to ship" philosophy: executes rather than seeks permission

## Cross-cutting structural patterns

### Pattern 1: Constraint-First Architecture
Bolt, Cline, Manus all declare environment limits BEFORE execution instructions. Users/model know what's impossible before attempting.

### Pattern 2: Anti-Verbosity as Explicit Rule
Bolt, Lovable, Cursor, Cline all explicitly forbid unnecessary explanation. Lovable: <2 lines response text. Bolt: "DO NOT be verbose." Claude Code: "One word answers are best."

### Pattern 3: NEVER Output Code Directly
Cursor, Windsurf both use identical rule: NEVER output code to USER, use edit tools. Forces tool use over inline generation.

### Pattern 4: One Tool / One Action Per Turn
Cline (requires user confirmation), Manus (single tool call per loop iteration), Devin (think before git ops). Slows execution, improves observability and rollback.

### Pattern 5: Custom XML Tags as Output Protocol
Bolt: `<boltArtifact>/<boltAction>`. Lovable: `<lov-code>/<lov-thinking>/<lov-write>`. v0: `<CodeProject>/<QuickEdit>`. Creates structured machine-parseable output AND guides model attention.

### Pattern 6: Explicit Mode Separation
Cline: Plan/Act. Devin: Planning/Standard/Edit. Lovable: Discussion/Implementation/Debugging. Forces deliberate phase transitions rather than blending thinking and acting.

### Pattern 7: CAPS Emphasis for Non-Negotiable Rules
Bolt: "ULTRA IMPORTANT", "CRITICAL". v0: "MUST", "DOES NOT". Cline: "ABSOLUTELY REQUIRED". Creates visual hierarchy in dense text.

### Pattern 8: Example-Driven Behavioral Specification
Lovable: entire `<examples>` sections with user/AI message pairs. v0: Do/Don't paired examples. More reliable than abstract rules.

### Pattern 9: Modular Conditional Loading (Claude Code)
Not one prompt — context-sensitive assembly of 110+ components. Different modes get different token budgets. Utility functions have their own specialized prompts.

### Pattern 10: Security Monitor as Separate Layer
Claude Code: dedicated security evaluation (5000+ tokens) evaluating every tool call against block/allow rules BEFORE execution. Pre-execution validation layer.

### Pattern 11: Tool Preference Hierarchy
Claude Code specifies preferred tools over shell: Read over cat, Glob over find. Prevents model defaulting to general bash commands when native tools exist.

### Pattern 12: Two-Model Architectures
Cursor: main agent proposes, secondary model applies edits. Claude Code: Haiku for parsing/lookups, Sonnet for reasoning. Model routing within a single agent interaction.

### Pattern 13: Self-Sufficiency Bias
Cursor: "Bias towards not asking the user for help if you can find the answer yourself." Same principle in Devin. Reduces unnecessary interruptions.

### Pattern 14: Completion Gates
Cline: `attempt_completion` tool required to finish. Devin: `block_on_user_response=DONE`. Forces explicit declaration rather than trailing off.

### Pattern 15: Rationale Inclusion
v0 includes WHY after each restriction. Helps model generalize to edge cases (not just follow rules blindly). Research shows this improves compliance.

## Methodology notes
- GitHub raw URLs for leaked text files often 404 — use rendered blob pages or gist links instead
- jujumilk3/leaked-system-prompts has dated snapshots — reliable for temporal comparison
- Piebald-AI/claude-code-system-prompts most authoritative for Claude Code (version-tracked)
- Windsurf "mother's cancer" prompt: confirmed R&D only, NOT production. Flag as common misinformation.
- Simon Willison blog (simonwillison.net) is the best single analysis source for leaked prompts
