---
name: synaxis
description: "Sync AI tool config across Claude Code, OpenCode, Codex, and Gemini CLI — skills, MCP, CE, from ~/officina/ as source of truth. Run after any config change."
user_invocable: true
triggers: [sync, synaxis, skill-sync, mcp-sync, config-sync]
---

# Synaxis

Single Rust binary that keeps all AI coding tools in sync from `~/officina/` as the source of truth.

## What it syncs

| Step | What | Source | Targets |
|------|------|--------|---------|
| Skills | Symlinks | `~/skills/` | `~/.claude/skills/`, `~/.opencode/skills/`, `~/.codex/skills/`, `~/.agents/skills/` |
| MCP | Config files | `~/officina/mcp-servers.json` | `~/.opencode/mcp.json`, `~/.codex/config.toml` (managed block) |
| CE | Plugin install | every-marketplace | codex, opencode, gemini |

Gemini CLI has no skills directory — CE only.

## Usage

```bash
synaxis              # Skills only (fast, ~50ms — runs on every git commit to ~/skills/)
synaxis --full       # Skills + MCP + CE across all platforms
synaxis --check      # Dry run — list skills, no changes
synaxis --help
```

## When to run

- **After any skill change:** automatic via `~/skills/.git/hooks/post-commit`
- **After MCP config change:** `synaxis --full`
- **After CE/compound-engineering update:** `synaxis --full`
- **New machine setup:** `synaxis --full`

## Source of truth

| Config | File |
|--------|------|
| Skills | `~/skills/` (git repo) |
| MCP servers | `~/officina/mcp-servers.json` |
| CE plugin | `~/.claude/plugins/marketplaces/every-marketplace/` |

### mcp-servers.json format

```json
{
  "mcpServers": {},
  "_codexExtras": {
    "context7": { "url": "https://mcp.context7.com/mcp" }
  }
}
```

- `mcpServers` → OpenCode (`~/.opencode/mcp.json`)
- `_codexExtras` → Codex TOML (`~/.codex/config.toml`, managed between `# synaxis-mcp-begin` / `# synaxis-mcp-end`)

## Binary

- Source: `~/code/synaxis/` (github.com/terry-li-hm/synaxis)
- Symlink: `~/bin/synaxis` → `~/code/synaxis/target/release/synaxis`
- Rebuild: `cd ~/code/synaxis && cargo build --release`

## Locations

| Platform | Skills | MCP | Instructions |
|----------|--------|-----|-------------|
| Source | `~/skills/` | `~/officina/mcp-servers.json` | `~/CLAUDE.md` |
| Claude Code | `~/.claude/skills/` | (manual via `claude mcp add`) | auto-loaded |
| OpenCode | `~/.opencode/skills/` | `~/.opencode/mcp.json` | — |
| Codex | `~/.codex/skills/`, `~/.agents/skills/` | `~/.codex/config.toml` | `~/.codex/AGENTS.md → ~/CLAUDE.md` |
| Gemini CLI | — | — | `~/.gemini/GEMINI.md` |

## Frontmatter validation

`synaxis` warns (`⚠`) on any `SKILL.md` missing a `---` YAML frontmatter block. Non-blocking — skill still syncs. Hard gate is the pre-commit hook in `~/skills/.git/hooks/pre-commit`.

## Gotchas

- **Dir-level symlinks break Codex skill discovery** — must be real dir with per-skill symlinks inside (bug [#11314](https://github.com/openai/codex/issues/11314))
- **Skills and hooks load at session startup only** — new/changed skills need a new session
- **CE install modifies CLAUDE.md** — idempotent, overwrites tool mapping block
- **Codex hooks** — `notify` only (post-turn). No pre/post-tool hooks. PR rejected by OpenAI.
- **OpenCode hooks** — TypeScript plugin system (`tool.execute.before/after`), not shell
