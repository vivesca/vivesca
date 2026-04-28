---
name: anam
description: Search past chat history and AI coding memories. Use when recalling what was discussed, finding past decisions, or looking up extracted learnings and gotchas.
effort: low
user_invocable: true
---

# History & Memory Search

Two layers of search:
- **`anam`** — raw transcript search (what happened, when, exact words)
- **`oghma`** — semantic memory search (extracted learnings, gotchas, preferences)

## Before Searching

Check canonical project note and `cerno` first. History search is for "I know we discussed this in a session" — not for facts that belong in the vault.

## anam — Raw Transcript Search

Rust CLI (`~/.cargo/bin/anam`). Programmatic, works from Claude Code. Source: `~/code/anam/`.

```bash
# Date scan
anam                          # Today's prompts (last 50)
anam yesterday
anam 2026-01-23
anam --full                   # All prompts (not just last 50)
anam --tool Claude

# Search (full transcripts by default — user + assistant)
anam search "keyword"                    # Last 7 days
anam search "keyword" --days=30
anam search "keyword" --tool Claude
anam search "keyword" --prompts-only     # User prompts only (faster)
anam search "keyword" --role claude      # AI responses only
anam search "keyword" --role you         # User messages only
anam search "keyword" --session b1b94317 # Specific session (prefix)
```

### Role aliases

| Value | Matches |
|---|---|
| `you` / `user` / `me` | User messages |
| `claude` / `assistant` / `ai` | AI responses |
| `opencode` | OpenCode responses only |

### claude-history (Interactive TUI — terminal only)

```bash
claude-history                 # Fuzzy search current project
claude-history --global        # All projects
claude-history --resume        # Resume selected session in Claude Code
```

## oghma — Semantic Memory Search

Extracted and indexed memories from AI coding transcripts. Best for "what's the right approach to X that we've learned."

```bash
# Note: prefer cerno over direct oghma search — cerno is QMD-first with oghma fallback
cerno "query"

# Direct oghma search (fallback only):
oghma search "query" --mode hybrid --limit 5
oghma search "query" --category learning    # learning | preference | project_context | gotcha | workflow
oghma search "query" --tool claude_code     # claude_code | codex | opencode
oghma status
```

**Search modes:** `keyword` (FTS5, fast) · `vector` (semantic) · `hybrid` (RRF fusion, best quality — default)

## Which Tool When

| Need | Tool |
|------|------|
| "What did we do today/yesterday?" | `anam` or `anam --full` |
| "Did X happen?" | Check daily note first, then `anam search --deep --role claude` |
| Find a draft/email I wrote | `anam search "keyword" --deep --role claude` |
| Drill into specific session | `anam search --session <8-char-prefix>` |
| Browse interactively | `claude-history` (terminal only) |
| Resume a past session | `claude-history --resume` (terminal only) |
| Recall a learning or gotcha | `oghma search "topic" --mode hybrid` |
| "What's the right approach to X?" | `oghma search "topic" --category workflow` |
| Find a preference or style choice | `oghma search "topic" --category preference` |

## Notes

- Always uses HKT (UTC+8) for day boundaries
- **Use single keywords, not phrases.** Multi-word queries match the full phrase literally — miss cases where terms appeared separately. Start with the most distinctive single word, narrow with `--session` if needed.
- **"Did X happen?" strategy:** Search for execution markers ("synthesis complete", "note written") not trigger words. Use `--role claude` to filter intent mentions.
- **Session storage gotcha:** Claude Code stores entries from session A inside session B's JSONL file. `--session` filter checks entry-level `sessionId`, not filename — this is correct.
- `chat_history.py` (`~/scripts/chat_history.py`) still works as fallback for anam
- `/daily` calls this skill for chat scanning

## Triggers

- anam
- search history
- past sessions
- what did we discuss
- recall conversation
