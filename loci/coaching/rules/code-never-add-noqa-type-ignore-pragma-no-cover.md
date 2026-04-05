---
title: NEVER add `# noqa`, `# type: ignore`, `# pragma: no cover`
impact: HIGH
impactDescription: pre-commit hook rejects
tags: code
---

## NEVER add `# noqa`, `# type: ignore`, `# pragma: no cover`

Fix the code. Common fixes: mutable class default `data: dict = {}` → `Field(default_factory=dict)`. Unused import → delete it. Broad `except Exception` → narrow the type. The pre-commit hook WILL reject noqa comments.
