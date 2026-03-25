---
title: "Oghma v0.4.0 Release — Test Failures & Migration Fixes"
date: 2026-02-06
category: test-failures
module: oghma
tags:
  - embedding-migration
  - sqlite-vec
  - test-fixtures
  - deduplication
  - pypi-publishing
  - git-signing
  - infinite-loop
severity: high
symptoms:
  - EmbeddingMigration.run(dry_run=True) hangs indefinitely
  - "Dimension mismatch for inserted vector" error from sqlite-vec
  - Test assertions fail after dedup behavior change
  - Git tag signing times out in SSH/tmux sessions
  - pytest hangs at 45% during full suite run
---

# Oghma v0.4.0 Release — Test Failures & Migration Fixes

## Context

During the Oghma v0.4.0 release, the full test suite revealed multiple failures and one infinite hang caused by behavioral changes (content-only dedup, writable MCP storage) and pre-existing bugs exposed by sqlite-vec now being available.

## Problem 1: Migration dry_run Infinite Loop

**Symptom:** `pytest tests/test_migration.py` hangs forever. Full test suite hangs at ~45%.

**Root cause:** `EmbeddingMigration.run(dry_run=True)` uses a `while True: fetch_unprocessed()` loop. In dry_run mode, the `continue` statement skips embedding but never marks memories as processed. `get_memories_without_embeddings()` returns the same batch every iteration.

```python
# BUG: infinite loop in dry_run
while True:
    batch = storage.get_memories_without_embeddings(limit=self.batch_size)
    if not batch:
        break
    processed += len(batch)
    if dry_run:
        continue  # Never mutates state, same batch returned forever
```

**Fix:** Extract dry_run to a single upfront query:

```python
if dry_run:
    batch = storage.get_memories_without_embeddings(limit=10_000)
    return MigrationResult(processed=len(batch), migrated=0, skipped=len(batch), failed=0)
```

**Rule:** Any `while True: fetch_unprocessed()` loop that `continue`s without modifying state will infinite-loop. Dry-run modes must not share the processing loop.

## Problem 2: sqlite-vec Vector Dimension Mismatch

**Symptom:** `sqlite3.OperationalError: Dimension mismatch for inserted vector for the "embedding" column. Expected 1536 dimensions but received 2.`

**Root cause:** `FakeEmbedder` in test returned `[float(len(text)), 0.0]` (2 dims) but the sqlite-vec virtual table was created with 1536 dimensions. Previously this test was skipped because sqlite-vec wasn't installed.

**Fix:** Match production dimensions:

```python
def embed(self, text: str) -> list[float]:
    vec = [0.0] * 1536
    vec[0] = float(len(text))
    return vec
```

**Rule:** Test doubles must match production constraints — dimensions, types, ranges, schemas.

## Problem 3: OpenCode Parser Test Fixture Paths

**Symptom:** `assert messages[0].content == "First part"` fails, gets empty string.

**Root cause:** Test created parts at `session_dir/part/msg_msg1/` but the parser resolves parts at `storage_root/part/<filename_stem>/` where `storage_root = file_path.parent.parent` and filename stem is `msg_0001` (not the JSON `id` field `msg1`).

**Fix:** Align test fixture paths to match actual parser resolution:

```python
# Before (wrong): parts under session dir with JSON id
part_dir = session_dir / "part" / "msg_msg1"

# After (correct): parts under storage root with filename stem
storage_dir = fixture_dir / ".local" / "share" / "opencode" / "storage"
part_dir = storage_dir / "part" / "msg_0001"
```

**Rule:** When writing parser tests, trace the actual path resolution in the parser code first. Don't assume path structure.

## Problem 4: Content-Only Dedup Test Assertions

**Symptom:** Tests `test_dedup_different_source_files_allowed` and `test_dedup_different_categories_allowed` fail — expected 2 memories, got 1.

**Root cause:** Dedup was changed from `(content + category + source_file)` hash to content-only hash. Same content now rejected regardless of source or category.

**Fix:** Update assertions:

```python
# Before: expected different sources to allow duplicates
assert memory_id_2 is not None
assert storage.get_memory_count() == 2

# After: content-only dedup rejects all duplicates
assert memory_id_2 is None
assert storage.get_memory_count() == 1
```

**Rule:** When changing core behavior (especially dedup/uniqueness), grep for ALL tests exercising that behavior. Don't just fix the first failure.

## Problem 5: PyPI Publishing & Git Signing in SSH

**PyPI token:** Stored in macOS Keychain, not env vars or config files:

```bash
security find-generic-password -s "pypi-api-token" -w
uv publish dist/*.whl dist/*.tar.gz --token "$(security find-generic-password -s 'pypi-api-token' -w)"
```

**Git tag signing:** GPG pinentry times out in SSH/tmux (no access to GUI passphrase prompt):

```bash
# Fails in SSH:
git tag -a v0.4.0 -m "message"  # GPG timeout

# Works:
git tag -a v0.4.0 --no-sign -m "message"
```

## Prevention Strategies

1. **Batch processing loops:** Always verify the loop invariant — does each iteration reduce the remaining work? Add a safety counter or `max_iterations` guard during development.
2. **Test doubles:** Centralize production constraints (vector dims, schema sizes) as constants. Test fixtures reference constants, not hardcoded values.
3. **Path-dependent tests:** Add a comment in the test documenting the expected directory structure. Trace the parser's resolution before writing fixtures.
4. **Behavior changes:** `grep -r "function_name\|behavior_keyword" tests/` before considering a behavioral change complete.
5. **Release checklist:** Check for credentials (`security find-generic-password`), test signing (`--no-sign` fallback), verify build (`uv build`), run full suite before publish.

## Related Docs

- [Polling Daemon Dedup Pattern](../best-practices/polling-daemon-dedup-pattern.md)
- [Compound Engineering Full Cycle — Oghma Case Study](../best-practices/compound-engineering-full-cycle-oghma.md)
- [Oghma MCP Orchestration Pattern](../workflow-issues/oghma-mcp-orchestration-pattern.md)
