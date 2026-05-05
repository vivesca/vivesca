---
name: video-digest
description: Video/podcast URL to full transcript + structured digest. Bilibili, YouTube, Xiaoyuzhou, Apple Podcasts, X, direct audio.
triggers:
  - video
  - podcast
  - bilibili
  - youtube
  - xiaoyuzhou
  - transcript
  - audio
  - media
  - digest
  - broadcast
user_invocable: false
source: Adapted from github.com/runesleo/x-reader (Feb 2026), rewritten for Gemini 3 Flash
---

# Video & Podcast Digest

Full transcription pipeline for video and podcast URLs. Called by `summarize` and `phagocytosis` skills when media URLs are detected — not invoked directly.

Uses **Gemini 3 Flash** for transcription + digest in a single API call. No Whisper, no segmentation, no second API key.

## When to Use

Route here when the URL matches a media platform and the user wants content extraction (not just metadata). For YouTube transcripts with available subtitles, `summarize` can handle directly via `youtube-transcript-api`. This skill is for: no subtitles, non-YouTube platforms, or audio-only content.

## Supported Platforms

| Platform | Subtitle path | Gemini path | Notes |
|----------|---------------|-------------|-------|
| YouTube | yt-dlp subtitles | Audio download → Gemini | Prefer `youtube-transcript-api` in `summarize` first |
| Bilibili | yt-dlp subtitles | Bilibili API audio → Gemini | yt-dlp gets 412 — use Bilibili API (Step 1d) |
| X/Twitter | N/A | Audio download → Gemini | Broadcasts: use video format, not audio-only (see gotcha) |
| Xiaoyuzhou | N/A | `__NEXT_DATA__` audio → Gemini | |
| Apple Podcasts | N/A | yt-dlp audio → Gemini | |
| Direct (.mp3/.mp4/.m4a/.webm) | N/A | File → Gemini | |

## Prerequisites

```bash
brew install yt-dlp jq   # yt-dlp for download, jq for JSON parsing
# ffmpeg already installed — audio conversion
```

Gemini API key in keychain. Retrieve:
```bash
GEMINI_API_KEY=$(security find-generic-password -s "gemini-api-key" -w 2>/dev/null)
```
Note: keychain service is `gemini-api-key`, NOT `gemini-api-key-secrets`.

## Pipeline

### Step 0: Detect Media Type

| URL Pattern | Route |
|-------------|-------|
| `xiaoyuzhoufm.com/episode/` | Step 1b (Xiaoyuzhou) |
| `podcasts.apple.com` | Step 1c (Apple Podcasts) |
| `bilibili.com`, `b23.tv` | Step 1d (Bilibili API) |
| `.mp3`, `.m4a` direct link | Skip to Step 2 |
| `x.com/i/broadcasts/` | Step 1f (X Broadcast) |
| Other video URL | Step 1a (try subtitles, fallback audio) |

### Step 1a: Extract Subtitles (YouTube, generic)

```bash
rm -f /tmp/media_sub*.vtt /tmp/media_audio.* /tmp/media_upload.* 2>/dev/null || true

# YouTube (prefer English, fallback Chinese)
yt-dlp --skip-download --write-auto-sub --sub-lang "en,zh-Hans" -o "/tmp/media_sub" "VIDEO_URL"
```

Check: `ls /tmp/media_sub*.vtt 2>/dev/null`
- Has subtitles: read VTT content, use directly for digest (Step 3) — no Gemini upload needed
- No subtitles: download audio (Step 1e) then Step 2

### Step 1b: Xiaoyuzhou — Extract Audio URL

```bash
AUDIO_URL=$(curl -sL -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "EPISODE_URL" \
  | grep -oE 'https://media\.xyzcdn\.net/[^"]+\.(m4a|mp3)' \
  | head -1)

curl -L -o /tmp/media_audio.mp3 "$AUDIO_URL"
```

If curl extraction empty: use `agent-browser` to render and extract.
Then: Step 2.

### Step 1c: Apple Podcasts — via yt-dlp

```bash
yt-dlp -f "ba[ext=m4a]/ba/b" --extract-audio --audio-format mp3 --audio-quality 5 \
  -o "/tmp/media_audio.%(ext)s" "APPLE_PODCAST_URL"
```

Then: Step 2.

### Step 1d: Bilibili — API Direct Audio

yt-dlp returns 412 for Bilibili. Use Bilibili's public API:

```bash
BV="BV1xxxxx"  # extract from URL

# Get video info
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=$BV" \
  -H "User-Agent: Mozilla/5.0" -H "Referer: https://www.bilibili.com/" \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(f/"Title: {d['title']}\nDuration: {d['duration']}s\nCID: {d['cid']}/")"

# Get audio stream URL
CID=<from_above>
AUDIO_URL=$(curl -s "https://api.bilibili.com/x/player/playurl?bvid=$BV&cid=$CID&fnval=16&qn=64" \
  -H "User-Agent: Mozilla/5.0" -H "Referer: https://www.bilibili.com/" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['dash']['audio'][0]['baseUrl'])")

# Download + convert (Referer required, otherwise 403)
curl -L -o /tmp/media_audio.m4s \
  -H "User-Agent: Mozilla/5.0" -H "Referer: https://www.bilibili.com/" "$AUDIO_URL"
ffmpeg -y -i /tmp/media_audio.m4s -acodec libmp3lame -q:a 5 /tmp/media_audio.mp3
```

Then: Step 2.

### Step 1e: Download Audio (no subtitles fallback)

```bash
# --cookies-from-browser chrome helps bypass YouTube bot detection
yt-dlp --cookies-from-browser chrome -f "ba[ext=m4a]/ba/b" --extract-audio --audio-format mp3 --audio-quality 5 \
  -o "/tmp/media_audio.%(ext)s" "VIDEO_URL"
```

Then: Step 2.

### Step 1f: X/Twitter — Broadcasts and Video Tweets

**Pre-check:** Run `bird read <URL>` first to determine content type. If tweet links to `x.com/i/broadcasts/`, use broadcast path. If embedded video, use video tweet path.

#### Broadcasts (Live Streams / Spaces Replays)

**CRITICAL GOTCHA:** `yt-dlp -f "ba"` on X broadcasts extracts a padded music/silence track — NOT the actual speech. Gemini will confidently hallucinate entire fake conversations from music-only audio. **Always download a video format and extract audio from it.**

```bash
# List formats to confirm broadcast
yt-dlp --cookies-from-browser chrome -F "BROADCAST_URL"

# Download VIDEO format (speech is in the video's audio track)
# replay-600 (528x336): good balance of speed vs quality — default
# replay-300 (368x232): faster download, adequate audio
# replay-2750 (1184x768): only if audio quality is poor at lower formats
yt-dlp --cookies-from-browser chrome -f "replay-600" \
  -o "/tmp/media_broadcast.mp4" "BROADCAST_URL"

# Extract audio from video
ffmpeg -y -i /tmp/media_broadcast.mp4 -vn -acodec libmp3lame -q:a 3 /tmp/media_audio.mp3
```

**Verify audio has speech before uploading to Gemini:**
```bash
# Check duration (broadcast video is often shorter than audio-only download)
ffprobe /tmp/media_audio.mp3 2>&1 | grep Duration

# Quick volume check — run from /tmp to avoid hook issues
cd /tmp && ffmpeg -i media_audio.mp3 -af "volumedetect" -f null /dev/null 2>&1 | grep mean_volume
# mean_volume > -30 dB = has content. ~-60 dB = silence.
```

For broadcasts >45 min, warn user before proceeding (large upload).

#### Video Tweets

Standard audio extraction works for regular video tweets:

```bash
yt-dlp --cookies-from-browser chrome -f "ba[ext=m4a]/ba/b" \
  --extract-audio --audio-format mp3 --audio-quality 5 \
  -o "/tmp/media_audio.%(ext)s" "TWEET_URL"
```

Then: Step 2.

### Step 2: Upload to Gemini File API + Transcribe/Digest

Single step — upload audio, then call generateContent with both the file and the digest prompt.

```bash
GEMINI_API_KEY=$(security find-generic-password -s "gemini-api-key" -w 2>/dev/null)
AUDIO_PATH="/tmp/media_audio.mp3"  # or whatever was downloaded
MIME_TYPE=$(file -b --mime-type "${AUDIO_PATH}")
NUM_BYTES=$(wc -c < "${AUDIO_PATH}" | tr -d ' ')

# 1. Resumable upload — get upload URL
curl "https://generativelanguage.googleapis.com/upload/v1beta/files" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -D /tmp/media_upload_headers.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d '{"file": {"display_name": "media_audio"}}' 2>/dev/null

UPLOAD_URL=$(grep -i "x-goog-upload-url: " /tmp/media_upload_headers.tmp | cut -d" " -f2 | tr -d "\r")

# 2. Upload the file
curl "${UPLOAD_URL}" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${AUDIO_PATH}" 2>/dev/null > /tmp/media_file_info.json

FILE_URI=$(jq -r ".file.uri" /tmp/media_file_info.json)

# 3. Generate transcript + digest in one call
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "contents": [{
      "parts": [
        {"text": "PROMPT_HERE"},
        {"file_data": {"mime_type": "'"${MIME_TYPE}"'", "file_uri": "'"${FILE_URI}"'"}}
      ]
    }]
  }' 2>/dev/null > /tmp/media_response.json

jq -r ".candidates[0].content.parts[0].text" /tmp/media_response.json
```

#### Prompts

**For pure transcript:**
```
Generate a verbatim transcript of this audio. Output the full text only, no timestamps, no commentary.
If the audio is in Chinese, transcribe in Chinese. If English, transcribe in English.
```

**For transcript + digest (default):**
```
Listen to this audio and produce:

1. TRANSCRIPT: Full verbatim transcript in the original language.

2. DIGEST:
- Title and duration
- Overview (2-3 sentences)
- Key Points (bullet points, dense)
- Notable Quotes (with approximate timestamps if possible)
- Action Items (if applicable)

For content over 20 minutes, add a Chapter Summary section segmented by topic shift.
Output the transcript first, then the digest.
```

### Step 3: Validate + Format Output

**Sanity-check before presenting** (especially X broadcasts):
- Does the content match the source topic?
- Are there real speaker names or topic references?
- If output is `[Music]`, `[No speakers identified]`, or <50 chars — wrong audio track. Re-download with video format (Step 1f).

If subtitles were found in Step 1a, summarize them directly in-context (no API call needed). Otherwise, use the Gemini response from Step 2.

## Error Handling

| Problem | Fix |
|---------|-----|
| No Gemini key in keychain | `security find-generic-password -s "gemini-api-key" -w` — check credential-isolation docs |
| Upload fails (413) | Shouldn't happen — Gemini File API handles large files. If it does, compress audio: `ffmpeg -i input -acodec libmp3lame -q:a 7 output.mp3` |
| Gemini rate limit (429) | Free tier: 1500 req/day. Wait and retry |
| X broadcast audio-only = music | **Never use `-f "ba"` for broadcasts.** Download video format (`replay-*`), then ffmpeg extract audio. Gemini hallucinates fake speech from music. |
| Gemini returns `[No speakers identified]` or very short output | Audio may be music-only. Verify with `ffmpeg -af volumedetect`. If volume OK but no speech, wrong audio track — try video download. |
| yt-dlp Bilibili 412 | Use Bilibili API (Step 1d) |
| yt-dlp YouTube bot detection | Add `--cookies-from-browser chrome` |
| Xiaoyuzhou curl extraction empty | Use `agent-browser` to render page |
| Spotify | Not supported (DRM). Tell user |
| Podcast over 2 hours | Warn + confirm before proceeding (cost: ~$0.05-0.10 for long audio) |

## Gemini 3 Flash Limits

- Model: `gemini-2.5-flash`
- Pricing: $0.50/$3 per Mtok (input/output)
- Context: 1M tokens input, 64K output
- Audio: native multimodal input, no separate transcription step
- File API: files persist 48 hours, resumable upload protocol
- Free tier: 1500 requests/day

## Motifs
- [escalation-chain](../motifs/escalation-chain.md)
- [verify-gate](../motifs/verify-gate.md)
