---
title: "GARP RAI CLI (rai.py) — Codex Audit + 11 Bug Fixes"
date: 2026-02-23
tags:
  - garp-rai
  - data-integrity
  - atomic-writes
  - error-handling
  - codex-audit
  - cli-tools
category: tool-hardening
severity: high
component: rai.py
related_files:
  - ~/garp-rai/rai.py
  - ~/garp-rai/skill.md
  - ~/code/epigenome/chromatin/GARP RAI Quiz Tracker.md
  - ~/code/epigenome/chromatin/.garp-fsrs-state.json
related_docs:
  - ~/docs/solutions/spaced-repetition-mode-selection.md
  - ~/docs/solutions/patterns/tightening-pass.md
  - ~/docs/solutions/ai-code-review-lessons.md
---

# GARP RAI CLI — Codex Audit + 11 Bug Fixes

## Problem

The GARP RAI spaced repetition CLI (`rai.py`) had accumulated subtle bugs across data integrity, file I/O, error handling, and UX. Discovered when:

- Session count stuck at 30 (Claude forgot to call `rai end` across 2 sessions)
- Claude kept suggesting quiz after daily quota was already met
- Summary counter drifted from topic row data

## Audit Methodology

**Tool:** Codex CLI (GPT-5.2) in `--approval-mode full-auto`
**Scope:** Full `rai.py` (~700 lines), targeting bugs, data integrity, edge cases, security
**Result:** 12 findings (4 HIGH, 4 MED, 4 LOW), 11 fixed, 1 deferred

Also attempted OpenCode (Gemini 2.5 Pro) but it hung — should have used GLM-4.7 (the configured free model for OpenCode).

## Findings & Fixes

### HIGH (4)

**1. Acquisition cap logs original rating, not capped**
When topic <60% accuracy and user rates good/easy, rating is capped to `hard` internally — but `rating_str` wasn't updated, causing FSRS state, review log, and tracker to diverge.
Fix: `rating_str = "hard"` after cap.

**2. Malformed JSON crashes all commands**
`load_state()` had no error handling. Corrupt `.garp-fsrs-state.json` would crash every CLI command.
Fix: `try/except json.JSONDecodeError` with fresh-state fallback, plus per-card `try/except` to skip corrupt cards.

**3. Non-atomic file writes**
`Path.write_text()` can leave partial files on crash (common with Blink/tmux disconnects).
Fix: `atomic_write()` helper — `tempfile.mkstemp()` → write → `os.replace()` (atomic on same filesystem). Applied to all 4 write sites.

**4. Reconcile trusts parser blindly**
`cmd_reconcile()` would zero out all counters if `parse_tracker()` returned empty topics (formatting drift).
Fix: Abort if fewer than 10 topics parsed (expect ~34).

### MEDIUM (4)

**5. Never-attempted topics starved**
Session planner only included topics with `attempts > 0`. New topics with no FSRS card were invisible.
Fix: Remove the `attempts > 0` guard — include all topics.

**6. History append scans past section boundary**
`in_history` flag was never reset on next `## ` heading. Could append to wrong section.
Fix: `break` on `line.startswith("## ")` after entering history section.

**7. `today` crashes on malformed timestamps**
`datetime.fromisoformat()` in session-counting loop had no error handling.
Fix: `try/except (ValueError, TypeError): continue`.

**8. `sessions_per_week` computed but unused**
`get_daily_quota()` returned a tuple; only first element used.
Fix: Return single `int` instead.

### LOW (3)

**9. No validation on session count arg** — reject negative/non-integer.
**10. Unused `State` import** — removed.
**11. Rich markup injection** — deferred (topic names are human-curated, low risk).

## New Features (same session)

- **`rai today`** — shows today's questions, sessions, accuracy, quota status
- **`rai session` quota banner** — green "quota met" message when daily dose done
- **`rai reconcile`** — recomputes summary counter from topic row data

## Prevention Patterns

**Atomic writes everywhere:** Replace all `Path.write_text()` with temp+rename. Especially important on mobile SSH (Blink disconnects).

**Guard every external parse:** JSON loads, datetime parsing, integer coercion — always `try/except` with fallback or skip.

**Sync all downstream refs after mutation:** When a value is transformed (capped, sanitized), update ALL variables that reference it in the same block. The rating/rating_str divergence is the classic case.

**Boundary checks in string scanning:** Always `break` on section delimiters when scanning markdown. Never let a scanner run past its intended scope.

**Don't require manual tracking when computable:** Session count relying on `rai end` being called is fragile. Better to derive from review_log at display time (future improvement).

**Audit with Codex CLI for personal tools:** `codex --approval-mode full-auto "audit this file"` is cheap, thorough, and catches things you'll miss reviewing your own code. 12 findings in ~4 minutes on a 700-line file.

## Key Commits

```
045e5df  rai: add today/reconcile commands + session quota banner
eb64365  skill: update CLI command list + quota check guidance
8d9fa18  rai: fix 11 audit findings (4 HIGH, 4 MED, 3 LOW)
```

Repo: `terry-li-hm/garp-rai` (GitHub)
