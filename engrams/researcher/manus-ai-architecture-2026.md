---
name: Manus AI Architecture & Landscape (Mar 2026)
description: Technical deep-dive on Manus AI agent — architecture, system prompt, context engineering, open-source clones, criticisms, Meta acquisition
type: reference
---

## Core Architecture

- **Wrapper model:** Claude 3.5/3.7 Sonnet (primary) + Alibaba Qwen (fine-tuned, secondary). Multi-model dynamic invocation.
- **Sandbox:** Per-task isolated Ubuntu 22.04 VM (cloud). Python 3.10, Node.js 20.18, internet access, root/sudo privileges.
- **Action mechanism:** CodeAct — executable Python as primary action format, not rigid tool API calls.
- **Agent loop:** Analyze events → select ONE tool → execute → observe → iterate → submit/standby. One tool per iteration is explicit.

## Leaked System Prompt (March 2025)

Leaked by user "jian" who asked Manus to output `/opt/.manus/` directory. 29–40+ tools confirmed including:
- `deploy_expose_port` (no human-in-the-loop — this is the security vuln)
- Browser automation (navigate, click, scroll, console access)
- Shell (with sudo), file read/write/replace/search
- Web search, deployment (static + Next.js)
- `message_notify` / `message_ask` for user communication

Key system prompt structure: `<tool_use_rules>`, `<browser_rules>`, `<error_handling>`, `<writing_rules>`, `<info_rules>`.

## Context Engineering (Official Blog, July 2025)

Manus's most technically substantive public disclosure. Key principles:
1. **KV-cache hit rate = #1 production metric.** 10x cost difference (Claude: $0.30 vs $3/MTok cached vs uncached). Stable prompt prefixes, append-only contexts, deterministic JSON serialization, explicit cache breakpoints.
2. **State machine over dynamic tool removal.** Rather than removing tools (breaks KV-cache), they mask token logits at decode time to constrain available actions.
3. **File system as external memory.** Files = unlimited, persistent, structured memory. Drop content from context, keep file paths. Enables restorable compression.
4. **todo.md attention hack.** Creates/updates todo.md continuously to push current goals into recent attention window. Combats "lost-in-the-middle" over 50+ tool-call tasks.
5. **Leave failures in context.** Failed actions + stack traces stay visible — enables implicit belief updates, prevents repeated mistakes.
6. **Controlled variation.** Introduces small serialization/phrasing noise to break repetitive patterns that cause model drift.

## Three-Tier Memory

1. Event stream (chronological, truncated for context limits)
2. File-based persistence (todo.md, findings.md, task_plan.md, progress.md)
3. Knowledge module (RAG — external knowledge injected as "Knowledge events")

## Wide Research (July 31, 2025)

Parallel 100+ agent swarm for large-scale research. Each subagent = full Manus instance with its own fresh context window and dedicated VM. Orchestrator decomposes task → assigns independent subtasks → collects structured outputs (spreadsheet, web page, report). Key differentiator vs OpenAI Deep Research / Google Deep Think: breadth-first vs sequential depth.

## Manus 1.5 (Late 2025)

- Speed: 15 min → under 4 min average task completion (~4x)
- Quality: +15% internal benchmark, +6% user satisfaction
- "Unlimited context" — file-based externalization, not true unlimited
- Re-architected engine, additional reasoning/compute allocation for complex tasks
- Full-stack web dev: backend + auth + DB + analytics + version control
- Two models: Manus-1.5 (full) and Manus-1.5-Lite (cost-optimized)

## Security Vulnerabilities

- **System prompt leak (Mar 2025):** Trivial — asked to list `/opt/.manus/` contents. Manus officially responded.
- **VS Code server kill chain (Jun 2025, Embrace The Red):** Indirect prompt injection → `deploy_expose_port` auto-invoked → VS Code password exfiltrated via markdown image render to attacker domain. "Lethal trifecta": no input validation + permissive tool permissions + data exfiltration channels.
- Status: Manus team aware, mitigations unclear as of disclosure.

## Meta Acquisition

- Deal announced Dec 29 2025, finalized early Jan 2026. ~$2B+ (4x April 2025 valuation of $500M).
- $100M ARR within 8 months, 22M monthly visits pre-acquisition.
- Some users left post-acquisition over Meta data/privacy concerns.
- Roadmap: "Powered by Manus" features in WhatsApp Business + Instagram Direct by mid-2026.
- China government reviewing deal (Bloomberg, Jan 2026).

## Open-Source Clones

| Project | Stars | Key Details |
|---------|-------|-------------|
| OpenManus (FoundationAgents/MetaGPT team) | 52K+ | Built in 3 hours, Python 3.12+, ReAct pattern, BaseAgent→ReActAgent→ToolCallAgent hierarchy, OpenManus-RL for RL fine-tuning |
| Suna (Kortix AI) | active | FastAPI + Next.js, Apache 2.0, LiteLLM backend (Anthropic/OpenAI/etc), browser automation, full sandbox |
| agenticSeek (Fosowl) | active | Fully local, no API keys, Ollama-based |
| henryalps/OpenManus | separate fork | Similar approach |

Benchmark: OpenManus 74.3% vs Manus 86.5% on some task suite (contested, methodology unclear).

## Key Criticisms

- "Claude wrapper with BrowserUse" — legitimate; core innovation is integration, prompting, and context engineering, not model
- Context limit failures on long tasks (pre-1.5)
- CAPTCHA/paywall blindness limits research depth
- Freezing/reliability issues (beta period)
- Pre-1.5: ~30% token waste from constantly rewriting todo.md
- Invite-only access and opaque credit pricing

## Source Quality Notes

- Official blog (manus.im/blog) = most technically reliable. Context Engineering post authored by "Yichao 'Peak' Ji" is the best primary source.
- GitHub gists (jlia0, renschni) = leaked prompt analysis, reliable for tool list.
- Embrace The Red = reliable for security analysis.
- MIT Tech Review (Mar 2025) = balanced early review.
- Medium/Dev.to comparisons = mixed quality; OpenManus star-count inflation common.
