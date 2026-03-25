# Text Before Media — Content Extraction Principle

## Pattern

For any content pipeline (podcast digests, article summarization, etc.), always check if **text** is available before downloading and processing **media** (audio/video).

## Why

| Method | Time | Cost | Quality |
|--------|------|------|---------|
| Web transcript scrape | ~2s | Free | Best (human-edited) |
| YouTube transcript API | ~1s | Free | Good (auto-captions) |
| Whisper API | ~30s | ~$0.006/min | Good |
| Local Whisper (mlx) | 5-10 min | Free | Good |
| Audio download alone | 1-2 min | Free | N/A (still needs transcription) |

100x speed difference between web scrape and local Whisper. Quality is often better too (web transcripts are human-edited).

## Where Text Lives

- **Substack podcasts** (Dwarkesh, Latent Space): Full transcript in episode page body
- **Lex Fridman**: Dedicated URL at `{episode_url}-transcript`
- **YouTube**: Auto-captions via `youtube-transcript-api` or `yt-dlp --write-subs`
- **Many podcasts**: Show notes or full transcripts on website (check RSS `<link>` element)

## Implementation

See `~/skills/digest/digest.py` — fallback chain:
1. YouTube transcript API
2. yt-dlp subtitles
3. Web transcript scrape (trafilatura)
4. Whisper API (<25MB files)
5. Local mlx-whisper

## Gotcha

- Whisper API has 25MB limit — most podcast episodes are 50-150MB, so it only covers short episodes
- `trafilatura` is the best generic HTML-to-text extractor (handles Substack, WordPress, etc.)
- YouTube transcript API getting blocked more often (IP bans from burst requests) — rate limiting helps

## Discovered

2026-02-19. Dwarkesh digest was downloading 141MB audio + transcribing locally for 5-10 min per episode. Web scrape gets same content in 2 seconds.
