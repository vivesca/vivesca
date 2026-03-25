# Gemini CLI Gotchas

## Auth Precedence

OAuth > API key. If `~/.gemini/oauth_creds.json` exists and `settings.json` has `"selectedType": "oauth-personal"`, the CLI ignores `GEMINI_API_KEY` env var entirely ("Loaded cached credentials").

To force API key auth: set `"selectedType": "gemini-api-key"` in `~/.gemini/settings.json`.

Between env vars: `GOOGLE_API_KEY` takes precedence over `GEMINI_API_KEY`. If both are set, CLI warns and uses `GOOGLE_API_KEY`.

API key can also live in `~/.gemini/.env` (global) or `./.gemini/.env` (project-level).

## Model Availability vs Plan

Not all models are available on all auth methods. As of Feb 2026:

- `gemini-3.1-pro-preview` — Available on OAuth/AI Pro plan ($20/mo) as of Feb 25 2026 (CLI v0.29.5). Also on API key (pay-as-you-go). Zero free tier quota (`limit: 0`).
- `gemini-3-pro-preview` — Available on both OAuth (Pro plan) and free tier API key.

## Rate Limits (Google AI Pro Plan, $20/mo)

| Dimension | Limit |
|---|---|
| Requests per minute | 120 RPM |
| Requests per day | 1,500 RPD |

**Practical budget is much lower:** One CLI prompt triggers multiple API requests internally (tool calls, thinking, retries). Expect ~250-500 actual prompts/day, not 1,500. [Source: Google Code Assist quotas docs + user reports](https://developers.google.com/gemini-code-assist/resources/quotas)

For comparison: Free = 60 RPM / 1,000 RPD. Ultra ($250) = 120 RPM / 2,000 RPD.

## Auto-Routing (Default Model Selection)

CLI defaults to "Auto" mode which routes by complexity:
- **Simple prompts** → Gemini 2.5 Flash (or 3 Flash preview when available)
- **Complex prompts** → Gemini 3 Pro

Force a specific model with `-m`: `gemini -p "prompt" -m gemini-3-pro`

## Flash 429 Capacity Errors

`gemini-3-flash-preview` frequently hits `MODEL_CAPACITY_EXHAUSTED` (HTTP 429). The CLI retries with exponential backoff automatically, but this adds ~30s delay. Error looks like:

```
"message": "No capacity available for model gemini-3-flash-preview on the server"
"reason": "MODEL_CAPACITY_EXHAUSTED"
```

**Workaround:** Force Pro to skip Flash entirely: `gemini -p "prompt" --yolo -m gemini-3-pro`

## Headless / Delegation Mode

For use as a delegation target from Claude Code:

```bash
gemini -p "<prompt>" --yolo
```

- `-p` = non-interactive (headless) mode
- `--yolo` = auto-approve all tool calls (file writes, shell commands)
- No prompt length issues (1M context window)
- Scans working directory on startup (WARN on unreadable dirs is harmless noise)

## Config Files

- `~/.gemini/settings.json` — auth type (`oauth-personal` or `gemini-api-key`)
- `~/.gemini/oauth_creds.json` — cached Google OAuth tokens
- `~/.gemini/.env` — API key for non-OAuth auth

## Terry's Setup

- Alias: `g` → `gemini` (in `.zshrc`)
- Auth: OAuth via Google AI Pro plan ($20/mo, subscribed Feb 22 2026)
- API key also configured in `.zshenv` + `.gemini/.env` for future pay-as-you-go use
- Delegation target in Claude Code `/delegate --gemini` skill
- `gemini-3.1-pro-preview` confirmed working via OAuth/AI Pro plan (tested Feb 25 2026, CLI v0.29.5)
