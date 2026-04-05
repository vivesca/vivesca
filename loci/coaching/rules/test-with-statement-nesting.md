---
title: `with` statement nesting
impact: HIGH
tags: test
---

## `with` statement nesting

`with A:\n    with B:` is fine but `with A:\n    with B:\n    with C:` is a SyntaxError. Use `with A, B, C:` for multiple context managers on one level.
