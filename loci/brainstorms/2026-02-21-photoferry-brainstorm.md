# Photoferry Brainstorm

**Date:** 2026-02-21
**Status:** Swift spike PASSED — Option A confirmed viable

## What We're Building

**photoferry** — an open-source macOS CLI that migrates Google Photos (via Google Takeout) to iCloud Photos. The full pipeline: disk-aware batching of 50GB Takeout zips, metadata preservation from sidecar JSON, automated import into Photos.app, per-file verification, and resumable state tracking.

**Gap:** Nobody has built this. osxphotos handles import but not batching/verification. GooglePhotosTakeoutHelper fixes metadata but doesn't import. Apple's DTP does cloud-to-cloud but flattens albums. See council research (2026-02-21).

## Why This Approach

### Target Users
- **v1:** Power users comfortable with CLI, Homebrew, Rust toolchain
- **Aspirational:** Non-technical Mac users (layered — GUI/guided CLI later if traction)

### Scope
- **v1:** Google Photos → iCloud only
- **Architecture:** Extensible with source/target adapter pattern for future sources (Flickr, Amazon Photos, Immich)

### Maintenance Model
- "Publish and forget" — ship, fix critical bugs, no ongoing feature work
- This favours compiled binaries over external runtime dependencies

## Key Decisions

### Architecture: Rust + Swift PhotoKit helper (CONFIRMED)

**Council decision (2026-02-21):** 5/5 initially recommended Option B (Rust + osxphotos subprocess) based on 3-4 weekend estimate. Revised after:
1. AI-assisted development collapses Swift helper to ~2-4 hours
2. **Swift spike passed** — PhotoKit works from CLI binary, no .app bundle or entitlements needed

**Spike results (2026-02-21):**
- PhotoKit `PHAssetChangeRequest` works from bare CLI binary
- Creation date, GPS location, favourite flag all applied correctly
- Returns structured JSON (localIdentifier, success, error) — perfect for Rust integration
- Batch mode via JSON lines on stdin — Rust streams requests, Swift processes
- Spike code: `/tmp/photoferry-spike/` (200 lines Swift)

**Decision: Option A (Rust + Swift).** True single-binary distribution. No Python dependency. Best product, best signal, viable timeline.

### Import backend as pluggable trait

Regardless of A vs B, the import step lives behind a clean Rust trait:

```
trait ImportBackend {
    fn import(&self, file: &Path, metadata: &PhotoMetadata) -> Result<ImportResult>;
    fn name(&self) -> &str;
}
```

v1 ships with either SwiftPhotoKit or OsxPhotos backend. Future contributors can add others.

### Signalling value

- LinkedIn post: "Migrated 2.25TB, nothing existed, built the orchestration layer"
- Open source portfolio piece for Capco role
- Rust + Swift cross-platform signal is strongest (if A works)
- "Gap-finder" framing: "osxphotos imports well, but nothing handled TB-scale orchestration"

## Resolved Questions

- [x] **Does PhotoKit work from a CLI binary?** YES — spike confirmed. No .app bundle, no entitlements, no sandbox issues.
- [x] **osxphotos --report JSON format** — Moot; we're using Swift PhotoKit directly. Our helper returns structured JSON per file.
- [x] **Google Takeout sidecar JSON format** — Fully documented. `photoTakenTime.timestamp` (Unix epoch string, UTC) for dates, `geoDataExif`/`geoData` for GPS, `favorited` (omitted when false), `people[].name`. Two naming eras: legacy `.json` and new `.supplemental-metadata.json` (2024+) with 51-char truncation bug. Need fuzzy sidecar matching (46-char truncation fallback, multiple suffix patterns). Source: immich-go parser, GPTH issues.
- [x] **Photos.app crash threshold** — `photolibraryd` crashes under memory pressure with rapid sequential imports. Mitigate: serial imports, release image data immediately, 10s timeout guard, retry queue, configurable batch pause (e.g., every 200 imports sleep 5s).
- [x] **Album strategy** — Named album folders (with `albumData` in `metadata.json`) → create as Photos.app albums via `PHAssetCollectionChangeRequest`. Year folders (`Photos from YYYY`) are containers — skip. Same photo in year folder + album = import once, add to album. One level of folder nesting is safe in Photos.app.
- [x] **Build/distribution** — Use `swift-rs` crate: Swift compiled as static `.a`, linked into Rust binary via `@_cdecl` + C-compatible types. Swift runtime in macOS 13+ base OS (no Xcode on user machine). `cargo install` won't work → distribute via Homebrew tap with pre-built binaries from GitHub Actions. Fallback: two-binary approach (embed Swift CLI via `include_bytes!`).

## Open Questions

- [ ] **Live Photos (v1)** — Include in v1 (user has lots of family Live Photos). Requires: (1) detect pairs by base filename + magic bytes (Google exports video as `IMG(1).JPG` with wrong extension), (2) embed shared UUID into JPEG (MakerApple key 17) and MOV (QuickTime `content.identifier` + `still-image-time` timed metadata track), (3) import via `PHAssetCreationRequest.addResource(.photo/.pairedVideo)`. If MOV already has Apple metadata (genuine Live Photo export), skip UUID embedding. ~3-4 hours with Claude Code.
- [ ] **Description/title metadata** — PhotoKit's `PHAssetChangeRequest` doesn't expose title/description setters directly. May need to write EXIF (via `CGImageDestination`) before import. Investigate during implementation.
- [ ] **`swift-rs` + PhotoKit async** — `@_cdecl` boundary is C-only, no Swift async. Need synchronous wrapper around PhotoKit's `performChanges` callback. The spike already handles this (semaphore pattern). Confirm `swift-rs` doesn't add complications.

## Technical Reference

### Takeout JSON → PhotoKit Mapping

| Takeout field | PhotoKit property | Notes |
|---|---|---|
| `photoTakenTime.timestamp` | `creationDate` | String → parse as Unix epoch (can be negative for pre-1970) |
| `geoDataExif` (preferred) / `geoData` (fallback) | `location` | `0.0` = absent. CLLocation(lat, lon) |
| `favorited` | `isFavorite` | Omitted when false |
| `people[].name` | Keywords | No face coordinates in export |
| `description` | Needs EXIF write pre-import | Not directly settable via PhotoKit |
| `title` | Needs EXIF write pre-import | Same |

### Sidecar Filename Matching (priority order)

1. `{name}.{ext}.supplemental-metadata.json` (new format, 2024+)
2. `{name}.{ext}.json` (legacy)
3. `{name}.json` (legacy alternate)
4. If filename >= 47 chars: first 46 chars + `.json`
5. Handle `(N)` dedup suffix: `{name}.{ext}(N).json` or `{name}.{ext}.supplemental-metadata(N).json`
6. Handle truncated `.supplemental-meta*.json` variants (51-char total cap)

### Batch Import Safety

- Serial imports only (no concurrent `performChanges`)
- Release image data after each import
- 10-second timeout per import (guard against `photolibraryd` crash)
- Retry queue for timeouts/errors
- Configurable batch pause: `--batch-pause 200:5` (every 200 imports, sleep 5s)

## Registry Names (Secured)

| Registry | Status |
|----------|--------|
| GitHub terry-li-hm/photoferry | Claimed |
| PyPI photoferry | Published (0.0.1 placeholder) |
| npm photoferry | Published (0.0.1 placeholder) |
| crates.io photoferry | Published (0.0.1 placeholder) |

## References

- Working prototype: `~/scripts/takeout-migrate.py`
- Council transcript: `~/code/vivesca-terry/chromatin/Councils/LLM Council - Photoferry Architecture - 2026-02-21.md`
- Naming council: `~/code/vivesca-terry/chromatin/Councils/LLM Council - Takeout Tool Name - 2026-02-21.md`
- Competitive research: In conversation (2026-02-21) — no tool covers full pipeline
