---
name: friction
description: Capture friction moments during work. Use when the user says "friction", types "/friction", or explicitly flags frustration. Dumps context to learning system.
user_invocable: true
---

# Friction

Manual signal for "something went wrong here worth remembering." Captures the moment while context is fresh.

## Triggers

- "/friction", "friction"
- "that was painful", "this keeps happening"

## Workflow

1. **Scan recent context** — What just happened? Look for:
   - Repeated tool failures (same command 3+ times)
   - Approach pivots ("wait, let me try something else")
   - Surprising behaviour from tools/APIs
   - Scope creep (task grew beyond original intent)
   - Unclear requirements that caused rework

2. **Classify** — What kind of friction?

   | Type | Route to |
   |------|----------|
   | Tool/API gotcha | `~/docs/solutions/` |
   | Skill gap or design issue | `~/skills/` relevant skill |
   | Process/workflow issue | Relevant vault note or daily note |
   | Recurring pattern | `MEMORY.md` (if 3+ occurrences) |

3. **Write** — Append a concise entry to the appropriate location:
   ```
   ## Friction: [one-line summary]
   **Date:** YYYY-MM-DD
   **Context:** What was being attempted
   **What went wrong:** Specific failure or pain point
   **Resolution:** How it was resolved (or "unresolved")
   **Prevention:** What would prevent this next time
   ```

4. **Confirm** — Tell the user what was captured and where.

## Design Notes

- This is a manual trigger by design. Automated sentiment detection was evaluated and rejected (Feb 2026 council decision) — manual signal has higher precision.
- Keep entries terse. If the learning is obvious ("typo in filename"), skip it.
- If `/legatum` would be more appropriate (end of session, broad sweep), suggest that instead.
