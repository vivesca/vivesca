# LRN-20260305-001: Waking Up HLS Download Failure Diagnosis

**Date:** 2026-03-05
**Pipeline:** `~/code/wu` — wu CLI for Waking Up transcript download/transcription

---

## Summary of Failures

From `batch_full.log` (ran 2026-02-20, 723 items, Deepgram Nova-3 backend):
- **Succeeded:** 225
- **Failed:** 498

Failure breakdown:
| Error type | Count | Root cause |
|---|---|---|
| `No segments found for audio <id>` | 212 | Wrong CDN — see below |
| `Deepgram API error 402 ASR_PAYMENT_REQUIRED` | 292 | Deepgram ran out of credits |
| `Deepgram API error 408 SLOW_UPLOAD` | 2 | Transient upload timeout |

---

## Root Cause 1: Wrong CDN for Episode/Talk Content (212 failures)

### What happened

The pipeline builds HLS segment URLs as:
```
https://d3amht9bmq5z6a.cloudfront.net/courses/audios/<id>/hls/segment_128_00000.ts
```

But **212 audio IDs of type `talk`** are podcast episodes hosted on a completely separate CDN:
```
https://d2uk1wgjryl0y1.cloudfront.net/show_episodes/audios/<id>/<filename>.m4a
```

These IDs return HTTP 403 on the courses HLS CDN, causing `find_segment_count()` to binary-search all the way to 0 and raise `DownloadError("No segments found")`. The pipeline never tried the direct URL because:

1. `batch_full.json` was built without `audio_url` in each item (field not present).
2. `process_audio()` does fall back to `load_mapping()` to look up `audio_url` — but at the time of the Feb 20 run, `audio_id_mapping.json` did not yet contain `audio_url` entries for episode content. That data was only added in commit `aa8c6e3` (2026-02-26).

### Current state

- All 212 failed IDs have `audio_url` in the current `audio_id_mapping.json`.
- These direct CDN URLs are live and return HTTP 200 with real audio data (~6-8 MB M4A files).
- **Zero of the 212 are currently in vault** — none have been retried since the fix.
- Of 1073 items in `batch_phase3.json`, 985 are in vault. **32 remaining `talk` types** map exactly to this failure class.

### Verification

```bash
# Confirm direct URL works for a sample failed ID
curl -I "https://d2uk1wgjryl0y1.cloudfront.net/show_episodes/audios/fe6a2908-7340-4add-a5b7-bafd3e81e4c1/City-of-Angels-Final.m4a"
# → HTTP/2 200, Content-Length: 6600479

# Confirm HLS CDN returns 403 for same ID
curl -I "https://d3amht9bmq5z6a.cloudfront.net/courses/audios/fe6a2908-7340-4add-a5b7-bafd3e81e4c1/hls/segment_128_00000.ts"
# → 403
```

---

## Root Cause 2: Deepgram Credits Exhausted (292 failures)

The batch ran sequentially and burned through Deepgram credits partway through. From batch_full.log, items 718-723 (and a large mid-batch stretch) all fail with `ASR_PAYMENT_REQUIRED`. Audio files were successfully downloaded (cached in `~/.cache/waking-up-audio/`) — only transcription failed.

These 292 items were subsequently retried using Gemini 3 Flash (current default backend), and most succeeded. The remaining 56 non-talk items still pending in vault appear to be a different batch subset (lessons, QA, conversations) — their HLS segments test as HTTP 200, so these are retryable.

---

## Current Pending Work (as of 2026-03-05)

From `batch_phase3.json` (1073 items, the canonical batch):
- In vault: **985** (~92%)
- Not in vault: **88**
  - `talk` type (episode CDN): **32** — need direct URL download path
  - Other types (lessons, QA, etc.): **56** — HLS segments accessible, just untranscribed

---

## Fix: The code already handles this correctly

Commit `aa8c6e3` (2026-02-26) added `_download_direct()` and the `audio_url` fallback to `download_hls_audio()`. The `audio_id_mapping.json` now contains `audio_url` for all episode content.

**The fix is already deployed.** Running the batch again will use the direct URL path automatically via `process_audio()` → `load_mapping()` → `audio_url`.

---

## Recommended Action

### Option A: Re-run batch_phase3.json (simplest)

```bash
cd ~/code/wu
uv run wu batch batch_phase3.json --model gemini-3-flash 2>&1 | tee batch_phase3_retry.log
```

The pipeline is idempotent — already-done items are skipped. The 32 talk items will now route through `_download_direct()` automatically.

### Option B: Build a targeted retry batch for just the pending items

```python
import json
from pathlib import Path

with open('/Users/terry/code/wu/batch_phase3.json') as f:
    items = json.load(f)

vault_base = Path('/Users/terry/notes/Waking Up')
pending = []
for item in items:
    found = list(vault_base.rglob(f"{item['title']}.md"))
    if not found:
        pending.append(item)

with open('/Users/terry/code/wu/batch_phase3_pending.json', 'w') as f:
    json.dump(pending, f, indent=2)

print(f'{len(pending)} pending items')
```

Then: `uv run wu batch batch_phase3_pending.json --model gemini-3-flash`

---

## Segment Expiry: Not a Concern Here

HLS segment expiry (CloudFront signed URL TTLs) is not relevant to this failure class:
- The HLS CDN (`d3amht9bmq5z6a.cloudfront.net/courses/`) uses **unsigned public URLs** — segments are permanently accessible for valid course content.
- The episode CDN (`d2uk1wgjryl0y1.cloudfront.net/show_episodes/`) similarly uses unsigned public URLs — tested live as of today, returning 200 with full file content.
- No time-sensitive window: these files have been accessible for the full duration of the project and show no TTL headers.

---

## Other Failure Type: Gemini Empty Transcript (9 failures, phase2 runs)

From `phase2.log`: 9 items failed with `Gemini returned empty transcript` or `Unexpected Gemini response: 'parts'`. These are Gemini safety/recitation blocks on specific audio content. Audio files are cached. Re-run with `--force` or try a different model (`nova-3`, `speechmatics`).

---

## Key Files

| File | Purpose |
|---|---|
| `~/code/wu/batch_full.log` | Original failure log (Feb 20, Deepgram run) |
| `~/code/wu/batch_phase3.json` | Canonical 1073-item batch |
| `~/code/wu/src/wu/download.py` | HLS download + direct URL logic |
| `~/code/wu/data/audio_id_mapping.json` | Audio ID → metadata + `audio_url` mapping |
| `~/.cache/waking-up-audio/` | Cached MP3s (skip re-download) |
