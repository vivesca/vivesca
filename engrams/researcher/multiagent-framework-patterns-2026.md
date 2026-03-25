---
name: Multi-Agent Framework Technical Patterns (Mar 2026)
description: Deep technical patterns from Google ADK, Microsoft AutoGen/Magentic-One, LangGraph, CrewAI, OpenAI Agents SDK, Claude Agent SDK — orchestration, state, planning, error recovery, HITL, observability, and eval. Researched March 2026.
type: reference
---

## Research scope

Covers Google ADK, Microsoft AutoGen / Magentic-One / Agent Framework, LangGraph 1.x, CrewAI Flows/Crews, OpenAI Agents SDK, Claude Agent SDK, plus cross-cutting topics: agent engineering as discipline, observability, eval frameworks.

---

## Google ADK — 8 documented orchestration patterns

**Key primitives:** `SequentialAgent`, `ParallelAgent`, `LoopAgent`, `LlmAgent`, `AgentTool`

### Patterns
1. **Sequential Pipeline** — `SequentialAgent` chains agents; `output_key` writes to shared `session.state`; downstream agents read via `{key}` placeholders.
2. **Coordinator/Dispatcher** — Central `LlmAgent` with sub-agent descriptions; ADK AutoFlow mechanism handles routing via LLM.
3. **Parallel Fan-Out/Gather** — `ParallelAgent` runs concurrently; agents write to unique state keys; `InvocationContext.branch` provides memory isolation per child.
4. **Hierarchical Decomposition** — Agents wrapped in `AgentTool` become callable tools for parent agents; results return as tool output.
5. **Generator-Critic** — Sequential pair; Critic reads `output_key` state; `condition_key` signals pass/fail; `LoopAgent` enforces loop.
6. **Iterative Refinement** — `LoopAgent` + `escalate=True` in `EventActions` for early exit; `max_iterations` as backstop.
7. **Human-in-the-Loop** — ApprovalTool pauses execution; execution resumes after external system signals human decision.
8. **Composite** — Combine above; e.g. Coordinator → Parallel → Generator-Critic.

### State management
- Shared `session.state` = shared whiteboard across all agents in invocation
- `temp:` prefix for turn-specific intra-agent data
- `context.state['key'] = data` for passive writes; `output_key` for automatic final-response persistence
- `InvocationContext.branch` for context isolation in parallel branches (shared state, distinct paths)

### AgentTool vs sub_agents distinction
| | Sub-Agents | AgentTool |
|---|---|---|
| Invocation | Dynamic via LLM transfer or workflow | Explicit function call |
| Control | Orchestrated | Tool-like, parent decides when |
| State | Same context passed directly | Results returned as tool output |

### Agent communication
Three modes: (1) Shared session state (passive), (2) LLM-driven `transfer_to_agent` (dynamic routing), (3) `AgentTool` explicit invocation (synchronous, controlled).

### Sources
- google.github.io/adk-docs/agents/multi-agents/
- developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

---

## Microsoft Magentic-One / AutoGen / Agent Framework

### Magentic-One architecture (the canonical Microsoft multi-agent pattern)

**Outer loop:** Orchestrator updates Task Ledger (facts + guesses + plan); triggers replanning when progress stalls.
**Inner loop:** Orchestrator updates Progress Ledger (self-reflection on task completion state); assigns next subtask to specialist.

**Specialist agents:** WebSurfer (accessibility tree browser), FileSurfer, Coder, ComputerTerminal (code execution).

**Error recovery:** Adaptive replanning — if progress stalls for N inner-loop iterations, outer loop fires; new plan generated from current state of Task Ledger.

**Data flow:** All results flow back to Orchestrator, which updates both ledgers before deciding next action.

### AG2 (AutoGen fork, community-led since Nov 2024)

Key patterns supported: swarms, group chats, nested chats, sequential chats, custom orchestration via registered reply methods.

**Group chat state:** All agents share the same conversation thread; no state isolation by default — a limitation vs ADK/LangGraph.

**State management gap:** AutoGen's Team abstraction has NO built-in checkpointing; requires external implementation.

### Microsoft Agent Framework (unification of AutoGen + Semantic Kernel)

**Adds to AutoGen:** Long-running durability, checkpointing, YAML-declarative workflows, human approval gates.

**Human approval gates:** Tools marked `requires_human_approval`; framework automatically emits pending approval requests routable to UI or queue.

**Orchestration modes:** Sequential, Concurrent, Group Chat, Handoff, and Magentic (manager + dynamic task ledger).

**State:** Agents "hydrate" from checkpoints after interruption; state isolation between executor-local and shared state.

**Open standards:** MCP, A2A, OpenAPI — pluggable memory across Redis, Pinecone, Weaviate.

### Sources
- microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/magentic-one.html
- devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework-the-open-source-engine-for-agentic-ai-apps/
- learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/

---

## LangGraph 1.x (stable since Oct/Nov 2025, current v1.1.2 Mar 12 2026)

### State machine primitives
- `StateGraph` + `TypedDict` state schema + reducer functions
- Nodes, edges, conditional edges
- `Annotated` types control how state fields merge on update

### Checkpointing
- After every node execution, full graph state serialized to checkpointer
- Built-in: InMemory, SQLite, PostgreSQL, Redis (cloud)
- State restoration enables arbitrary replay from any prior checkpoint

### HITL interrupt mechanism (key technical detail)
- `interrupt()` raises a special exception; runtime catches, serializes state, waits indefinitely
- Resume via `Command(resume=value)` with same `thread_id`
- **Critical gotcha:** Node re-executes from beginning on resume — any code before `interrupt()` runs TWICE. Pre-interrupt operations must be idempotent.
- Static interrupts (`interrupt_before`/`interrupt_after` on nodes) = for debugging only, not production HITL
- Multiple simultaneous interrupts (parallel branches) = resume as dictionary keyed by interrupt ID

### Streaming
- `stream_mode=["messages", "updates"]` with `subgraphs=True` for simultaneous message streaming + interrupt detection
- LangGraph 1.1 added `version="v2"` streaming with full type safety

### Multi-agent subgraphs
- Subgraphs as nodes — one graph can call another as a node
- Parent state ↔ subgraph state translation handled at boundary
- `subgraphs=True` in stream enables nested trace visibility

### Error recovery
- Retry policies per-node configurable
- Checkpoints enable resume after infrastructure failure, not just HITL

### Known production issues
- Infinite loop risk with unmanaged sub-agents (token burn)
- `create_react_agent` from `langgraph.prebuilt` deprecated → use `langchain.create_agent`
- CVE-2025-64439: RCE in checkpoint deserialization — patch to checkpoint v3.0.0

### Sources
- docs.langchain.com/oss/python/langgraph/interrupts
- blog.raed.dev/posts/langgraph-hitl (double execution problem)
- latenode.com/blog LangGraph 2025 architecture guide

---

## CrewAI — Dual architecture: Crews + Flows

### Crews (autonomous team collaboration)
- Agents have true agency — decide when to delegate, when to ask
- Roles: Manager (oversight), Worker (execution), Researcher (information)
- Manager agents can dynamically reassign tasks mid-execution

### Flows (event-driven production orchestration, major Jan 2026 update)
- Decorator-based event model: `@start()`, `@listen(method_name)`, `@router(upstream_method)`
- State = Pydantic `BaseModel` shared across all steps; mutations auto-serialized
- No globals, no manual argument passing — `self.state` access from any step
- `@router` returns string matching downstream `@listen("string")` decorator — mismatch = silent skip (gotcha)
- Stacked `@listen` decorators = fan-in (step runs when ANY upstream completes)

### Crew-Flow composition
- Flows contain Crews as sub-units: a Flow step calls `crew.kickoff()`, stores result in state
- `.raw` property extracts string output from `CrewOutput` object

### Novel patterns in CrewAI
- Typed state contracts (Pydantic validation prevents runtime shape mismatches)
- Conditional branching via routers — no explicit conditionals in orchestration logic
- Native async chain capabilities (Jan 2026)
- Global flow configuration for HITL feedback (Jan 2026)
- Streaming tool call events for real-time monitoring

### Scale claim
12 million Flow executions/day (vendor claim, Mar 2026)

### Sources
- docs.crewai.com/en/changelog
- markaicode.com/crewai-flows-event-driven-agent-orchestration/
- dev.to/linou518 (2026 framework comparison)

---

## OpenAI Agents SDK

### Handoffs — technical architecture

**Mechanism:** Handoffs are exposed as tools to the LLM. "Transfer to Refund Agent" becomes callable tool `transfer_to_refund_agent`.

**Data transfer options:**
- Default: entire prior conversation history passed to receiving agent
- `RunConfig.nest_handoff_history` (opt-in beta): collapses prior transcript into single `<CONVERSATION HISTORY>` summary block
- `input_type` parameter: structured metadata (reason, priority, summary) generated by LLM AT handoff time — separate from history
- `input_filter`: transforms `HandoffInputData` before transfer (input history, pre-handoff items, new items, run context)

**Context model:** Application state/dependencies belong in `RunContextWrapper.context`, not `input_type`

**Handoff scope:** Stays within a single run. One-way transfer — original agent drops out.

**Customization:** `tool_name_override`, `tool_description_override`, `on_handoff` callback, `is_enabled` (boolean or runtime function)

### Guardrails — three-tier architecture

**Input guardrails:** Validate user input before agent execution. Only run on FIRST agent in chain. `GuardrailFunctionOutput` → `.tripwire_triggered` flag.
- Parallel mode (default): runs concurrently with agent, agent may consume tokens before cancellation
- Blocking mode: agent never starts if tripwire triggered, prevents token consumption

**Output guardrails:** Inspect final agent output. Only run on LAST agent. No parallel execution.

**Tool guardrails:** Wrap individual `function_tool` instances; validate BEFORE and AFTER tool invocation; can skip calls, replace output, or trigger tripwire. Does NOT apply to handoffs, hosted tools, or built-in execution tools.

**Tripwire pattern:** Raises typed exceptions (`InputGuardrailTripwireTriggered`, `OutputGuardrailTripwireTriggered`); halts execution immediately.

### Agent-as-tool pattern
- Sub-agents callable as tools from main orchestrator
- Main agent retains thread control; sub-agents don't take over conversation
- Different from handoffs: main agent decides when to call sub-agent and receives results

### Sources
- openai.github.io/openai-agents-python/handoffs/
- openai.github.io/openai-agents-python/guardrails/
- openai.com/business/guides-and-resources/a-practical-guide-to-building-agents

---

## Claude Agent SDK (renamed from Claude Code SDK)

### Core architecture
- `query()` function as primary interface; async generator yields messages
- Agent loop (tool execution, state updates, context management) handled internally
- `ClaudeAgentOptions`: `allowed_tools`, `agents` (subagent definitions), `mcp_servers`, `permission_mode`, `hooks`, `resume`

### Subagents
- `AgentDefinition` with description + prompt + tools
- Main agent invokes subagents via `Agent` tool (must be in `allowedTools`)
- Messages from subagent include `parent_tool_use_id` for lineage tracking
- `resume=session_id` for multi-session continuity with full context

### Sessions (key differentiator)
- Session ID captured from `init` message (`message.subtype == "init"`)
- `resume=session_id` continues prior session with full context — "it" refers to files already read
- Context compaction: SDK auto-summarizes when context limit approaches

### Hooks
- Available: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`
- Callback signature: `(input_data, tool_use_id, context) -> {}`
- `HookMatcher` with regex `matcher` field (e.g., `"Edit|Write"`)
- Use for: audit logging, permission gates, quality checks, notification

### Planning approach (from engineering blog)
- Feedback loop: gather context → take action → verify → repeat
- "Agentic search" preferred over semantic search — file system + bash commands (grep, tail) for context gathering
- Context isolation: subagents receive only relevant excerpts from parent, not full context
- Folder structure treated as "a form of context engineering"

### Error recovery
- Tool execution errors auto-fed back to Claude; Claude sees error output and adjusts
- Rules-based validation preferred over LLM-as-judge for feedback (faster, more reliable)
- Visual feedback loops (screenshots) for UI verification tasks

### Novel design choices vs other frameworks
1. **Computer access model** — agent writes bash scripts, creates files, runs commands iteratively (mimics human programmer loop)
2. **Code as output** — generates Python/TypeScript rather than text/structured data for complex operations
3. **Semantic vs agentic search trade-off** — recommends starting with agentic search, add semantic only if performance critical
4. **Permission modes** — `acceptEdits`, `bypassPermissions`, `default` — fine-grained tool authorization

### Sources
- platform.claude.com/docs/en/agent-sdk/overview
- claude.com/blog/building-agents-with-the-claude-agent-sdk
- anthropic.com/research/building-effective-agents
- venturebeat.com/ai/anthropic-says-it-solved-the-long-running-ai-agent-problem-with-a-new-multi

---

## Cross-Cutting Planning Patterns

### ReAct (Reasoning + Acting)
- Loop: Thought → Action → Observation → repeat
- Strengths: adaptability, built-in error recovery (continuous feedback)
- Weakness: high token usage, high latency
- Use when: interactive, ambiguous, requires mid-plan pivots

### ReWOO (Reasoning Without Observation)
- Three phases: Planner (full plan upfront) → Workers (parallel deterministic execution) → Solver (synthesis)
- Workers use abstract placeholders; execute without per-step LLM reasoning
- ~5x token reduction vs ReAct; enables parallelism
- Weakness: brittle; cannot self-correct mid-workflow
- Use when: predictable, structured, high-throughput batch

### CodeAct
- Loop: Reason → Code Generation → Sandboxed Execution → Observe/Debug
- Agent generates Python/SQL/bash; iterates on error traces
- Strengths: genuinely novel problem-solving, interpretable, token-efficient on success
- Weakness: security risk, high cost on repeated failures; requires sandboxing
- Dominant pattern in DeepSeek agentic training; used by Manus AI

### LATS (Language Agent Tree Search)
- Combines Tree-of-Thoughts + ReAct + planning; backtracking + structured alternatives
- Excels at complex coding, interactive QA, web navigation
- More resource-intensive than ReAct; rarely used in production frameworks yet

### Hybrid pattern (2025-2026 production standard)
- ReWOO for predictable retrieval → CodeAct for processing → ReAct for ambiguous synthesis
- If ReWOO worker fails → fallback to ReAct with accumulated context

---

## Agent Engineering as Discipline (2025-2026 State)

### Production state (LangChain survey, N=1340, Nov-Dec 2025)
- 57.3% of orgs have agents in production (up from 51% prior year)
- Top blockers: quality (32%) > latency (20%) > security (enterprises 24.9%)
- 89% have observability; 62% have full per-step tracing
- 52.4% run offline evals on test sets; 37.3% online evals (44.8% for prod agents)
- 59.8% human review; 53.3% LLM-as-judge
- 75%+ deploy multiple models; 57% don't fine-tune (prompt engineering + RAG)

### AgentOps emerging discipline
- Continuous monitoring, evaluation, observability, intervention AFTER deployment
- "Flow engineering" = discipline of designing control flow, state transitions, decision boundaries AROUND LLM calls (not optimizing the calls themselves)

---

## Observability Infrastructure

### Key platforms (2026)
- **LangSmith**: LangGraph-native; full traces (prompts, retrieved context, tool selection, inputs/outputs, errors); virtually zero overhead; best-in-class for LangChain ecosystem
- **Arize Phoenix**: OpenTelemetry-based; framework-agnostic; out-of-box for OpenAI Agents SDK, Claude Agent SDK, LangGraph, CrewAI, Mastra, LlamaIndex, DSPy
- **AgentOps**: time-travel debugging, multi-agent workflow visualization, session replay; Python-only, cloud-only

### OpenTelemetry for agents
- OpenInference (Arize): standardized semantic conventions for AI agent telemetry
- Auto-instrumenting MCP client + server with OpenTelemetry propagates context between them — unified traces showing tool call ↔ server execution
- Each platform has own logging formats/APIs currently; convergence toward OTel expected

### What agent observability tracks beyond traditional APM
- Multi-step execution chains
- Token usage + latency + cost at each step (not just overall)
- Tool invocations with inputs/outputs and their influence on decisions
- Response quality, hallucination rate, task completion
- Agent reasoning/decision rationales
- Drift detection across environments

---

## Eval Frameworks

### Offline vs online
- **Offline**: post-inference, experimentation/benchmarking, no latency constraints; used for CI/CD regression gates
- **Online**: real-time production evaluation, LLM judges integrated into dashboards and feedback loops

### LLM-as-judge patterns
- G-Eval (DeepEval): CoT + form-filling + token weight summation for nuanced rubric evaluation
- Agent-as-judge (arxiv:2508.02994): agent evaluates agent's entire action chain, not just final output; 0.3% disagreement with humans vs 31% for LLM judge on code
- Panel of judges > single judge (PoLL pattern, arxiv:2404.18796): 7x cheaper, less intra-model bias

### Key tools
- DeepEval (confident-ai/deepeval): G-Eval + task completion + answer relevancy + hallucination detection
- LangChain OpenEvals: readymade evaluators
- Langfuse: LLM-as-judge docs, open-source tracing
- DeepEval LLM-as-trainer: judges feed back into fine-tuning pipeline

---

## Source URLs (validated working for WebFetch)

- google.github.io/adk-docs/agents/multi-agents/ — works
- developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/ — works
- microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/magentic-one.html — works
- devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework — works
- docs.langchain.com/oss/python/langgraph/interrupts — works
- blog.raed.dev/posts/langgraph-hitl — works
- markaicode.com/crewai-flows-event-driven-agent-orchestration/ — works
- openai.github.io/openai-agents-python/handoffs/ — works
- openai.github.io/openai-agents-python/guardrails/ — works
- platform.claude.com/docs/en/agent-sdk/overview — works
- claude.com/blog/building-agents-with-the-claude-agent-sdk — works (after redirect from anthropic.com/engineering/*)
- anthropic.com/research/building-effective-agents — works
- langchain.com/state-of-agent-engineering — works (rich survey data)
- capabl.in/blog/agentic-ai-design-patterns-react-rewoo-codeact-and-beyond — works
- sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/ — 403
- towardsai.net agent observability article — returns thin summary only (Medium paywall)
