---
title: `ribosome-daemon clean` does NOT evict zombie running tasks
impact: LOW
tags: env
---

## `ribosome-daemon clean` does NOT evict zombie running tasks

It only purges completed/failed queue entries. Zombie running tasks (process dead, daemon still tracking) must be cleared by emptying `~/.local/share/vivesca/ribosome-running.json`. Symptom: `status` shows tasks running for 7+ hours with no matching process in `ps aux`.
