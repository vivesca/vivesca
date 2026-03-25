---
name: Context Engineering & Agent Meta-Techniques (Mar 2025–Mar 2026)
description: Comprehensive survey of meta-techniques for effective AI agents — context engineering, memory architectures, planning patterns, self-correction, prompt engineering, and evaluation. Covers academic papers and production evidence.
type: reference
---

# Context Engineering & Agent Meta-Techniques — Mar 2026

## What "Context Engineering" Is

Coined/popularized by Karpathy (Jun 25 2025 X post): "the delicate art and science of filling the context window with just the right information for the next step." The analogy: LLM = CPU, context window = RAM. Managing RAM (not just writing better CPU instructions) is the core engineering problem.

Karpathy's taxonomy of LLM app complexity:
1. Single context call
2. Context engineering (managing what goes in the window)
3. Orchestrating multiple LLM calls in DAGs
4. Building application-specific oversight interfaces
5. Autonomous agents with "autonomy sliders"

The field agrees context engineering surpasses "prompt engineering" as the organizing concept for production agentic systems.

Key sources: karpathy.bearblog.dev/year-in-review-2025/, simonwillison.net/2025/jun/27/context-engineering/, rlancemartin.github.io/2025/06/23/context_engineering/

---

## 1. CONTEXT ENGINEERING TECHNIQUES

### 1.1 Four-Category Framework (LangChain/LangGraph + Karpathy)

The canonical taxonomy for organizing context engineering:

| Category | What It Does | Key Techniques |
|----------|--------------|----------------|
| **Write** | Persist info outside context | Scratchpads, long-term memory, file system externalization |
| **Select** | Pull relevant info in | Memory retrieval, RAG, tool selection, knowledge retrieval |
| **Compress** | Reduce tokens, keep semantics | Summarization, trimming, trained pruners |
| **Isolate** | Split across components | Multi-agent, sandboxing, state schemas |

Source: rlancemartin.github.io/2025/06/23/context_engineering/, blog.langchain.com/context-engineering-for-agents/

### 1.2 KV-Cache Hit Rate Optimization (Manus)

**The #1 production metric for long-running agents.** Claude Sonnet: $0.30/MTok cached vs $3.00/MTok uncached = 10x cost difference. With Manus's 100:1 input-to-output token ratio, cache optimization dominates cost.

Techniques:
- Keep prompt prefixes stable — even single-token differences invalidate downstream cache
- Append-only contexts — avoid modifying previous actions or observations
- Deterministic serialization — stable JSON key ordering
- Explicit cache breakpoints for long sessions

Source: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

### 1.3 File System as External Memory (Manus)

**Problem:** Context windows fill up on long tasks; compressing loses information.
**Solution:** Treat the file system as unlimited, persistent, externalized memory. Agent reads/writes files on demand. Context holds file paths even when dropping content, enabling restoration.

Three pain points this solves:
1. Unlimited observation storage (web pages, PDFs)
2. Recovery from context length degradation
3. Cost reduction despite aggressive caching

Used by: Manus (primary), Claude Code (tools write to files), Devin (repository indexing)

### 1.4 Attention Manipulation via Recitation (Manus todo.md hack)

**Problem:** "Lost-in-the-middle" — in 50+ tool-call tasks, earlier goal specification drifts out of effective attention.
**Solution:** Create and continuously rewrite a `todo.md` file throughout task execution. Current objectives are always in the recent attention window.

Caveat: Manus found this introduced ~30% token waste pre-1.5 from constant rewrites. Trade-off is real.

Source: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

### 1.5 Error Retention (Leave Failures in Context)

**Counter-intuitive principle:** Rather than cleaning up failed actions or retrying silently, keep failed traces in context. Models implicitly update their beliefs based on visible failures and reduce repeated mistakes.

Evidence: Production pattern at Manus; error recovery underrepresented in academic benchmarks.

Source: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

### 1.6 Context Compression — Academic SOTA

**ACON (arxiv:2510.00615):** Gradient-free, unified framework for compressing both environment observations AND interaction history. Works with closed-source models. Results on 15+ step multi-step benchmarks:
- 26-54% peak token reduction
- 32% performance improvement on AppWorld, 20% on OfficeBench, 46% on Multi-objective QA
- Distillable: 95% accuracy preserved when compressor distilled to smaller model

**Provence (arxiv:2501.16214):** Trained pruner for RAG contexts. Sequence labeling approach; combines pruning with reranking. Negligible performance drop while removing irrelevant sentences. XProvence: multilingual extension (Jan 2026, arxiv:2601.18886).

**Hierarchical summarization:** Claude Code uses this (auto-compact). Older segments get progressively compressed; recent exchanges remain verbatim. Cognition (Devin) uses fine-tuned models for critical handoffs.

**Selective RAG for tool selection:** LangGraph's Bigtool library. RAG-based semantic search over tool descriptions improves selection accuracy 3x (LangChain blog claim, no independent benchmark).

---

## 2. AGENT MEMORY ARCHITECTURES

### 2.1 What Works in Production — Evidence Summary

No independent academic benchmark tests ≥5 production backends side-by-side (gap confirmed in prior research). Vendor benchmarks are contested. Best available evidence:

| System | Architecture | Best Evidence | Caution |
|--------|-------------|---------------|---------|
| **Mem0** | Vector + KV + graph hybrid | 26% accuracy gain, 91% latency reduction, 90% token savings vs full-context (LOCOMO, arxiv:2504.19413) | Own paper; 10% improvement over RAG is the honest headline |
| **Zep/Graphiti** | Temporal knowledge graph | 15-18% accuracy gain on LongMemEval; 90% latency reduction (arxiv:2501.13956) | Short conversation test limitation (60 msgs) |
| **A-MEM** | Zettelkasten-inspired, dynamic self-linking | 2x better on multi-hop vs MemGPT, 1200-2500 tokens vs 16900 | LOCOMO dataset only, not production tested |
| **RAG** | Vector retrieval | Reliable baseline | Struggles with preference inference, temporal reasoning |
| **Full-context** | Dump everything | Highest raw accuracy (73% vs Mem0's 67%) | 10x+ latency, 90%+ more tokens, infeasible at scale |

### 2.2 Memory Type Taxonomy (Practical)

Three memory types matter for agents:

1. **Episodic** — what happened (conversation history, event streams). Good for: personalization, context recovery. Best implementation: Zep temporal graph (bi-temporal modeling — tracks when events occurred AND when ingested).

2. **Semantic** — what I know (facts, domain knowledge, user preferences). Good for: cross-session user understanding. Best implementation: Mem0's concise fact extraction approach (abstracts salient facts from conversations, not raw chunks).

3. **Procedural** — how to do things (past task trajectories distilled into instructions). Good for: repeatable tasks. Best implementation: Mem^p (arxiv:2508.06433) — distills trajectories into step-by-step instructions + higher-level scripts. Shows steadily improving success rates on TravelPlanner + ALFWorld as memory repository is refined.

### 2.3 Scratchpad / Working Memory

**Short-lived, task-scoped.** Holds: current goal, active sub-tasks, intermediate results, recent tool outputs. Distinct from long-term memory.

Key principles:
- Schema-based working memory uses merge semantics (agent only updates changed fields)
- Summarize tool outputs before adding to scratchpad, not raw error logs
- At session end, triage scratchpad: promote enduring facts to long-term, discard temporaries

Redis = fast scratchpad; Postgres = long-term facts. Production pattern (sitepoint.com article).

### 2.4 File System as Memory (Cross-reference)

Covered in Section 1.3. Key production insight from Devin/Manus: directory-indexed memory (automatically generated wikis, architecture diagrams, indexed repos) enables agents to function in large codebases. Cognition trains SWE-grep/SWE-grep-mini for fast parallel context retrieval across repos.

---

## 3. PLANNING PATTERNS

### 3.1 ReAct (Reasoning + Acting)

**Paper:** arxiv:2210.03629, ICLR 2023. Authors: Shunyu Yao et al.
**Pattern:** Thought → Action → Observation → (repeat). LLM reasons aloud, then acts, then incorporates observation.
**Evidence:** 34% and 10% absolute improvements on ALFWorld and WebShop vs RL methods trained with 10^3-10^5 instances.
**Status:** Foundational — most agentic frameworks implement this as default. Still state of practice (not SOTA) in 2025. Fails at: tasks requiring significant upfront planning, highly dynamic environments.
**Production adoption:** LangChain, CrewAI, AutoGen all built on ReAct pattern. De facto production baseline.

### 3.2 Plan-then-Execute (Plan-and-Execute)

**Pattern:** Separate planner LLM creates full multi-step plan → executor LLM (or deterministic code) carries out steps independently. Explicit decoupling.
**Advantages:** More cost-efficient (planner called once), better for well-scoped tasks, predictable.
**Limitation:** Brittle to unexpected results mid-execution. No adaptive replanning unless explicitly added.
**Best for:** Multi-step workflows where path is knowable upfront (data pipelines, report generation, structured research).
**Comparison to ReAct:** ReAct wins on dynamic adaptation; Plan-execute wins on cost efficiency and predictability.

Source: arxiv:2509.08646 (Architecting Resilient LLM Agents)

### 3.3 CodeAct (Executable Code as Actions)

**Paper:** arxiv:2402.01030, ICML 2024. Authors: Xingyao Wang et al.
**Pattern:** Agent generates executable Python code as its action format, rather than JSON/function calls. Python interpreter executes code; output becomes observation.
**Evidence:** 20% higher success rate on API-Bank; outperforms alternatives on 12/17 evaluated LLMs.
**Why it works:** Code = structured, composable, debuggable. Complex multi-step logic in one action. Dynamic control flow (loops, conditionals) not possible in JSON tool calls.
**Production adoption:** Manus uses CodeAct as primary action format. OpenHands (Xingyao Wang's follow-up work) is the leading open-source implementation.

### 3.4 ReWOO (Reasoning WithOut Observation)

**Pattern:** Planner creates all tool calls upfront with variable placeholders; Solver executes in parallel using the pre-built plan; Concluder synthesizes results.
**Advantage:** Decouples reasoning from tool call latency — all tools can execute in parallel.
**Best for:** Tasks with many parallel, independent tool calls. Research, web scraping, multi-source retrieval.
**Source:** nutrient.io/blog/rewoo-vs-react-choosing-right-agent-architecture/

### 3.5 Tree of Thoughts (ToT)

**Pattern:** Explores multiple reasoning branches simultaneously, selects most promising via evaluation.
**Status in 2025:** Largely superseded by test-time compute scaling (o1/o3/R1 patterns). The reasoning model does ToT internally without explicit scaffolding. External ToT scaffolding adds latency without matching internal reasoning performance.
**Remaining use case:** Multi-criteria decision problems where you want human-readable branch exploration.

### 3.6 Emerging 2025 Pattern: Deterministic Backbone + Scoped Agent Intelligence

The pattern emerging from production deployments (Skywork AI analysis, 2025): not pure ReAct or pure Plan-execute, but:
- Deterministic workflow backbone (state machine, defined transitions)
- Agent LLM invoked only at specific decision points
- Comprehensive observability + human-in-the-loop checkpoints at risk points

This is what Anthropic's "Building Effective Agents" recommends: start with workflows (deterministic), only add full agent autonomy where it demonstrably improves outcomes.

---

## 4. SELF-CORRECTION / REFLECTION

### 4.1 Reflexion (Verbal RL)

**Paper:** arxiv:2303.11366 (2023).
**Pattern:** After each trial, agent writes verbal reflection on what went wrong → stores in episodic memory buffer → uses reflection to guide next attempt.
**Evidence:** 91% pass@1 on HumanEval (vs GPT-4's 80%). Significant gains on multi-step reasoning tasks.
**2025 extensions:**
- Agent-R (arxiv:2501.11425): MCTS-based training data generation for iterative self-training; +5.59% over baseline.
- Multi-Agent Reflexion (MAR, arxiv:2512.20845): Multiple agents cross-reflect; HumanEval 76.4% → 82.6%.
**Limitation:** Verbal reflection alone is insufficient for pure reasoning self-correction (Huang et al. finding). Requires external feedback signal or execution results to be grounded.

### 4.2 Self-Correction Limits — Critical Finding

**Huang et al. (2023/2024) finding:** LLMs cannot reliably self-correct reasoning without external feedback. Models that "self-correct" reasoning tasks without ground truth often degrade performance (they convince themselves wrong answers are right).

**What does work:**
- Self-correction with execution feedback (code compiles, tests pass = external signal)
- Self-correction with retrieval (agent can look things up to verify)
- Self-correction of format/style (no external ground truth needed)
- Self-correction of factual claims via tool use

**Practical implication:** Don't prompt agent to "check your work" on pure reasoning. Do give agents tools to verify (run tests, search, calculate) and then self-correct.

### 4.3 Fresh-Context Self-Review (Osmani)

**Pattern:** Have the model review its own output with a clean context window — no contamination from the generation process.
**Why:** Models subconsciously defend outputs they just produced. Fresh context = no prior commitment bias.
**Cost:** Low (same model, same call, fresh context).
**Evidence:** Production pattern at Addy Osmani's team; widely adopted in agentic coding workflows.
**Source:** addyosmani.com/blog/agentic-engineering/

### 4.4 MIRROR Architecture (Inner Monologue, Jun 2025)

**Paper:** arxiv:2506.00430.
**Pattern:** Dual-process separation — Talker (immediate response) + Thinker (asynchronous background reasoning). Inner Monologue Manager runs 3 parallel threads: goal tracking, reasoning, memory. Cognitive Controller synthesizes into bounded internal state.
**Status:** Promising academic result; no confirmed production adoption as of Mar 2026.

### 4.5 Automatic Verification Gates (Production Pattern)

The most reliable production self-correction: don't ask the agent to reflect — run automated tests.
- Code agent: test suite run after each change
- Research agent: source verification tool call
- Planning agent: constraint checker on output plan

Anthropic explicitly confirms for SWE-bench implementation: automated tests are the primary correctness signal, not reflection.

---

## 5. PROMPT ENGINEERING FOR AGENTS

### 5.1 System Prompt Design

**Key principles from Anthropic "Building Effective Agents" and production sources:**

1. **Simplicity over complexity.** "The most successful implementations weren't using complex frameworks" — they used simple, composable patterns. Add complexity only when it demonstrably improves outcomes.

2. **Explicit tool planning separation.** Implement distinct PLAN MODE vs ACT MODE (Cline pattern). Prevents hasty decisions.

3. **Constitutional document structure.** System prompt = governing constitution. Use clear headings, lists, XML tags for structure. Well-structured = parseable by both humans and models.

4. **Environmental context completeness.** Include: OS, directory structure, tool limitations, permissions, what the agent CAN'T do. Agents cannot infer what's in your head.

5. **Operational principles over rules.** Long rule lists fail when situations are novel. Principles + reasoning = better generalization.

### 5.2 Tool Description Design (Agent-Computer Interface)

Anthropic invested more time optimizing tools than overall prompts for their SWE-bench agent.

**What works:**
- Specific > general: `search_contacts` not `list_contacts` (avoid wasting context on irrelevant results)
- Consolidate related tools: `get_customer_context` (compiles all relevant info at once) vs 3 separate tools
- Document *when* to use each tool, not just how
- Include parameter examples, not just type signatures
- Semantic identifiers in responses (resolve UUIDs to meaningful labels)
- Add `response_format` enum (concise vs detailed) for token-efficient retrieval
- Prefix namespacing: `browser_*`, `shell_*` — enables stateless constraint enforcement

**Poka-yoke principle:** Design parameters to make mistakes hard to commit. Make dangerous operations require explicit confirmation flags.

**Error messages:** Actionable and specific. Guide agent toward correct usage, not just report failure.

Source: anthropic.com/engineering/writing-tools-for-agents

### 5.3 Few-Shot Examples for Agents

**What works:**
- 3-5 diverse, high-quality complete examples
- Show entire input→output cycle (not just partial patterns)
- Include sequencing dependencies ("create file before running it")
- Bolt-style: full artifact structure with proper nesting, not fragments

**What fails:**
- Uniform examples → model "few-shots itself into a rut" (Manus insight)
- Introduce controlled variation in serialization, phrasing, ordering to prevent pattern lock
- Sparse examples that show expected schema but not real behavior

### 5.4 Anthropic's ACI Design Principle

"Agent-Computer Interface (ACI) deserves the same design investment as HCI (Human-Computer Interface)." — Anthropic Building Effective Agents.

Practical: Test tools extensively with multiple inputs. Identify failure modes. Iterate on tool design as rigorously as feature development.

Evidence: Claude-optimized Slack/Asana MCP servers significantly outperformed human-written versions on held-out test sets (anthropic.com/engineering/writing-tools-for-agents).

---

## 6. EVALUATION

### 6.1 Key Agent Benchmarks (Mar 2026)

| Benchmark | What It Tests | SOTA Performance | Notes |
|-----------|--------------|------------------|-------|
| SWE-bench Verified | Real GitHub issues (coding) | ~65-75% (top agents) | Most trusted coding eval |
| TheAgentCompany | Real workplace tasks, 175 items | 30.3% (Gemini 2.5 Pro) | Best "consequential real-world" eval |
| Tau-bench (arxiv:2406.12045) | Tool-agent-user interaction | GPT-4o <50%, pass^8 <25% | Multi-trial reliability measure |
| Tau2-bench (arxiv:2506.07982) | Dual-control, agent+user coordination | Frontier models only recently viable | Harder than Tau-bench |
| LongMemEval | Memory over long conversations (~115K tokens) | ~70% with Zep (GPT-4o) | Memory-specific |
| LOCOMO | Conversational memory, multi-hop | Mem0: 67%, RAG: 61% | Memory eval standard |

### 6.2 Evaluation Methodology

**Pass@k metric (τ-bench):** Measures reliability across k trials. Single-trial pass rate inflates performance; pass^8 (solving 8 of 8) better reflects reliability.

**Progress Rate (AgentBoard):** Compares actual trajectory against expected trajectory. Fine-grained measure — partial credit for advancing toward goal, not just binary success.

**Cost-of-pass metric:** Expected monetary cost to generate a correct solution. Critical for production decisions — accuracy alone misleads.

**Trajectory reduction (AgentDiet, arxiv:2509.23586):** Reducing input tokens by 39.9-59.7% while maintaining performance. Efficiency dimension often neglected.

### 6.3 Evaluation Anti-Patterns

- **Single-trial evaluation:** Agents have high variance. Always run multiple trials (τ-bench recommends pass^k with k≥3).
- **Benchmark overfitting:** Models get trained on benchmark distributions. TheAgentCompany and τ-bench use procedural generation to resist this.
- **Ignoring cost:** An agent that's 5% more accurate but 10x more expensive is a worse product choice.
- **Testing only happy paths:** Agents fail on edge cases and error recovery. Error recovery performance is a key indicator of real agentic capability (Manus insight).

---

## 7. CONTEXT WINDOW OPTIMIZATION

### 7.1 Hierarchy of Approaches (by effectiveness)

1. **Don't put it in the window.** File system externalization (section 1.3). Most effective; unlimited capacity.
2. **KV-cache** (section 1.2). 10x cost reduction without changing context quality.
3. **Trained context compression** (ACON). 26-54% token reduction, maintains performance.
4. **Selective retrieval.** RAG over memory/tools. 3x tool selection improvement (unverified claim).
5. **Hierarchical summarization.** Older = more compressed. Preserves recency.
6. **Hard trimming.** Remove old messages. Loses information but simple.

Optimal context utilization rate: 60-80%. Below 60% = over-provisioning. Above 80% = capacity risk.

### 7.2 Multi-Agent Context Isolation

**Problem:** Single agent has one context window. As tasks get longer, context fills up and performance degrades.
**Solution:** Subagents with separate context windows, specialized for specific sub-tasks.

Evidence: Anthropic's multi-agent researcher — parallel subagents exploring different aspects significantly outperformed monolithic single-agent design. LangGraph's native support via isolated subagent contexts.

But caution: Multi-agent coordination overhead is real (arxiv:2512.08296). Only beneficial when tasks are genuinely parallelizable. Sequential reasoning actually degrades -39-70% with multi-agent vs single-agent.

---

## 8. META-PATTERNS: WHAT ACTUALLY WORKS IN PRODUCTION

### 8.1 Karpathy's "Agentic Engineering" Thesis

The winning agent architecture (2025-2026):
1. **Local deployment** — agents run where the developer's context lives (tools, env vars, codebase). Cloud agents miss 80% of relevant context.
2. **Rich environmental integration** — access to existing env: installed tools, configs, secrets, private data.
3. **Low-latency interaction** — responsiveness > distributed orchestration.
4. **Loopy problem-solving** — chains of tool use + reasoning, not single-shot.

Source: karpathy.bearblog.dev/year-in-review-2025/

### 8.2 Anthropic's Harness Patterns

From "Effective harnesses for long-running agents" (anthropic.com/engineering/effective-harnesses-for-long-running-agents):

Three-agent pattern for long tasks:
1. **Initializer agent:** Sets up scaffolding (feature list JSON, progress tracking, git repo, init scripts) for all future sessions.
2. **Coding agent:** Incremental progress — one feature per session, commit after each feature, tests before completion.
3. Use JSON for feature lists (models less likely to corrupt JSON vs Markdown).

Key failure modes this solves:
- Agents attempting too much at once (one-shotting full applications)
- Premature completion declarations
- Poor state handoffs between sessions

### 8.3 Manus's "Stochastic Graduate Descent"

**Philosophy:** Context engineering is an experimental science. No first-principles derivation of optimal prompts/architecture.
**Practice:** Rebuild the framework entirely if needed. Manus rebuilt 4 times.
**Implication:** Budget for multiple iterations. The first architecture will be wrong.

Source: manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

### 8.4 Devin/Cognition Insights (Production, 2025 Annual Review)

- Verifiability as design constraint: prefer tasks with objective success criteria
- Parallelization > persistence: agents succeed on independent-subtask work
- Pattern matching > novel reasoning: agents replicate and modify existing patterns more reliably than generating novel architectures
- Scope brittleness: agents handle clear upfront scoping but struggle with mid-task requirement changes

Source: cognition.ai/blog/devin-annual-performance-review-2025

---

## Key Papers Index

| Paper | Topic | ArXiv |
|-------|-------|-------|
| ReAct | Reasoning+Acting pattern | 2210.03629 |
| Reflexion | Verbal RL self-correction | 2303.11366 |
| CodeAct | Executable code as actions | 2402.01030 |
| Mem0 | Production memory system | 2504.19413 |
| Zep | Temporal knowledge graph | 2501.13956 |
| A-MEM | Zettelkasten-style dynamic memory | 2502.12110 |
| ACON | Agent context compression | 2510.00615 |
| Provence | RAG context pruning | 2501.16214 |
| Agent-R | Iterative self-training via MCTS | 2501.11425 |
| MAR | Multi-agent reflexion | 2512.20845 |
| MIRROR | Inner monologue architecture | 2506.00430 |
| AgentDiet | Trajectory reduction | 2509.23586 |
| TheAgentCompany | Real-world agent benchmark | 2412.14161 |
| Tau2-bench | Tool-agent-user benchmark | 2506.07982 |
| Mem^p | Procedural memory | 2508.06433 |

## Source Reliability Notes

- manus.im/blog: WebFetch works, primary source for context engineering production insights
- karpathy.bearblog.dev: WebFetch works
- anthropic.com/research/* and /engineering/*: WebFetch works, full content
- rlancemartin.github.io: WebFetch works
- arxiv HTML pages: work well; PDF = binary garbage
- cognition.ai/blog: WebFetch works
- simonwillison.net: WebFetch works
- prompthub.us: WebFetch works
- arxiv.org abstract pages: limited detail, use /html/ version
