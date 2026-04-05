---
title: Python 3 except syntax only
impact: CRITICAL
impactDescription: 93+ instances in one migration
tags: code
---

## Python 3 except syntax only

`except (A, B):` not `except A, B:`. The comma form is Python 2 and causes SyntaxError. This has burned us repeatedly — 93 instances in one migration, then 51 more found on 2026-04-05. Ribosomes MUST run `ast.parse()` to catch this.
