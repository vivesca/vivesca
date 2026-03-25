# Multi-LLM Deliberation Architecture Research

**Researched:** 2026-03-03
**Sources:** background agent (15 papers) + pplx pro search + pplx deep research (sonar-deep-research, Mar 2026)
**Applied to:** consilium (`~/code/consilium`)

## Key Papers

- **Du et al. 2023 (ICML 2024)** — Founding MAD paper. 3 agents, 2 rounds improves math/factuality. Works on black-box models. [arxiv 2305.14325](https://arxiv.org/abs/2305.14325)
- **Khan et al. 2024 (ICML Best Paper)** — Asymmetric debate: expert argues correct vs incorrect. 48% → 76–88% accuracy. Optimising for persuasiveness improves judge accuracy. [arxiv 2402.06782](https://arxiv.org/abs/2402.06782)
- **ReConcile 2024 (ACL)** — 3 cross-lab models, 3 rounds, confidence-weighted voting. +11.4% over homogeneous MAD, beat GPT-4 on 3 datasets. Response similarity 0.87 (cross-lab) vs 0.91 (single model). [arxiv 2309.13007](https://arxiv.org/html/2309.13007v3)
- **Language Model Council 2024** — 20 models, peer review format. Panel judges more human-aligned than any single judge. [arxiv 2406.08598](https://arxiv.org/abs/2406.08598)
- **ChatEval (ICLR 2024)** — One-by-one sequential beats simultaneous. Diverse role prompts essential; same role = degradation. [arxiv 2308.07201](https://arxiv.org/abs/2308.07201)
- **"Debate vs Vote" (NeurIPS 2024)** — **CRITICAL:** Majority voting alone accounts for most debate gains. Debate is a martingale — no improvement in *expected* correctness without targeted interventions (challenger, diversity, confidence weighting). [openreview iUjGNJzrF1](https://openreview.net/forum?id=iUjGNJzrF1)
- **Estornell & Liu (NeurIPS 2024)** — Convergence to majority = key failure mode. Shared training data → shared misconceptions → debate reinforces wrong answers. [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/32e07a110c6c6acf1afbf2bf82b614ad-Abstract-Conference.html)
- **ICLR Blogpost 2025** — MAD fails to consistently beat CoT+Self-Consistency. Model diversity (GPT-4o-mini + Llama 70b) showed consistent gains. [blog](https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/)
- **"Peacemaker or Troublemaker"** — Sycophancy cascades intensify in rounds 3+. r=0.902 correlation sycophancy↔wrong answer. Mixed peacemaker/troublemaker outperforms uniform. [arxiv 2509.23055](https://arxiv.org/html/2509.23055v1)
- **"Talk Isn't Always Cheap"** — Stronger models flip correct→wrong from weaker peers more often than weaker learn from stronger. Heterogeneous groups can degrade. [arxiv 2509.05396](https://arxiv.org/html/2509.05396v1)
- **CALM — Justice or Prejudice** — 12 judge biases. Key: Compassion-Fade (model identity leakage), Self-Enhancement (self-preference), Fallacy-Oversight (worst, 0.566 score), Position bias. [llm-judge-bias.github.io](https://llm-judge-bias.github.io/)
- **DEBATE (ACL 2024 Findings)** — Devil's advocate role outperforms SOTA on SummEval + TopicalChat. [ACL 2024](https://aclanthology.org/2024.findings-acl.112/)
- **Multi-Agent Debate for LLM Judges** — Adaptive stopping via KS test; Beta-Binomial convergence tracking. Beats fixed rounds + majority vote. [arxiv 2510.12697](https://arxiv.org/abs/2510.12697)
- **"Heterogeneity > Scale"** — 2 heterogeneous agents match/exceed 16 homogeneous on same budget (8x efficiency). 4-layer diversity: prompting → persona → model → combined. Each layer adds non-trivially. [arxiv 2602.03794](https://arxiv.org/html/2602.03794v1)
- **Dynamic Role Assignment** — 2-stage meta-debate: first elicit role-specific proposals, then peer-review to select optimal assignment. Up to 74.8% improvement over fixed/random role assignment. [arxiv 2601.17152](https://arxiv.org/html/2601.17152v1)
- **IBC / Anonymization Paper** — Identity Bias Coefficient: conformity (sycophancy) substantially exceeds obstinacy across GPT-4o, Claude 3.5 Sonnet, Llama 3.1. Response anonymization reduces conformity most. Validates anonymous=true design. [arxiv 2510.07517](https://arxiv.org/html/2510.07517v1)
- **Calib-n / Confidence Calibration** — Inter-model agreement is a better confidence proxy than verbalized N/10 scores. Auxiliary models trained on agreement patterns outperform all baselines. Focal loss > binary cross-entropy for aggregation. [ACL 2025](https://aclanthology.org/2025.acl-long.188.pdf)
- **Entropy Dynamics (MAS Uncertainty)** — Uncertainty determined in round 1, not later rounds. High inter-agent entropy dispersion in later rounds → failure (ρ≥0.66). "Certainty preference" + "base uncertainty" + "task awareness" are the three key factors. [arxiv 2602.04234](https://arxiv.org/html/2602.04234v1)
- **Judge Panel Size** — 2 judges (collaborative discussion) > 1 judge; 3 judges shows slight decline vs 2. Optimal: small collaborative panel. [arxiv 2504.17087](https://arxiv.org/html/2504.17087v1)
- **CONSENSAGENT** — Prompt optimization framework: detects sycophancy via rapid consensus on identical explanations, answer-swapping, or obstinacy; dynamically adjusts prompts. 7-30% sycophancy reduction. [ACL 2025 Findings](https://aclanthology.org/2025.findings-acl.1141.pdf)

## What Works

- Cross-lab diversity (+11.4% ReConcile; ICLR 2025 consistent gains)
- 2 heterogeneous agents > 16 homogeneous on same budget — diversity beats scale 8:1
- Blind first round (prevents Compassion-Fade and authority anchoring)
- Rotating challenger / devil's advocate (DEBATE ACL 2024)
- Mixed peacemaker/troublemaker composition
- Confidence-weighted voting > majority vote (ReConcile) — but use inter-model agreement as proxy, not raw verbalized scores
- Separate judge not in panelist pool (prevents Self-Enhancement)
- 2-judge collaborative panel > 1 judge; stop at 2 (3 shows slight decline)
- Persuasive debaters help non-expert judges reach truth (Khan 2024)
- Adaptive stopping > fixed rounds (KS test, arxiv 2510.12697)
- Response anonymization reduces conformity (IBC paper) — already implemented as anonymous=true

## What Fails

- Sycophancy cascades at rounds 3+ — 2-3 round cap is critical
- Weaker models can drag stronger models to wrong answers (confidence weighting mitigates)
- Simple majority voting ≈ debate value; need targeted interventions
- Shared training data → shared misconceptions (cross-lab partially mitigates)
- Model identity leakage biases judge (Compassion-Fade)
- Fallacy-Oversight: judges ignore logical errors (worst bias, 0.566 score)
- Position/presentation order bias (randomize per round to mitigate)
- Self-Enhancement: judge favors same-lab outputs
- Verbalized confidence (N/10) is often poorly calibrated — models can be overconfident on hard questions and underconfident where they have expertise; inter-model agreement is a more reliable signal
- Single agent outperforms multi-agent in ~43% of cases when uncertainty accounted for; MAD is not universally better
- CommonSenseQA: debate consistently *hurts* performance — failure mode is task-specific
- High inter-agent entropy dispersion in later rounds → strong predictor of failure (ρ≥0.66)
- **Regulatory-framing groupthink:** Blind convergence on a technical concern can be the same reasoning pattern repeated (not genuinely independent priors), especially when all agents share domain training. Observed live: 4/5 panelists flagged "training signal" as SR 11-7 MRM risk — but the reasoning was identical across all four. Judge caught it after Gemini critique. Implication: discount unanimous alarm on domain-specific regulatory concerns; check whether the convergence reflects independent reasoning or shared framing bias.

## Protocol Selection by Task Type

| Protocol | Task type | Improvement |
|---|---|---|
| Voting / aggregation | Complex reasoning (multi-step derivation) | +13.2% |
| Consensus-seeking | Knowledge / judgment | +2.8% |

Consilium's judge-reads-debate architecture is closer to consensus-seeking, which suits its primary use case (judgment, analysis, decisions). If extended to hard reasoning chains, aggregating diverse model votes rather than seeking narrative consensus would be more effective.

## Common Misinformation

- "More rounds = better" — FALSE after round 3
- "More agents = better" — diminishing returns; weaker agents can HURT
- "MAD beats CoT" — NOT reliably; CoT+Self-Consistency often wins
- "Debate improves expected correctness" — FALSE; it's a martingale without interventions

## Consilium Architecture Assessment (Mar 2026)

| Design Choice | Evidence | Status |
|---|---|---|
| 5-model cross-lab panel | ReConcile, ICLR 2025 | ✅ Well-grounded |
| Blind first round | CALM Compassion-Fade | ✅ Well-grounded |
| anonymous=true (Speaker N labels) | CALM Compassion-Fade | ✅ Already implemented — judge sees "Speaker 1/2" not model names |
| Rotating challenger | DEBATE ACL 2024, Peacemaker | ✅ Well-grounded |
| Anti-capitulation prompt | Peacemaker sycophancy research | ✅ Already in council_debate_system |
| POSITION CHANGE labelling | Debate martingale research | ✅ Already required in prompt |
| Confidence: N/10 requested | ReConcile confidence weighting | ✅ In prompt; now also extracted for judge (shipped Mar 2026) |
| Opus judge not in panelist pool | Self-Enhancement bias | ✅ Good choice |
| Default 1 round, --deep = 2 | Sycophancy cascade at 3+ | ✅ Within safe range |
| Gemini critique layer | Multi-pass judgment literature | ✅ Good; now has CONSILIUM_MODEL_CRITIQUE_ENV |

## Improvements Shipped (Mar 2026)

1. **Confidence score extraction for judge** — `extract_confidence_score()` in council.rs. Extracts "Confidence: N/10" from last debate response per panelist. Judge user message now includes a "Final self-reported confidence scores" section, instructing Opus to weight high-confidence + independently-agreed positions more heavily, and to cross-check confidence drops against POSITION CHANGE labels.

2. **Gemini AI Studio fallback** — updated from `gemini-2.5-pro` → `gemini-3.1-pro-preview` in both `COUNCIL` const and `resolved_council()`.

3. **`CONSILIUM_MODEL_CRITIQUE_ENV`** — critique model now env-configurable, matching the judge env-override pattern.

## Remaining Gaps (lower priority)

- **Fallacy-Oversight**: Gemini critique prompt doesn't explicitly target logical fallacies. Fix: add rubric items for unsupported premises, invalid inferences, false dichotomies to the critique system prompt.
- **Response order randomization**: Same speaker order shown each debate round can create position anchoring. Fix: shuffle `previous_speakers` presentation order per round.
- **Position-swap check on judge**: Run Opus twice with response order reversed; flag low-confidence if verdict changes. Expensive — only worth it for `--deep`.
- **Confidence calibration**: ~~Current `extract_confidence_score()` reads raw N/10 from panelists. Per Calib-n research, this is poorly calibrated. A better signal is inter-model agreement (did multiple panelists independently reach the same position?). Short-term fix: in the judge prompt, note that verbalized scores can be overconfident on hard questions — treat high scores from models in disagreement skeptically.~~ **Shipped Mar 2026:** judge now receives full `BLIND CLAIMS` section + count of independent respondents. CONVERGENCE SIGNAL prompt updated with explicit blind→debate position comparison and sycophancy-drift detection. Judge can directly compare what each speaker said before vs after debate.
- **Dynamic role assignment**: Matching models to roles based on question-specific strengths (not static) can yield up to 74.8% improvement. Not feasible without a meta-debate stage, but worth revisiting if consilium gets a planning layer.
- **pplx `research` subcommand**: Returns 401 when credits are low (sonar-deep-research at $0.40/call has higher minimum than search/ask). Use `pplx ask` as fallback.
