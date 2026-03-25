# Chrome Cookie Decryption: rusqlite Silent Type Mismatch

**Date:** 2026-02-23
**Component:** photoferry (`~/code/photoferry/src/downloader.rs`)
**Tags:** rusqlite, Chrome, cookies, SQLite, Google Takeout, type coercion

## Problem

Google Takeout downloads failed silently — all HTTP requests sent with **zero cookies** despite Chrome having 29 valid Google auth cookies. No error was raised.

## Symptoms

1. HEAD request to Takeout URL returned `200 OK` with `text/html` (Google login page)
2. Downloaded files contained `<!DOCTYPE html>` instead of ZIP data
3. Cookie extraction reported "29 cookies loaded" but cookie header was empty (0 bytes)

## Root Cause: Two Layers

### Layer 1: rusqlite silent type mismatch

Chrome's cookies SQLite DB stores `meta.version` as **TEXT** (`'24'`), not INTEGER. The Rust code used:

```rust
// BROKEN — silently returns Err when column is TEXT
let db_version: i64 = conn
    .query_row("SELECT value FROM meta WHERE key='version'", [], |r| {
        r.get::<_, i64>(0)
    })
    .unwrap_or(0);  // ← Always 0 because get() fails on TEXT
```

With `db_version = 0`, the SHA256(host_key) prefix stripping (required for Chrome 130+, DB version >= 24) was skipped. Every decrypted cookie value retained 32 bytes of binary hash prefix, failing the ASCII filter in `build_client()` — **zero cookies passed**.

### Layer 2: Google Takeout passkey re-auth

Even with cookies fixed, Google Takeout (as of Feb 2026) requires a **passkey re-authentication challenge** (`/v3/signin/challenge/pk`). This is a JavaScript-based flow that `reqwest` cannot handle — it requires a real browser.

## Fix

### DB version parsing (String-first fallback):

```rust
let db_version: i64 = conn
    .query_row("SELECT value FROM meta WHERE key='version'", [], |r| {
        r.get::<_, String>(0)
            .ok()
            .and_then(|s| s.parse::<i64>().ok())
            .map(Ok)
            .unwrap_or_else(|| r.get::<_, i64>(0))
    })
    .unwrap_or(0);
```

### SHA256 prefix: strip unconditionally when db_version >= 24

```rust
let value_bytes = if db_version >= 24 && decrypted.len() > 32 {
    &decrypted[32..]  // Strip prefix regardless of hash match
} else {
    decrypted
};
```

### Chrome-delegated download (`--chrome` flag):

New `download_via_chrome()` function opens the URL in Chrome via `open -a "Google Chrome"`, then polls the download directory for completed zip files. Chrome handles passkey/2FA natively.

Detection gotcha: Chrome uses `Unconfirmed XXXXXX.crdownload` (not `takeout-*.crdownload`) as the temp filename.

## Generic Lesson: SQLite + Rust Type Coercion

**SQLite has loose typing.** A column declared as `INTEGER` can hold TEXT, and vice versa. Chrome's cookies DB exploits this — `meta.value` is TEXT but holds numeric strings.

**rusqlite's `row.get::<_, T>()` fails silently** when the actual SQLite type doesn't match `T`. Combined with `.unwrap_or(default)`, this produces silent data corruption.

**Pattern:** Always try `String` first for any SQLite column you're not 100% sure about:

```rust
fn get_int_loose(row: &rusqlite::Row, idx: usize) -> rusqlite::Result<i64> {
    row.get::<_, String>(idx)
        .ok()
        .and_then(|s| s.trim().parse::<i64>().ok())
        .map(Ok)
        .unwrap_or_else(|| row.get::<_, i64>(idx))
}
```

## Prevention

1. **Assert cookie count > 0** before building the HTTP client — fail loudly, not silently
2. **Detect HTML content-type** on HEAD response — bail with "use --chrome" guidance
3. **Test decrypted values are ASCII-printable** — catches binary garbage from broken decryption

## Related

- `~/docs/solutions/photoferry-reference.md` — project reference with operational gotchas
- `~/docs/solutions/browser-automation/` — agent-browser patterns (alternative to Chrome delegation)
- `~/docs/solutions/integration-issues/linkedin-api-cookie-auth-dead.md` — similar pattern (cookie injection fails on anti-bot platforms)
