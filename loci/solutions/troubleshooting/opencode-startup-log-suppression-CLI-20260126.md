---
module: CLI Config
date: 2026-01-26
problem_type: ui_bug
component: cli_tool
symptoms:
  - "Hardcoded INFO logs at startup: service=models.dev refreshing"
  - "Log level flags (--log-level WARN) ignored during initialization"
root_cause: hardcoded_log_in_binary
severity: low
tags: [opencode, zsh, logging, stderr-filtering]
---

# Opencode Startup Log Suppression

## Problem Statement
Every time the `opencode` CLI (or its alias `o`) is invoked, an informational log message is printed to `stderr` during the initialization phase:
`INFO  2026-01-26T12:32:02 +67ms service=models.dev file={} refreshing`

This happens even when the user specifies `--log-level WARN` because the model refresh sequence occurs before the log-level configuration is fully applied.

## Findings
- **Location**: Hardcoded in the binary `/opt/homebrew/bin/opencode`.
- **Symptoms**: Extra line of text before the logo/output.
- **Failed Attempts**:
    - Setting `--log-level WARN` or `ERROR` (ignored during boot).
    - Setting `LOG_LEVEL=warn` environment variable (ignored).
    - Searching for a "silent" or "quiet" flag in `--help` (none exists for this specific log).

## Proposed Solutions

### Option 1: Shell-level Stderr Filtering (Selected)
Filter the specific log line at the shell level using process substitution. This ensures that only the annoying line is removed while other legitimate errors are still visible.

**Implementation**:
Modify the alias in `~/.zshrc`:
```zsh
alias o="opencode 2> >(grep -v 'service=models.dev' >&2)"
```

## Recommended Action (SUPERSEDED)
> [!WARNING]
> **This approach is DEPRECATED.** While it successfully filters logs, the process substitution `2> >(...)` interferes with the `opencode` TUI, causing rendering issues and instability. 
> 
> See the updated solution: [TUI Interruption via Shell Process Substitution](../logic-errors/opencode-tui-redirection-interference-20260126.md)

### Updated Recommendation
Use the native `--log-level ERROR` flag instead of shell redirection.

## Technical Details
- **Affected Files**: `~/.zshrc`
- **Shell Pattern**: `2> >(command >&2)` redirects stderr to a subshell.
- **Side Effect**: Forked subshells for `grep` break terminal control sequences for interactive TUIs.

## Acceptance Criteria
- [x] Running `o` no longer shows the `service=models.dev` log.
- [x] Logo and normal output remain visible.
- [x] Legitimate errors (e.g., command not found) are still reported.

## Work Log
### 2026-01-26 - Issue Resolved
Documented the fix after verifying the shell alias successfully suppressed the log line without side effects.
