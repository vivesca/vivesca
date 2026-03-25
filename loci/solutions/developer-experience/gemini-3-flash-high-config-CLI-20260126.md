---
module: CLI Config
date: 2026-01-26
problem_type: developer_experience
component: tooling
symptoms:
  - "Difficulty setting Gemini 3 Flash High variant as default in opencode"
  - "Standard 'opencode run' command doesn't expose variant identity easily"
root_cause: incomplete_setup
resolution_type: config_change
severity: low
tags: [opencode, gemini-3-flash, configuration, zsh, aliases]
---

# Gemini 3 Flash High Configuration

## Problem Statement
The user wanted to ensure that `opencode` defaults to the **Gemini 3 Flash High** variant. While `opencode` supports a `--variant` flag, it lacked a persistent "set" command similar to `claude-set`, making it difficult to maintain the "High" reasoning effort across interactive and non-interactive sessions.

## Findings
- **Discovery**: `opencode` persists model preferences in `/Users/terry/.local/state/opencode/model.json`.
- **Constraint**: There is no dedicated CLI command (e.g., `opencode config set model ...`) to easily toggle variants globally.
- **Verification**: Using `opencode --model opencode/gemini-3-flash --variant high run` works, but the model response doesn't explicitly confirm the "high" variant status in its self-identification text.

## Proposed Solutions

### Option 1: Zsh Aliases (Selected)
Modify shell aliases to inject the specific model and variant flags for every invocation. This is the most reliable way to force the preference across all terminal sessions.

**Implementation**:
Modify `~/.zshrc`:
```zsh
alias o="opencode --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias oc="opencode --continue --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias or="opencode --model opencode/gemini-3-flash --variant high run --log-level ERROR"
```

### Option 2: State File Modification
Directly edit the JSON state file to register the variant for the TUI.

**Implementation**:
Edit `/Users/terry/.local/state/opencode/model.json`:
```json
"variant": {
  "opencode/gemini-3-flash": "high"
}
```

## Recommended Action
Use **Option 1 (Aliases)** for immediate CLI use and **Option 2 (State File)** to ensure the TUI interactive mode also respects the variant.

## Technical Details
- **Affected Files**:
    - `/Users/terry/.zshrc`
    - `/Users/terry/.local/state/opencode/model.json`
- **Tooling**: `opencode` CLI version 2026.

## Prevention
- When configuring new models in `opencode`, always check `~/.local/state/opencode/` for persistence files.
- Use aliases to override default behavior when the CLI doesn't provide a persistent configuration command.

## Related Issues
- See also: [opencode-startup-log-suppression-CLI-20260126.md](../troubleshooting/opencode-startup-log-suppression-CLI-20260126.md)
