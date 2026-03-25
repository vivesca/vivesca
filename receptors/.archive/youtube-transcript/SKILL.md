---
name: youtube-transcript
description: Extract transcripts and subtitles from YouTube videos via yt-dlp.
user_invocable: false
---

# YouTube Transcript Extractor

Extract transcripts from YouTube videos using yt-dlp (primary) with youtube-transcript-api as fallback.

## When to Use

- User asks for transcript/subtitles from a YouTube video
- User wants to analyze or summarize video content
- User provides a YouTube URL or video ID

## Quick Start

```bash
uv run ~/skills/youtube-transcript/extract_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Options

| Flag | Description |
|------|-------------|
| `-l, --language` | Language code(s) in priority order (default: en) |
| `-t, --timestamps` | Include timestamps in output |
| `-c, --clean` | Remove [Music], [Applause], speaker labels |
| `-o, --output FILE` | Save to file instead of stdout |
| `--method` | Force method: `auto`, `ytdlp`, or `api` |
| `--browser` | Browser for cookies: `chrome`, `firefox`, `safari`, `edge`, `brave` |
| `--cookies` | Path to Netscape-format cookies.txt file |

## Examples

```bash
# Basic
uv run ~/skills/youtube-transcript/extract_transcript.py dQw4w9WgXcQ

# Clean output, save to file
uv run ~/skills/youtube-transcript/extract_transcript.py VIDEO_ID --clean -o /tmp/transcript.txt

# Use browser cookies for auth (if bot detection triggers)
uv run ~/skills/youtube-transcript/extract_transcript.py VIDEO_ID --browser chrome
```

## YouTube Bot Detection (Common Issue)

YouTube aggressively blocks scripted access. If you see "Sign in to confirm you're not a bot":

### Option 1: Use Browser Cookies
```bash
uv run ~/skills/youtube-transcript/extract_transcript.py VIDEO_ID --browser chrome
```
**Note:** Requires the browser to have an active YouTube/Google login. May fail if:
- Browser cookies are encrypted (Chrome on macOS)
- Browser is sandboxed (Safari)

### Option 2: Export Cookies Manually
1. Install browser extension: "Get cookies.txt LOCALLY" or similar
2. Visit YouTube while logged in
3. Export cookies to file
4. Use: `--cookies /path/to/cookies.txt`

### Option 3: Use Browser Automation (Nuclear Option)
If all else fails, use Claude in Chrome or similar browser automation to:
1. Navigate to video
2. Open transcript panel (click "..." → "Show transcript")
3. Extract text from the page

## Requirements

- **deno** — Required by yt-dlp for YouTube. Install: `brew install deno`
- **yt-dlp** — Auto-installed by `uv run`
- **youtube-transcript-api** — Auto-installed by `uv run`

## How It Works

1. **yt-dlp** (primary) — Downloads VTT subtitles directly. More reliable but requires deno runtime and may need authentication.

2. **youtube-transcript-api** (fallback) — Python API for transcripts. Often blocked by YouTube on cloud/VPN IPs.

## Known Limitations

- YouTube actively blocks scripted access — authentication often required
- Age-restricted videos may not be accessible
- Some videos have transcripts disabled by uploader
- Auto-generated transcripts may contain errors
- Cloud server IPs are frequently blocked
