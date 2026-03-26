---
name: assay
description: Detect active life experiments and probe during sessions. "how's the experiment", "assay", or auto-detect at session start.
user_invocable: false
---

# assay -- experiment awareness

Thin judgment layer over the `assay` CLI. Fires when active experiments exist.

## Detection

Check for active experiments:

```bash
~/germline/effectors/assay list 2>/dev/null
```

If any show `[active]`, this skill applies.

## When to fire

- Session start (any session during an active experiment window)
- User mentions the experiment topic (e.g. "coffee", "caffeine", "sleep")
- User asks "what's next", "how am I doing", or any health check
- Ultradian / interphase routines

## Probe sequence

1. Run `~/germline/effectors/assay check` to pull latest Oura data and append to the experiment log.
2. Read the check-in output -- surface the delta vs baseline in one line.
3. Ask one question about the intervention ("any caffeine slip-ups?" / "how's energy?"). Keep it to one question, not a checklist.
4. If day >= experiment duration, suggest running `assay close` and interpreting results.

## Interpretation (at close)

When `assay close` runs, the verdict section is `_TBD_`. Fill it with:

- **Signal strength:** did the metrics move more than day-to-day noise? (sleep +/- 5, readiness +/- 5, HRV +/- 10 are within noise)
- **Direction:** better, worse, or flat
- **Confounds:** anything in the check-in notes that could explain the change (stress events, travel, illness)
- **Recommendation:** continue, revert, or modify the intervention

Be honest about whether the data is conclusive. 14 days with Oura noise is borderline -- say so if the signal is weak.
