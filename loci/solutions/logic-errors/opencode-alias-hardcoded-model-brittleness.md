---
title: Hardcoded Model and Variant Flags in 'o' Alias Cause Brittleness
created: 2026-01-27
category: logic-errors
tags:
  - cli-aliases
  - shell-environment
  - opencode
  - configuration-management
module: .zshrc
symptoms:
  - CLI alias 'o' fails when hardcoded model versions are deprecated or renamed
  - Command line flags passed to 'o' are ignored or conflicted by hardcoded parameters
  - Inflexible switching between different LLM providers or variants
  - Redundant configuration drift between .zshrc and tool-specific config (opencode.json)
root_cause: hardcoding model and variant identifiers in high-frequency shell aliases instead of relying on tool defaults or environment variables.
---

## Summary
The `o` alias (and related `oc`, `or`) for `opencode` hardcoded a specific model (`opencode/gemini-3-flash`) and variant (`high`). This made the alias brittle as model versions changed and interfered with the TUI when manual overrides were needed.

## Symptoms
Users encountered issues where the `o` alias stuck to older or specific model versions even when newer ones were available or preferred. Attempts to pass different model flags to the alias also conflicted with the hardcoded defaults in the alias definition.

## Investigation steps
1.  _Search configuration_: Used `rg` to find the definition of the `o` alias in shell startup files.
2.  _Verify tool help_: Checked `opencode --help` to identify native flags for model selection and logging.
3.  _Audit alias usage_: Identified that hardcoding `--model` and `--variant` prevented the application from using its internal preference system (e.g., `model.json`).

## Root cause
-   _Static definition_: The alias used a fixed string for the model and variant, which does not adapt to updates in the tool's available models.
-   _Preference conflict_: Hardcoded flags in the alias take precedence over settings in `opencode.json` or `model.json`, making it difficult to use the application's native configuration management.

## Working solution
Simplified the shell aliases in `~/.zshrc` to remove hardcoded model identifiers and used alias chaining to eliminate redundancy while retaining safety flags like `--log-level ERROR`.

_Before (hardcoded and brittle):_
```zsh
alias o="opencode --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias oc="opencode --continue --model opencode/gemini-3-flash --variant high --log-level ERROR"
alias or="opencode --model opencode/gemini-3-flash --variant high run --log-level ERROR"
```

_After (clean and flexible):_
```zsh
alias o="opencode --log-level ERROR"
alias oc="o --continue"
alias or="o run"
```

## Prevention strategies
1.  _Use native config_: Prefer setting default models and variants in `~/.config/opencode/opencode.json` or `model.json` instead of shell aliases.
2.  _Generic aliases_: Keep aliases minimal. If you need a specific version frequently, use an environment variable (e.g., `export OPENCODE_MODEL="..."`) that the alias references.
3.  _Regular audit_: Periodically check `alias | grep opencode` to ensure aliases have not accumulated stale flags.

## Cross-references
- [[Gemini 3 Flash High Configuration]]
- [[TUI Interruption via Shell Process Substitution]]
- [[LFG Namespace and Sync Robustness]]
