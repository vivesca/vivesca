# Group Deliberation Research — Key Findings for AI Deliberation Design

Researched: 2026-02-18. Purpose: informing multi-LLM deliberation tool design.

## 1. Group Deliberation Core Findings

**Key pathologies:**
- Group polarization (choice shift): deliberation amplifies initial leanings, not corrects them
- Hidden profile effect (Stasser & Titus 1985): groups over-discuss shared info, suppress unique info
- Groupthink: cohesion + social pressure → suppressed dissent, illusion of unanimity
- Common knowledge bias: majority-known information dominates discussion

**What actually helps:**
- Cognitive diversity in the pool (diverse perspectives > large homogenous group)
- Prediscussion individual commitment (write before sharing)
- Making it a "solve" vs "judge" task (demonstrably correct answers surface unique info better)
- Transparency about who holds what unique information
- Naive (undecided) groups detect hidden profiles better than pre-committed ones

## 2. Delphi Method — Why It Works

Key structural features that matter:
- Anonymity: removes dominance effects, reduces social pressure
- Iteration with feedback: experts revise in light of others' positions (controlled, not real-time)
- Statistical aggregation: avoids pressure-to-conform; aggregates independent judgments
- No face-to-face: eliminates status/personality confounds

Design translation: asynchronous, structured rounds > open free-form discussion

## 3. Devil's Advocate vs. Authentic Dissent (Nemeth, Berkeley)

Critical finding: Assigned devil's advocate is LESS effective than authentic dissent.

- DA produces cognitive bolstering of the original position (people argue against DA)
- Authentic dissent produces divergent thinking — broader information search, higher creativity
- Mechanism: authenticity signals the dissenter is paying a "cost" — this signals genuine belief, which is cognitively stimulating in a way role-play is not
- Key paper: Nemeth (2001), EJSP — "Devil's advocate versus authentic dissent"

Design implication: Don't assign a devil's advocate role. Instead, use genuinely distinct model perspectives, or require each agent to independently argue from a different epistemic prior before seeing others' outputs.

## 4. Wisdom of Crowds — Conditions for Aggregation to Work

Surowiecki's four required conditions:
1. Diversity of opinion (different information/models)
2. Independence (judgments not influenced by each other before formed)
3. Decentralization (can draw on local/specialized knowledge)
4. Aggregation mechanism (turns private judgments into collective output)

Key failure mode: Too much communication destroys independence → herding → crowds become dumb
Key success: Errors cancel out only when independent — correlated errors don't cancel

Design implication: Generate independent first-pass answers before any exposure to other agents' outputs. Never let agents see each other before forming initial position.

## 5. Groupthink (Janis) — Subsequent Research Update

Original Janis (1972) symptoms: illusion of invulnerability, collective rationalization, pressure on dissenters, self-censorship, illusion of unanimity.

What subsequent research found:
- The cohesion → groupthink link is NOT consistently supported empirically
- Structural conditions (directive leadership, homogeneity, lack of procedures) are better predictors
- Park (1990) meta-analysis: no significant main effect of cohesiveness on groupthink symptoms
- The SYMPTOMS Janis identified are real; the antecedents he proposed are weaker

Design implication: Structural safeguards (forced independent generation, explicit dissent protocols) matter more than trying to engineer "low cohesion" between agents.

## 6. Superforecasting / Good Judgment Project (Tetlock & Gardner)

Key findings:
- Team collaboration substantially improves accuracy, but only with the right culture
- Leaders should NOT reveal their opinion at the start (anchoring destroys independence)
- Psychological safety for dissent is critical — teams need permission to challenge
- "Extremizing" aggregation: if normally-disagreeing agents agree, the consensus should be pushed further toward certainty than the average
- Deliberation time correlates with accuracy
- Brief training on probabilistic reasoning has persistent effects (>1 year)
- Decomposing complex questions into sub-questions (Fermi estimation) improves accuracy

Design implication: Weight aggregated outputs more heavily when independent agents converge. Use extremizing aggregation. Decompose complex questions before distributing to agents.

## 7. Structured Analytic Techniques (SATs) — Intelligence Community

Key techniques:
- Analysis of Competing Hypotheses (ACH, Heuer): list ALL hypotheses first, evaluate evidence against each simultaneously, eliminate rather than confirm
- Key assumption check: make assumptions explicit before analysis
- Pre-mortem / Red Team: imagine failure, work backward

Effectiveness evidence:
- RAND (RR1408): IC doesn't systematically evaluate SATs; evidence base is weak
- ACH did not consistently outperform simpler techniques in controlled studies
- But: Dhami (2019, Applied Cognitive Psychology) finds ACH is useful specifically when evidence is incomplete/uncertain/contradictory
- Practitioner value: forcing structure surfaces hidden assumptions; main benefit is process discipline, not outcome superiority

Design implication: ACH logic is useful for structuring agent tasks — force each agent to consider multiple hypotheses and argue for/against rather than advocate a single conclusion.

## 8. LLM Multi-Agent Debate (MAD) — Current Research State

Original positive result: Du et al. (2023, ICML 2024) — multiagent debate improves factuality and mathematical reasoning; "society of minds" approach reduces hallucinations.

Sobering replication/extension (ICLR 2025 blog, multiple 2024-2025 papers):
- MAD frameworks fail to consistently outperform single-agent + self-consistency
- Majority voting alone accounts for most apparent gains from MAD
- Multi-Persona (rigid devil's advocate structure) performed worst
- Mixing models of different capabilities HARMS performance (contradicts diversity assumption)

Key failure mode — sycophancy:
- Agents converge toward agreement regardless of correctness
- "Correct-to-incorrect" flips exceed "incorrect-to-correct" improvements
- Agents most likely to change position when isolated (social conformity effect)
- Disagreement rate decreases as debate progresses — correlated with performance degradation
- CONSENSAGENT (ACL 2025) proposes dynamic prompt refinement to mitigate sycophancy

What design choices show promise:
- Fine-grained reasoning analysis (not whole-response deliberation)
- Confidence/credibility weighting (not equal-weight consensus)
- Independent verification before exposure to other agents
- Penalizing unsupported conformity
- Task-specific training (generic pretrained models may not debate well)
- Heterogeneous specialist agents > homogenous generalists (but must be same capability tier)

## Design Principles Summary (Cross-Source)

1. **Independence first**: Generate independent outputs before any cross-exposure. This is the single most consistent finding across wisdom of crowds, Delphi, Tetlock, and MAD research.

2. **Authentic perspectives > assigned roles**: Don't assign devil's advocate. Use genuinely distinct priors, personas, or specializations.

3. **Diverge before you converge**: Force divergent thinking first (brainstorm, independent analysis), then structured convergence. Don't run open discussion from the start.

4. **Surface unique information explicitly**: Hidden profile effect is severe. Structure prompts so each agent must contribute what only it knows/thinks, not just discuss common ground.

5. **Extremize converging consensus**: When independent agents agree, treat this as stronger signal than the average suggests. Weight convergent independent judgments heavily.

6. **Leader/moderator stays neutral**: Anchor effects from early revealed preferences are large. Any aggregating/synthesizing role should not express a view first.

7. **Penalize sycophancy structurally**: Reward maintained positions under challenge, not position changes. Flag agents that shift without presenting new evidence.

8. **Structure the task**: ACH logic — list competing conclusions, evaluate evidence against each. Don't free-form debate.

9. **Decompose complex questions**: Sub-questions before synthesis. Fermi estimation approach.

10. **Iterate with controlled feedback**: Delphi model — not real-time debate but structured rounds with summary feedback between rounds.
