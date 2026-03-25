#!/usr/bin/env bash
# Wrapper for comes nudge LaunchAgent — injects secrets from keychain

source /Users/terry/.config/comes/env

exec /Users/terry/.cargo/bin/comes nudge
