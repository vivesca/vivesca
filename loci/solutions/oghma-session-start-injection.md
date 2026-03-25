# Oghma Session-Start Memory Injection

## Problem

Oghma has 10K+ memories but only ~20 are always in context (MEMORY.md). The remaining 201-10,000 are only accessible if the AI proactively calls `oghma_search` via MCP — which it rarely does because it doesn't know what it doesn't know ("unknown unknowns").

## Solution

A `UserPromptSubmit` hook that auto-injects the top 3 relevant memories on session start.

**File:** `~/.claude/hooks/oghma-session-inject.py`

### How it works

1. Hook fires on every user message (Claude Code `UserPromptSubmit` event)
2. Checks state file (`~/.claude/.oghma-inject-state`) — if same cwd and <30 min old, skip
3. Uses directory basename as FTS5 keyword search query against Oghma SQLite
4. Injects top 3 results in `<session_context>` XML block
5. Updates state file

### Key design decisions

- **FTS5 keyword search, not vector** — 142ms total vs ~500ms+ with embedding API. Repo basename is a good enough query for session-start context.
- **Debounce by cwd + 30 min** — only fires once per repo per session. Subsequent messages are silent.
- **Direct Python import** (`from oghma.storage import Storage`) — no subprocess, no CLI parsing.
- **Truncate to 150 chars per memory** — keep injection under token budget.
- **Skip generic dirs** — `~`, `Users`, `terry` would return noise.

### Council deliberation

Ran frontier-council on "MCP vs auto-injection vs hybrid". Key outcome:
- All 5 models agreed hybrid is needed
- Judge said "ship session-start injection as v1, skip per-turn injection until you have data"
- Threshold tuning (0.75-0.88) was premature — just use 0.75 for FTS5 results
- Full transcript: `~/.frontier-council/sessions/20260210-130140-*.md`

### v2 candidates

- Per-turn injection with verb triggers ("create", "fix", "refactor")
- Tiered visibility (high confidence = full text, medium = title + [VERIFY])
- Injection logging to SQLite for measurement
