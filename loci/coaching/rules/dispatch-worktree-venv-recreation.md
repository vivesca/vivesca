---
title: Worktree .venv recreation
impact: MEDIUM
tags: dispatch
---

## Worktree .venv recreation

`uv` recreates `.venv` in worktrees. This is normal — it will show as a "changed file" but should be excluded from merge conflict detection.
