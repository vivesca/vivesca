# Reference Skills Are Anti-Tokens

## Problem

Reference skills (non-user-invocable, `user_invocable: false`) were designed to separate guidance from action — e.g., `content-fetch` tells Claude which tool to use for URLs, while `summarize` actually does the work.

But each skill costs ~80 tokens/turn in the system prompt just for the name+description listing, regardless of whether it's ever consulted. With 13 reference skills, that's ~1,000 tokens/turn of passive overhead.

## Fix

Merge reference skills into their parent (action) skill. The guidance content lives in the parent's SKILL.md, so Claude gets the same knowledge when it reads the skill — but with zero marginal token cost for the listing.

## When to keep a reference skill separate

- It serves multiple parent skills equally (no natural home)
- It's large enough that merging would bloat the parent beyond readable size
- It changes at a different cadence than the parent

## Applied (Feb 2026)

| Reference skill | Merged into | Size added |
|---|---|---|
| llm-routing | ask-llms | ~30 lines (routing tree + cost table) |
| delegation-reference | delegate | Already had most content |
| content-fetch | summarize | ~40 lines (fallback chain + WeChat) |
| pii-mask | delegate | ~20 lines (usage + entity list) |

Result: 46 → 37 active skills, ~720 tokens/turn saved.

## General principle

Every persistent context item (skill listing, MCP tool, system prompt section) has a per-turn token cost. Consolidate unless there's a clear structural reason to separate.
