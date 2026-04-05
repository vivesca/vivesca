---
name: comes
description: "Personal AI life coach CLI (crate: phron). Health monitoring, morning brief, overnight research, proactive nudges. `comes brief`, `comes health`, `comes overnight`, `comes nudge`"
user_invocable: false
---

# comes — AI Life Coach CLI

Crate: `phron` on crates.io. Binary: `comes`. Source: `~/code/phron/`. GitHub: https://github.com/terry-li-hm/phron

## Commands

| Command | What it does |
|---|---|
| `comes health` | Oura readiness → Green/Yellow/Red + HRV + sleep score |
| `comes brief` | Morning brief: health + calendar (fasti) + LLM synthesis |
| `comes nudge` | If Red: pacemaker Due reminder + Telegram alert |
| `comes overnight` | OpenRouter research per topic → vault digest → Telegram summary |
| `comes status` | Stub (Phase 3) |

## Telegram Bot Commands (comes-bot)

| Message type | What it does |
|---|---|
| `/health` | Same as `comes health` — Oura readiness report |
| `/brief` | Same as `comes brief` — morning synthesis |
| `/status` | System status |
| `/help` | Available commands |
| Voice message | Whisper transcription → librosa audio analysis → 5-dimension speaking critique |
| PDF document | pdftotext extraction → 5-dimension deck/presentation critique (structure, exec clarity, MECE, evidence, action) |

## Config

`~/.config/comes/config.toml` — copy from `~/code/phron/config.toml.example`

Key fields:
- `[vault] path` — Obsidian vault root (e.g. `~/epigenome/chromatin`)
- `[vault] overnight_dir` — subdir for overnight digests
- `[llm] synthesis_model` — OpenRouter model ID (e.g. `anthropic/claude-sonnet-4-5`)
- `[research] topics` — list of overnight research topics
- `[thresholds] health_red / health_yellow` — Oura score cutoffs

## Required env vars (injected by 1Password)

- `OURA_TOKEN` — Oura personal access token
- `OPENROUTER_API_KEY` — for all LLM synthesis (brief + overnight)
- `TELEGRAM_BOT_TOKEN` — outbound Telegram alerts
- `TELEGRAM_CHAT_ID` — your personal chat ID

## Gotchas

- **`ANTHROPIC_API_KEY` does NOT work for direct API calls** — it's the Claude Code Max plan key, not a pay-per-token API key. All LLM calls route through OpenRouter (`OPENROUTER_API_KEY`). This is by design.
- **OpenRouter model IDs** use `provider/model` format: `anthropic/claude-sonnet-4-5`, `google/gemini-flash-1.5`. Not the same as Anthropic's native model IDs (`claude-sonnet-4-6`).
- **`pacemaker add` auto-syncs to iPhone via CloudKit** — no `--sync` flag needed (flag doesn't exist). Syntax: `pacemaker add --date YYYY-MM-DD "<title>"`.
- **LaunchAgents exit 0 always** — nudge and overnight commands catch all errors internally and log to `~/logs/comes-*.log`. Never let LaunchAgent retry on business logic failures.
- **config.toml must exist** — binary panics with a clear error if missing. Run `scripts/setup-config.sh` on first install.
- **`cargo install --path .`** to update the installed binary after code changes. `cargo build --release` alone does NOT update `~/.cargo/bin/comes`.
- **`PHRON_SCRIPTS_DIR` must be set** for `comes-bot` when running as an installed binary (not from `target/release/`). Add to LaunchAgent plist or `~/.zshenv`: `PHRON_SCRIPTS_DIR=/Users/terry/code/phron/scripts`. Without it, librosa analysis silently skips (critique still works, just no audio metrics).
- **`OPENAI_API_KEY` needed for Whisper** — separate from OpenRouter. Whisper uses OpenAI's API directly. Check 1Password for key.
- **`pdftotext` needed for deck review** — install via `brew install poppler`. Deck review silently fails without it. Already installed on iMac (`/opt/homebrew/bin/pdftotext`).
- **Image-only PDFs not supported** — pdftotext extracts text layer only. Scanned decks → empty output → error returned to user.
- **Deck text truncated at 12K chars** — LLM context limit. For very long decks, only first ~12K chars are critiqued.

## LaunchAgents

Templates in `~/code/phron/launchd/`. Install:
```bash
cp ~/code/phron/launchd/com.phron.*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.phron.nudge.plist
launchctl load ~/Library/LaunchAgents/com.phron.overnight.plist
```
Logs: `~/logs/comes-nudge.log`, `~/logs/comes-overnight.log`

## Phase roadmap

- **Phase 1+2 (done):** `comes health`, `comes brief`, `comes nudge`, `comes overnight`
- **Phase 3 (next):** Telegram bot (`comes-bot`) — voice message → Whisper → librosa → Claude critique
- **Phase 4:** Status dashboard, amicus integration, pre-meeting auto-brief

## File paths

- Source: `~/code/phron/`
- Config: `~/.config/comes/config.toml`
- State: `~/.config/comes/state.json`
- Vault output: `~/epigenome/chromatin/<vault.overnight_dir>/YYYY-MM-DD-digest.md`
- Logs: `~/logs/comes-*.log`
- Plan: `~/officina/docs/plans/2026-03-06-feat-phron-ai-life-coach-plan.md`
- Brainstorm: `~/officina/docs/brainstorms/2026-03-06-life-coach-brainstorm.md`
