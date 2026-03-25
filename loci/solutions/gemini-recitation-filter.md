# Gemini RECITATION Filter Behaviour

## What It Is

Gemini returns `finishReason: "RECITATION"` when it detects copyrighted content in the output (poems, sacred texts, song lyrics, etc.). The response has `content: {}` — no parts, no text.

## Key Findings

### Paid tier is STRICTER than free tier

- **Free tier (no billing):** ~6% RECITATION rate on Waking Up meditation transcripts
- **Paid tier (billing-enabled key):** ~75% RECITATION rate on the same content

This is counterintuitive — paying more gets you more blocking. Likely Google's liability posture: free tier has lower enforcement because there's no commercial relationship to protect.

### OpenRouter bypasses RECITATION entirely

OpenRouter's `google/gemini-3-flash-preview` passes through content that direct Gemini blocks. All 3 tested RECITATION failures transcribed successfully via OpenRouter. Likely because OpenRouter proxies the request without Google's safety layer, or uses different API settings.

### Detection in code

The response structure when blocked:
```json
{
  "candidates": [{
    "finishReason": "RECITATION",
    "content": {}
  }]
}
```

Must check `finishReason` BEFORE accessing `content.parts` — otherwise you get a cryptic `KeyError: 'parts'` that doesn't indicate the real problem.

## OpenRouter File Size Limit

OpenRouter consistently returns 500/502 on base64 audio payloads >~40MB (which is ~30MB pre-encoding). Not a concurrency issue — fails even at `-c 2`. These files must go through Deepgram `nova-3` or direct Gemini File API (but File API triggers RECITATION on copyrighted content — catch-22 for meditation audio).

## Routing Decision

- **Copyright-sensitive audio** (meditation, poetry, sacred texts): Use OpenRouter or Deepgram
- **Large files (>30MB MP3):** Deepgram `nova-3` is the only viable path for copyrighted content — OpenRouter 502s, direct Gemini blocks RECITATION
- **General content**: Gemini free tier is fine
- **Never use paid Gemini** for content likely to trigger RECITATION — worse results at higher cost

*Discovered: 2026-02-25, wu Phase 3 transcription batch*
