# melete source line range lookup — gotcha and fix pattern

**LRN-20260312-001**

## Problem

`melete session` shows a `Read` path with a line range for each topic. For topics without an explicit `search_terms` entry in `~/code/melete/src/main.rs`, the binary falls back to word-splitting the topic name (e.g. `M2-rl-value-functions` → `["Rl", "Value", "Functions"]`) and searches for the first heading or content line in the raw module file that matches any term.

Module 2 raw content is ~32K lines with repeated OCR artefacts (table of contents blocks). Generic terms like "Value", "Data", "Linear" match early unrelated sections (regression trees, ANN option pricing) before reaching the correct section.

## Affected session

Mar 12 — Q4 (M2-rl-value-functions → pointed to regression trees at line 237), Q8 (M2-data-types → pointed to ANN example at line 628).

## Fix

Add explicit `search_terms` entries in `fn search_terms(topic: &str)` in `src/main.rs`. Use heading text that uniquely identifies the correct section.

Entries added Mar 12:
- `M2-data-types` → `["Data Collection And Preparation", "Structured", "Unstructured"]`
- `M2-data-cleaning` → `["Data Cleaning", "1.3.2"]`
- `M2-train-val-test-split` → `["Training Validation And Testing", "Cross Validation", "7.7"]`
- `M2-linear-regression` → `["Ordinary Least Squares", "7.2 Least Squares", "Linear Regression"]`
- `M2-rl-value-functions` → `["Terminology in Reinforcement", "Value Function", "Action-Value"]`
- `M2-nlp-pipeline` → `["Data Pre Processing", "Tokenization", "Stemming", "Lemmatization"]`

## Rule

When adding a new topic to the FSRS state, **immediately** check if the auto-generated terms will collide with early unrelated content. If the topic name contains generic words (Data, Value, Type, Linear, Model) → add an explicit `search_terms` entry before the next session. Don't wait for a wrong question to surface it.

Verify with: `melete session 1 2>&1 | grep <topic>` and check the line range points to the right section.
