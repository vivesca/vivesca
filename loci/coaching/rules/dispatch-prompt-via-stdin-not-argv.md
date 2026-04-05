---
title: Prompt via stdin, not argv
impact: MEDIUM
tags: dispatch
---

## Prompt via stdin, not argv

For large prompts, write to a temp file and pipe via stdin to avoid ARG_MAX limits. After 3 consecutive failures, disable delegation for remaining tasks with an explicit message.
