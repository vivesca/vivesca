---
title: NEVER hardcode `/Users/terry/`
impact: HIGH
impactDescription: breaks on Linux
tags: test
---

## NEVER hardcode `/Users/terry/`

The path is `/home/terry/` on gemmule (Linux). Use `Path.home()` or `Path(__file__).parent.parent` for all paths. This breaks every time on the other platform.
