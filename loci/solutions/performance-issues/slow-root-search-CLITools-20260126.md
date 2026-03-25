module: CLI Tools
date: 2026-01-26
problem_type: performance_issue
component: assistant
symptoms:
  - "Global grep/glob on /Users/terry is extremely slow"
  - "CLI hangs during unconstrained searches"
root_cause: config_error
resolution_type: code_fix
severity: high
tags: [performance, grep, glob, safe-search, friction-point]
---

# Troubleshooting: Slow Root Directory Search Performance

## Problem
Searching the entire home directory (`/Users/terry`) using `grep` or `glob` without a specific path is extremely slow and causes the CLI to hang. This occurs because the search crawls through massive, irrelevant system directories and hidden caches.

## Environment
- Module: CLI Tools / Assistant
- Affected Component: Search Tools (grep, glob)
- Date: 2026-01-26

## Symptoms
- `grep` or `glob` tool calls take a long time to return or are interrupted.
- High latency during initial project exploration.
- CLI unresponsive while waiting for broad file system operations.

## What Didn't Work

**Attempted Solution 1:** Direct `grep` or `glob` on root.
- **Why it failed:** The home directory contains `Library`, `Pictures`, `Downloads`, and other large folders that are irrelevant to coding tasks but contain millions of files.

## Solution

Implemented a multi-layered "Friction Point" strategy to enforce efficient search patterns.

**1. Technical Control: Safe Search Script**
Created a Python script to intercept and validate searches before execution.

**Code changes** (new script `~/scripts/safe_search.py`):
```python
# Hard block on searching the root directly
if search_path == root_path or search_path == "/Users/terry":
    print("ERROR: Searching the root directory is PROHIBITED due to performance.")
    print("Please specify a sub-directory (e.g., notes, bank-faq-chatbot).")
    sys.exit(1)

# Use ripgrep with smart exclusions for speed
cmd = [
    "rg", 
    "--glob", "!.Library/*",
    "--glob", "!.Trash/*",
    "--glob", "!Pictures/*",
    "--glob", "!Downloads/*",
    pattern, 
    search_path
]
```

**2. Policy Control: AGENTS.md Hard Constraints**
Updated the core instructions to define root searches as a "HARD CONSTRAINT" violation.

**Commands run**:
```bash
# Created scripts directory
mkdir -p /Users/terry/scripts
# Made script executable
chmod +x /Users/terry/scripts/safe_search.py
```

## Why This Works

1. **Root Cause:** The agent's tendency to use "lazy" global searches when unsure of a file's location.
2. **Technical fix:** The `safe_search.py` script enforces a `path` parameter and provides `ripgrep` (`rg`) performance with intelligent exclusions (Library, Trash, etc.).
3. **Psychological fix:** Adding "HARD CONSTRAINT" to `AGENTS.md` (CLAUDE.md) ensures the agent checks for this limitation during the planning phase, preventing the slow tool call from being initiated in the first place.

## Prevention

- **Narrow the scope**: Always specify a `path` parameter (e.g., `path: 'bank-faq-chatbot'`) in tool calls.
- **Use safe_search.py**: For any broad search, use `python3 /Users/terry/scripts/safe_search.py "<pattern>" <path>`.
- **Prefer rg**: Use `ripgrep` via the `bash` tool for any search touching multiple directories.
- **Subagent Exploration**: Use `subagent_type="explore"` for deep architectural discovery instead of broad grepping.

## Related Issues
No related issues documented yet.

