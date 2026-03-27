---
name: assay
description: Detect active experiments and probe during sessions. "assay"
user_invocable: false
---

# assay -- experiment awareness

Thin judgment layer over the `assay` CLI. Fires when active experiments exist.

## Detection

Check for active experiments:

```bash
~/germline/effectors/assay list 2>/dev/null
```

If any show `[active]`, this skill applies. Experiment files live at `~/epigenome/chromatin/Experiments/assay-*.md`.

## When to fire

- Session start (any session during an active experiment window)
- User mentions the experiment topic (e.g. "coffee", "caffeine", "sleep")
- User asks "what's next", "how am I doing", or any health check
- Circadian routines
- User says "we logged X" or asks about intake/symptoms during an experiment

## How the system works

The assay system is a closed loop:

- **`assay new`** creates an experiment file with auto-generated `watch_keywords` from the name and hypothesis. Keywords include domain synonyms (e.g. "caffeine" expands to coffee, cappuccino, espresso, latte, matcha, cola).
- **`ingestion_log_meal`** and **`nociception_log`** auto-cross-link to active experiments when logged content matches watch_keywords. Cross-links appear as `> **Intake logged:**` and `> **Symptom logged:**` blockquotes in the experiment file.
- **`assay check`** pulls Oura data AND scans the meal plan for keyword-matching intake entries since experiment start. Appends a unified check-in.
- **`circadian_sleep`** auto-surfaces active experiment context alongside Oura scores.
- **`ecphory_logs`** searches experiment files, meal plan, and symptom log. Use when the user asks "we logged X" or "where did I log".
- **`assay close`** aggregates all cross-linked intake/symptom notes into a "Cross-linked Events" section before the verdict.

## Probe sequence

1. Run `~/germline/effectors/assay check` to pull latest Oura data + intake matches and append to the experiment log.
2. Read the check-in output -- surface the delta vs baseline in one line.
3. If cross-linked intake or symptom events exist since the last check-in, mention them (e.g. "cappuccino logged yesterday -- that's a protocol break").
4. Ask one question about the intervention ("any caffeine slip-ups?" / "how's energy?"). Keep it to one question, not a checklist.
5. If day >= experiment duration, suggest running `assay close` and interpreting results.

## Retrieval

When the user asks about something logged during an experiment:
1. **`ecphory_logs`** first -- searches meal plan, symptom log, and experiment files
2. **`engram search`** as fallback -- searches session transcripts (has fuzzy matching for typos)
3. Do NOT rely on only one source. Fan out if the first returns nothing.

## Interpretation (at close)

When `assay close` runs, the verdict section is `_TBD_`. Fill it with:

- **Signal strength:** did the metrics move more than day-to-day noise? (sleep +/- 5, readiness +/- 5, HRV +/- 10 are within noise)
- **Direction:** better, worse, or flat
- **Confounds:** review the Cross-linked Events section -- intake breaches, symptom events, and external stressors all count
- **Recommendation:** continue, revert, or modify the intervention

Be honest about whether the data is conclusive. 14 days with Oura noise is borderline -- say so if the signal is weak.
