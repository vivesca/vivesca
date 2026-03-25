---
title: "Chrome-delegated download stall detection and recovery in photoferry"
date: 2026-02-23
component: "src/downloader.rs::download_via_chrome()"
tags:
  - download-robustness
  - stall-detection
  - retry-logic
  - duplicate-guard
  - photoferry
  - chrome
problem_type: reliability
severity: high
---

# Chrome Download Stall Detection and Recovery

**Component:** `~/code/photoferry/src/downloader.rs` — `download_via_chrome()`

## Problem

Chrome-delegated downloads in photoferry could fail in three ways:

1. **Duplicate downloads:** Opening the download URL in Chrome while one was already in progress spawned a second competing download — two `.crdownload` files that competed for bandwidth and both stalled
2. **Silent stalls:** A `.crdownload` file could sit with zero size growth for minutes, and the watcher had no mechanism to detect this
3. **Manual recovery required:** Kill watcher, delete `.crdownload` files, re-launch — no automatic recovery

**Trigger we hit:** The watcher or a manual retry opened the URL in Chrome a second time. Two `Unconfirmed XXXXXX.crdownload` files appeared, both ~14GB, both frozen at the same timestamp. The original code polled indefinitely without noticing.

## Root Cause

Two gaps in the original `download_via_chrome()`:

1. **No pre-flight check:** `open -a "Google Chrome"` ran unconditionally — no check for existing `.crdownload` files
2. **No stall detection:** The poll loop tracked whether a `.crdownload` existed and reported size, but never compared sizes across polls to detect stalls

## Solution

### 1. Duplicate Download Guard

Check for existing `.crdownload` files before opening Chrome. If found, attach to the existing download:

```rust
let pre_existing_crdownloads: Vec<PathBuf> = std::fs::read_dir(dir)?
    .filter_map(|e| e.ok())
    .map(|e| e.path())
    .filter(|p| p.extension().map_or(false, |ext| ext == "crdownload"))
    .collect();

if !pre_existing_crdownloads.is_empty() {
    // Attach to existing download — don't open Chrome again
} else {
    Command::new("open").args(["-a", "Google Chrome", &url]).spawn()?;
}
```

### 2. Stall Detection (2-minute timeout)

Track cumulative `.crdownload` file size each poll. If unchanged for 120 seconds, flag as stalled:

```rust
let current_size: u64 = crdownloads.iter()
    .filter_map(|p| p.metadata().ok())
    .map(|m| m.len())
    .sum();

if current_size != last_size {
    last_size = current_size;
    last_size_change = std::time::Instant::now();
} else if last_size_change.elapsed() > stall_timeout {
    // Stall detected — trigger retry
}
```

### 3. Auto-Retry on Stall (up to 3 attempts)

When stall is detected: delete stalled files, re-open URL in Chrome, reset tracking:

```rust
for cd in &crdownloads {
    let _ = std::fs::remove_file(cd);
}
Command::new("open").args(["-a", "Google Chrome", &url]).spawn()?;
crdownload_seen = false;
last_size = 0;
last_size_change = std::time::Instant::now();
```

After 3 failed retries, bail with actionable error: "Delete .crdownload files and retry manually."

### Poll Loop Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Poll interval | 5s | Fast enough to detect completion promptly |
| Progress reporting | 30s | Keeps user informed without spam |
| Stall timeout | 120s | 2 min of zero growth = definitely stalled, not just slow |
| Max retries | 3 | Enough to recover from transient issues |
| Overall timeout | 2h | Hard cap per part |

## Prevention: Browser-Delegated Download Patterns

When delegating downloads to an external process (browser, CLI tool), enforce these invariants:

- **Idempotence check before spawn:** Enumerate existing side-effect files before launching. Don't assume the external process deduplicates.
- **Stall detection via `(timestamp, size)` watermarks:** Poll-based wrappers must compare state across polls, not just report current state.
- **Atomic naming awareness:** Chrome uses `.crdownload` → atomic rename to `.zip` on completion. Different browsers/tools use different naming — filter by extension, not filename pattern.
- **Clean isolation between retries:** Delete partial files before retry. Reset all timers and counters. Don't let retry N inherit state from retry N-1.
- **Actionable bail messages:** Include what was tried, what was observed, and what the operator should do next.

## Related

- `~/docs/solutions/chrome-cookie-decryption-rusqlite-fix.md` — the cookie decryption bug fixed in the same session (prerequisite for Chrome downloads working at all)
- `~/docs/solutions/photoferry-reference.md` — project reference with operational gotchas
- `~/docs/solutions/integration-issues/linkedin-api-cookie-auth-dead.md` — similar pattern (cookie auth fails on anti-bot platforms)
