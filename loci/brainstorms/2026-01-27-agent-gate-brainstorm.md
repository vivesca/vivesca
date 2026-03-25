---
date: 2026-01-27
topic: agent-gate-local-guard
---

# Agent-Gate: Local Shell Guard for AI Agents

## What We're Building
`agent-gate` is a lightweight, open-source utility designed to protect developers from "runaway" AI agents. It intercepts expensive or broad search commands (like `grep`, `rg`, `find`) at the shell level and prevents them from scanning massive directories like the user's root (`/Users/terry`), `~/Library`, or `~/Downloads`.

## Why This Approach
We chose the **Shadowed Binaries** approach because it is "Agent-Native":
1. **Invisible Enforcement**: The agent doesn't need to be told to be safe; the tools it already uses (via the shell) become safe automatically.
2. **Zero-Config Prompting**: Developers don't need to waste precious context tokens instructing the agent on what NOT to search.
3. **High Performance**: By blocking broad searches before they even start, it eliminates the "agent hang" that occurs when a model waits for a 5-minute recursive scan to complete.

## Key Decisions
- **PATH Prioritization**: The utility will install itself in a prioritized `bin` directory (e.g., `~/.agent-gate/bin`) to intercept calls to system binaries.
- **Python-Based Gatekeeper**: The core logic will be a single, portable Python script for easy installation and modification.
- **Fail-Fast Policy**: Any prohibited search will be terminated immediately with a clear, agent-readable error message explaining *why* it was blocked and *how* to fix the path.
- **Massive Directory Denylist**: Hard-coded blocks for known bottlenecks (Library, Trash, Downloads, Pictures).

## Open Questions
- **Dynamic Thresholds**: Should we allow the guard to "peek" at a directory's size before blocking (e.g., if a folder has >10,000 files, block it)?
- **Custom Denylist**: How should users define project-specific "No-Go Zones" (e.g., a massive data folder)?
- **Bypass Mechanism**: Should there be a way to force a search if the user explicitly wants it?

## Next Steps
→ `/workflows:plan` to scaffold the repository and implement the core installer.
