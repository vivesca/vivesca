---
title: Vasomotor sensor reads credentials from wrong path
tags: [gotcha, vasomotor, budget, credentials]
created: 2026-03-27
---

## Problem

`vasomotor_sensor.py` was reading OAuth token from macOS Keychain (`Claude Code-credentials`), which doesn't exist. CC CLI stores credentials in `~/.claude/.credentials.json`.

Consequence: `sense_usage()` fell back to stale cache (`~/.local/share/respirometry/history.jsonl`), reporting 82% when actual was 90%.

## Fix

Changed `get_oauth_token()` to read `~/.claude/.credentials.json` as primary source, Keychain as legacy fallback. Added expiry checks.
