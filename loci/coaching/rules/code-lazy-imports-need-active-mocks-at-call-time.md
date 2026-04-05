---
title: Lazy imports need active mocks at call time
impact: HIGH
impactDescription: sent real Telegram messages
tags: code
---

## Lazy imports need active mocks at call time

If a function does `from X import Y` inside its body, `patch.dict("sys.modules")` must wrap the CALL, not just the exec. To force ImportError, set `sys.modules["X"] = None`. Just popping it lets the real import succeed on systems where the module is installed — this caused circadian-probe tests to send real Telegram messages.
