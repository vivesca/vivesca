# LRN-20260308-003: Rust + DuckDB — Three Options, One Winner

## TL;DR
Use `bundled` feature. First build ~3min (C++ compile once), then cached at ~0.3s. Self-contained binary. Static `.a` from Homebrew fails (macOS version mismatch). System dylib fast but not self-contained.

## Problem
`duckdb` crate v1.x with `features = ["bundled"]` compiles the entire DuckDB C++ library
from source (~1M lines). Takes 10+ minutes, saturates the Mac, blocks the session.

## Solution
Use the pre-built Homebrew library:

```bash
brew install duckdb   # installs libduckdb.dylib + headers in /opt/homebrew/
```

In `Cargo.toml` — use `chrono` feature but NOT `bundled`:
```toml
duckdb = { version = "1", features = ["chrono"] }
```

In `.cargo/config.toml` (project-local):
```toml
[env]
DUCKDB_LIB_DIR = "/opt/homebrew/lib"
DUCKDB_INCLUDE_DIR = "/opt/homebrew/include"
```

Build time: **~4s cold, ~0.7s incremental** (vs 10+ min bundled).

## Bonus: `chrono` feature
With `features = ["chrono"]`, `NaiveDate` and `NaiveDateTime` implement `ToSql`/`FromSql`
directly — no string-casting workarounds needed in SQL or row mapping.

## Runtime
The binary links against `/opt/homebrew/opt/duckdb/lib/libduckdb.dylib` — requires
Homebrew duckdb to be installed on the machine running the binary. Fine for personal CLIs.

## Reference
- Project: `~/code/nyx/`
- GitHub: `terry-li-hm/nyx` (private)
