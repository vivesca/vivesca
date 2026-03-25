# Shell Wrapper: Allow stdin Pipes via execv Passthrough

## Problem

A Python wrapper shadowing `grep`/`rg`/`find` inspects args for a path argument to decide whether to block the search. When no path arg is found, defaulting to `os.getcwd()` turns piped stdin reads (`curl | grep "foo"`) into blocked filesystem searches — the wrapper sees cwd as the search path and may reject it.

```python
# BAD — turns 'curl url | grep pattern' into a blocked search on cwd
if not search_path:
    search_path = os.getcwd()   # wrong: cwd could be ~, /Users/terry, etc.
```

## Fix

When no path arg is found, the command is reading from stdin — pass it straight through to the real binary via `os.execv`. No path validation needed.

```python
# GOOD — piped stdin reads pass through untouched
if not search_path:
    os.execv(BINARIES.get(binary_name, binary_name),
             [BINARIES.get(binary_name, binary_name)] + args)
```

`os.execv` replaces the current process entirely — no subprocess overhead, no return.

## When This Bites You

- `curl <url> | grep <pattern>` → blocked
- `strings <binary> | grep <pattern>` → blocked
- `cat <file> | rg <pattern>` → blocked
- Any pipeline where grep/rg reads from stdin, not a file path

## General Rule

For any shell wrapper that intercepts a command: **check whether the command is doing a filesystem operation before applying path-based restrictions.** stdin reads have no path — passthrough is always safe.

## Discovered

2026-03-08 — `~/officina/bin/search-guard` was blocking `curl | grep` and `strings | grep` piped commands. Fixed by replacing cwd fallback with execv passthrough.
