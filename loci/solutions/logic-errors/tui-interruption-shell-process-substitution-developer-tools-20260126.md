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
tags: [shell, alias, tui, process-substitution, logging]
---

# TUI Interruption via Shell Process Substitution

## Problem
The shell alias `o` (an alias for `opencode`) was broken. When invoked, it would either fail to start the TUI correctly or cause visual glitches. This was due to an attempt to filter out specific noisy stderr messages using shell process substitution.

## Environment
- **Platform:** Darwin (macOS)
- **Shell:** zsh/bash
- **Tool:** opencode (CLI with TUI)

## Symptoms
- The alias `alias o='opencode 2> >(grep -v "specific noise")'` caused the TUI to hang or render incorrectly.
- Direct invocation of `opencode` worked fine, but the alias failed.
- The terminal state seemed corrupted after attempting to run the aliased command.

## What Didn't Work
Using shell-level redirection to filter logs:
```bash
alias o='opencode 2> >(grep -v "noisy log message" >&2)'
```
While this successfully filtered the text, the way process substitution handles the file descriptors interfered with how the TUI (likely using libraries like `blessed` or `termion`) took control of the terminal's STDIN/STDOUT/STDERR.

## Solution
Instead of using shell redirection to filter output, use the tool's native logging controls to suppress noise at the source.

Updated aliases in shell configuration:
```bash
alias o='opencode --log-level ERROR'
alias oc='opencode --log-level ERROR'
alias or='opencode --log-level ERROR'
```

## Why This Works
By using `--log-level ERROR`, the application itself decides not to write the noisy info/warn messages to stderr. This keeps the stderr stream clean without requiring the shell to fork a sub-process for `grep`, which preserves the integrity of the terminal's control sequences for the TUI.

## Prevention
- Avoid using process substitution (`>(...)`) or complex pipe chains for CLI tools that implement a full-screen TUI.
- Always prefer native application flags for log level control (`--verbose`, `--quiet`, `--log-level`) over shell pipe filtering.
- Test TUI aliases in a clean shell environment to ensure terminal control codes are not being intercepted.

## Related Issues
- - See also: [hardcoded-project-references-compound-plugin-20260126.md](hardcoded-project-references-compound-plugin-20260126.md)
