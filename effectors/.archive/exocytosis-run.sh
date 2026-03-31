#!/bin/bash
# Wrapper for exocytosis LaunchAgent — injects 1Password env before running uv script.
set -e

# Source service account token (no Touch ID required)
# shellcheck source=~/.zshenv.local
source "$HOME/.zshenv.local"

# Inject all API keys from 1Password template
eval "$($HOME/.local/bin/op inject -i "$HOME/.zshenv.tpl" 2>/dev/null)" || true

exec $HOME/.local/bin/uv run --python 3.13 --script $HOME/reticulum/bin/exocytosis.py
