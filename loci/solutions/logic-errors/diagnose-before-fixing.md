# Diagnose Before Fixing

## Problem

Spent a session flip-flopping on a fix (raw table query → revert → raw table again) because we guessed at the root cause instead of verifying first.

## Context

STR relabelling appeal exclusion wasn't working. Hypothesised status 18 was missing from model table. Applied fix, then data showed status 18 DID exist (20K rows), so reverted. Turns out the model table was incomplete for *specific* records — original hypothesis was partially right but we wasted cycles bouncing.

## Lesson

When a logic fix doesn't work as expected:
1. Write a small diagnostic query FIRST (takes 5 min)
2. Verify the data matches your assumptions
3. THEN change code

The diagnostic script cost almost nothing but would have saved 3 rounds of edits + gist updates.

## Applies To

Any data pipeline debugging where you can't run the code locally.
