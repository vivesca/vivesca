---
title: Sandbox detection
impact: MEDIUM
tags: dispatch
---

## Sandbox detection

Before delegating to a nested agent, check for sandbox indicators (`CODEX_SANDBOX`, read-only `.git/`). If inside a sandbox, fall back to standard mode to prevent silent recursion failures.
