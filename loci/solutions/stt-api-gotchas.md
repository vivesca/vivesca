# STT API Gotchas

Learnings from the `wu` meditation transcript pipeline (Feb 2026).
See also: `deepgram-nova3-transcription.md`, `waking-up-api.md`

## Speechmatics

- **`speaker_diarization_config.max_speakers` removed** (breaking change, Feb 2026).
  Error: "Additional property max_speakers is not allowed". Remove the entire
  `speaker_diarization_config` sub-object; `diarization: "speaker"` still works alone.

- **sounds_like doesn't guarantee term recognition.** Speechmatics with Vipassana in
  vocabulary still heard "a person" instead of "Vipassana" in a real test.
  sounds_like helps but isn't a hard match — it's a soft phoneme hint.

- **Async batch API is Speechmatics-specific.** The `batch-async` command in the wu
  pipeline (submit → poll → fetch) doesn't generalize to Gemini/OpenAI. Use `batch`
  for those.

## Gemini File API (audio transcription)

- **`gemini-2.0-flash` deprecated for new users.** Use `gemini-2.0-flash-001` (stable
  versioned) or preferably `gemini-2.5-flash` (current best flash model).

- **`gemini-3-flash-preview` appeared to truncate — it was a missing config field.**
  Without `maxOutputTokens` set, the default is ~8192 tokens. Set it high and the API
  silently caps to the model's actual max. With `maxOutputTokens: 65536`, a 56-min
  session completed at 44,332 chars. Gemini 3 Flash is the *successor* to 2.5 Flash
  and slightly cleaner output (naturally drops filler words like "uh").

- **generateContent timeout: use 600s, not 300s.** For a 27-min audio (17MB MP3),
  Gemini transcription took >5 minutes. 300s timeout hits regularly.

- **Multipart upload format for File API:**
  ```python
  boundary = "wu_gemini_boundary"
  metadata = json.dumps({"file": {"display_name": audio_path.name}}).encode()
  body = (
      f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
      + metadata
      + f"\r\n--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n".encode()
      + audio_bytes
      + f"\r\n--{boundary}--".encode()
  )
  r = requests.post(
      "https://generativelanguage.googleapis.com/upload/v1beta/files"
      "?uploadType=multipart&key={api_key}",
      headers={"Content-Type": f"multipart/related; boundary={boundary}"},
      data=body,
      timeout=300,
  )
  ```

- **generateContent JSON uses camelCase `fileData`, not snake_case:**
  ```python
  {"fileData": {"mimeType": "audio/mpeg", "fileUri": file_uri}}
  ```

- **Poll URL:** `GET https://generativelanguage.googleapis.com/v1beta/{file_name}?key=...`
  where `file_name` is `"files/abc123"` (from upload response `file.name`).

- **Gemini 2.5 Flash quality:** Matches or beats Speechmatics for Buddhist/meditation
  transcription in direct comparison. Correctly identifies "Vipassana" where Speechmatics
  failed. ~62% cheaper than Speechmatics ($0.0015/min vs $0.004/min).

## Gemini Empty `parts` Response (Feb 2026)

- **Gemini returns `finishReason: STOP` with no `parts` key.** Response looks like
  `{'candidates': [{'content': {'role': 'model'}, 'finishReason': 'STOP'}]}` —
  `usageMetadata` shows prompt tokens consumed but zero completion tokens. Not a quota
  or rate limit issue; the model processes the audio but generates no text.

- **Affects specific audio files consistently.** Same files fail on Gemini 3 Flash
  and sometimes 2.5 Flash, but succeed on retry or with a different model. Not correlated
  with file size (failed on 14.6–45.7 MB). Likely a content-level issue (safety filter
  or model confusion on certain audio patterns).

- **Fallback chain that worked:**
  1. `gemini-3-flash` (default) — if empty `parts`, try:
  2. `gemini-2.5-flash` — fixed 6/8 failures. If still failing:
  3. Split audio into 15-min chunks (`ffmpeg -ss START -t 900`), transcribe each via
     OpenRouter (`or:gemini-3-flash`), concatenate with `"\n\n".join()`.

- **Split-and-concatenate recipe:**
  ```python
  # Split: ffmpeg -y -i input.mp3 -ss 0 -t 900 -q:a 5 chunk0.mp3
  #         ffmpeg -y -i input.mp3 -ss 900 -t 900 -q:a 5 chunk1.mp3 ...
  # Transcribe each chunk separately
  # Join: full_transcript = "\n\n".join(chunk_transcripts)
  ```
  Chunk boundaries may have minor discontinuities but acceptable for reference transcripts.

## OpenRouter Audio Transcription (Feb 2026)

- **OpenRouter supports audio input for Gemini models.** Use `input_audio` content type
  with base64-encoded audio. Model ID: `google/gemini-3-flash-preview`. System prompt
  and `max_tokens` work as expected.
  ```python
  {"type": "input_audio", "input_audio": {"data": audio_b64, "format": "mp3"}}
  ```

- **Truncates on large audio files (>20MB base64).** Returns `finish_reason: error` with
  partial transcript and zero token usage. On very large payloads (50MB+), Cloudflare
  returns 502 before the request reaches OpenRouter.

- **Use OpenRouter for audio <20MB only.** For larger files, use Gemini's File API
  (uploads binary separately, no base64 bloat in the JSON payload). Or split audio first.

- **`or:model-name` prefix pattern** in the wu CLI routes to OpenRouter. Maps short names
  to OpenRouter model IDs (e.g., `or:gemini-3-flash` → `google/gemini-3-flash-preview`).

## Gemini CLI for Audio (Feb 2026)

- **Gemini CLI can't directly process audio files.** Its `read_file` tool handles text/code
  but not binary audio. It works around this by shelling out to ffmpeg and Python scripts.

- **`--include-directories` flag** grants access to directories outside the project workspace.
  Without it, `read_file` errors with "Path not in workspace."

- **429 `MODEL_CAPACITY_EXHAUSTED`** on `gemini-3-flash-preview` via the CLI's `cloudcode-pa`
  endpoint. Different endpoint from the `generativelanguage.googleapis.com` API. Free tier
  and even paid plans hit capacity limits. `gemini-2.5-flash` usually has availability.

## Quality Verification Post-Batch

- **Short transcripts aren't always errors.** Guided meditations (mostly silence) and
  introduction sessions (1-2 min) produce legitimately short transcripts. Always cross-reference
  transcript length against audio duration before flagging.

- **Post-batch quality scan checklist:**
  - Transcripts <2000 chars → check audio duration (short session or truncated?)
  - Preamble text ("Sure, here's the transcript") → model didn't follow instructions
  - Timestamps in output → model ignored "no timestamps" instruction
  - `finish_reason: error` → truncated, needs retry

## gpt-4o-transcribe

- **Hard 1400-second (~23 min) audio duration limit.** Any session longer than 23 min
  returns HTTP 400 with `"audio duration X seconds is longer than 1400 seconds"`.
  Rules it out for most meditation sessions (typically 20-60 min).

- **`gpt-4o-transcribe` supports `prompt` field; `gpt-4o-mini-transcribe` does NOT.**
  The prompt is a short vocabulary hint (≤224 tokens for Whisper-based models; gpt-4o-
  transcribe may allow more but keep concise).

- **`openai` package must be explicitly installed** if you want `gpt-4o-transcribe` as
  an option in a pipeline. It's not in the default Speechmatics/requests stack.
