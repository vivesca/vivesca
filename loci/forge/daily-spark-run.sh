#!/bin/bash
set -e
# Wrapper for daily-spark LaunchAgent
# Uses claude --print (Max20 plan) — no API key needed, just claude on PATH

source "$HOME/.zshenv.local"

exec /usr/bin/python3 /Users/terry/vivesca/loci/forge/daily-spark.py
