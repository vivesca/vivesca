---
title: Effectors are scripts, not importable modules
impact: HIGH
impactDescription: import causes execution
tags: test
---

## Effectors are scripts, not importable modules

NEVER `import lacuna` or `from telophase import`. Load via `exec(open(path).read(), ns)` with `__name__` set to a non-`__main__` value, or test by invoking `subprocess.run([path, ...])` and checking stdout/exit code. The test file for `test_ribosome_daemon.py` shows the correct pattern.
