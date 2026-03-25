# Rust Rewrite Decisions (Feb 2026)

## Default: Rust for new projects (decided Feb 27)

With AI coding agents (Opus 4.6), the traditional Rust downsides collapse:

| Old objection | Status with AI agent |
|---|---|
| Slower to write | AI writes both at same speed. **Gone.** |
| Boilerplate (lifetimes, traits, error types) | AI handles it. **Gone.** |
| Steep learning curve | You review, not write from scratch. **Gone.** |
| Slower prototyping | AI iterates just as fast. **Gone.** |

**Remaining Python-only cases:**
- **Data/ML work** — pandas, sklearn, torch have no Rust equivalent. Ecosystem, not language.
- **Existing working scripts** — don't rewrite, that's a rabbit hole.

**Decision:** Default new projects to Rust. Python only for data/ML and throwaway scripts. The AI shifted the cost-benefit — distribution, performance, reliability, and type safety come ~free now.

## Legacy Heuristic (pre-AI-agent, superseded)

Only rewrite in Rust if the tool is **CPU-bound or startup-sensitive**. Most of Terry's toolkit is I/O/network-bound — Rust won't make APIs or Chrome faster. *Note: this was the right call when humans wrote the code. With AI agents, the write-time cost argument no longer holds — the remaining benefits (single binary, no runtime deps, no bit-rot) tip the balance.*

| Tool | Bottleneck | Rust help? |
|---|---|---|
| pplx | Already Rust | Done |
| qianli | CDP websocket + SPA rendering | No |
| oghma/qmd | Embedding + SQLite query | Marginal |
| agent-browser | Playwright + Chrome launch | No |
| gphotos | Google SPA rendering | No |
| consilium | LLM API response time | No |
| gog | Already Go | No |
| taobao | nodriver + anti-bot waits | No |

For I/O-bound tools, **daemon mode** (keep process hot) helps more than a language rewrite.

## Claude Code / OpenCode Rust Rewrite — No

The value of a coding agent is system prompt engineering, tool-use calibration, and context management — not the binary. A Rust wrapper around the Anthropic API is a chatbot with `exec`, not a coding agent.

## ZeroClaw — Watch

OpenClaw rebuilt in Rust by theonlyhennygod (github.com/theonlyhennygod/zeroclaw). Released Feb 14, 2026.

- 3.4MB binary (vs 28MB OpenClaw), 0.38s cold start (vs 3.31s)
- 22+ providers, trait-based architecture (swap via config)
- Multi-channel: CLI, Telegram, Discord, Slack, iMessage
- Day-1 hype (250 stars). Revisit March 2026.
