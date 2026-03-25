
## no_hallucination criterion — proper noun false negatives (LRN-20260311-002)

When using `no_hallucination` as a judge criterion, the judge will sometimes flag
unfamiliar proper nouns (org names, product names, internal acronyms) as hallucinations.

**Example:** Judge failed a correct outreach message because "CNCBI" was flagged as
"possibly fabricated organisation name" — even though it's China CITIC Bank International.

**Fix:** Add to the judge system prompt:
> "For no_hallucination: only flag claims that contradict the input or are internally
> inconsistent. Do NOT flag proper nouns, organisation names, or technical terms
> simply because you don't recognise them."

Or alternatively: provide sender/context profile in the judge prompt so the judge
has ground truth for proper nouns.

Source: eval_judge_calibration.py JC003 (Mar 2026)

---

## Eval harness as regression test (LRN-20260311-003)

Once an eval suite exists, treat it as a **regression baseline for prompt/model changes**.
Before changing a system prompt, swapping a model, or adjusting rubric criteria:

1. Run the full eval suite → record baseline scores
2. Make the change
3. Re-run — any drop in pass rate is a regression signal

Suite at `~/code/eval-demo/`: oghma extraction, speculor triage, judge calibration.
Baseline: oghma 5/5, speculor 7/7, judge 7/8.

False positive rate is the key metric — **never pass bad work**. Acceptable to
be strict (false negatives); unacceptable to be lenient (false positives).
