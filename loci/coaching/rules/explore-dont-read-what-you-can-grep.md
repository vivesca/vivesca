---
title: Don't read what you can grep
impact: MEDIUM
tags: explore
---

## Don't read what you can grep

To check if a file has try/except, use `grep -l "try:" hooks/*.py`, don't open each file.
