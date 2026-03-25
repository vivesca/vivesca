---
title: sopor DuckDB stale lock after crash
tags: [sopor, duckdb, lock]
---

## Symptom
`sopor today` fails with: `Could not set lock on file ... Conflicting lock is held in ... (PID XXXX)`
But `ps -p XXXX` shows process is gone.

## Fix
Remove stale WAL/tmp files:
```bash
rm -f ~/.local/share/sopor/sopor.duckdb.wal ~/.local/share/sopor/sopor.duckdb.tmp
```
Then retry. No data loss — WAL from a dead process is safely removable.
