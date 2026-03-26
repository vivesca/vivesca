---
name: ecphory
description: Cue-routed retrieval across all memory stores — routes by query intent (episodic vs semantic), age, and store type before fanning out. Use when searching for prior-session data, past decisions, or anything entered in a previous session. "find what we decided", "I entered this before", "we talked about X", "ecphory", "what did we say about".
user_invocable: true
model: sonnet
triggers:
  - "I entered this before"
  - "we talked about"
  - "find what we decided"
  - "what did we say"
  - "I mentioned this before"
  - "prior session"
  - "ecphory"
allowed-tools:
  - Bash
  - mcp__vivesca__histone_search
  - mcp__vivesca__chemotaxis_search
---

# Ecphory — Cue-Routed Memory Retrieval

> In neuroscience, ecphory is the process where a retrieval cue reactivates a stored memory trace (Tulving, 1983). Neither the cue alone nor the trace alone produces retrieval — they must interact. This skill implements that principle: route the cue to the store whose memory type matches the query, synthesise from partial hits.

## Routing Table

The organism has four stores with distinct memory profiles:

| Store | Memory type | Access | Best for |
|-------|-------------|--------|----------|
| `anam search` | Episodic (raw session transcripts) | `anam search "<pattern>" --days N` | "we talked about X", "I entered Y", unpersisted session data |
| `histone_search` | Episodic + semantic hybrid | MCP tool | Named facts from sessions that were explicitly saved to oghma |
| `receptor-scan` / vault | Semantic | `receptor-scan "<query>"` | Stable reference knowledge, vault notes, research |
| `oghma` | Semantic structured | `oghma search "<query>"` | Categorised memory objects with metadata |

## The Retrieval Protocol

### Step 1 — Parse the cue

Classify the query along two axes:

**Recency signal:**
- "yesterday", "this morning", "we just", "last session" → recent (anam first)
- "last week", "a while ago", "I think we" → medium (histone first)
- "I established", "the rule is", "the pattern is" → old/stable (vault/oghma first)
- No signal → assume episodic (anam first)

**Memory type signal:**
- Event-based ("what did we decide", "when did we", "what happened with") → episodic → anam + histone
- Fact-based ("what is the rule", "what's the approach", "the framework for") → semantic → vault + oghma
- Mixed or ambiguous → episodic first, semantic second

### Step 2 — Route to primary store

Fire the most specific cue against the primary store first. Be generous with synonyms — the original encoding may have used different words.

```
# Episodic primary (recent)
anam search "<keyword variants>" --days 7

# Episodic primary (older)
anam search "<keyword variants>" --days 30

# Semantic primary
receptor-scan "<query>"
# or
oghma search "<query>" --mode hybrid
```

### Step 3 — Fan out if not found

If primary store returns nothing or only weak matches, hit the next tier:

```
Episodic miss → try histone_search, then vault/oghma
Semantic miss → try histone_search, then anam (last 14 days)
```

Explicit fan-out order:
1. anam (episodic, unpersisted)
2. histone_search (persisted session memory)
3. receptor-scan / vault grep (semantic, stable)
4. oghma (structured semantic)

### Step 4 — Synthesise

Do not dump raw hits. Reconstruct from partial matches:

- If single strong match: confirm the match, present it, note the source
- If multiple partial matches: synthesise across them — "In anam on Mar 20 you entered X; in vault there's a related note Y; the combined picture is Z"
- If weak or contradictory: surface the contradiction explicitly, ask for confirmation before acting on it
- If nothing found: say so clearly, do not confabulate

## Anti-patterns

- **Uniform sweep**: running all stores in parallel before classifying the cue. Wastes tool calls, adds noise.
- **Stopping at anam**: anam has the richest episodic data but misses anything explicitly persisted to oghma or vault.
- **Exact-match only**: encode at one vocabulary, retrieve at another. Use synonyms, related terms, and topic expansions in the cue.
- **Confabulation**: if no clear match is found, do not synthesise a plausible-sounding answer. Return empty with path taken.

## Biology note

Ecphory is reconstructive, not reproductive — what gets returned is built from cue + partial trace, not a faithful playback. This is both a warning (partial matches need synthesis, not literal reporting) and a feature (partial hits from different stores can be assembled into a complete picture).
