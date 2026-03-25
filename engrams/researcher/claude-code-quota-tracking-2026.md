---
name: Claude Code In-Session Quota Tracking
description: How to check Max plan quota (5-hour/weekly %) from inside a running Claude Code session — endpoint, token gotchas, tool landscape
type: reference
---

## The Canonical Approach (Mar 2026)

**Endpoint:** `GET https://api.anthropic.com/api/oauth/usage`
**Headers:** `Authorization: Bearer <accessToken>`, `anthropic-beta: oauth-2025-04-20`
**Token source (macOS):** `security find-generic-password -s "Claude Code-credentials" -w` → JSON → `.claudeAiOauth.accessToken`

Response fields: `five_hour.utilization`, `seven_day.utilization`, `seven_day_sonnet.utilization`, `extra_usage.amount_usd/limit_usd` (all %s 0-100).

This is what Terry's `usus` tool (`~/code/usus/`) does. It is the best available tool for this use case.

## Critical Scope Requirement
Token must have **both** `user:inference` AND `user:profile` scopes. Only browser-based OAuth login at CC startup generates this. `claude setup-token` gives only `user:inference` → 403 on usage endpoint.

## Token Expiry — The Core Problem
Access token expires ~1hr after CC session start. Stored `expiresAt` timestamp in Keychain. No community tool handles programmatic refresh. OAuth uses refresh token rotation (RFC 9700) — single-use, opaque endpoint, and refresh sometimes drops `user:profile` scope (GH #34785). Workaround: restart Claude Code (new session refreshes Keychain token).

## What the Other Tools Do (and Don't Do)
- **ccusage** — reads local JSONL, token accounting only, NO quota %
- **Claude-Code-Usage-Monitor** — reads JSONL + ML prediction, NO quota %
- Both miss cross-platform usage (web, mobile, Desktop)
- No MCP server for quota tracking exists as of Mar 2026

## Statusline Integration
statusLine JSON payload does NOT include quota fields — open FR (GH #15366, #22428, no Anthropic response). Workaround: call `usus --statusline` from statusLine command. Goes dark when token expires.

## Hook-Based Injection
`UserPromptSubmit` hook can inject quota into Claude's context via `additionalContext` before each message. Same token expiry problem applies.

## OTEL
`CLAUDE_CODE_ENABLE_TELEMETRY=1` exports token/cost metrics per-request but NOT quota utilization %. Not useful for the in-session display problem.

## Source Reliability
- gist.github.com/jtbr — most complete community statusline guide, reliable
- codelynx.dev/posts/claude-code-usage-limits-statusline — reliable, Keychain details
- gist.github.com/omachala — simple CLI gist, reliable
- GH issues #13585, #15366, #22428 — feature requests confirming no official solution
- code.claude.com/docs — authoritative (statusline, auth, monitoring)
- ccusage.com — reliable but limited scope (JSONL only)
