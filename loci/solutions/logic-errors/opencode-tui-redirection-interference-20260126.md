---
module: developer-tools / shell-config
date: 2026-01-26
problem_type: logic_error
component: shell_alias
symptoms:
  - "Broken 'o' alias for 'opencode'"
  - "TUI interface flickering or failing to render correctly"
  - "Process substitution '2> >(grep -v ...)' interfering with terminal input/output"
root_cause: "Process substitution used for log filtering redirected stderr in a way that interfered with the TUI's terminal control sequences."
resolution_type: "native_feature_switch"
severity: medium
tags: [opencode, zsh, alias, tui, process-substitution, logging]
---

# TUI Interruption via Shell Process Substitution

## Problem
The shell alias `o` (an alias for `opencode`) was broken. When invoked, it would either fail to start the TUI correctly or cause visual glitches. This was due to an attempt to filter out specific noisy stderr messages using shell process substitution which interfered with the TUI's ability to control the terminal.

## Environment
- **Platform:** Darwin (macOS)
- **Shell:** zsh (Blink/tmux)
- **Tool:** opencode (CLI with TUI)
- **Date:** 2026-01-26

## Symptoms
- The alias `alias o='opencode 2> >(grep -v "specific noise")'` caused the TUI to hang, flicker, or render incorrectly.
- Direct invocation of `opencode` worked fine, but the alias failed to maintain a stable TUI session.
- Terminal control characters were likely being intercepted or misdirected by the subshell created for process substitution.

## What Didn't Work
Using shell-level redirection to filter startup logs as documented in earlier troubleshooting steps:
```bash
# This caused the TUI interference:
alias o="opencode --model opencode/gemini-3-flash --variant high 2> >(grep -v 'service=models.dev' >&2)"
```
While this successfully filtered the text during the initialization phase, it remained active during the TUI session, causing constant interference with terminal drawing operations.

## Solution
Replaced the shell-level filtering with the native `opencode` logging flag.

Updated aliases in `~/.zshrc`:
```bash
alias o="opencode --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias oc="opencode --continue --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias or="opencode --model opencode/gemini-3-flash --variant high run --log-level ERROR"
```

## Why This Works
1. **Source Suppression**: By using `--log-level ERROR`, the application itself suppresses the `INFO` logs at the source, preventing them from ever reaching `stderr`.
2. **Terminal Integrity**: Removing the `2> >(...)` process substitution ensures that the `stderr` stream remains directly connected to the terminal, allowing the TUI library to use ioctl and escape sequences without interference from a forked `grep` process.

## Prevention
- **Avoid Pipe/Redirection with TUIs**: Never use process substitution or complex pipe chains (`|`) for CLI tools that implement an interactive TUI.
- **Prefer Native Flags**: Always prioritize application-level flags (`--log-level`, `--quiet`, `-s`) for output control.
- **Test interactive Mode**: When wrapping CLI tools in aliases, always test the full interactive TUI mode, not just the non-interactive output.

## Related Issues
- **Direct Cause**: [Opencode Startup Log Suppression](../troubleshooting/opencode-startup-log-suppression-CLI-20260126.md) (Previous attempted fix using redirection).
- **Configuration**: [Gemini 3 Flash High Configuration](../developer-experience/gemini-3-flash-high-config-CLI-20260126.md) (Standardizing the alias structure).
