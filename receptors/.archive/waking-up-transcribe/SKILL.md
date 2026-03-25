---
name: waking-up-transcribe
description: Transcribe Waking Up app audio lessons into Obsidian notes. Use when user says "transcribe waking up", "waking up transcript", or wants to add meditation transcripts.
---

# Waking Up Transcribe

Transcribe Waking Up app audio lessons into Obsidian notes.

## Trigger

Use when:
- User says "transcribe waking up", "waking up transcript"
- User says "transcribe [lesson name]", "add waking up lessons"

## Inputs

- **audio_ids**: List of audio IDs to transcribe (from HLS URLs)
- **titles**: Corresponding lesson titles
- **teacher** (optional): Defaults to "Unknown"
- **pack** (optional): Defaults to "Uncategorized"
- **model** (optional): Transcription model, defaults to `gpt-4o-mini-transcribe`

## Paths

- **Repo:** `~/repos/waking-up-transcripts/`
- **Output:** `~/notes/Waking Up/[Pack]/[Title].md`
- **Cache:** `~/.cache/waking-up-audio/`

## Workflow

1. **Capture Audio IDs** (Browser — manual step):
   - Open https://app.wakingup.com and log in
   - Open DevTools → Network tab, filter by "hls" or "audios"
   - Click on each session to trigger HLS requests
   - Copy UUIDs from URLs: `courses/audios/{UUID}/hls/`

2. **Create batch file** at `~/repos/waking-up-transcripts/batch.json`:
   ```json
   [
     {
       "audio_id": "f5e2e44b-04c1-4ddc-bba6-9aed02767558",
       "title": "The Logic of Practice",
       "teacher": "Sam Harris",
       "pack": "Fundamentals"
     }
   ]
   ```

3. **Run transcription**:
   ```bash
   cd ~/repos/waking-up-transcripts
   python download_and_transcribe.py --batch batch.json --model base
   ```

4. **Verify output** in `~/notes/Waking Up/[Pack]/`

## Error Handling

- **If "No segments found"**: Wrong audio ID — refresh page and check console
- **If rate limit errors**: Script has built-in retry; wait
- **If batch interrupted**: Re-run same command — it skips completed files

## Output

Markdown files in `~/notes/Waking Up/[Pack]/[Title].md`

## Models

| Model | Cost/min | Notes |
|-------|----------|-------|
| gpt-4o-mini-transcribe | $0.003 | Recommended, 50% cheaper |
| whisper-1 | $0.006 | Legacy |
| gpt-4o-transcribe | $0.006 | Highest accuracy |

## Dependencies

- Python 3.11+
- ffmpeg (`brew install ffmpeg`)
- openai (`pip install openai`)
- requests (`pip install requests`)
