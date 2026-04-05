---
title: No hallucinated imports
impact: CRITICAL
impactDescription: causes ImportError on dispatch target
tags: code
---

## No hallucinated imports

Only import functions that already exist. If original code was inline, keep it inline.
