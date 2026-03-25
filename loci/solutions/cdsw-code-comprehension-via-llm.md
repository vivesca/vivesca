# CDSW: Use Internal LLM for Code Comprehension, Not Grep Scripts

## Problem

Writing keyword-matching scripts to extract answers from CDSW codebase produces too much noise. Each iteration returns "too many lines" for Terry to type back. Went through 6+ rounds before realising the approach was fundamentally wrong.

## Solution

Extract full function bodies with a Python script, save to a text file with a focused prompt, then paste into Open WebUI (Qwen 32B) for comprehension.

Pattern:
1. Script indexes all `nodes.py` functions, extracts targets + dependencies
2. Includes relevant config (parameters.yml, catalog.yml)
3. Saves complete prompt to `~/apm_kedro/marco_prompt.txt`
4. Terry downloads and pastes into Open WebUI
5. Qwen answers directly — no typing code back

## Key Details

- Tell the LLM to reply concisely ("MAX 2 lines per question, no preamble")
- Include domain context in the prompt (status codes, table names, known constraints)
- Add a dependency crawl: regex for `function_call(` in target bodies, extract those helper functions too
- Include config files (parameters.yml for thresholds, catalog.yml for data sources)
- Output to `~/apm_kedro/` not `/tmp/` (hidden on CDSW)

## Anti-Pattern

Don't write increasingly complex grep/keyword scripts for CDSW. The CDSW gist pattern ("scripts should answer, not dump") still applies — but for code comprehension, the "answerer" should be an LLM, not regex.
