# photoferry Reference

Project: `~/code/photoferry`

## Commands
- **Binary:** `./target/release/photoferry`
- Commands: `check`, `run`, `verify`, `albums`, `import`, `download`

## Key Gotchas
- **Manifest location:** `~/Downloads/.photoferry-manifest-<zip-stem>.json` (one per zip)
- **PHFetchResult batch verify confirmed safe at 2704 IDs** — silently omits missing assets; diff input vs found set
- **`verify` command**: reads manifests, batch-queries PhotoKit, reports Missing / Wrong date. Old manifests (no `creation_date`) skip date check gracefully
- **PhotoKit does NOT dedup at import time**, but **Photos.app auto-merges duplicates post-import** — silently removes the duplicate `local_id`, causing verify to report false "Missing" for cross-part duplicates. A small missing count (~1-2 per part) is expected and normal when Takeout parts overlap.
- **Google Takeout parts overlap:** Same photo can appear in adjacent parts with Google's `(1)` suffix (e.g., `IMG_1741.JPG` in part 006, `IMG_1741(1).JPG` in part 005).
- **Zip 1 result:** 2704 imported, 0 failed, all verified OK (Feb 2026)
- **Parts 001+002 result:** 4610 imported, 0 failed (Feb 23 2026). Zips deleted, manifests retained.
- **Stream-from-ZIP (Feb 23):** `process_zip_streaming` indexes ZIP entries in Phase 1 (no I/O), then extracts one directory at a time. Peak disk: ~1-2GB vs full ZIP size.
- **Live-photo pair gotcha in streaming:** Already-imported media MUST be extracted alongside importable files for correct live-pair detection. Without this, a video whose paired photo is already imported would be imported as a standalone video (duplicate). The `should_import` flag separates "needed for analysis" from "needs importing".
- **Google Takeout export (Feb 2026):** 4,845 GB across 98 parts (~49.5GB each). Available until Feb 28.

## Download Mode (Hybrid HTTP + Chrome)
- **`--chrome` flag removed.** Hybrid is now default: tries HTTP first, falls back to Chrome on auth errors.
- **Direct Takeout URLs cause 500 errors.** Must navigate via `takeout.google.com` referrer. See `browser-automation/google-takeout-chrome-automation.md`.
- **Always use `--urls-file` with scraped URLs.** Constructed URLs lack `rapt` session tokens. Scrape from the Takeout manage page while authenticated.
- **Full job ID matters.** Truncated job ID (`65a591a2-167351b8dc4a`) caused 500s. Full ID from page: `65a591a2-7f11-483f-9e04-d952f087a07f`.
- **User ID from page:** `118329727694314214742`
- **Chrome cookie DB version stored as TEXT.** `rusqlite` `r.get::<_, i64>()` silently fails → `unwrap_or(0)` → SHA256 prefix never stripped. Fixed: parse as String first.
- **Google Takeout requires passkey re-auth** for downloads. `reqwest` can't handle the JS `/v3/signin/challenge/pk` flow. Chrome fallback handles auth natively.
- **Chrome `.crdownload` naming:** `Unconfirmed XXXXXX.crdownload` until complete, then atomic rename.
- **Progress files:** `.photoferry-download-<prefix>-<hash>.json`. Tracks completed, failed, and attempts (max 5 per part).
- **Google allows max 5 download attempts per part per export.** Exhausted parts need a new export.
- **AppleScript Chrome control requires:** Chrome → View → Developer → Allow JavaScript from Apple Events.
- **Chrome download policy set:** `defaults write com.google.Chrome DownloadDirectory` + `PromptForDownloadLocation false`.

## Current State (Feb 25 2026)

**Status:** Paused — waiting for external drive.

**Completed:** Parts 0, 1, 3, 4, 5, 6 (imported+verified, zips deleted)
**Partial:** Part 008 — partially imported (disk full mid-import)
**Exhausted:** Parts 2, 4 (hit 5-download limit — need new Takeout export)
**Remaining:** Parts 7–98 (92 parts)

**Blocked on:** WD Elements Desktop 12TB (WDBWLG0120HBK) — ordered from Yoho, HK$2,057. USB-A→C adapter ordered from Taobao.

**Resume (after drive arrives):**
1. Re-auth Chrome to Google (session expired)
2. `photoferry download --job "65a591a2-7f11-483f-9e04-d952f087a07f" --user "118329727694314214742" --start 7 --end 98 --concurrency 1 --urls-file ~/Downloads/.photoferry-scraped-urls.txt`
3. May need `--download-dir /Volumes/<drive>/`

**Cleanup:** Delete test photo from Photos (red screenshot, 2020-06-15, UUID 086748BD)

## swift-rs (Rust ↔ Swift FFI)
Used by photoferry for PhotoKit integration.

- **Swift package URL is dead on crates.io 1.0.7:** `nicklimmm/swift-rs` repo removed from GitHub. Use `Brendonovich/swift-rs` in Package.swift instead. The Rust crate from crates.io still works fine — only the SwiftPM dependency URL is broken.
- **SwiftPM cache corruption:** If `~/Library/Caches/org.swift.swiftpm/` has stale entries, `swift package resolve` loops. Nuke the whole cache dir + `.build` + `.swiftpm` to fix.
- **`Bool` not `bool` in FFI declarations:** `swift!(fn foo() -> Bool)` needs `swift_rs::Bool`, not Rust's `bool`. Convert with `.into()`.
