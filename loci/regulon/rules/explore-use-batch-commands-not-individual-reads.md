---
title: Use batch commands, not individual reads
impact: MEDIUM
tags: explore
---

## Use batch commands, not individual reads

`grep -c "def test_" assays/*.py` beats reading 100 files. `wc -l metabolon/**/*.py` beats opening each one. One shell command replaces 100 tool calls.
