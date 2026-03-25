# Multi-LLM Deliberation Architecture Research (Mar 2026)

## Key Papers

- **Du et al. 2023 (ICML 2024)** — "Improving Factuality and Reasoning through Multiagent Debate": arxiv.org/abs/2305.14325. Primary result: debate among 3 agents over 2 rounds improves math/factuality. Performance scales with agent count and round count. Works across black-box models.
- **Khan et al. 2024 (ICML Best Paper)** — "Debating with More Persuasive LLMs Leads to More Truthful Answers": arxiv.org/abs/2402.06782. Asymmetric debate (expert advocates for correct answer vs incorrect) gets 76-88% accuracy vs 48-60% naive baseline. Optimising for persuasiveness improves judge accuracy.
- **ReConcile 2024 (ACL)** — arxiv.org/html/2309.13007v3. 3 cross-lab models (ChatGPT, Bard, Claude2), 3 rounds, confidence-weighted voting. +11.4% over homogeneous MAD baselines; outperformed GPT-4 on 3 datasets. Diversity reduces response similarity (0.87 vs 0.91 cosine score).
- **Language Model Council 2024** — arxiv.org/abs/2406.08598. 20 models, peer review format, more robust and human-aligned than any single judge.
- **ChatEval 2023/ICLR 2024** — arxiv.org/abs/2308.07201. One-by-one communication better than simultaneous for ChatGPT. Diverse role prompts essential — same role = performance degradation.
- **"Debate vs Vote" (NeurIPS 2024)** — openreview.net/forum?id=iUjGNJzrF1. Majority voting alone accounts for most gains attributed to MAD. Debate is a martingale — doesn't improve expected correctness without targeted interventions.
- **Estornell & Liu NeurIPS 2024** — Multi-LLM Debate Framework. Convergence to majority opinion = key failure mode, especially when models share training data misconceptions.
- **ICLR Blogpost 2025** — d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/. MAD fails to consistently beat CoT+Self-Consistency. Model diversity (GPT-4o-mini + Llama 70b) showed consistent improvements.
- **"Peacemaker or Troublemaker"** — arxiv.org/html/2509.23055v1. Sycophancy cascades intensify in later rounds. Mixed peacemaker/troublemaker config outperforms uniform. r=0.902 correlation between sycophancy and wrong answer convergence.
- **"Talk Isn't Always Cheap"** — arxiv.org/html/2509.05396v1. Stronger agents flip correct→wrong when exposed to weaker peers more often than weaker learn from stronger. Heterogeneous groups with weaker models can degrade performance.
- **Justice or Prejudice (CALM)** — llm-judge-bias.github.io. 12 judge biases identified. Key: Compassion-Fade (model identity leakage), Self-Enhancement (self-preference), Fallacy-Oversight (worst score: 0.566), Position bias.
- **DEBATE (ACL 2024 Findings)** — aclanthology.org/2024.findings-acl.112. Devil's advocate role assignment outperforms state-of-the-art on SummEval + TopicalChat.
- **Multi-Agent Debate for LLM Judges** — arxiv.org/abs/2510.12697. Adaptive stopping via KS test; Beta-Binomial mixture for consensus tracking; outperforms majority voting.

## Reliable Source Access Patterns
- arxiv.org abstract pages: WebFetch works but gets abstract only; use search summaries for key numbers
- arxiv.org/html/ versions: WebFetch works, returns full paper content
- aclanthology.org: metadata only via WebFetch; .pdf versions return binary
- openreview.net: WebFetch works on forum pages (abstract + reviews)
- proceedings.neurips.cc: WebFetch works on abstract pages
- composable-models.github.io: WebFetch works

## Key Facts for Consilium Architecture Assessment

### What works
- Cross-lab diversity consistently improves performance (ReConcile +11.4%, ICLR 2025 findings)
- Blind first round prevents authority/identity bias (confirmed by CALM 12-bias taxonomy)
- Rotating challenger / devil's advocate role statistically improves accuracy (DEBATE ACL 2024)
- Mixed peacemaker/troublemaker composition outperforms uniform (Peacemaker paper)
- Confidence-weighted voting (not simple majority) is better aggregation (ReConcile)
- Adaptive stopping better than fixed rounds (KS test paper, arxiv 2510.12697)
- Separate judge from panelists — judge seeing debate transcript improves over single-shot (ChatEval, DEBATE)
- Persuasive debaters help non-expert judges reach truth (Khan 2024)

### What fails
- Sycophancy cascades intensify in rounds 3+ — 2-3 rounds is sweet spot
- Weaker models in panel can cause stronger models to flip correct→wrong
- Simple majority voting ≈ debate value in many settings; targeted interventions needed
- Shared training data = shared misconceptions → debate reinforces rather than corrects
- Model identity leakage biases judge (Compassion-Fade in CALM)
- Fallacy-Oversight: judges ignore logical errors in reasoning steps (worst bias, 0.566 score)
- Position/presentation order affects judge; mitigate with response-swap test
- Self-Enhancement: judge favors own outputs; use cross-lab judge not from panelist family

### Optimal configuration guidance
- 3-5 models sufficient; returns diminish past 5-7
- 2-3 rounds max; sycophancy worsens after
- Blind label (Response A/B/C not model name) for judge
- Judge should be different model family from all panelists
- Run swap-order test on judge outputs to detect position bias
- Confidence-weighted > majority vote > simple average
- Devil's advocate role should be rotating, not fixed (stale adversary loses effect)
- KS-test or distributional convergence > fixed round count for stopping

## Common Misinformation
- "More rounds = better" — FALSE after round 3; sycophancy intensifies
- "More agents = better" — diminishing returns; weaker agents can HURT quality
- "MAD beats CoT" — NOT reliably; CoT+Self-Consistency often wins on benchmarks
- "Debate alone improves expected correctness" — FALSE; it's a martingale; need targeted interventions
