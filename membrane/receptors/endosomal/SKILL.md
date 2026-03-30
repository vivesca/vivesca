---
name: endosomal
description: Triage email — classify, archive noise, extract action items. "email", "inbox"
model: sonnet
---

# Endosomal — sort before surfacing

**Rule: classify first, act in batches — never archive without categorizing.**

## When this fires

- User asks to clear inbox or triage email
- Batch of emails need routing (newsletters, notifications, threads)
- Building a new Gmail filter rule for recurring noise
- Auditing what action items are buried in inbox

## Discipline

1. **Search before browsing** — use `endosomal_search` with Gmail query syntax; negation clauses (`-in:inbox`) must be one string arg, not separate tokens.
2. **Fetch full threads, not snippets** — `endosomal_thread` with `--full`; snippets miss context that changes the category.
3. **Categorize before archiving** — run `endosomal_categorize` on ambiguous emails; the deterministic pass handles most, LLM only fires on genuine ambiguity.
4. **Batch archive** — collect all `archive_now` IDs, then one call to `endosomal_archive`. Never archive one at a time.
5. **Filter last** — only propose `endosomal_filter` (dry_run=True first) after you've seen the pattern recur in at least 3 messages from the same sender/subject pattern. Confirm before setting dry_run=False.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Archive without classifying | Categorize, then batch archive |
| Assume newsletter = archive_now | Check for action signals in body |
| Create filters for one-off senders | Wait for 3+ recurrences |
| Mark read without archiving action items | Surface action_required before touching read state |
| Pass negation as separate args | Pass as one quoted query string |
