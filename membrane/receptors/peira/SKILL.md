---
name: peira
description: >-
  Autonomous experiment-optimize loop for any measurable target. Use when
  prompt engineering, habit tuning, performance benchmarking, classifier
  improvement, config search — any "what works better?" question with a
  quantifiable metric. Trigger: /peira, "launch exp", "run experiment",
  "compare X vs Y", "benchmark", "let's test".
user_invocable: true
---

# Peira — Experiment Loop

Karpathy's autoresearch loop, generalized: **propose → run → measure → keep/discard → log → repeat**. For evaluation theory (what to measure, Goodhart traps, vanity vs diagnostic metrics): consult `kritike`.

## CLI

```bash
peira init <topic>                          # scaffold campaign dir + brief.md + log.toml
peira status [--campaign <name>]            # current best, experiments run vs budget
peira log --score <n> [--decision keep|discard] [--notes "..."] [--campaign <name>]
peira best [--campaign <name>]             # print winning experiment
```

Campaigns live in `~/epigenome/chromatin/Experiments/peira-YYYY-MM-DD-<topic>/`. Active campaign = most recent. `--campaign` matches by substring.

Log is TOML (`log.toml`); brief stays human-editable markdown (`brief.md`). Source: `~/code/peira/`.

Works for anything with a quantifiable metric: prompts, habits, benchmarks, classifier tuning, writing structure, CLI config.

## Phase 1: Setup (once, before any experiments)

Answer all four before starting. If any is unclear → ask. Do not begin the loop without them.

1. **Target** — what changes each experiment? (the "train.py" equivalent)
2. **Metric** — how do we measure success? Must be a number. State direction: lower = better or higher = better.
3. **Baseline** — run or observe the current state now. Record its metric score.
4. **Budget** — max experiments, API cost cap, or time limit. Default: **10 experiments**. This is a hard stop — do not exceed without explicit user approval mid-session.
5. **Metric discipline** — pick one metric and lock it in. Do not add a second metric mid-campaign because the first looks bad. If you need multiple metrics, rank them and use only the primary for keep/discard decisions.

Create two files immediately:

**Log:** `~/epigenome/chromatin/Experiments/peira-YYYY-MM-DD-<topic>/log.md`
**Brief:** `~/epigenome/chromatin/Experiments/peira-YYYY-MM-DD-<topic>/brief.md`

The brief is the living research context — the human iterates on it, not Claude:
```
## Brief: <topic>
- Goal: [what we want to achieve, in plain English]
- Target: [what changes each experiment]
- Metric: [name + direction] — LOCKED
- Baseline: [score]
- Budget: [N] experiments — HARD STOP
- Constraints: [what must not change]
- Hypothesis backlog: [ideas not yet tried]
- Ruled out: [what we've learned doesn't work]
```

Write the setup block at the top of the log:
```
## Setup
- Target: [what we're changing]
- Metric: [name, direction]
- Baseline: [score]
- Budget: [N experiments / $X / T minutes]
- Mode: autonomous | human-in-loop
```

## Phase 2: The Loop

Repeat until budget exhausted or user stops.

### 2a. Hypothesize

Propose **one change**. One variable only — never vary two things simultaneously.

State explicitly: *"I hypothesize that [change] will improve [metric] because [reason]."*

Prefer:
- Exploit: build on what worked in prior experiments
- Every 3rd experiment if stuck: explore something qualitatively different

### 2b. Run

| Mode | When | How |
|------|------|-----|
| **Autonomous** | Metric is machine-readable (script output, API, benchmark) | Execute directly |
| **Human-in-loop** | Metric needs human judgment or real-world observation | Describe the experiment; ask user to run it and report the metric value |
| **Overnight** | Long autonomous session before AFK | Kick off loop; review log on return |

If the experiment fails to run → log as `FAILED: [reason]`, propose a minimal fix, count against budget.

### 2c. Measure

Record metric value. Compare to: (a) baseline, (b) current best.

### 2d. Decide

- Better than current best → **KEEP**. Update current best.
- Worse or equal → **DISCARD**. Revert to prior state.
- Result is ambiguous (noise suspected) → note it, move on. Do not re-run without explicit budget approval.

### 2e. Log

Append to the experiment log:

```
## Experiment N — [one-line description]
- Hypothesis: [what and why]
- Change: [exact diff, prompt text, or description]
- Metric: [value]  (baseline: X, prev best: Y)
- Decision: KEEP / DISCARD
- Notes: [anything surprising or informative]
```

Never skip logging. The log is the deliverable — not just the winning config.

## Phase 3: Wrap

When budget is exhausted:

1. State the best config found and delta vs baseline: *"Improved from X to Y (+Z%)"*
2. Apply the winning config permanently (or give user the exact change to apply)
3. Save the log to vault
4. Note any cross-experiment patterns: what kinds of changes helped? what didn't?

## Boundaries

- **One variable per experiment.** Always. Multi-variable changes produce uninterpretable results.
- Do NOT declare a winner before budget is exhausted unless gain is dramatic (>20%).
- Do NOT run autonomous mode for experiments with external side effects (sending emails, publishing, spending >$1 real money) without explicit per-experiment approval.
- Do NOT re-run failed experiments without diagnosing why they failed first.
- Do NOT change the metric mid-campaign. If the metric feels wrong, stop, reset, and restart with a corrected brief.
- Budget is a hard gate. When N experiments are done, stop and report — even if the best result is worse than baseline.

## Examples

**Prompt engineering (autonomous)**
- Target: system prompt for Libra STR classifier
- Metric: F1 on 50-item held-out set (higher = better)
- Budget: 15 experiments or $3 API cost
- Baseline: F1 = 0.74

**Sleep habit (human-in-loop)**
- Target: bedtime window (10:30pm vs 11:30pm vs midnight)
- Metric: Oura readiness score, 7-day rolling average (higher = better)
- Budget: 3 experiments (1 week each)
- Baseline: readiness = 71

**Consulting slide structure (human-in-loop)**
- Target: section order of AI value prop deck
- Metric: Terry's clarity rating after cold read (1–5, higher = better)
- Budget: 5 variants
- Baseline: 3/5

## Source

Adapted from Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) (Mar 2026).
Key ideas taken: fixed budget as hard gate, single locked metric, brief.md as human-editable research context, append-only experiment log.
Generalized from GPU/ML training to any measurable target.

## Motifs
- [verify-gate](../motifs/verify-gate.md)
