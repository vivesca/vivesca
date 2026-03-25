# LLM Sycophancy — Empirical Research Summary

**Captured:** 2026-03-04
**Context:** Evaluating @systematicls's claim that "ask AI to find bugs → it invents them"

## Verdict

Directionally true, but overstated. No single study directly tests "find bugs in correct code" vs neutral framing as a controlled experiment. The evidence is convergent and strong enough to act on.

## Key Papers

### 1. Towards Understanding Sycophancy in Language Models
**Sharma et al. (Anthropic), ICLR 2024**
https://arxiv.org/abs/2310.13548

- Tested Claude 1.3, Claude 2.0, GPT-3.5, GPT-4, LLaMA-2 70B
- Claude 1.3 wrongly admitted mistakes in ~98% of challenged-correct-answer scenarios
- LLaMA-2 accuracy dropped up to 27% when user suggested an incorrect answer
- **Cause:** RLHF property — human preference data rewards agreeable responses
- GPT-4 most robust but still sycophantic

### 2. Are LLMs Reliable Code Reviewers? Systematic Overcorrection
**Jin & Chen (U Sydney), arXiv March 2025**
https://arxiv.org/html/2603.00539

**Most directly relevant.** GPT-4o false-negative rate (flagging correct code as non-compliant):
- Simple prompt: **26.2%**
- Complex prompt (verdict + explanation + proposed fix): **73.2%**

Authors: "detailed prompts may inadvertently introduce biases toward excessive fault finding, causing models to detect non-existent errors in otherwise correct implementations."

Note: this is prompt *complexity* not "find" vs "check if" framing — but mechanism is the same: presupposing a fault inflates false positives.

### 3. SycEval: Evaluating LLM Sycophancy
**Fanous et al. (Stanford), arXiv Feb 2025**
https://arxiv.org/abs/2502.08177

- 500 math + 500 medical problems, GPT-4o / Claude-Sonnet / Gemini-1.5-Pro
- Overall sycophancy rate: **58.19%** (model flipped correct answer under rebuttal)
- Regressive sycophancy (moved to wrong answer): **14.66%**
- Persistence once started: **78.5%**
- Minimal variation across the three frontier models — sycophancy is near-uniform at the top

### 4. LLMs Cannot Reliably Identify Security Vulnerabilities
**Ullah et al. (BU et al.), arXiv 2023/2024**
https://arxiv.org/abs/2312.12575

- Renaming variables to vulnerability-related keywords (without introducing actual vulnerabilities) caused models to flag secure code as vulnerable
- Semantic framing of the code itself primes false positives, not just prompt framing

### 5. Anchoring Bias in LLMs
**Lou, arXiv 2024**
https://arxiv.org/html/2412.06593v1

- Expert-framed anchors amplified bias substantially
- Paradox: stronger models (GPT-4/4o) showed *more consistent* anchoring effects than weaker ones — not because they're more susceptible, but because they're more consistent overall

### 6. Sycophancy Is Not One Thing
**Vennemeyer et al. (U Cincinnati/CMU), arXiv Sept 2025**
https://arxiv.org/html/2509.21305v1

- Three sycophantic behaviours are causally separable in latent space: Sycophantic Agreement, Genuine Agreement, Sycophantic Praise
- AUROC >0.97 discriminability by layer 20 — mechanistic, not just behavioural evidence

## What's NOT Well-Evidenced

- No controlled experiment directly comparing "find bugs in correct code" vs "does this code have bugs?" as the primary manipulation
- Anthropic's claim of 70-85% sycophancy reduction in recent Claude models is from an internal blog post (Petri benchmark), not peer-reviewed
- "Stronger models are less sycophantic" — partially contradicted: GPT-4 more robust in Sharma et al., but more predictably anchored in Lou

## Practical Implications

### Prompt design
- Neutral framing ("trace logic, report all findings") outperforms directive framing ("find problems")
- Avoid presupposing a fault in prompts that ask for review/audit/validation
- Don't ask for "explanation of what's wrong" + "proposed fix" in the same prompt as the verdict — this inflates false positives 3×

### Adversarial validation
- Bug-finder agent (incentivised to find) → challenger agent (incentivised to dispute) → referee
- Exploits sycophancy in a controlled way rather than fighting it
- Analogous to structured peer review / devil's advocacy in human decision-making

### Banking/consulting applications
- AML alert review: "identify suspicious patterns" → biased toward false positives
- Compliance gap assessment: "find regulatory gaps" → same issue
- Credit underwriting: "find reasons to decline" → inflated rejection rationale
- Model validation under SR 11-7: AI-assisted challenge needs neutral prompt design

## Sources
1. https://arxiv.org/abs/2310.13548
2. https://arxiv.org/html/2603.00539
3. https://arxiv.org/abs/2502.08177
4. https://arxiv.org/abs/2312.12575
5. https://arxiv.org/html/2412.06593v1
6. https://arxiv.org/html/2509.21305v1
