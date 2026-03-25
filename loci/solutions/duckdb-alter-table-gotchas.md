# DuckDB ALTER TABLE Gotchas

**Context:** Lacuna deployment on Railway, Mar 2026.

## ADD COLUMN IF NOT EXISTS segfaults

DuckDB (at least the Python package version on Railway/Python 3.11) **segfaults** on `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` when the table already has the column. This is not a Python exception — it crashes the process entirely. `try/except` doesn't catch it.

**Fix:** Check `information_schema.columns` first, or use `SELECT <column> LIMIT 0` in a try/except to test if the column exists before attempting ALTER TABLE.

```python
try:
    conn.execute("SELECT content FROM policies LIMIT 0")
except Exception:
    conn.execute("ALTER TABLE policies ADD COLUMN content TEXT")
```

## ALTER TABLE appends columns at the END

When you `ALTER TABLE ADD COLUMN`, the new column goes to the **end** of the column list, regardless of where it appears in your original `CREATE TABLE`. If you have code that maps `SELECT *` rows to dicts using a hardcoded column list, the mapping will be wrong — the new column is last, but your list may have it in the middle.

**Fix:** Never use `SELECT *` with positional column mapping. Use explicit column names:

```python
_COLUMNS = "policy_id, title, path, summary, content, status, version, owner, created_at, updated_at"

def get(self, policy_id):
    result = conn.execute(f"SELECT {self._COLUMNS} FROM policies WHERE policy_id = ?", [policy_id]).fetchone()
```

## Corrupt WAL blocks startup

If DuckDB crashes (e.g. from the segfault above), the WAL file can become corrupt. On next startup, `duckdb.connect()` throws `InternalException: Failure while replaying WAL file`. The only recovery is deleting the WAL — but this loses any uncommitted data.

**Fix:** Add WAL cleanup as a one-time recovery, not as a permanent startup step (deleting WAL on every deploy causes full data loss).
