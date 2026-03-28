---
name: methylation
description: Weekly crystallization — turn repair experience into permanent probes and patterns.
user_invocable: true
triggers:
  - methylation
  - methylation review
  - weekly crystallization
  - crystallize repairs
context: fork
epistemics: [execute, review]
model: sonnet
---

# Methylation -- weekly crystallization of repair patterns

Run the methylation effector and review its output. This turns recurring repairs into permanent capability (new probes, new repair patterns, architectural observations).

## When to use

- Weekly review (usually Saturday)
- After a week with many inflammasome repairs
- When asked to crystallize, methylate, or review repair patterns

## Protocol

### Step 1: Run the effector

```bash
~/germline/effectors/methylation
```

This reads three signal sources from the past 7 days:
- `~/.cache/inflammasome/methylation-candidates.jsonl` (successful repairs)
- `~/.local/share/vivesca/infections.jsonl` (infection patterns)
- `~/logs/inflammasome.log` (probe failures)

It groups patterns, dispatches a synthesis call for any pattern seen >= 2 times, and writes:
- `~/tmp/methylation-proposal-YYYY-MM-DD.md` (main proposal)
- `~/tmp/hybridization-proposals-YYYY-MM-DD.md` (new subsystem designs, if gaps found)

### Step 2: Check the log

```bash
tail -30 ~/logs/methylation.log
```

If "no patterns above threshold" -- report clean week, no crystallization needed.

### Step 3: Review proposals

Read the proposal file(s) in `~/tmp/`. For each proposal:

- **TYPE: probe** -- evaluate if the probe is safe and useful. Pure path/import checks can be applied directly to `~/germline/metabolon/organelles/inflammasome.py`.
- **TYPE: repair** -- evaluate if the repair pattern is deterministic and safe. Present to Terry for approval.
- **TYPE: architectural** -- present the observation. Never auto-apply architectural changes.

### Step 4: Check standing entries

```bash
tail -10 ~/germline/methylation.jsonl
```

Standing entries (type "standing") are permanent audit rules that must be checked every run. Report compliance.

### Step 5: Present

Summarize:
1. Signal counts (repairs, infections, probe failures this week)
2. Crystallizable patterns found (or "clean week")
3. Proposals generated and their types
4. Standing rule compliance
5. Any hybridization proposals (new subsystem designs)

## Do NOT

- Auto-apply anything except pure path/import probe checks
- Skip the hybridization pass output if it exists
- Run this more than once per week unless explicitly asked
