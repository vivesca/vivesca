# Life Coach — Brainstorm

**Date:** 2026-03-06
**Status:** Design phase

## What We're Building

A personal AI life coach for the professional Terry — a unified system that monitors health state, coaches speaking and presentation skills, does background career intelligence, and synthesises across all three domains to give proactive, personalised guidance.

This is not a Capco transition tool that retires in April. It's a long-term system that grows as goals shift from "survive week 1 at HSBC" to "build a book of business" to whatever comes after.

**In scope:** Health (as it affects professional performance), career prep and intelligence, communication coaching.
**Out of scope:** Meal planning, hobby tracking, finances, general productivity — anything not directly tied to professional performance.

## Why This Approach

Terry already has rich data sources (Oura, calendar, vault, email, amicus) and capable tools for each domain. What's missing is synthesis — nothing cross-references health state with workload intensity, or connects relationship decay with calendar gaps, or ties speaking practice to upcoming client meetings. The life coach is the integration layer that makes all of this coherent.

"Life coach" is also the right framing because it implies a relationship with feedback loops, not just data surfacing. A dashboard shows you numbers. A coach tells you what to do about them.

## Key Decisions

### 1. Shape: Open-source Rust CLI

- **Crate name:** `phron` (crates.io) — distinctive proper name, OSS-friendly
- **Binary name:** `comes` — what Terry types; set via `[[bin]]` in `Cargo.toml`
- Open-source from day one (MIT license). Generic engine; personal content stays in private config.
- All paths, tokens, and API keys configurable via `~/.config/comes/config.toml` — no hardcoded personal data in the repo
- Optional feature flags for modules: `--features oura`, `--features telegram`, `--features overnight`
- Runnable from any terminal and LaunchAgents, independent of Claude Code

### 2. Modes

| Command | What it does |
|---|---|
| `comes brief` | Morning brief: Oura readiness + calendar intensity + one prep prompt + overnight digest summary |
| `comes coach` | Speaking practice: asks a scenario question, records answer, returns structured critique |
| `comes overnight` | Background research runner: HSBC/Capco/regulatory/competitor digest → vault + Telegram |
| `comes health` | On-demand health check: Oura analysis + recommendation (Green/Yellow/Red) |
| `comes nudge` | Proactive alert check: runs via LaunchAgent, pushes to Due/Telegram when action needed |
| `comes status` | Dashboard: drill coverage, recent digests, health trend, relationship decay alerts |

### 3. LLM routing

- Interactive use (building, iterating, brief synthesis): Anthropic API direct (Sonnet 4.6)
- Overnight research: OpenRouter via noesis (~$0.006-0.40/run depending on depth)
- Simple classification/extraction: Haiku via API (~$0.05/night)
- Voice coaching analysis: Whisper API (transcription) + Claude (qualitative critique)
- **Not** Max20/Claude Code — isolated from interactive budget, consistent across heavy and light weeks

### 4. Speaking coach stack

- Record audio on Mac (built-in mic or external)
- Transcribe: Whisper API
- Audio features: ffmpeg + librosa (WPM, pause detection, pitch variation, resonance analysis)
- Critique dimensions: filler words, pace, structure (answer-first, MECE), executive presence, accent clarity, voice texture
- Practice loop: `comes coach --scenario "explain AML model to non-technical CFO"` → record → critique

### 5. Overnight research

- Runs at 5am via LaunchAgent
- Sources: HSBC news + filings, Capco publications, HKMA/MAS/FCA regulatory updates, McKinsey/BCG/Deloitte AI consulting moves
- Output: digest written to `~/code/epigenome/chromatin/Capco/Daily Intelligence/YYYY-MM-DD-digest.md`
- Summary pushed to Telegram

### 6. Health layer

- Reads Oura API: readiness, HRV, sleep score
- Maps to Green/Yellow/Red state
- `comes brief` shows state + one-line recommendation
- `comes nudge` (LaunchAgent, 8am): Red state → Due reminder to reschedule heavy tasks
- Pattern tracking: flags multi-day HRV decline before crash

### 7. State and config

- Config: `~/.config/comes/config.toml` (API keys, Oura token, Telegram chat ID)
- State: `~/.config/comes/state.json` (drill history, last overnight run, health trend, coaching sessions)
- Vault output: `~/code/epigenome/chromatin/Capco/Daily Intelligence/` for overnight digests

## Integrations

| System | How |
|---|---|
| Oura Ring | Oura API (personal access token) |
| Telegram | Bot API (already used by deltos/daemon pattern) |
| Due | moneo CLI |
| Obsidian vault | Direct file writes to `~/code/epigenome/chromatin/` |
| Calendar | fasti/gog calendar list |
| Research | noesis (OpenRouter) |
| Transcription | Whisper API |
| Audio analysis | ffmpeg + librosa (Python subprocess or Rust binding) |

## Phasing

Given 4 weeks to Capco start (Apr 8) and GARP exam Apr 4:

**Phase 1 — Pre-Capco (this month):**
- `comes brief` (morning brief with Oura + Capco prep hint)
- `comes overnight` (research daemon + LaunchAgent)
- `comes health` (on-demand Oura check)
- `comes nudge` (Red state alert)

**Phase 2 — First 90 days at Capco:**
- `comes coach` (speaking practice loop)
- `comes status` (dashboard with trend data)
- Relationship decay detection (amicus integration)

**Phase 3 — Ongoing:**
- Learning velocity tracking (vault note analysis)
- Pre-meeting context assembly (auto-brief before calendar events)
- Pattern detection across time (behavioural insights)

## Architecture Revision: Telegram-First Interface

The speaking coach input method resolved a key architecture question. Since Terry primarily accesses the Mac via Blink (iOS SSH), terminal audio recording doesn't work — the mic is on the iPhone. **Telegram becomes the primary interactive interface**, not just the notification channel.

**Two-surface architecture:**
- **CLI (`comes`)** — background and scheduled jobs: overnight research (LaunchAgent), health nudges (LaunchAgent), morning brief (invoked from terminal or Blink)
- **Telegram bot** — interactive coaching: voice message → transcription → critique, on-demand health check, quick status queries

This means `comes coach` lives entirely in Telegram:
1. Terry records a voice note in Telegram (on iPhone, anywhere)
2. Bot receives audio, calls Whisper API for transcription
3. ffmpeg extracts audio features (WPM, pause distribution, pitch variation)
4. Claude synthesises a structured critique across all five dimensions
5. Bot replies with the critique in Telegram

The Telegram bot also becomes the natural interface for anything interactive on mobile — reducing reliance on Blink for anything that isn't purely read/write.

## Resolved Questions

- [x] **Name:** Run consilium to generate alternatives before committing
- [x] **Audio input:** Telegram voice messages — works from iPhone anywhere, no file transfer, zero friction
- [x] **Whisper:** API (not local) — latency acceptable for async coaching, no local GPU needed
- [x] **Audio features:** ffmpeg + Python subprocess for librosa — acceptable for a coaching use case that isn't latency-sensitive

## Open Questions

- [x] Name: **crate `phron`** (crates.io, OSS discovery — reads as a proper name, not an English verb) + **binary `comes`** (what Terry types daily — companion framing). Set independently in `Cargo.toml [[bin]]`. Both FREE on crates.io.
- [ ] Oura API auth: check `oura` skill for existing personal access token setup
- [ ] Telegram bot: create new bot for `comes` or extend existing infrastructure?
- [ ] librosa subprocess: acceptable latency for Telegram bot response? (estimate: 10-20s for a 2-min recording)

## Related

- `capco-prep` skill (retiring Apr 8) — drill questions migrate to `comes coach`
- `oura` skill — Oura API pattern to reuse
- `auspex` skill — morning brief pattern, `comes brief` extends/replaces for this use case
- `~/code/epigenome/chromatin/Capco/` — vault home for overnight digests and drill state
