---
title: Claude Code with Alternative Backends (Kimi, GLM)
date: 2026-02-21
category: tool-configuration
tags: [claude-code, kimi, moonshot, glm, zhipu, cost-optimization, resilience]
symptoms:
  - "Auth conflict: Both a token and an API key are set"
  - "API Error: 401 Invalid Authentication"
  - "Not found the model claude-opus-4-5-20251101"
  - "Claude API is down"
---

# Claude Code with Alternative Backends (Kimi, GLM)

## Purpose

Use Claude Code CLI with non-Anthropic models as fallback when Claude is down, or for cheaper bulk work.

## Architecture

Each provider gets an isolated HOME directory to avoid auth conflicts with the main Claude login. The `settings.json` in each home sets `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MODEL`. Shell aliases blank out the main credentials and point to the isolated home.

## Current Setup (Feb 2026)

| Command | Model | Endpoint (CN) | Cost |
|---------|-------|----------------|------|
| `c` | Claude Opus 4.6 | api.anthropic.com | Max plan |
| `cs` | Claude Sonnet 4.6 | api.anthropic.com | Max plan |
| `ck` | Kimi K2.5 | api.moonshot.cn/anthropic/ | ~$0.60/M in, $3/M out |
| `cg` | GLM-5 | open.bigmodel.cn/api/anthropic | ~$1.30/M in, $4.16/M out |

## Files

### Kimi: `~/kimi-home/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "<MOONSHOT_API_KEY from ~/.secrets>",
    "ANTHROPIC_BASE_URL": "https://api.moonshot.cn/anthropic/",
    "ANTHROPIC_MODEL": "kimi-k2.5"
  }
}
```

Key source: https://platform.moonshot.cn/console/api-keys

### GLM: `~/glm-home/.claude/settings.json`

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "<Zhipu key from OpenCode auth>",
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
    "ANTHROPIC_MODEL": "glm-5"
  }
}
```

Key source: https://open.bigmodel.cn/ (also stored in `~/.local/share/opencode/auth.json` under `zhipuai-coding-plan`)

### Launcher scripts (`~/bin/ck`, `~/bin/cg`)

Scripts (not aliases) because env var precedence in aliases is unreliable — `ANTHROPIC_API_KEY=` in an alias gets overridden by settings.json or vice versa.

```bash
#!/bin/bash
# ~/bin/ck
export HOME=~/kimi-home
export ANTHROPIC_API_KEY="<moonshot-key>"
export ANTHROPIC_BASE_URL="https://api.moonshot.cn/anthropic/"
export ANTHROPIC_MODEL="kimi-k2.5"
unset ANTHROPIC_AUTH_TOKEN
exec /Users/terry/.local/bin/claude --dangerously-skip-permissions "$@"
```

Same pattern for `~/bin/cg` with GLM credentials. `~/bin` added to PATH in `~/.zshenv`.

## Key Insights

1. `ANTHROPIC_MODEL` env var is what overrides the model — not `--model` flag, not `model` in settings.json
2. Separate HOME directory avoids auth token conflicts with claude.ai login
3. CN domains (`api.moonshot.cn`, `open.bigmodel.cn`) work from HK — no VPN needed
4. Both providers expose native Anthropic-compatible `/anthropic/` endpoints — no proxy needed
5. Direct endpoints confirmed: Kimi K2.5 supports tool use; GLM-5 supports tool use
6. **Pre-seed `$HOME/.claude.json` for clean launch:** Copy from main `~/.claude.json` (minus `oauthAccount`, `clientDataCache`, sensitive caches). Key fields: `customApiKeyResponses.approved` must contain the **last 20 chars** of the provider API key to skip the "custom API key detected" prompt. Also needs all migration flags (`opusProMigrationComplete`, etc.) and `hasCompletedOnboarding: true` with `lastOnboardingVersion` to skip theme picker. The `--dangerously-skip-permissions` acceptance is also stored here — accept once, then sync to other isolated homes.

## What Didn't Work (historical)

| Approach | Result |
|----------|--------|
| `--settings` flag with env block | Triggers "custom API key detected" prompt; key lands in `.claude.json` rejected list. Not viable for seamless switching. |

| Approach | Result |
|----------|--------|
| `--model kimi-k2-turbo-preview` flag | Ignored, still sent claude-opus |
| `model` key in settings.json | Ignored |
| `ANTHROPIC_AUTH_TOKEN` | 401 with moonshot.cn endpoint |
| `api.moonshot.ai/anthropic/` endpoint | 401 with standard moonshot key |
| `api.kimi.com/coding/` endpoint | Requires `sk-kimi-*` format key |

## Caveats

1. **Cost display is inaccurate** — Claude Code shows Anthropic pricing formulas
2. **UI still shows "Opus"** — but requests go to the alternative model (verify with `/status`)
3. **MCP servers won't load** — isolated homes have no MCP config
4. **Skills won't load** — no `~/.claude/skills/` in isolated homes (could symlink if needed)
5. **Extended thinking may silently degrade** on non-Claude models

## Other Providers with Direct Anthropic Endpoints

| Provider | ANTHROPIC_BASE_URL | Notes |
|----------|-------------------|-------|
| DeepSeek | `https://api.deepseek.com/anthropic` | Silently maps any model name to deepseek-chat |

## Proxy Projects (if direct endpoint unavailable)

- **LiteLLM** — officially recommended by Anthropic, 100+ providers
- **claude-code-proxy** (3.1K stars) — OpenAI/Gemini backends
- **openbridge** — Kimi/GLM/Qwen/DeepSeek
- **CCProxy** — multi-provider with config file

## References

- [fsck.com: Claude Code with Kimi K2](https://blog.fsck.com/2025/07/13/claude-code-with-kimi-k2/)
- [claude-code-switch tool](https://github.com/foreveryh/claude-code-switch)
- [Kimi Third-Party Agents Docs](https://www.kimi.com/code/docs/en/more/third-party-agents.html)
- [Claude Code LLM Gateway Docs](https://code.claude.com/docs/en/llm-gateway)
- [Zhipu Anthropic endpoint](https://open.bigmodel.cn/)
