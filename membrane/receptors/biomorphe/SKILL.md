---
name: biomorphe
description: Cell biology as agent design manual — 20 heuristics. Use when designing agent architecture or evaluating system health. "bio heuristics", "agent design patterns"
version: 1
tags: [reference, agents, architecture, biology]
triggers:
  - biomorphe
  - biology design
  - agent architecture
  - cell biology patterns
  - bio heuristics
disable-model-invocation: true
---

# Biomorphe — Cell Biology as Agent Design Manual

> biomorphe (bio + morphe): life-shaped. Agent architecture derived from biological mechanisms.

Reference skill. Consult when designing multi-agent systems, evaluating system health, or making architectural decisions. Twenty heuristics from four specimens, each transferable to AI agent design.

## Specimen 1: Immune System — Trust & Error Handling

### 1. Negative selection before deployment (clonal deletion)
T cells that attack self are killed during maturation. **Test agents against known-good cases before deployment, not just known-bad ones.** Most agent testing asks "does it catch the bad thing?" The harder, more important test: "does it leave the good thing alone?" False positives erode trust faster than false negatives.
- **Anti-pattern:** validation that only tests edge cases, never the happy path
- **Signal:** users bypassing your guardrail = autoimmune disease

### 2. Explicit tolerance mechanisms (regulatory T cells)
The immune system actively learns what NOT to react to. Harmless foreign material (food, gut bacteria) gets suppressed, not attacked. **Agent systems need allowlists, not just blocklists.** An agent that flags every anomaly becomes an ignored alarm.
- **Design question:** what's your regulatory T cell — the thing that actively suppresses false alarms?

### 3. Measure inflammation duration, not error count
Acute inflammation is the healing response. Chronic inflammation is the disease. **Errors and retries are healthy (acute). Persistent error loops are pathological (chronic).** Don't count errors. Measure how long the system has been in an error state.
- **Rule:** alert on duration, not frequency. 10 errors in 1 minute during recovery = fine. 1 error per hour for a week = investigate.

### 4. Every guardrail is a potential autoimmune disease
When the immune system attacks self = autoimmunity. **Over-aggressive validation that blocks legitimate changes is autoimmune.** The cost of false positives compounds faster than false negatives because it erodes trust in the guardrail itself.
- **Test:** if your team routinely bypasses a check, the check is autoimmune — fix the check, not the team.

### 5. Antigen presentation: adaptive teaches innate (the feedback loop)
Adaptive immunity (LLM-based detection) discovers new threats. Antigen presentation feeds those discoveries back to innate immunity (regex/rules). **Every LLM-based detection should have a pathway to become a deterministic rule.** Without this loop, your system has two disconnected detectors instead of a learning immune system.
- **Mechanism:** LLM finds pattern -> human validates -> pattern added to rule set -> LLM moves to next unknown

## Specimen 2: Endocrine Signaling — Coordination Without Central Control

### 6. Two signaling systems: nerves and hormones
Nerves: fast, point-to-point, ephemeral. Hormones: slow, broadcast, sustained. **Agents need both.** Direct tool calls = nerves. Constitution/config files = hormones. CLAUDE.md is a hormone — it changes everything's behavior without targeting anything specific.
- **Smell:** a system with only nerve-like signaling (direct calls) has no way to shift global behavior without updating every agent individually.

### 7. Tune receiver sensitivity, not signal strength (receptor density)
Cells regulate sensitivity by changing receptor count, not by controlling the hormone level. **Agents should tune their thresholds, not try to control the signal.** If an agent over-reacts to budget warnings, change the agent's threshold, not the budget calculation.
- **This IS allostasis:** metabolic tiers change behavior (receptor density), not the budget itself (hormone level).

### 8. Pulsatile, not constant (hormonal rhythms)
Hormones pulse. Constant cortisol causes Cushing's disease. The rhythm IS the signal — cells respond to change, not level. **Agent nudges should be intermittent, not constant.** A reminder every session becomes invisible. A reminder that fires only in matching context stays salient.
- **Anti-pattern:** always-on advisory messages that nobody reads
- **Pattern:** priming (context-triggered reminders) — fires once on context match, then deletes itself

### 9. Positive feedback for irreversible transitions
Negative feedback = thermostat (stabilize). Positive feedback = labor contractions (amplify until transition). **Most agent systems only have negative feedback (error -> correction). Positive feedback is needed for momentum — when something works, commit harder.** Biology uses positive feedback exclusively for irreversible transitions (birth, clotting, nerve firing).
- **Design question:** where in your system do you want runaway amplification? Those are your commitment points.

## Specimen 3: Cellular Metabolism — Resource Allocation

### 10. Universal currency decouples production from consumption (ATP)
Cells convert all energy to ATP first, then spend ATP. **Token budgets should be a universal unit that abstracts away provider differences.** Don't track "how many OpenAI calls" — track a normalized budget that lets you swap providers without changing allocation logic.
- **Already working:** respirometry abstracts utilization across providers

### 11. Pathways, not reactions (glycolysis)
Glucose isn't burned in one step — it flows through 10+ steps, each producing useful intermediates. **Complex agent tasks should produce useful intermediates at each step.** If the chain breaks at step 5, steps 1-4 should still have value.
- **Anti-pattern:** monolithic prompts where partial completion = zero value
- **Pattern:** plan -> spec -> delegate -> build -> review, where each artifact is independently useful

### 12. Regulate at a different site than execution (allosteric regulation)
An enzyme's activity is controlled by molecules binding at a DIFFERENT site from the active site. **Modify agent behavior through context (constitution, tier, time-of-day), not by changing the prompt itself.** The regulator doesn't compete with the substrate.
- **This IS metabolic tiers:** allostasis changes the agent's shape, not the task

### 13. Prevent futile cycles
When opposing pathways run simultaneously (synthesis + breakdown of same molecule), energy is wasted with no net progress. **Agents that simultaneously generate and critique in the same loop create futile cycles.** Separate generation from evaluation temporally.
- **Anti-pattern:** "write code and review it" in one prompt
- **Pattern:** sortase separates build from review. Ribosomes write, CC judges.

### 14. Distinct modes for proteasome and anabolism
Breaking down vs building up. Both essential, but not simultaneously on the same substrate. **Agent systems need distinct modes for cleanup (debugging, auditing, deleting) vs creation (building, extending).** Running both on the same codebase creates confusion.
- **Validates:** metabolic tier system — catabolic mode for cleanup, anabolic for building

## Specimen 4: Ecosystems — Multi-Agent Dynamics

### 15. Identify keystones by connectivity, not throughput
A keystone species isn't the most abundant — it's the most connected. Remove it and the ecosystem collapses. **The critical agent isn't the one doing the most work — it's the one with the most dependencies.** Identify keystones before modifying.
- **In vivesca:** CC is the keystone — not most work (ribosome does more) but most dependencies route through it.

### 16. Ecological succession: stages create conditions for the next
Bare rock -> lichens -> moss -> forest. Each stage enables the next. **Don't design complex agents from nothing.** Let simple agents (reliable CLIs, basic automation) establish conditions before layering complex ones (multi-model councils, autonomous repair).
- **Vivesca trajectory:** scripts -> skills -> ribosomes -> temporal dispatch -> autonomous teams. Each stage only worked because the previous was stable.

### 17. Niche partitioning prevents competitive exclusion
Species sharing the same resource either specialize or one goes extinct (competitive exclusion principle). **Multiple agents sharing the same task type must specialize or they create waste.** Explicit niche assignment.
- **Pattern:** goose for bulk coding, codex for review, gemini for research. Provider routing IS niche partitioning.

### 18. No decomposers = nutrient lock-in
Without organisms that break down dead matter, nutrients get locked in dead tissue and the ecosystem starves. **Without cleanup agents, the system accumulates cruft that starves active components of attention.** Dead skills, stale memories, abandoned experiments.
- **Decomposers in vivesca:** integrin (health scan), debridement (naming sweep), chromatin-hygiene (orphan notes)
- **Test:** is your decomposer budget proportional to your creation rate?

### 19. Carrying capacity is set by maintenance, not creation
Every ecosystem has a maximum sustainable population. Overshoot -> crash. **There's a maximum number of skills/agents/automations a system can sustain given its maintenance budget.** Adding past carrying capacity causes cascading failures.
- **Signal:** skills going stale, configs drifting, context window overflow = overshoot
- **Rule:** before adding a new skill, check if maintenance budget can absorb it. If not, decompose something first.

### 20. Mutualism requires interface stability
Symbiotic relationships (clownfish/anemone, mitochondria/cell) persist because the interface is stable even as the organisms evolve independently. **Multi-agent systems survive when the interface contracts (MCP tools, CLI flags, file formats) are stable, even as implementations change behind them.**
- **Anti-pattern:** changing a CLI's output format without versioning = destroying a mutualism
- **Pattern:** MCP tool schemas as stable interfaces. Implementations swap freely behind them.

## How to Use This Skill

**When designing:** scan heuristics 6-9 (signaling), 10-14 (resources), 15-20 (multi-agent) for relevant patterns.
**When debugging:** scan heuristics 1-5 (trust), 3 (inflammation), 13 (futile cycles), 18-19 (ecosystem health).
**When evaluating system health:** heuristics 4 (autoimmunity), 8 (constant signals), 18 (decomposers), 19 (carrying capacity).

## Cross-References

- **bouleusis** — planning theory. Heuristic 11 (pathways not reactions) directly applies to plan decomposition.
- **mandatum** — delegation theory. Heuristics 13 (futile cycles), 17 (niche partitioning) inform delegation design.
- **kritike** — evaluation theory. Heuristic 1 (negative selection) is the evaluation analog.
- **parsimonia** — simplification. Heuristic 19 (carrying capacity) provides the ecological framing for when to simplify.
- **praecepta** — heuristics theory. This skill IS an application of praecepta's framework.
- **taxis** — system architecture. All 20 heuristics apply to organism design decisions.
- **histology** — architecture review. Heuristics 15 (keystone), 18 (decomposers), 19 (carrying capacity) are histology lenses.
