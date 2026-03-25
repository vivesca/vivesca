---
name: Token Budget & Compute Management in AI Agents — Research Findings (Mar 2026)
description: Specific tools, papers, and frameworks for tracking/responding to LLM token/cost consumption — the "mitochondria" problem. Covers within-generation, within-run, cross-session, and behavioral adaptation layers.
type: reference
---

## Researched: 2026-03-25

The landscape splits into four distinct layers. Key findings:

### Layer 1: Within-Generation (Research)
- **TALE** (arXiv 2412.18547): injects `"use less than N tokens"` into CoT prompt. 67% token reduction, <3% accuracy loss. Code: github.com/GeniusHTX/TALE
- **BudgetThinker** (arXiv 2508.17196): periodically inserts special control tokens during inference signaling % budget consumed. Two-stage SFT+RL training. 4.9% accuracy improvement with precise budget adherence.
- **Anthropic `effort` param**: production mechanism. `low/medium/high/max` controls thinking depth AND tool verbosity AND response length. `budget_tokens` deprecated on 4.6 models.

### Layer 2: Within-Run Agent Budget (Research → Emerging Production)
- **BATS** (arXiv 2511.17006): Budget Tracker appends "Tool Used: ##, Remaining: ##" after each tool call. Four behavioral modes: HIGH(≥70%) explore broadly, MEDIUM(30-70%) converge, LOW(10-30%) verify only, CRITICAL(<10%) stop tool use. 37.4% vs 30.7% accuracy over ReAct on BrowseComp.
- **Budget-Aware Agentic Routing** (arXiv 2602.21227): routes each step to cheap vs expensive model. Boundary-Guided Training (BoPO). Key insight: cheap models can cost MORE in agents because they loop.
- **Agent Contracts** (arXiv 2601.08815): formal framework with conservation laws — child agents can't exceed parent's remaining budget. 90% token reduction, 525x lower variance. Most complete formal treatment.
- **CostBench** (arXiv 2511.02734): benchmark for evaluating cost-aware planning. All models score poorly; GPT-5 <75% in static, ~35% under dynamic cost changes.
- **OpenAI Agents SDK**: native `result.context_wrapper.usage` (requests/input/output/total tokens per run). RunHooks expose usage at each lifecycle moment for real-time intervention.

### Layer 3: Cross-Session / Per-User (Production)
- **LiteLLM Proxy**: most full-featured open-source budget enforcement. Per-user `max_budget` + `budget_duration`, budget routing across providers, model-specific limits. Hard stop (429) not behavioral adaptation.
- **Helicone**: gateway + observability. Graduated thresholds (50/80/95%), multi-level rate limiting. ~19K GitHub stars, MIT.
- **Langfuse**: open-source tracing with per-trace cost tracking. OTel-native. Best for post-hoc analysis.

### The Gap (What Doesn't Exist Yet)
No system combines: (a) continuous budget sensing across steps, (b) graduated multi-mode behavioral change, (c) cross-step cost trajectory memory, and (d) proactive conservation before hitting critical thresholds. BATS + BudgetThinker together get closest. Agent Contracts is the most complete formal model but not productionized.

**Vault note:** ~/code/vivesca-terry/chromatin/Reference/token-budget-compute-management-agents.md
