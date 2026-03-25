---
name: Claude Code Power User Patterns
description: Comprehensive survey of hooks, CLAUDE.md patterns, skills, MCP combos, multi-agent workflows, CI/CD integrations, session management, and cost optimization used by power users (Mar 2025–Mar 2026)
type: reference
---

## What's Covered
Research conducted Mar 18 2026. Covers the full power-user ecosystem that emerged around Claude Code from launch through early 2026.

## Key Sources
- https://github.com/hesreallyhim/awesome-claude-code — primary curated list
- https://github.com/rohitg00/awesome-claude-code-toolkit — 135 agents, 42 commands, 19 hooks
- https://github.com/disler/claude-code-hooks-mastery — 13 hooks with UV single-file scripts
- https://github.com/SuperClaude-Org/SuperClaude_Framework — 30 commands, 16 personas, 7 modes
- https://github.com/parcadei/Continuous-Claude-v3 — ledger/handoff context continuity
- https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees
- https://github.com/Piebald-AI/claude-code-system-prompts — extracted 110+ internal prompts
- https://github.com/bmad-code-org/BMAD-METHOD — agile multi-agent dev methodology

## Hook Patterns
- PreToolUse is the ONLY hook that can block — all enforcement hooks use this
- Stop hook with exit 2 forces Claude to continue (use `stop_hook_active` check to prevent infinite loops)
- PreCompact hook runs before compaction — use for transcript backup
- UV single-file scripts with embedded deps = best hook implementation pattern (eliminates venv mgmt)
- Key pattern: PreToolUse on Bash + regex allowlist/blocklist for destructive command guard
- UserPromptSubmit stdout injection = buggy as of early 2026 (stdout causes errors, use file workaround)
- Hook input modification (v2.0.10+): PreToolUse can modify tool inputs rather than just block

## CLAUDE.md Patterns
- Target <200 lines per file; use ancestor+descendant hierarchy for monorepos
- Context thresholds: 70% = attention, 85% = hallucinations increase, 90%+ = /clear mandatory
- Cascade structure: global ~/.claude/CLAUDE.md → project root CLAUDE.md → subdirectory CLAUDE.md
- `/compact` with custom prompt preserves relevant context while discarding noise
- InstructionsLoaded hook fires when CLAUDE.md loads — can trigger environment setup
- "agnix" linter validates CLAUDE.md/SKILL.md/hooks with 156 rules

## Skills/Slash Commands
- SuperClaude: 30 commands, 16 cognitive personas (auto-activate by context), 7 modes (brainstorm/research/token-efficient/etc), quality scoring 0.0-1.0
- BMAD Method: 9 agent roles (PM, Architect, Dev, UX, Scrum Master...), 15 workflow commands, story files carry full context between phases
- /batch command: decomposes work into 5-30 independent units, spawns one background agent per unit in isolated worktree, each opens a PR
- Todo-worktree slash command: manages worktree lifecycle from task list
- /ticket: fetches JIRA/Linear ticket, implements, updates status, creates PR — full round-trip
- Scheduled agents via GitHub Actions: monthly docs sync, weekly quality review, biweekly dependency audit

## MCP Combinations
- Playwright MCP (Microsoft official): accessibility-tree-based, more token-efficient than screenshot approaches
- Memory MCP: knowledge graph of preferences, project context, decisions (persists cross-session)
- GitHub MCP: PR creation, issue management, diff review — closes automation loops
- Tool Search MCP: lazy-loads tools on-demand when >10% context would be consumed by tool defs
- SuperClaude uses 8 coordinated MCPs: Tavily, Context7, Playwright + 5 others

## Parallel/Multi-Agent Patterns
- Git worktree pattern: each agent in its own worktree = isolated branch + filesystem, no conflicts
- Josh Lehman's /project:start-task: ensures main up-to-date, creates worktree, loads task context, begins impl
- Agent Interviews parallel pattern: /project:init-parallel N + /project:exe-parallel spec.md N — spawns N subagents in N worktrees implementing same spec (deliberate LLM variance as feature)
- incident.io `w` function: one bash function manages worktree create/switch/run, 7 concurrent sessions
- Agent Teams (experimental Feb 2026): teammates communicate directly with each other, not just through lead
- Addy Osmani's competing hypotheses debugging: 5 teammates each investigate different bug theory, then debate
- ccswarm: multi-agent system with git worktree isolation and specialized agents
- ccpm: GitHub Issues + worktrees for parallel agent project management
- BMAD sprint automation: two-wave architecture across 14 specialized agents

## CI/CD Integration
- claude-code-action (Sep 29 2025, Claude Code 2.0): GitHub Actions integration triggered on PR events
- /install-github-app: sets up GitHub app + secrets in one command
- Patterns: auto PR review, path-specific review, external contributor review, scheduled maintenance
- GitHub Actions + hooks as quality gates: hooks run in CI to block merges
- Scheduled GitHub Actions workflows replace LaunchAgent-style cron patterns

## Session Management
- claude --continue / claude --resume: picks up last or selected sessions
- Session Memory (Feb 2026, v2.1.30+): writes summaries continuously in background; compaction loads pre-written summary
- Continuous-Claude v3 "Compound, don't compact": YAML handoff files before sessions end, continuity ledgers (markdown tracking decisions), 5-layer AST code analysis achieves 95% token savings vs raw file reads
- claude-mem plugin: PostToolUse hook captures session, Haiku compresses, SQLite full-text search for future retrieval
- recall MCP: Redis-backed persistent memory, retrieves relevant context automatically on next session
- /compact with targeted custom prompt: "Focus on code samples and API usage"

## Cost Optimization
- OpusPlan: Opus for plan phase, Sonnet for execution — 5x cost reduction on implementation
- Haiku for subagents doing exploration/file search/simple lookups — 10-20x cheaper than Opus
- Defer loading (ToolSearch/lazy MCP): tool definitions not in context until needed — 85% token reduction possible
- Compaction at 60% utilization (not 90%) — models degrade well before context fills
- CLI tools (gh, aws, gcloud) more token-efficient than MCP servers — no persistent tool definitions
- Disable thinking: /effort or MAX_THINKING_TOKENS=8000 for non-reasoning tasks
- Prompt caching enabled by default — keep stable prefixes for KV-cache hits
- Average cost: ~$6/dev/day; 40-70% reduction achievable with full optimization stack

## Non-Obvious / Novel Patterns
- Piebald-AI extracted 110+ internal prompts: Claude Code uses conditional prompt assembly (dozens of fragments), not a monolithic prompt
- Daniel Miessler pre-built UFC (universal file context) and dynamic skill loading before Anthropic shipped native versions
- Britfix hook: auto-converts American → British English in comments/docstrings only, not code identifiers
- cc-notify: desktop notifications with duration tracking when Claude needs input
- HCOM: lightweight CLI for real-time comms between Claude Code subagents
- Stop hook TTS: audio completion messages with provider fallback chain (OpenAI → Anthropic → Ollama)
- PermissionRequest hook: auto-allows read-only ops (Read, Glob, Grep, safe Bash) without prompting
- Cross-tool orchestration agents: route tasks between Claude Code, Gemini CLI, OpenCode, Codex based on complexity

## Reliable Sources for This Domain
- code.claude.com/docs — official, authoritative
- github.com/hesreallyhim/awesome-claude-code — best community curation
- claudefa.st/blog — strong technical depth
- addyosmani.com/blog — practitioner patterns from senior engineer
- incident.io/blog — real production case study
- github.com/disler/* — concrete hook implementations
- github.com/Piebald-AI/claude-code-system-prompts — internals research
