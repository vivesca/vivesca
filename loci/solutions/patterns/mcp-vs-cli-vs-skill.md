# MCP vs CLI vs Skill: Architecture Decision Framework

Build in this order:

1. **CLI first** — universal, fast, human-testable, works in every AI tool with shell access
2. **MCP server if stateful** — worth it when the tool maintains state across calls (DB connections, browser sessions, auth). Also gives auto-discovery in MCP-native tools
3. **Skill to document both paths** — so any agent knows which interface to use

## When MCP beats CLI
- Consumer speaks MCP natively (Claude Code, Codex)
- Tool is stateful (persistent DB conn, warm embedder, browser page)
- Structured I/O matters (typed schemas, param validation)

## When CLI beats MCP
- Cross-tool portability
- Stateless queries (search, stats, status checks)
- Human debugging (`oghma search "x"` vs `mcporter call oghma.oghma_search query="x"`)
- Speed for cold calls (no server startup)

## Token cost: Skill > MCP for Claude Code

MCP tool schemas cost ~350-500 tokens/turn in the system prompt, regardless of use. A skill (SKILL.md) teaches Claude to use the CLI via Bash instead — zero overhead, only loaded on invocation. Ship a skill alongside any MCP server for token-constrained users. Example: Oghma's `oghma install claude-code`.

## Anti-pattern
Wrapping a working CLI in an MCP server just to have MCP. If `gog gmail list` already works, an MCP wrapper adds latency and maintenance for zero benefit. The skill pointing at the CLI is enough.

## See also
- Enterprise architecture (consulting reference): `~/docs/solutions/mcp-vs-cli-enterprise.md`
- Skill + CLI split pattern: `~/docs/solutions/skill-cli-boundary-pattern.md`
- Claude Code extension mechanisms: `~/docs/solutions/claude-code-extension-mechanisms.md`
