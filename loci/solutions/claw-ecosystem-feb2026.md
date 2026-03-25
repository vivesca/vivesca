# Claw Ecosystem — Feb 2026

Karpathy coined/popularised "claw" (emoji: 🦞) as the term for personal AI agents with orchestration, scheduling, context, tool calls, and persistence. Running on dedicated hardware (Mac mini is the default).

## Landscape

| Project | LOC | Lang | Key Trait |
|---------|-----|------|-----------|
| **OpenClaw/Clawdbot** | ~400K | Mixed | Kitchen sink, huge attack surface |
| **NanoClaw** | ~3.9K | TypeScript | Container isolation, Anthropic Agents SDK |
| **Nanobot** | ~4K | Python | HKUDS, ultra-lightweight |
| **PicoClaw** | Tiny | Go | Self-bootstrapped rewrite of Nanobot |
| **ZeroClaw** | ? | ? | Referenced by Roemmele |

## NanoClaw Details

- **Repo:** <https://github.com/qwibitai/nanoclaw>
- **Stack:** Single Node.js process, 15 files, SQLite, Apple Container (macOS) / Docker (Linux)
- **Interface:** WhatsApp first-class, Telegram via skills
- **Memory:** Per-group CLAUDE.md + isolated filesystem per container
- **Skills:** AI-native — `/add-gmail` style commands where Claude Code modifies the codebase to integrate services. Karpathy: "the new meta — write the most forkable repo possible, then have skills to fork it into any desired configuration"
- **Agent Swarms:** Teams of specialised agents collaborating within a chat
- **Setup:** Clone → `claude` → `/setup` (Claude Code handles everything)

## Security Model Comparison

- **OpenClaw:** 400K lines of vibe code, public skill registry, reports of RCE, supply chain poisoning. Karpathy "sus'd."
- **NanoClaw:** Container isolation per group. Agent can only see mounted directories. IPC via JSON files validated by host process.
- **Our setup (Claude Code):** Hook-based hard gates (bash-guard, safe_rm). Catches bad commands pre-execution but no post-execution blast radius isolation. Container isolation is complementary — worth stealing for untrusted code execution.

## Relevance to Our Setup

NanoClaw solves "messaging-platform-first AI agent for people without a terminal workflow." We already have the equivalent and more:

- Skills (~46 vs handful)
- Memory (3-tier: MEMORY.md + Oghma + QMD vs per-group CLAUDE.md)
- Multi-model routing vs Claude-only
- Hook enforcement vs container isolation (complementary, not competing)

**One adoptable idea:** Container isolation for high-risk delegated tasks — but existing tools already cover this (see below). Not needed yet; our hook-based gates handle the current threat model.

**Not worth adopting:** The messaging-as-UI pattern, the single-model constraint, the simpler memory system.

## Sandboxing Tools (When Needed)

If we ever need to isolate delegated agent tasks (untrusted code, public skill registries, etc.):

| Tool | Isolation Level | Setup | Notes |
|------|----------------|-------|-------|
| **Claude Code `/sandbox`** | OS-level (seatbelt) | Zero — built in | For Claude Code itself |
| **`srt`** ([anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime)) | OS-level (seatbelt) | `npm install -g @anthropic-ai/sandbox-runtime` | Prefix any CLI: `srt opencode`. Writes restricted to CWD. |
| **macbox** ([srdjan/macbox](https://github.com/srdjan/macbox)) | OS-level + worktree | Deno + clone | sandbox-exec + git worktrees per session |
| **Docker Sandboxes** ([docs](https://docs.docker.com/ai/sandboxes)) | MicroVM | Docker Desktop 4.58+ (not OrbStack) | `docker sandbox run claude [PATH]`. Strongest local isolation. |
| **microsandbox** ([zerocore-ai/microsandbox](https://github.com/zerocore-ai/microsandbox)) | HW VM (Apple HVF) | `curl` one-liner | Beta. 4.8K stars. True VM on Apple Silicon. |

**Quickest path:** `srt` — one npm install, then `srt <agent-command>`. Same engine as Claude Code's built-in sandbox.

**Caveat:** Both `srt` and macbox depend on macOS `sandbox-exec`, which Apple has deprecated (still ships on macOS 26, no removal timeline). Docker Sandboxes or microsandbox are the long-term alternatives.

**Current assessment (Feb 2026):** Not needed. Our threat model is own code + own repos + hook gates. Karpathy's concern (public skill registries, 400K LOC strangers' code) doesn't apply. Revisit if we start running untrusted external skills or public agent code.

## Sources

- [Simon Willison write-up](https://simonwillison.net/2026/Feb/21/claws/)
- [Karpathy X post](https://x.com/karpathy/status/2024987174077432126)
- [NanoClaw GitHub](https://github.com/qwibitai/nanoclaw)
- [NanoClaw official site](https://nanoclaw.dev/)
- [The New Stack](https://thenewstack.io/nanoclaw-minimalist-ai-agents/)
- [VentureBeat](https://venturebeat.com/orchestration/nanoclaw-solves-one-of-openclaws-biggest-security-issues-and-its-already)
