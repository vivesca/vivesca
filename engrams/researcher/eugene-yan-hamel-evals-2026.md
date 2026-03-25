---
name: Eugene Yan & Hamel Husain LLM Evaluation Content
description: Comprehensive index of Eugene Yan (eugeneyan.com) and Hamel Husain (hamel.dev) posts on LLM evaluation, LLM-as-judge, and eval-driven development. Key frameworks, practical approaches, and common pitfalls.
type: reference
---

# Eugene Yan & Hamel Husain: LLM Evaluation Posts & Frameworks

## Eugene Yan (eugeneyan.com) — Core Articles

### 1. **Evaluating the Effectiveness of LLM-Evaluators (aka LLM-as-Judge)**
**URL:** https://eugeneyan.com/writing/llm-evaluators/

**Key Insight:** LLM-evaluators vary wildly in effectiveness; no one-size-fits-all. Provides decision tree: objective tasks (classification/toxicity) → direct scoring + binary; subjective tasks (tone/coherence) → pairwise comparisons (more stable).

**Framework Sections:**
- Key considerations (baseline, scoring, metrics)
- Use cases (summarization, QA, toxicity, hallucination detection)
- Prompting techniques (chain-of-thought, pairwise, multi-turn)
- Alignment strategies (calibration workflows)
- Finetuning approaches (custom evaluator models)
- Critical analysis (biases, limitations)

**Critical Recommendation:** Pairwise comparisons yield more stable results for subjective evals; use Cohen's kappa to measure agreement (not correlation alone).

---

### 2. **Product Evals in Three Simple Steps**
**URL:** https://eugeneyan.com/writing/product-evals/

**Key Insight:** Consistency and scalability > perfect accuracy. Three mechanical steps: (1) label small dataset, (2) align LLM evaluator via iteration, (3) integrate into experiment harness.

**Labeling Best Practices:**
- **Binary > Likert scales.** The difference between "3" and "4" is fuzzy for both humans and LLMs. Binary decisions (pass/fail, win/lose) are clearer and more consistent.
- **Balanced failure representation:** Need at least 50-100 failures out of 200+ samples (not sparse failure cases).
- **Single-criterion evaluators:** Build individual evaluators for one metric each (e.g., "factuality" separate from "tone"), not multi-dimensional evals.

**Alignment Principle:** Real benefit isn't exceeding human performance but enabling reliable, round-the-clock evaluation at scale.

---

### 3. **An LLM-as-Judge Won't Save The Product—Fixing Your Process Will**
**URL:** https://eugeneyan.com/writing/eval-process/

**Key Insight:** The core problem is process, not tools. LLM-as-judge is a band-aid for organizational lack of discipline. Evals are the scientific method in disguise.

**Three Interconnected Practices (not tools):**
1. **Scientific method:** Observe → annotate → hypothesize → experiment → measure. Identify and address failure modes systematically.
2. **Eval-driven development (EDD):** Define success criteria via evals before building. Measurable alignment from the start.
3. **Continuous human oversight:** Active sampling, annotation, feedback analysis. Automated evals amplify rather than replace human judgment.

**Verdict:** Tool-buying can't fix process failure. Organizational discipline matters more than eval infrastructure.

---

### 4. **Task-Specific LLM Evals that Do & Don't Work**
**URL:** https://eugeneyan.com/writing/evals/

**Key Insight:** Generic evals fail for complex tasks. Human evaluation still gold standard for reasoning, QA, domain-specific knowledge. Specific guidance per task type.

**What Works:**
- **Classification:** ROC-AUC, PR-AUC (accuracy too coarse)
- **Summarization:** Finetuned NLI models for factual consistency (ROC-AUC 0.85 post-tuning vs 0.56 baseline); reward models for relevance
- **Translation:** chrF, COMET, COMETKiwi outperform BLEU; COMETKiwi enables reference-free eval

**What Doesn't Work (unreliable/impractical):**
- N-gram metrics (ROUGE, METEOR)
- Similarity-based approaches
- LLM-based evals like G-Eval (insufficient recall, costly)
- Reference-based summarization evals (require expensive gold annotations)

**Recommendation:** Human evaluation remains essential for complex/open-ended tasks.

---

### 5. **Evaluating Long-Context Question & Answer Systems**
**URL:** https://eugeneyan.com/writing/qa-evals/

*Specific guidance for Q&A evaluation via human annotations and LLM-evaluators.*

---

### 6. **AlignEval: Building an App to Make Evals Easy, Fun, and Automated**
**URL:** https://eugeneyan.com/writing/aligneval/

*Tooling for eval alignment and collaboration.*

---

## Hamel Husain (hamel.dev) — Complementary Articles

### 1. **Using LLM-as-a-Judge For Evaluation: A Complete Guide**
**URL:** https://hamel.dev/blog/posts/llm-judge/

**Key Insight:** Don't start with the judge. Start with domain expert judgment and data review. "Critique Shadowing" workflow extracts alignment from human decisions.

**Seven-Step Process (Critique Shadowing):**
1. Identify principal domain expert (the person whose judgment drives success)
2. Build diverse dataset (features, scenarios, personas)
3. Collect pass/fail judgments + detailed critiques (expert's binary decisions)
4. Fix discovered errors
5. Build LLM judge iteratively (prompt templates from examples)
6. Perform error analysis (classify failures by root cause)
7. Create specialized judges (targeted evaluators per failure pattern)

**Critical Mistakes to Avoid:**
- Arbitrary 1-5 scoring scales (inconsistent, fuzzy boundaries)
- Skipping human data review (this step drives business value, not the judge)
- Too many metrics (focus on what matters)

**Best Practices:**
- Start with ~30 examples; continue until no new failure modes emerge
- Detailed critiques: "detailed enough a new employee understands"
- Include external context (user metadata, system info)
- Measure precision & recall separately (not just agreement)
- Use most powerful model you can afford (judges often require more compute than production systems)

**Core Truth:** Real value comes from analyzing data carefully, not from the judge infrastructure.

---

### 2. **LLM Evals: Everything You Need to Know**
**URL:** https://hamel.dev/blog/posts/evals-faq/

**Key Insight:** Error analysis is foundational. Start with manual review of 20-50+ traces to identify YOUR failure modes, not generic metrics.

**Minimum Viable Setup:**
- 30 minutes reviewing production outputs when making changes
- One domain expert as "benevolent dictator" (single point of judgment)
- Notebooks for reviewing traces (not fancy infrastructure)

**Binary Over Likert:** "Binary evaluations force clearer thinking and more consistent labeling."

**Error Analysis Process (structured):**
1. Gather representative traces
2. Open coding (write notes about issues)
3. Axial coding (group failures into categories)
4. Iterate until theoretical saturation (~100 traces reviewed)

**Skip Generic Metrics:** "These metrics measure abstract qualities that may not matter for your use case." Build application-specific evaluators from discovered failure patterns.

**Custom Annotation Tools:** Teams with customized interfaces iterate ~10x faster than off-the-shelf solutions (even simple tools showing all context in one place help dramatically).

**Time Budget:** Expect 60-80% of eval development time on error analysis and annotation (not automation).

**Domain-Specific Guidance:**
- **RAG:** Separate retrieval metrics (IR metrics) from generation metrics
- **Multi-turn conversation:** Fix first upstream failure (resolves dependent failures)
- **Complex workflows:** Log entire processes with human handoffs and business outcomes, not just LLM calls

---

### 3. **Your AI Product Needs Evals**
**URL:** https://hamel.dev/blog/posts/evals/

*Foundational argument for eval-driven product development.*

---

### 4. **A Field Guide to Rapidly Improving AI Products**
**URL:** https://hamel.dev/blog/posts/field-guide/

*Structured approach to error analysis and systematic improvement.*

---

## Key Frameworks Summary

### Eugene Yan's Decision Tree (LLM-as-Judge)
```
Objective tasks (factuality, toxicity)
  → Direct scoring + binary classification
Subjective tasks (tone, coherence)
  → Pairwise comparisons (more stable)
Development phase
  → LLM APIs + chain-of-thought
Production guardrails
  → Finetuned classifiers (latency/cost)
```

### Hamel's Critique Shadowing (7 Steps)
Domain expert → Diverse dataset → Pass/fail + critiques → Fix errors → Iterate LLM judge → Error analysis → Specialized judges

### Process Framework (Eugene Yan)
Scientific method (observe → annotate → hypothesize → experiment → measure) + Eval-driven development (define criteria upfront) + Continuous human oversight (human-in-the-loop feedback).

---

## Common Pitfalls (Cross-Referenced)

| Pitfall | Yan | Hamel | Recommendation |
|---------|-----|-------|-----------------|
| Likert scales (1-5) | ✓ | ✓ | Use binary (pass/fail, win/lose) |
| Multi-dimensional evals | ✓ | ✓ | Single-criterion evaluators |
| Starting with automation | ✓ | ✓ | Start with manual error analysis |
| Generic metrics | ✓ | ✓ | Build application-specific evals |
| Too many metrics | — | ✓ | Focus on what matters |
| Assuming judge > data review | — | ✓ | Data review drives value |

---

## When to Apply Each Approach

**Eugene Yan best for:**
- Understanding which eval approaches work per task type (classification, summarization, translation)
- Task-specific metric guidance
- Deciding between LLM judges vs finetuned classifiers

**Hamel Husain best for:**
- Operational process (how to actually build an evaluator)
- Error analysis methodology
- Organizational/team coordination
- Avoiding premature automation

**Both together:**
- Understand the process (Hamel) + pick the right tool (Yan)
- Error analysis + eval alignment workflows
- Binary evals as the shared baseline

---

## Additional Resources Mentioned

- **Hamel + Shreya Shankar:** "AI Evals For Engineers & PMs" (Maven course)
- **Hamel's Lenny's Newsletter post:** "Evals, error analysis, and better prompts: A systematic approach to improving your AI products"
- **Eugene Yan's Book:** "AI Evals for PMs and Engineers" (O'Reilly, has chapter on building LLM-evaluators)

---

## Search Strategy for Future Research

- **Site-specific:** `site:eugeneyan.com eval` or `site:hamel.dev eval` for tag-based browsing
- **Key terms:** "LLM-as-judge," "error analysis," "critique shadowing," "eval-driven development," "binary evaluation"
- **Follow-ups:** Both authors cite academic papers; search their posts for arxiv links for deeper dives

---

**Last Updated:** 2026-03-14 (WebFetch verified, all URLs tested)
