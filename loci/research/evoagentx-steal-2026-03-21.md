# Stealable Techniques for Vivesca Metabolism

Source: EvoAgentX framework + "Awesome Self-Evolving Agents" survey (2025).

## Mutation Strategies Worth Stealing

**1. Differential Evolution for descriptions (from EvoPrompt DE/best/2).** Take two donor tool descriptions, diff them, mutate the differences, splice into the current best. This is stronger than naive "rewrite this prompt" because it forces the LLM to reason about *what varies* between successful and unsuccessful variants. Vivesca has ~24 tools — enough genetic diversity for meaningful diffs.

**2. Zero-order mutation prompts (from SEW).** Generate the mutation instruction itself via `thinking_style + problem_description → LLM → mutation_prompt`. The mutation prompt is *derived*, not hardcoded. This means the system adapts its mutation strategy to the specific tool's failure mode rather than applying generic rewriting.

**3. TextGrad's selective freezing.** Mark which parts of a tool genome are mutable (`requires_grad=True`). For vivesca: tool descriptions and parameter hints are mutable; schema structure and function signatures are frozen. This prevents mutations from breaking contracts while allowing semantic drift.

**4. MIPRO's Bayesian candidate selection.** Instead of evaluating all mutations, use TPE (Tree-structured Parzen Estimator) to model which mutation directions are promising. At 20-30 signals/day, you can't afford to waste evaluations. Optuna's TPE is lightweight and works with tiny sample sizes — directly applicable.

## Fitness Measurement (Adapted for 1-User Scale)

EvoAgentX uses exact-match against benchmarks — useless for vivesca. Steal the *structure*, not the metric:

- **Implicit signal extraction.** Tool call succeeded/failed, was the result used or discarded, did the user retry with different parameters, did the user correct the output. These are your fitness proxies.
- **Process reward over outcome reward.** Math-Shepherd's insight: score intermediate steps, not just final results. For vivesca: did the tool get *invoked correctly* (schema fitness) even if the task failed for other reasons?
- **Self-consistency as cheap fitness.** Generate 3 candidate descriptions, ask which one a model would invoke for a given task. The one that wins plurality is fitter. Zero human labels needed.

## What Actually Works vs. Theoretical

**Works (strong evidence):** Edit-based prompt evolution (GPS, GrIPS), EvoPrompt's GA/DE, TextGrad for prompt refinement, MIPRO's Bayesian search. All have reproducible benchmark gains.

**Fragile:** Unified optimization (evolving everything simultaneously), gradient-based text optimization (TextGrad/REVOLVE at scale), self-referential improvement (Promptbreeder). These need careful tuning or degrade.

**Theoretical only:** Zero-data self-play, emergent tool creation, convergence guarantees for evolutionary prompt search. Don't build on these.

## Failure Modes to Design Against

1. **Mode collapse.** Evolved descriptions converge to one style that works for recent tasks but loses generality. Fix: keep a "founding population" of 2-3 original descriptions as diversity anchors. Git history is your archive.
2. **Reward hacking.** Descriptions evolve to game the fitness signal (e.g., always getting invoked by being vague). Fix: fitness must include *downstream success*, not just invocation rate.
3. **Drift without pressure.** Tools that rarely fire never get selection pressure, so mutations accumulate neutrally. Fix: periodic "maintenance evaluation" — test dormant tools against synthetic tasks.
4. **Catastrophic mutation.** One bad rewrite breaks a tool. Fix: EvoAgentX's snapshot-and-rollback pattern — evaluate *before* promoting. Git commit only on fitness improvement.

## Personal Adaptation / Taste

The survey reveals this is underdeveloped. PersonaAgent is the only system explicitly targeting user preference. Key insight: **memory-based adaptation (Memento, A-MEM) outperforms fine-tuning for single-user personalization** — you don't need to change the model, you need to change what the model sees. Vivesca's markdown genomes are already this pattern. Strengthen it by recording *why* Terry corrected a tool output, not just *that* he did.

## Recommended Architecture for Vivesca Metabolism

Steal the three-phase loop: **evaluate → mutate → select**, running asynchronously on accumulated signals. Use DE mutation for descriptions (proven), TPE for candidate selection (sample-efficient), git snapshots for rollback (already have this). Fitness = composite of invocation accuracy + downstream success + user non-correction. Run daily, promote weekly after manual review.
