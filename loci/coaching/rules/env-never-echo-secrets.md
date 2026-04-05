---
title: Never echo secrets
impact: HIGH
tags: env
---

## Never echo secrets

Use `test -n "$VAR"` to check key existence, not `echo $VAR | head`. Even partial key exposure in logs is a security issue.
