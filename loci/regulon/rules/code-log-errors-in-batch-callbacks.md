---
title: Log errors in batch callbacks
impact: HIGH
impactDescription: invisible data loss
tags: code
---

## Log errors in batch callbacks

When using `BatchHttpRequest` or similar batch APIs, don't silently discard failed items (`if exception is None: ...`). At minimum log the exception. Silent drops make debugging invisible -- a batch of 100 returns 99 results with no indication one was lost.
