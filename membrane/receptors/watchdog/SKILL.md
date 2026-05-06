---
name: watchdog
description: "Pair-programmer that watches a primary CC session for execution drift and direction drift. Fresh-context CC reads primary's transcript against the original spec and course-corrects."
triggers:
  - "watchdog"
  - "pair programmer"
  - "watch this session"
  - "drift check"
  - "watch primary"
---

# Watchdog — pair-programmer drift monitor

Fresh-context CC reads a primary session's recent turns against the original spec and flags drift. Distinct from `securin` (which watches mtor dispatch) and from the architect-implementer split (CC → ribosome). Watchdog watches CC's own primary session.

Inspired by Eugene Yan's pattern (eugeneyan.com May 2026): a secondary tmux pane periodically scans the primary's transcript for misalignment with the spec.

## Two drift classes

- **Execution drift** (tactical, check often): ignored an error, reported a fabricated metric, skipped a verification step, diverged from spec on file paths or interfaces. Local fixes, fast feedback.
- **Direction drift** (strategic, check occasionally): misinterpreted intent, building the wrong thing, scope expanded beyond the original ask. Requires hard reframe.

Default cadence: execution drift every ~15 turns or ~30 min; direction drift every ~60 turns or ~2 hours.

## Setup

Inputs the watchdog needs:
1. **Spec** — path to the original task spec, plan, or kickoff prompt. Required.
2. **Primary transcript** — `~/.claude/projects/-home-vivesca/<session-id>.jsonl` (find via `ls -lt`).
3. **Window** — last N user+assistant turns to scan (default 30).

## Mechanism

Self-ping loop in the watchdog session:

```
Bash(command="sleep 1800 && watchdog-tick <session-id> <spec-path>", run_in_background=true)
```

Each tick:

1. Tail the primary's JSONL — last N turns, both roles.
2. Re-read the spec file (it may have evolved).
3. Compare against four checks:
   - Does the primary's recent action match a step in the spec?
   - Are there ignored errors (assistant said "moving on" / "I'll skip" without resolution)?
   - Are there fabricated outcomes (claims a test passed without showing the run; claims a file changed without diff)?
   - Has the topic drifted (last 5 turns about something not in the spec)?
4. If any check fires: write a structured note to a shared file the primary watches (e.g. `~/.claude/watchdog/<session-id>.md`) with severity + suggested correction.
5. Schedule next tick.

## Output format

Write to `~/.claude/watchdog/<session-id>.md`. Append-only, timestamped. Primary's UserPromptSubmit hook can surface the latest unread entry.

```
## 2026-05-06 13:42 — execution drift
Spec §3 says "smoke-test container builds before full run."
Primary skipped smoke test, ran full eval (turn 47).
Suggest: stop, build smoke test, then resume.
```

## When to invoke

- Long agentic runs (>30 min, dispatch + verify loops).
- Multi-step specs with clear exit criteria where forgetting a step is plausible.
- Sessions touching unfamiliar code where drift is hard to self-detect.

Do **not** invoke for:
- Brainstorming, exploration, drafting (drift is the point).
- Sessions under ~30 min (overhead exceeds value).
- Tasks already covered by a deterministic gate (pre-commit, assays, securin).

## Boundary vs adjacent skills

- `securin` — watches **mtor/ribosome** dispatch, not CC. Watchdog watches CC.
- `autopoiesis` — self-repair loop after detection. Watchdog is the detection layer.
- `examen` — premise audit before delegating. Watchdog audits during execution.
- Architect-implementer (`ribosome`) — CC dispatches ribosome to do work. Watchdog is a third party reading both.

## Status

Skeleton — `watchdog-tick` CLI not yet built. Open question: hook vs skill vs background loop. Hook (PostToolUse periodic) is cheapest but lacks judgment; skill + scheduled tick is the closest match to Eugene's pattern.
