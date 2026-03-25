---
title: Credential Isolation via macOS Keychain
date: 2026-02-24
category: security
tags: [credentials, keychain, prompt-injection, bash-guard, claude-code]
problem: All API keys in .zshenv and .secrets visible to AI agent shells via env/echo/cat
trigger: Saw claw-wrap (credential proxy for sandboxed agents) and evaluated lighter alternative
---

# Credential Isolation via macOS Keychain

**Problem:** 26 API keys in `.zshenv` and `.secrets` were visible to Claude Code (and all AI coding tools) via `env`, `echo $VAR`, or `cat ~/.secrets`. Any prompt injection could trivially exfiltrate them.

**Solution:** Migrated credentials to macOS Keychain with a tty guard in `.zshrc` and bash-guard patterns blocking direct credential access.

## Architecture

```
Interactive shell (Terry)          AI agent shell (Claude/OpenCode/Codex)
      │                                  │
  .zshrc loads                      .zshrc loads
      │                                  │
  stdin is a tty (-t 0)            stdin is NOT a tty
      │                                  │
  eval "$(keychain-env)"           SKIP credential loading
      │                                  │
  26 env vars set                  NO credentials in env
      │                                  │
  Tools work normally              Tools with _keychain() fallback
                                   still work (grok, wu transcribe)
```

## Components

1. **`~/bin/keychain-env`** — Python script mapping env var names to Keychain service names. Shell mode: `eval "$(keychain-env)"`. Python mode: importable module with `load_keychain_env()`.
2. **`.zshrc` tty guard** — `[[ -t 0 ]]` check loads credentials only when stdin is a terminal. Catches all AI tools (Claude Code, OpenCode, Codex, Cursor) since none attach a real tty.
3. **bash-guard.js** — Blocks `cat .secrets`, `security find-generic-password`, and `env | grep KEY/TOKEN/SECRET/PASSWORD`.
4. **Tool-level Keychain fallback** — Python scripts (`grok`, `wu/transcribe.py`, `oura-data/sync.py`) call `security find-generic-password` directly when env var is missing. This lets them work in agent shells without exposing credentials to the agent's env.

## Keychain Service Names

| Env Var | Keychain Service |
|---------|-----------------|
| XAI_API_KEY | xai-api-key |
| DEEPGRAM_API_KEY | deepgram-api-key |
| SPEECHMATICS_API_KEY | speechmatics-api-key |
| GEMINI_API_KEY | gemini-api-key-secrets |
| GOOGLE_API_KEY | google-api-key-secrets |
| GOG_KEYRING_PASSWORD | gog-keyring-password |
| OPENROUTER_API_KEY | openrouter-api-key |
| ANTHROPIC_API_KEY | anthropic-api-key |
| OPENAI_API_KEY | openai-api-key |
| MOONSHOT_API_KEY | moonshot-api-key |
| BRAVE_API_KEY | brave-api-key |
| TAVILY_API_KEY | tavily-api-key |
| PERPLEXITY_API_KEY | perplexity-api-key |
| EXA_API_KEY | exa-api-key |
| SERPER_API_KEY | serper-api-key |
| PYPI_TOKEN | pypi-token |
| OP_MASTER_PASSWORD | op-master-password |
| OP_SECRET_KEY | op-secret-key |
| OURA_TOKEN | oura-token |
| LLAMA_CLOUD_API_KEY | llama-cloud-api-key |
| MXBAI_API_KEY | mxbai-api-key |
| KILO_API_TOKEN | kilo-api-token |
| HKGBOOK_API_KEY | hkgbook-api-key |
| TELEGRAM_BOT_TOKEN | telegram-bot-token |
| TELEGRAM_CHAT_ID | telegram-chat-id |
| PLAYWRIGHT_MCP_EXTENSION_TOKEN | playwright-mcp-token |

## Adding a New Credential

```bash
# 1. Store in Keychain
security add-generic-password -a "$USER" -s "service-name" -w "secret-value" -U

# 2. Add mapping to ~/bin/keychain-env CREDENTIALS dict
"ENV_VAR_NAME": "service-name",
```

## Investigation Steps

1. Evaluated [claw-wrap](https://github.com/dedene/claw-wrap) — full credential proxy for sandboxed agents. Sound architecture (daemon outside sandbox, HMAC-signed requests from client inside) but requires a sandbox boundary to be meaningful. Without firejail/nono, proxy adds ceremony without isolation.
2. Checked Claude Code's shell: parent process is `/Users/terry/.local/bin/claude`, `tty` returns "not a tty". Both are reliable discriminators.
3. Initial implementation used parent-process name check (`ps -o comm= -p $PPID != */claude*`). Realized this only blocks Claude Code — OpenCode, Codex, Cursor would still get credentials. Switched to tty check (`-t 0`) which catches all AI tools generically.
4. Discovered `.secrets` file (sourced from `.zshrc`) had 20+ additional credentials beyond `.zshenv` — including 1Password master password, Telegram bot token, and all LLM API keys. Migrated everything.
5. Added bash-guard patterns as defense-in-depth layer.
6. Added `_keychain()` fallback to Python tools that Claude Code legitimately calls (`grok`, `wu transcribe`, `oura sync`).

## Known Limitations

- **Go/Rust binaries** (gog, pplx) can't be patched — they work in interactive shells (env set) but not in AI agent shells. Acceptable: credential isolation means agents can't use these tools directly.
- **Claude Code Read tool** bypasses bash-guard (which only gates Bash tool). Can read `~/bin/keychain-env` and see service names (but not values).
- **Gemini CLI** expects `GOOGLE_API_KEY` in env — works in Terry's shell, not in agent shells.
- **bash-guard patterns are bypassable** by creative prompt injection (base64 encoding, variable indirection, Python subprocess). Defense in depth, not absolute.

## Threat Model

Raises the bar from "trivially in env" to "need to know macOS security CLI + exact service names + bash-guard blocks the obvious paths." Not a sandbox — a speed bump that defeats casual prompt injection. Defence layers: (1) credentials not in env, (2) bash-guard blocks direct access patterns, (3) tools fetch their own credentials without exposing them to the calling process's env.

## Options Considered

| Option | Approach | Verdict |
|--------|----------|---------|
| **A — Keychain + tty guard** | Move creds to Keychain, tty guard in .zshrc | **Implemented** |
| **B — bash-guard only** | Block `cat .secrets`, `env \| grep KEY` | Implemented as complement; insufficient alone |
| **C — claw-wrap + sandbox** | Full credential proxy with sandbox boundary | Bookmark for Q2; needs sandbox to be meaningful |
| **D — nono sandbox (macOS)** | Deny-by-default process isolation | Future; creates trust boundary for Option C |

## Future Hardening

1. **Output redaction hook** — PostToolUse hook scanning for key prefixes (`sk-`, `ghp_`, `AIzaSy`, `pplx-`, `xai-`). Strip before returning to agent.
2. **Command allowlisting** — Expand bash-guard to allowlist mode for sensitive tools (e.g. only specific `gh` subcommands).
3. **Credential rotation alerting** — PostToolUse hook flagging when credential patterns appear in conversation output.
4. **Sandbox adoption** — When Claude Code or macOS tooling supports deny-by-default sandboxing, adopt claw-wrap for proper architectural isolation.

## Inspired By

[claw-wrap](https://github.com/dedene/claw-wrap) by Peter Dedene — full credential proxy for sandboxed agents. Shared in reply to Karpathy's concerns about agent credential exposure. claw-wrap is the proper solution when a sandbox boundary exists; this Keychain approach is the lightweight alternative for unsandboxed setups.

## Credential Recovery Search Pattern (LRN-20260307-001)

When recovering a lost/forgotten API key for a CLI tool, search in this order:

1. **`~/.config/<toolname>/`** — XDG standard, often overlooked when tool uses a non-standard dir
2. **`~/.<toolname>/`** — legacy dotdir
3. **`~/Library/Application Support/<toolname>/`** — macOS standard
4. **1Password** — `op item list | grep -i <toolname>`
5. **Env files** — `~/.zshenv`, `~/.zshenv.tpl`, `~/.zshenv.local`
6. **App DB** — e.g. `~/.local/share/<toolname>/*.db` (SQLite)

Use `/usr/bin/find <dir> -type f` to map all files first, then inspect. Don't grep for the key pattern until you know where the tool writes config — grepping blindly misses the right file and wastes time.

**Real example:** Moltbook API key (`moltbook_sk_...`) was in `~/.config/moltbook/credentials.json` — found only after exhausting Clawdbot dirs, OpenCode DB, 1Password, and env files. Would have been found in step 1 with this checklist.
