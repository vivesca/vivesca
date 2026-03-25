# LRN-20260308-001: Mine history before declaring a baseline

## Pattern

Before running a peira experiment campaign, search `anam` for historical data on the behaviour you're trying to change. Don't assume the baseline — measure it.

## What happened

Designed a peira campaign to test whether explicit yes/no answers in wrap Step 0B prevent silent skips. Declared baseline as 0/3 (all three items silently skipped). Before running experiment 2, searched `anam search "consulting arsenal" --deep --days 30`. Found that LinkedIn and consulting arsenal were being addressed ~80% of the time in normal wraps. The real baseline was ~2/3, not 0/3.

The failure mode was narrower than assumed: silent skips happen specifically in re-wraps and compact-adjacent sessions, not uniformly. Running 5 experiments against the wrong hypothesis would have produced uninterpretable results.

## Rule

**For any peira campaign tracking a behavioural change: run `anam search` before setting the baseline.** One or two targeted searches (the metric keyword + the specific check name) is enough. Takes 30 seconds, can correct the entire experiment design.

## Generalisation

This applies beyond peira. Any time you're about to measure "how often does X happen", check whether you already have data before starting the clock. Session history, daily notes, vault logs — check first.

## Anti-pattern

"I saw it fail once today so the baseline is 0." One observation is not a baseline. Especially for behavioural patterns (wrap execution, skill compliance, tool usage) where the failure mode may be situational rather than systematic.
