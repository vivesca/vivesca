---
name: judex
description: "Empirical validation over theoretical debate — when two approaches are plausible and measurable, run the experiment instead of deliberating."
user_invocable: false
triggers:
  - judex
  - experiment
  - benchmark
  - routing
  - compare approaches
  - empirical
---

# judex — Empirical Validation

Not user-invocable. Internal guidance consulted when facing a choice between two approaches.

## The Core Rule

> **quorate** = outcome is uncertain, needs perspectives.
> **judex** = outcome is measurable, needs evidence.
> **kritike** = consult for what to measure and how (Goodhart traps, vanity vs diagnostic, evaluation theory).

Before spinning up a deliberation or asking the user to decide: can you just run both and compare?

**Trigger conditions:**
- You'd reach for `AskUserQuestion` to choose between two tools/approaches
- Benchmark says X but experience feels like Y
- Two implementations are plausible and neither is obviously better
- You've been burned by the routing before on a similar task

**When judex doesn't apply:**
- The outcome isn't measurable (strategic choices, value trade-offs, personal preferences) → quorate
- One option is clearly dominant → just pick it
- The experiment would take longer than the task itself → just pick, note the uncertainty

## The Pattern

```
1. Create two lucus worktrees (prevents git add -A conflicts)
2. Write identical prompts to /tmp/<task>-<tool-a>-prompt.txt and /tmp/<task>-<tool-b>-prompt.txt
3. Launch both in parallel (Bash run_in_background: true)
4. Wait for completion
5. Apply your verification criteria (build + test, or benchmark, or output quality check)
6. Diff scope: git diff --stat per branch (watch for out-of-scope changes)
7. Pick the winner. Document why. Update routing notes.
```

The experiment must have **a measurable pass/fail criterion set before launch** — not a subjective judgment after the fact.

## Case 1 — AI Tool Routing: Codex vs Gemini on Rust Feature (2026-03-04)

**Decision:** Which tool for quorate Feature A (Rust, 4 files, model swap + new API branch)?

**Hypothesis to test:** Gemini (LiveCodeBench #1) vs Codex (Terminal-Bench #1) on a task requiring `cargo build` validation.

**Criterion:** `cargo build --release && cargo test && cargo clippy` all pass, 0 errors.

| | Codex | Gemini |
|---|---|---|
| Build | ❌ Failed (workspace conflict) | ✅ Passed (1m08s) |
| Tests | — | ✅ 3/3 |
| Clippy | — | ✅ Clean |
| Files changed | 11 | 13 |
| Out-of-scope? | No | No (extras were required) |

**Root causes of Codex failure:**

| Gap | Cause | Fixable with better prompt? |
|-----|-------|-----------------------------|
| Workspace conflict | Codex sandbox blocks `cargo build` (DNS) — can't discover compile errors | ❌ No — structural |
| Missing `main.rs` threading | Prompt scoped to `src/modes/*.rs`, missed entry point | ✅ Yes |
| Error pattern ignored | Explicit `is_error_response()` instruction not followed | Maybe |

**Routing update:** For Rust tasks where `cargo build` validation is required → prefer Gemini. It runs on your machine and discovers compile errors. Codex sandbox blocks DNS/cargo.

**Prompt fix discovered:** "search all call sites in `src/modes/*.rs`" misses the entry point. Template: "search ALL callers including `src/main.rs` and `src/modes/*.rs`."

**Permanent fix shipped:** Added `[workspace]` to quorate `Cargo.toml` — prevents all future lucus worktree build conflicts.

## Routing Heuristics (from real cases)

| Signal | Prefer | Avoid | Source |
|--------|--------|-------|--------|
| Rust feature requiring `cargo build` | **Gemini** | Codex | Case 1 |
| Multi-file repo nav + complex test loops | **Codex** | — | Benchmark (unvalidated) |
| Isolated algorithmic logic | **Gemini** | — | Benchmark (unvalidated) |
| Bulk boilerplate, routine edits | **OpenCode** | — | Benchmark (unvalidated) |

Mark heuristics as `(unvalidated)` until a judex case confirms them.

## Experiment Template (Rust / Codex+Gemini)

```bash
# 1. Write prompts to files (avoid shell quoting issues)
cat > /tmp/<task>-codex-prompt.txt << 'EOF'
<prompt>
EOF
cat > /tmp/<task>-gemini-prompt.txt << 'EOF'
<prompt>
EOF

# 2. Create worktrees
lucus new <task>-codex
lucus new <task>-gemini

# 3. Launch in parallel (run_in_background: true on each Bash call)
cd ~/code/<repo>.<task>-codex && codex exec --skip-git-repo-check --full-auto "$(cat /tmp/<task>-codex-prompt.txt)"
cd ~/code/<repo>.<task>-gemini && gemini -p "$(cat /tmp/<task>-gemini-prompt.txt)" --yolo

# 4. Verify
cd ~/code/<repo>.<task>-codex && cargo build --release && cargo test && cargo clippy
cd ~/code/<repo>.<task>-gemini && cargo build --release && cargo test && cargo clippy

# 5. Diff scope
cd ~/code/<repo>.<task>-codex && git diff --stat
cd ~/code/<repo>.<task>-gemini && git diff --stat

# 6. Commit winner and merge
cd ~/code/<repo>.<task>-gemini && git add -A && git commit -m "feat: ..."
cd ~/code/<repo> && git merge <task>-gemini --no-edit

# 7. Cleanup
lucus remove <task>-codex
lucus remove <task>-gemini
```

## Naming

*Judex* — Latin, "judge/arbiter" (*just* + *dicare*). Named by quorate quick (2026-03-04). Crux (Claude's pick) was taken on crates.io; Judex was free and semantically equivalent.
