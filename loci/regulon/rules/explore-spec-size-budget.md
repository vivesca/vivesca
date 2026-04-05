---
title: Spec size budget
impact: MEDIUM
tags: explore
---

## Spec size budget

Total prompt (coaching + spec) must be under ~10KB. For modules >200 lines, embed API signatures only — read the full source yourself. Prompts >15KB cause immediate exit (1-2s, 0 output).
