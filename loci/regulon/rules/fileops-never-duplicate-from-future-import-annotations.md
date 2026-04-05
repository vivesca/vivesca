---
title: NEVER duplicate `from __future__ import annotations`
impact: HIGH
tags: fileops
---

## NEVER duplicate `from __future__ import annotations`

This import MUST appear only once, at the very top of the file (line 1 or 2, before the docstring). Placing it after the docstring AND at the top causes a SyntaxError. Check: if the file starts with `from __future__`, do NOT add another one anywhere.
