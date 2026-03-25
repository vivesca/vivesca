# Eval Designer Agent Memory

## Pattern: RAG + Regulated FS

**Recurrent across HK/FS RAG systems:**
- Source fabrication (F2) and factual hallucination (F1) are always Critical — 0% acceptable
- Officers treat confident outputs as authoritative under time pressure regardless of disclaimers — design evals around behavioral reality, not intended use
- Corpus version control is a prerequisite for any meaningful eval — if client can't tell you what version a document is, you can't run M5 or M8
- Citation existence check (M1) is the one deterministic check that catches the worst failure mode cheaply — always lead with it
- ROUGE/BERTScore/cosine similarity are useless for compliance RAG — surface similarity ≠ factual accuracy; document this explicitly so clients don't request them

**Non-technical operator protocol:**
- Binary pass/fail per failure mode, not Likert scales — Likert scores cannot be acted on or audited
- Stratified random sampling beats convenience sampling; document the stratification logic
- Two named reviewers with a calibration set beats rotating reviewers — consistency is defensible
- Weekly (automated) + monthly (human review) + quarterly (adversarial battery) cadence works for FS clients with no MLOps team

**Adversarial test design:**
- "Plausible-sounding no-answer" questions are the gold standard for hallucination testing — must be written by someone who knows the corpus
- Any substantive answer on a no-answer question is an automatic Critical failure, not a rate to be tracked

**Go/no-go gates:**
- Never deploy into regulatory filing workflows without passing: citation existence 100%, factual accuracy >95%, adversarial hallucination 0% — in that order
- Do not claim business impact until technical thresholds hold for two consecutive review cycles

## Vanity Metrics to Reject

- ROUGE, BERTScore, cosine similarity (surface similarity ≠ accuracy)
- User satisfaction (satisfied with confident wrong answer is worse than neutral)
- % questions answered (high coverage on a hallucinating system = dangerous)
- Retrieval score (internal scoring doesn't predict answer accuracy)
