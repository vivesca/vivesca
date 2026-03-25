# Cell-Level Design Gaps

Three design improvements surfaced by forcing cell-level naming on neuro-level tool names (25 Mar 2026).

## 1. Germination: conditions, not schedules

**Source:** `arousal` → `germination`. Spores germinate when conditions are right, not on a timer.

**Current:** Overnight agents run on cron (polarization). Results accumulate. User manually checks with `germination_brief` in the morning.

**Cell insight:** Germination is conditions-triggered. The spore detects nutrients, moisture, temperature — then activates. It doesn't wait for a clock.

**Design:** Results should surface when ready, not when asked.
- Pulse/cron detects completed overnight results
- Evaluates: anything flagged NEEDS_ATTENTION?
- If yes → emit to efferens queue (pull, not push)
- If no → stay dormant until asked
- `germination_brief` still works for manual check, but the organism doesn't depend on it

**Size:** ~20 lines in pulse.py. Check overnight-gather output, emit if flagged.

## 2. Proprioception: gradients, not states

**Source:** `interoception` → `proprioception`. Cells sense structural gradients — is tension increasing? Is shape changing?

**Current:** `proprioception` dumps a status report for one target. Point-in-time snapshot. No history, no trend.

**Cell insight:** Proprioception detects CHANGE, not state. A muscle fiber senses stretch RATE, not length. The organism should sense "constitution getting longer" not "constitution is 200 lines."

**Design:** Gradient sensing over time.
- Store proprioception readings to `~/logs/proprioception.jsonl` (target, timestamp, key metrics)
- On each reading, compute delta from last N readings
- Surface trends: "token usage +15% this week", "constitution +3 rules since last sweep", "hook fires decreasing"
- Optional: threshold alerts when gradient exceeds setpoint

**Size:** ~50 lines. JSONL append + delta computation + trend formatting.

## 3. Secretory: quality control (chaperones)

**Source:** `efferens` → `secretory`. The secretory pathway has chaperones that check protein folding before export.

**Current:** Output goes straight out. `exocytosis_text` sends to Telegram. `emit_publish` pushes to garden. No quality check.

**Cell insight:** In the ER, chaperones verify protein folding. Misfolded proteins are rejected (ER-associated degradation — ERAD). The output pathway should CHECK before releasing.

**Design:** Pre-export quality control.
- Garden posts: check frontmatter, check length, check for AI slop markers
- Telegram messages: check for PII, check tone matches relationship
- Tweets: check length, check for special characters (Blink constraint)
- Rejection pathway: misfolded output → log + flag, don't send
- Chaperone is deterministic (regex, rules), not LLM-mediated — it's a reflex, not reasoning

**Size:** ~30 lines per output type. Decorators or pre-hooks on secretory functions.

---

**Priority:** Secretory quality control is highest value — prevents bad output. Proprioception gradients compound over time. Germination conditions are a nice-to-have (manual check works fine).

**All three are cell-level reflexes, not LLM-mediated.** They should be deterministic. The cell doesn't reason about quality control — it checks shape.
