# Eval Flywheel Reference — Hamel + Eugene Yan

ID: LRN-20260314-001

## Sources
- Hamel Husain: "Using LLM-as-Judge" (hamel.dev/blog/posts/llm-judge/)
- Eugene Yan: "Product Evals in 3 Steps" (eugeneyan.com/writing/product-evals/)

## Core Principles (both authors agree)

1. **Binary pass/fail > Likert scales.** 1-5 scores are uncalibrated and unactionable. Nobody knows the difference between 3 and 4.
2. **Error analysis before automation.** Look at data first. The judge is a trick to force you to look at data.
3. **One evaluator per dimension.** Never build a "God Evaluator" for 5-10 criteria at once. Build separate judges, combine via heuristics.
4. **Domain expert drives alignment.** Their judgment is the ground truth, not a rubric you wrote before seeing data.
5. **Start with ~30 examples, keep going until no new failure modes emerge.**

## Hamel: Critique Shadowing (step-by-step)

1. Find Principal Domain Expert (for thalamus: Terry)
2. Create dataset (diverse inputs — use existing + synthetic)
3. Domain expert makes pass/fail + writes detailed critiques
4. Fix obvious errors first (prompt gaps, missing tools, engineering bugs)
5. Build LLM judge using expert critiques as few-shot examples
6. Iterate until >90% agreement (typically 3 iterations)
7. Perform error analysis on remaining disagreements

Key insight: "You cannot write a good judge prompt until you've seen the data." The critiques ARE the prompt — they become few-shot examples.

## Eugene Yan: Three Steps

1. **Label data** — binary pass/fail, aim for 50-100 fail cases. Use weaker models (Haiku) to generate organic failures. Synthetic defects are out-of-distribution — organic failures are messier and more realistic.
2. **Align evaluator** — split data 75/25 dev/test. Iterate on prompt template against dev set. Measure precision/recall on fail class + Cohen's Kappa (0.4-0.6 = substantial, >0.7 = excellent). Benchmark = human performance, not perfection.
3. **Run eval harness** — combine individual evaluators, run with each config change. Tight feedback loop = fast iteration. 200 samples for 95% CI on 5% defect rate.

## Anti-Patterns

- Off-the-shelf metrics (they lead people astray — build task-specific evals)
- Synthetic defects as sole eval data (too clean, out of distribution)
- Building a judge before looking at data
- Multi-dimensional scoring in a single prompt
- Skipping the human labeling step because "we can automate it"

## Applied to Thalamus

- **Dimension 1:** "Is the banking_so_what actionable for HSBC governance consulting?"
- **Dimension 2:** "Are regulatory_exposure references grounded in the source article?"
- **Dimension 3:** (if needed) "Is the consulting_use classification correct?"
- **Organic failures:** Run same articles through Haiku extraction to generate natural failures
- **Critiques format:** "FAIL — The so-what is generic ('banks should watch this') instead of HSBC-specific ('HSBC should update their agent governance framework to cover plugin supply chain risk')"
- **Hamel's note on DSPy:** "I haven't had much luck with prompt optimizers like DSPy." Try manual iteration first.
