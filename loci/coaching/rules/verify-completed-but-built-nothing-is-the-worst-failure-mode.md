---
title: "Completed but built nothing" is the worst failure mode
impact: CRITICAL
impactDescription: worst failure mode
tags: verify
---

## "Completed but built nothing" is the worst failure mode

GLM sometimes runs to max turns, reads files, discusses the plan, but never actually creates the target file or commits. The workflow reports COMPLETED, the review finds no diff, and the task sits in retry limbo. Root causes: (1) spending all turns on exploration/reading without writing, (2) import errors that silently prevent the file from being created, (3) test failures that block the commit step. **Fix: write the target file in your FIRST 3 tool calls.** Skeleton first, fill in later. A partial file that fails tests is better than no file at all — at least the next attempt can read and fix it.
