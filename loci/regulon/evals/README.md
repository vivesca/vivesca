# Regulon Evals

Prompt evaluation configs for coaching rules. Tests whether GLM/ZhiPu backends
actually follow the rules when given bad code.

## Stack

- **[promptfoo](https://github.com/promptfoo/promptfoo)** — CLI eval runner
- **polymerase --test-cases** — extracts Incorrect/Correct pairs from rules into JSON
- **peira** — for experiment loops over multiple prompts

## Workflow

1. Write a rule in `rules/` with Incorrect/Correct code blocks.
2. Run `polymerase --test-cases` to extract them into `test-cases.json`.
3. Write a `promptfooconfig.yaml` that loads the bad examples, sends them to
   the coaching-prepended backend (ZhiPu/GLM), and asserts the output matches
   the good example pattern.
4. Run `promptfoo eval` in CI to measure compliance.

## Status

- `test-cases.json` currently empty — rules don't have Incorrect/Correct blocks yet.
- Populate the top 10 highest-impact rules first (CRITICAL + HIGH).
- Target: measure GLM compliance against coaching rules, not vibes.
