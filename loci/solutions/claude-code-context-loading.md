# Claude Code: Context Loading Architecture

Source: official docs at https://code.claude.com/docs/en/memory

## CLAUDE.md vs MEMORY.md Loading

| File | Loads | Limit | After /compact |
|------|-------|-------|----------------|
| CLAUDE.md | Full file, session start | Soft: ~200-500 lines (docs conflict; both are adherence guidance, not hard cutoffs) | **Explicitly re-read from disk, re-injected fresh** |
| MEMORY.md | First 200 lines only, session start | **Hard 200-line cutoff — silently dropped beyond** | Not mentioned in docs — assumed not re-injected |
| Rules (no paths) | Session start | Same as CLAUDE.md | Unclear — docs only mention CLAUDE.md explicitly |
| Rules (with paths) | When matching file read | Same as CLAUDE.md | Unclear |
| Topic files (debugging.md etc.) | On demand, not at startup | — | — |

**Key:** Neither is re-injected per turn. Both load at session start.
`/compact` gives CLAUDE.md a second life mid-session (re-read from disk). MEMORY.md does not get this benefit.

## `.claude/rules/` Mechanism

Rules files are markdown files in `.claude/rules/`. Two types:

**No `paths` frontmatter** → loads unconditionally at session start, same priority as CLAUDE.md.

**With `paths` frontmatter** → loads only when Claude reads a file matching the glob pattern (not at session start, not on every tool use — only on file read).

```yaml
---
paths:
  - "**/*.rs"
  - "**/*.py"
---
Rules here only fire when editing Rust or Python files.
```

## Scope

| Location | Scope |
|----------|-------|
| `~/.claude/rules/` | User-level — applies to every project on this machine |
| `./.claude/rules/` | Project-level — applies to this project only |

Project rules take precedence over user rules.

## Enforcement Hierarchy

| Layer | When fires | Best for |
|-------|-----------|---------|
| Hooks | Every tool call | Mechanical rules — must not fail |
| CLAUDE.md | Session start + after /compact | Core rules, orientation |
| Rules (no paths) | Session start | Supplementary rules (same as CLAUDE.md) |
| Rules (path-scoped) | When matching file is read | Language/task-specific rules |
| MEMORY.md (first 200 lines) | Session start | Gotchas — keep concise |
| Topic files | On demand | Detailed notes Claude reads when needed |

Truly reliable mid-session enforcement = **hooks only**.

## Terry's Setup

- `~/.claude/rules/coding.md` — Implementation Quality, fires on code file edits
- `~/.claude/CLAUDE.md` — user-level CLAUDE.md (same as `~/CLAUDE.md` symlink)
- MEMORY.md — gotchas, 138 lines (well under 200-line limit)
- Hooks — mechanical enforcement (grep scope, rm safety, gist privacy)

## Practical Notes

- "Shorter CLAUDE.md = better adherence" is about quality, not a hard cutoff. Full file always loads.
- MEMORY.md 200-line limit is hard. Content beyond line 200 silently not loaded.
- `/compact` re-reads CLAUDE.md from disk — mid-session refresh mechanism.
- Topic files in memory dir (debugging.md etc.) are NOT auto-loaded. Claude reads on demand only.
- **Skills are the explicitly recommended solution** (per official docs) for workflow-specific instructions — they load on-demand, keeping base context smaller. Rules and CLAUDE.md for always-relevant rules; skills for specific workflows.
- CLAUDE.md line limit: docs conflict (200 lines in memory.md, 500 lines in costs.md). Both are soft adherence guidance — no hard cutoff. 200 is more conservative.
