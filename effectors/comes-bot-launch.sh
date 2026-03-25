#!/usr/bin/env bash
# Wrapper for comes-bot LaunchAgent — injects secrets from 1Password

source /Users/terry/.config/comes/env

exec /Users/terry/.cargo/bin/comes-bot
