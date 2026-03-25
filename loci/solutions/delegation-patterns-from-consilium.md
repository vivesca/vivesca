# Delegation Patterns — Lessons from consilium v0.1.4

*Source: Feb 28 2026 session. 4 features delegated in ~10 min wall-clock.*

## What Worked

### CE plan → delegate is the sweet spot for multi-feature releases
- Write a detailed plan doc with exact file paths, line numbers, integration points
- Delegates read the plan doc rather than needing everything inlined in the prompt
- Plan lives in the repo (`docs/plans/`) so delegates can read it directly

### Phase dependencies prevent file conflicts
- Tasks touching the same files (cli.rs, council.rs) must be sequenced, not parallelized
- Tasks touching different files (admin.rs vs cli.rs) can run in parallel
- Pattern: Phase 1 (parallel independent tasks) → Phase 2 (tasks depending on Phase 1 output)

### Routing matched the task well
- OpenCode (GLM-5) for the two low-complexity tasks: flag wiring + stats enrichment
- Gemini CLI (3.1 Pro) for the algorithmic task: context compression design + debate loop modification
- Gemini handled the complex branching logic (compressed vs full context paths) correctly

## What to Watch

### Gemini touches more than asked
- Asked to modify 3 files (config.rs, council.rs, discuss.rs), touched 10
- "Bonus" clippy fixes across admin.rs, api.rs, tui.rs, quick.rs, redteam.rs
- Added global `#![allow(clippy::too_many_arguments)]` in lib.rs — suppresses warnings project-wide
- **Not harmful this time** but could introduce regressions. Review diff scope after Gemini delegation.

### Gemini CLI prompt with `{curly_braces}` causes shell parse errors

Gemini CLI receives the prompt as a positional shell argument. Any `{word}` in the prompt string (e.g. `{rendered}`, `{line}`) gets parsed as shell brace expansion and fails with `parse error near '}'`. Fix: write the prompt to `/tmp/prompt.txt` and pass via `gemini -p "$(cat /tmp/prompt.txt)" --yolo`, or just do the edit directly if the change is small.

### Gemini's replace tool errors are noisy but recoverable
- Hit 3 replace errors (wrong occurrence count, string not found)
- Recovered and found alternative edits each time
- Don't panic at errors in the output — check the final result

### Delegates don't write tests
- Neither OpenCode nor Gemini added tests despite the plan calling for them
- Both said "all 62 tests passed" — meaning existing tests, not new ones
- **If you need tests, make it a separate delegation task** with explicit test file paths and assertions

### Version test gotcha
- Integration test checks exact version string: `"consilium 0.1.3"`
- Must update `tests/cli_test.rs` on every version bump
- Both delegates caught this (OpenCode bumped the version, Gemini didn't need to)

## Review Checklist After Delegation

1. `cargo clippy` — zero errors (warnings OK if pre-existing)
2. `cargo test` — all pass
3. `git diff --stat` — verify scope matches what was asked
4. Read the core logic (branching, indexing, error handling) — delegates get structure right but edge cases wrong
5. Check for global allows or suppressed warnings
6. Verify the "else" path — delegates often nail the happy path but miss fallback behavior

## Cost

- OpenCode: free (GLM-5 via ZhipuAI)
- Gemini: free (Google AI Pro plan, counts against 1500 RPD)
- Claude Code: ~5 min orchestration time (plan writing + delegation + review)
- Total: $0 for implementation, Claude Code tokens for orchestration only
