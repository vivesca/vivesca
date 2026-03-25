---
module: Oghma
date: 2026-02-06
problem_type: best_practice
component: cli_tool
symptoms:
  - "Same memory extracted 8-12 times from the same transcript"
  - "Database grows unboundedly with duplicate entries"
  - "4956 memories but only ~4825 unique"
root_cause: mental_model_error
resolution_type: config_change
severity: medium
tags: [oghma, daemon, dedup, polling, sqlite, content-hash]
---

# Polling Daemon Dedup Pattern

## Problem

When a daemon polls files for changes (by mtime/size), detects a change, and re-processes the **entire file** — every extraction gets re-inserted on every poll cycle. Without dedup, the database fills with exact duplicates.

This is especially bad for append-only files (like chat transcripts) where the file changes frequently but most content is old.

## Symptoms

- Same content inserted N times with timestamps ~5 minutes apart (matching poll interval)
- Database size grows linearly with poll cycles, not with new content
- Search results dominated by duplicates of the same fact

## Root Cause

Three missing pieces:
1. **No offset tracking** — daemon re-reads entire file instead of only new content
2. **No content dedup** — INSERT without checking for existing identical content
3. **No unique constraint** — database schema allows unlimited duplicates

## Solution

Content-hash based deduplication (Option A — simpler than offset tracking):

1. Add `content_hash` column: `SHA-256(content + category + source_file)`
2. Add unique index: `CREATE UNIQUE INDEX idx_dedup ON memories(content_hash, source_file)`
3. Use `INSERT OR IGNORE` instead of `INSERT`
4. Return `None` when a duplicate is skipped

### Migration for existing data

Order matters — must backfill hashes and delete dupes BEFORE creating the unique index:

```python
def _migrate_dedup(self, cursor):
    # 1. Drop index if exists (idempotent re-runs)
    cursor.execute("DROP INDEX IF EXISTS idx_dedup")

    # 2. Add column if missing
    cursor.execute("ALTER TABLE memories ADD COLUMN content_hash TEXT")

    # 3. Backfill hashes
    for row in cursor.execute("SELECT id, content, category, source_file FROM memories WHERE content_hash IS NULL"):
        hash_val = sha256(f"{row[1]}{row[2]}{row[3]}".encode()).hexdigest()
        cursor.execute("UPDATE memories SET content_hash = ? WHERE id = ?", (hash_val, row[0]))

    # 4. Delete duplicates (keep earliest)
    cursor.execute("""
        DELETE FROM memories WHERE id NOT IN (
            SELECT MIN(id) FROM memories GROUP BY content_hash, source_file
        )
    """)

    # 5. NOW create the unique index
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dedup ON memories(content_hash, source_file)")
```

## Prevention

- When building polling daemons: always plan for dedup from day one
- Prefer offset/position tracking for append-only files (reads only new content, saves API costs)
- Content hashing is a good safety net even with offset tracking
- Consider: exact hash catches exact dupes; near-dupes need semantic dedup (harder, separate concern)

## Limitation

Exact hash only catches **identical** extractions. The LLM often produces slightly different phrasings of the same fact ("relative to the script location" vs "relative to its location"). Semantic dedup would require embedding similarity, which is a separate feature.
