# LLM Extraction Needs Negative Examples

When building LLM extraction/classification pipelines, negative examples reduce noise more than positive examples improve recall.

## The Problem
Oghma's extraction prompt said "extract key memories" with no guidance on what NOT to extract. Result: 21% of the corpus was narration — the LLM restating system prompt content as memories.

## The Fix
Adding explicit "DO NOT EXTRACT" rules with bad examples was dramatically more effective than vague quality guidance like "skip trivial content."

## Pattern
For any LLM extraction/classification task:
1. Start with positive examples (what to extract)
2. Add negative examples (what NOT to extract) — this is the high-leverage step
3. Add a deterministic post-filter for known noise patterns as cheap insurance
