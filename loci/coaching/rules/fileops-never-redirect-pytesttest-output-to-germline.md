---
title: Never redirect pytest/test output to ~/germline/
impact: MEDIUM
tags: fileops
---

## Never redirect pytest/test output to ~/germline/

Use `/tmp/` for throwaway output (`pytest > /tmp/pytest_out.txt`). The repo root is not a scratch pad.
