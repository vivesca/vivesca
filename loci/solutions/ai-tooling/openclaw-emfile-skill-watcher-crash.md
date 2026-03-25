---
module: OpenClaw
date: 2026-02-04
problem_type: runtime_error
component: cli_tool
symptoms:
  - "EMFILE: too many open files"
  - "OpenClaw gateway won't start"
  - "OpenClaw connect error after skill changes"
  - "Skills watcher errors in gateway.err.log"
root_cause: config_error
resolution_type: config_change
severity: high
tags: [openclaw, emfile, file-watcher, venv, skills, gateway]
related_files:
  - ~/.openclaw/logs/gateway.err.log
  - ~/.openclaw/skills/
  - ~/skills/
---

# OpenClaw EMFILE crash from skill watcher exhausting file descriptors

## Problem

OpenClaw gateway crashes on startup with `EMFILE: too many open files` errors. The gateway process cannot start, preventing any connection to OpenClaw.

## Symptoms

```
Error: EMFILE: too many open files, watch at '/Users/terry/skills/memu/.venv/lib/python3.11/site-packages/...'
```

- Gateway fails to start
- `openclaw doctor` hangs or fails
- Log file shows hundreds of EMFILE errors pointing to `.venv` directories

## Root Cause

OpenClaw's skill file watcher recursively monitors all directories symlinked into `~/.openclaw/skills/` plus any paths in `extraDirs` config (which includes `~/skills/`).

The watcher follows symlinks and monitors ALL files, including:
- Python virtual environments (`.venv`)
- Node modules (`node_modules`)
- Build artifacts

A single Python `.venv` can contain 10,000+ files. macOS default file descriptor limit is 10,240. One large virtual environment can exhaust this limit entirely.

**The specific culprit:** `memu` (a Python memory framework project) was symlinked into `~/.openclaw/skills/` despite not being a valid OpenClaw skill (no `SKILL.md`). Its 133MB `.venv` directory contained thousands of Python packages.

## Why This Is Easy to Miss

1. The symlink looks innocent: just another skill directory
2. OpenClaw doesn't validate skills have `SKILL.md` before watching
3. Error logs show deep `.venv` paths, not the symlink that caused them
4. The crash is immediate on gateway start, giving no debugging time

## Solution

### Immediate Fix

1. Find the offending symlink:
   ```bash
   ls -la ~/.openclaw/skills/ | grep -E 'venv|node_modules'
   # Or check logs for paths
   grep EMFILE ~/.openclaw/logs/gateway.err.log | head -5
   ```

2. Remove invalid skill symlinks:
   ```bash
   rm /Users/terry/.openclaw/skills/memu  # or whatever project
   ```

3. Restart OpenClaw:
   ```bash
   pkill -f "openclaw"
   openclaw doctor
   ```

### Verify Fix

```bash
# Should start without EMFILE errors
openclaw doctor

# Check logs are clean
tail ~/.openclaw/logs/gateway.err.log
```

## Prevention

### Hard Rule

**Only symlink actual OpenClaw skills** (directories containing `SKILL.md`) into `~/.openclaw/skills/`.

### Before Symlinking Any Directory

1. Verify it has `SKILL.md`:
   ```bash
   ls ~/skills/project-name/SKILL.md
   ```

2. Check for heavy directories:
   ```bash
   du -sh ~/skills/project-name/.venv ~/skills/project-name/node_modules 2>/dev/null
   ```

3. If the project needs `.venv` for development, don't symlink it as a skill

### For Projects in `~/skills/`

The `~/skills/` directory is watched via `extraDirs`. If you must have Python projects there:

1. Add `.venv` and `node_modules` to `.gitignore`
2. Delete `.venv` before checking if it's causing issues
3. Better: keep Python projects in `~/projects/` instead of `~/skills/`

## Investigation Path

This is the diagnostic sequence that found the issue:

1. **Check gateway logs first:**
   ```bash
   cat ~/.openclaw/logs/gateway.err.log | head -50
   ```

2. **Extract the watched path from EMFILE errors:**
   ```
   Error: EMFILE: too many open files, watch at '/Users/terry/skills/memu/.venv/...'
   ```
   The path before `.venv` is the culprit project.

3. **Find where it's symlinked:**
   ```bash
   ls -la ~/.openclaw/skills/
   ```

4. **Verify it's not a real skill:**
   ```bash
   ls ~/skills/memu/SKILL.md  # File not found = not a skill
   ```

## Key Insight

OpenClaw's architecture assumes skill directories are small (markdown, a few scripts). It watches everything recursively with no exclusion patterns. A single Python project with dependencies can bring down the entire gateway.

**File descriptor math:**
- macOS limit: ~10,240 FDs
- Typical Python .venv: 5,000-15,000 files
- OpenClaw + other processes: ~500 FDs
- Result: One .venv = instant exhaustion

## Related Issues

If you see EMFILE in other contexts, the pattern is the same: something is watching too many files. Check:
- FSWatch processes
- Node file watchers (webpack, vite, esbuild)
- IDE indexers

The fix is always: reduce watched scope or increase ulimit (temporary workaround).
