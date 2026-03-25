---
name: OpenClaw / Claw Ecosystem Landscape
description: Overview of the OpenClaw AI agent ecosystem — origin, forks, alternatives, security incidents, and non-claw competitors as of March 2026
type: reference
---

## Landscape summary (March 2026)

**OpenClaw** is the fastest-growing open-source repo in GitHub history (~280K stars, 35K+ forks). Built by Austrian developer Peter Steinberger (ex-PSPDFKit founder). Originally "Clawdbot" (Nov 2025) → "Moltbot" (Jan 27 2026, after Anthropic trademark complaint) → "OpenClaw" (Jan 30 2026). Creator joined OpenAI Feb 2026.

Core concept: messaging-native AI agent (WhatsApp, Telegram, Slack, Discord, 20+ platforms). Config via SOUL.md files. Skill marketplace: ClawHub (~13,700 skills). Language: TypeScript.

## Security incidents that spawned alternatives

- **ClawHavoc** (Feb 2026): ~341/2,857 skills (12%) in ClawHub confirmed malicious — keyloggers, AMOS Atomic Stealer. No sandboxing on skills.
- **ClawJacked** (Oasis Security): Malicious websites could brute-force the local WebSocket gateway (rate limiter exempted localhost). Once in, attacker had full agent control: config dump, device enumeration, log access. Fixed in v2026.2.25 (patched within 24h of disclosure).
- **7 additional CVEs** (CVE-2026-25593, -24763, -25157, -25475, -26319, -26322, -26329): RCE, command injection, SSRF, auth bypass, path traversal.
- **Root cause**: Admin-level system access by default, plaintext credential storage, no skill sandboxing.

## Key ecosystem projects (March 2026)

| Project | Stars | Language | Built by | Key differentiator |
|---------|-------|----------|----------|-------------------|
| OpenClaw | ~280K | TypeScript | Peter Steinberger | Largest ecosystem, 13,700+ skills, 20+ platforms |
| NanoClaw | ~22K | TypeScript | Gavriel Cohen / NanoCo | 700-line auditable codebase; mandatory Linux container isolation; Docker partnership (Mar 2026) |
| Nanobot | ~27K | Python | HKUDS (HK Uni CS dept) | 4,000 lines vs 430,000 in OpenClaw; Python-native; 2-min deploy; research/academic focus |
| ZeroClaw | ~26K | Rust | Harvard/MIT + Sundai.Club | 3.4MB binary, <10ms boot, runs on $10 hardware; Rust trait-driven; <10MB RAM |
| PicoClaw | ~13K | Go | Sipeed (embedded HW company) | Built in one day; targets embedded hardware; single Go binary |
| Moltis | ~2K | Rust | Fabien Penso | 150K lines, zero `unsafe` blocks; Prometheus + OpenTelemetry + voice I/O (8 TTS, 7 STT); enterprise observability |
| IronClaw | N/A | Rust | Near AI | Zero-trust via WASM sandboxing; cryptographic skill verification |
| NullClaw | N/A | Zig | Community | 678KB binary, ~1MB RAM, <2ms boot; absolute minimalism |
| MicroClaw | N/A | Rust | Community | 14+ platform adapters incl. Asian platforms (Feishu, DingTalk); Matrix, Nostr, Signal, IRC |
| NemoClaw | alpha (released Mar 17 2026) | Unknown | NVIDIA | Enterprise stack on top of OpenClaw; data privacy controls, local data handling, CrowdStrike partnership for security ops; Jensen Huang GTC Mar 17 keynote confirmed |

## NanoClaw story (notable)
Creator Gavriel Cohen built it in a weekend after OpenClaw's security crisis. Launched Hacker News → viral. Andrej Karpathy tweet ~3 weeks later → second wave. Docker partnership announced Mar 13 2026 (Docker Sandboxes replacing Apple container tech). Cohen shut down his AI marketing startup to found NanoCo.

## Non-claw competitors
No direct named competitors surfaced in research — the "claw" naming has dominated the messaging-native agent category. Broader adjacent competition: traditional agent frameworks (LangGraph, CrewAI, AutoGen) but they solve a different problem (code/pipeline orchestration vs messaging-native personal agents).

## Lethal trifecta and security architecture

The "lethal trifecta": agent simultaneously holds (1) access to sensitive data, (2) exposure to untrusted content, (3) ability to perform external actions. When all three coexist, prompt injection + data exfiltration become probable, not edge cases. Email is the canonical example — untrusted senders, confidential content, and outbound channel all in one.

**How each alternative addresses it:**
- **NanoClaw**: OS-level container isolation (Docker, mandatory not optional). Every session = ephemeral container. Explicit allowlist for filesystem + network access, enforced at container level (cannot be bypassed by prompting). Audit logging baked in. Best for: regulated industries, auditability-first.
- **IronClaw**: WASM sandbox with capability-based security (seL4-inspired). Skills get zero permissions by default; require explicit capability tokens (FileRead, NetConnect, EnvRead). Static analysis tool "iron-verify" catches over-privileged skills pre-deployment (23/25 problematic skills caught in testing, ~15ms overhead). Best for: zero-trust / blockchain-adjacent / high-assurance.
- **Moltis**: 150K lines, zero `unsafe` Rust (memory safety at compile time). 15 lifecycle hooks, circuit breakers, destructive command guards, Prometheus/OTel for runtime anomaly detection. Best for: enterprise observability, production monitoring.
- **ZeroClaw**: Minimalism as security — smaller attack surface, Rust memory safety, trait-driven architecture. No explicit security controls. Marketing exceeds substance here.
- **NemoClaw**: "command-and-control for agent behavior and data handling" — vague. Early alpha; no published sandboxing spec, no compliance certifications. Futurum Research: addresses runtime deployment end but not full governance lifecycle. Rough edges acknowledged by NVIDIA.

**Honest verdict**: No alternative eliminates the trifecta — Thoughtworks confirmed "there is no magic sandbox." The tension between security and utility is structural. Best-in-class mitigation stack: NanoClaw container isolation + network egress allowlists + short-lived scoped tokens + anomaly detection (Moltis/Prometheus). Detection-and-response will eventually need to supplement containment.

## "NonaClaw" — does not exist
No project named "NonaClaw" or "Nona Claw" appears in any source as of March 2026. Not a real alternative.

## Source quality notes
- aimagicx.com comparison table: most comprehensive structured comparison, WebFetch works
- ibl.ai blog on IronClaw/NanoClaw security architecture: WebFetch works, good technical depth
- thoughtworks.com/en-de OpenClaw blog: WebFetch works, honest "no magic sandbox" analysis
- techcrunch.com NemoClaw article: WebFetch partially gated (metadata only)
- dataconomy.com NemoClaw article: thin on technical detail
- nemoclaw.so/blog/gtc-2026-preview: WebFetch works, pre-GTC preview (honest about unknowns)
- thenewstack.io NemoClaw article: 403 on WebFetch
- adversa.ai OpenClaw CVE guide: JS-gated, returns CSS only
- techcrunch.com NanoClaw article: authoritative on creator story, WebFetch partially gated
- thehackernews.com ClawJacked: authoritative security write-up
- Wikipedia OpenClaw page exists and appears factual
