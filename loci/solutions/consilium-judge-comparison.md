---
title: Consilium Judge Model Comparison
date: 2026-03-19
tags: [consilium, experiment, judge-models]
---

# Consilium Judge Model Comparison

**Question:** "What is the biggest risk of AI in banking?"
**Mode:** `--council` (blind → debate → critique → final synthesis)
**Date:** 2026-03-19

## Summary

| Dimension | Gemini (gemini-3.1-pro-preview) | Opus (claude-opus-4-6) | Sonnet (claude-sonnet-4-6) |
|-----------|------|------|--------|
| **Cost** | ~$0.27 | ~$0.27 | ~$0.28 |
| **Time** | 328.8s | 359.8s | 458.8s |
| **Final answer** | Macro-prudential fragility via second-order AI correlation | Correlated model failure via homogenization of models, data & vendor infra | Automation velocity expanding blast radius faster than governance can contain it, with shared data dependencies as coupling mechanism |
| **Framing style** | Academic/regulatory — "second-order correlation" as concept | Systemic/structural — 2008 analogy as proof of concept | Operational/practical — blast radius, velocity, governance gap |
| **Key insight** | AI filters reality for human decision-makers; humans execute the crash themselves | Advisory influence on gated decisions IS the transmission mechanism, not a defence | Data supply chain (not model architecture) is the real single point of failure |
| **Strongest move** | Called out 5/5 LLM convergence as reflecting shared pre-training, not independent discovery | Demoted kill-switch drills from "Do Now" — can't switch off a recommendation that already shaped a mental model | Challenged its own prior synthesis on explainability; upgraded adversarial red-teaming to "Do Now" |
| **Critique response** | Revised to acknowledge epistemic limitations of LLM consensus; refined 2008 analogy | Acknowledged compound-risk framing was evasion; forced self to pick load-bearing component (correlation) | Most significant self-correction: reversed "skip explainability entirely" to "useful detection mechanism, not primary control" |

## Detailed Observations

### Gemini as Judge

**Character:** The most rhetorically polished and structurally clean. Uses evocative framing ("the wood and the spark") that makes the synthesis memorable. Thinks in terms of regulatory architecture.

**Epistemics:** Uniquely flagged that 5/5 blind-phase convergence likely reflects shared pre-training rather than independent discovery — the only judge to question the epistemic validity of the council's consensus. This is a genuinely sophisticated meta-cognitive move.

**Weakness:** The recommendations are the most conventional (map vendor overlap, audit pipelines, enforce air-gaps). The "Consider Later" section is thin — a single bullet on circuit breakers.

**Final synthesis core:** "Macro-prudential fragility driven by second-order AI correlation." When a widely shared AI data pipeline is poisoned, the error bypasses human oversight because humans implicitly trust their AI dashboards, propagating instantaneously across the sector.

### Opus as Judge

**Character:** The most intellectually rigorous and self-critical. Engages with the critique at the deepest level, genuinely updating its views rather than cosmetically adjusting. Thinks in terms of causal mechanisms and historical precedent.

**Epistemics:** Made the strongest single argument in the entire experiment: "Speaker 1's observation that most AI is still behind human gates describes the transmission mechanism, not a defence against it." This reframing — that human-gated advisory AI is *how* correlated failure propagates, not what prevents it — is the most original insight across all three judges.

**Weakness:** The recommendations, while well-argued, are pitched at institutional risk management level rather than regulatory architecture. Less actionable for a regulator, more actionable for a CRO.

**Final synthesis core:** "Correlated model failure driven by homogenization of models, training data, and vendor infrastructure — amplified by the fact that this correlation operates through advisory influence on human decisions, not just autonomous execution." The 2008 precedent is not an analogy — it is a proof of concept.

### Sonnet as Judge

**Character:** The most operationally grounded and self-aware about its own reasoning process. Engages in explicit metacognition about sycophancy, asymmetric treatment of convergence, and its own prior errors. Thinks in terms of blast radius, velocity, and governance gaps.

**Epistemics:** Made the sharpest correction to its own prior synthesis — reversing the dismissal of explainability from "skip" to "useful harm detection mechanism for tail cohorts." Also uniquely identified the asymmetry between credit and trading blast radii (different time-to-harm profiles requiring different controls).

**Weakness:** The final synthesis is the longest and most qualified. The proliferation of nuance occasionally dilutes the punch of the core argument. The "Consider Later" section has 4 items — arguably too much deferred.

**Final synthesis core:** "AI-driven decisions executing at automation velocity against shared upstream data infrastructure, generating harm in tail subpopulations before operational signals register — at a scale and speed that outstrips the organisational authority to halt them." Coupling runs through shared data and incentives, not architecture.

## Key Differences in Recommendations

| Priority | Gemini | Opus | Sonnet |
|----------|--------|------|--------|
| **Do Now #1** | Map sector-wide vendor/model overlap | Map correlation exposure across 5 decision categories | Operational signal monitoring (complaints, freeze volumes, decline concentrations) |
| **Do Now #2** | Audit second-order perception pipelines | Stress-test AI-advised decisions under regime-change scenarios | Data dependency audit |
| **Do Now #3** | Enforce logical air-gaps between assistive AI and execution | Red-team AI-enabled controls with adversarial inputs | Adversarial red-team of credit/fraud models |
| **Skip** | Firm-level MRM (SR 11-7) alone | Bias/fairness as primary frame; human overrides as sufficient; kill-switch drills as primary mitigation | Model architecture diversity mandates alone; explainability as primary safety control |

## Verdict

All three judges converged on the same structural diagnosis (correlated failure via homogenization) but differed meaningfully in:

1. **Where they locate the coupling:** Gemini says vendor/model overlap; Opus says models + data + incentives; Sonnet says data supply chain specifically (not architecture).
2. **What they do with the critique:** Opus made the deepest intellectual update. Sonnet made the most operationally consequential corrections. Gemini made the most epistemically interesting observation (questioning LLM consensus validity).
3. **Recommendation style:** Gemini is regulatory-architecture-first. Opus is causal-mechanism-first. Sonnet is operational-readiness-first.

**For consulting use:** Sonnet's operationally grounded framing and specific blast-radius thinking would land best with a banking client. Opus's synthesis would be strongest for a regulator or policy audience. Gemini's framing is best for an academic or thought-leadership piece.

**Overall quality ranking:** Opus > Sonnet > Gemini (marginal). Opus wins on intellectual depth and the quality of its self-correction. Sonnet wins on operational specificity. Gemini wins on rhetorical clarity and the epistemic meta-point about LLM consensus.

## Reproduction

```bash
consilium --council "What is the biggest risk of AI in banking?" -J gemini
consilium --council "What is the biggest risk of AI in banking?" -J opus
consilium --council "What is the biggest risk of AI in banking?" -J sonnet
```
