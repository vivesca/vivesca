---
name: hook-health
description: Audit hook fire patterns, error rates, latency. Surface broken or silent hooks.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Audit the vivesca hook nervous system. Hooks fail silently — catch it here.

1. Inventory hooks: `ls ~/.claude/hooks/` — list all configured hooks
2. Check hook logs: `ls ~/logs/` and grep for hook-related errors in last 24h
   - Look for: FAILED, ERROR, timeout, exit code != 0
3. Check hook consolidation script health: the 7 Python scripts from consolidation
   - `ls ~/code/vivesca/bin/*.py | xargs -I{} head -3 {}` — confirm they exist and are valid Python
4. Fire rate: check if any hooks are firing too frequently (logs > 100 lines/day)
5. Silent hooks: hooks that haven't fired in > 7 days (may be dead or bypassed)
6. nociceptor specifically: confirm it fires in scripts and doesn't block claude
7. hebbian_nudge.py: is advisory accuracy tracking working? Check its output log

Output:
- HEALTHY: N hooks firing normally
- BROKEN: list with last error
- SILENT: hooks that haven't fired recently
- NOISY: hooks firing excessively

Recommend: fix, disable, or investigate for each issue.
