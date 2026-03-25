#!/bin/bash
# Wrapper for exocytosis LaunchAgent — injects 1Password env before running uv script.
set -e

# Source service account token (no Touch ID required)
# shellcheck source=/Users/terry/.zshenv.local
source "$HOME/.zshenv.local"

# Inject all API keys from 1Password template
eval "$(/Users/terry/.local/bin/op inject -i "$HOME/.zshenv.tpl" 2>/dev/null)" || true

exec /Users/terry/.local/bin/uv run --python 3.13 --script /Users/terry/reticulum/bin/exocytosis.py
