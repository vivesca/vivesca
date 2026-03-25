# DSPy Optimization Strategies for Vivesca Metabolism

Research from DSPy optimizer docs, EvoPrompt (Guo et al. 2023), and Compounding Engineering pattern.

## 1. Optimizer Selection for Low Signal Volume

At 20-30 signals/day, most DSPy optimizers are overfit risks. Two are viable:

- **BootstrapFewShot**: Works with ~10 examples. Teacher module generates candidate demonstrations, metric function filters them. Cheapest optimizer — one pass, deterministic output. This is the starting point.
- **SIMBA**: Stochastic mini-batch sampling finds high-variability examples (where the tool description produces inconsistent results), then uses LLM introspection to generate corrective rules. This is the most vivesca-aligned optimizer — it discovers *why* a tool description fails, not just *that* it fails.

Avoid: MIPROv2 (needs 200+ examples), BootstrapFinetune (needs weight access), BetterTogether (compound overhead).

**GEPA** is worth watching: it reflects on execution traces and proposes prompt fixes from domain-specific feedback. Could work at low volume if traces are rich.

## 2. EvoPrompt Mutation Strategies (Steal These)

EvoPrompt treats prompts as genomes in a population (N=10), evolved over iterations. Two strategies:

**Differential Evolution (DE) — best for vivesca:**
1. Compare two tool descriptions, identify *different* parts only
2. Mutate only the differences (preserves proven shared components)
3. Combine mutations with the current best-performing description
4. Crossover result with the base description

Key insight: mutating only diffs outperforms mutating everything (75.5% vs 69.9%). This maps directly to vivesca genomes — when a tool description underperforms, diff it against the best variant, mutate only the delta.

**Genetic Algorithm (GA) — simpler alternative:**
1. Roulette-wheel selection (probability proportional to fitness score)
2. LLM-driven crossover of two parent descriptions
3. LLM-driven mutation of the offspring
4. Keep top-N from union of old + new population

**Population size 10, temperature 0.5, top-p 0.95.** These are directly applicable parameters. With 24 tools, each tool's description is a population of 1 (current) — expand to 3-5 variants, evaluate against signal history, promote the winner.

## 3. The Compounding Loop — What to Steal

The "compounding engineering" pattern: review → triage → plan → learn. Each cycle's outputs feed the next. For vivesca:

- **What persists**: The winning genome (tool description) in git, plus the signal history that selected it.
- **What mutates**: The description text, parameter schemas, example fragments. Never the tool's code.
- **Feedback signal**: Tool selection accuracy (was the right tool chosen?), execution success, user corrections. Failed invocations become negative examples for the next mutation round.
- **Failed plans become few-shot examples for retries** — this is the compounding mechanism. Every failure enriches the optimization context.

## 4. Low-Data Techniques to Apply

1. **Accumulate, don't stream.** At 20-30/day, batch weekly (140-210 signals) before running optimization. BootstrapFewShot needs ~10 good examples; one week provides that.
2. **Metric-filtered generation.** BootstrapFewShot only keeps demonstrations that pass the metric. Define a tight metric (tool-selection accuracy on held-out signals) and let it filter aggressively.
3. **SIMBA's variability detection.** Run the same signal through current descriptions multiple times. High-variance outputs flag weak descriptions — focus mutation there, not uniformly.
4. **KNNFewShot for context-dependent tools.** Find signals most similar to the current input, use those as few-shot examples. Useful when tool selection depends on phrasing.

## 5. Production Gotchas

- **Optimization cost is low.** A typical run: ~$2, ~10 minutes. At vivesca's scale, weekly optimization is pennies.
- **Optimized programs serialize to plain JSON.** Git-friendly — each optimized genome is a diffable file.
- **Overfitting is the main risk at low volume.** Never optimize on the same data you evaluate on. Hold out 20% of weekly signals as test set.
- **No online/continuous optimization in DSPy.** All optimizers are batch. Build the accumulate-then-optimize cycle yourself.
- **Composability works.** Run BootstrapFewShot first, then feed output to SIMBA for failure analysis. Sequential chaining is supported and cheap.
