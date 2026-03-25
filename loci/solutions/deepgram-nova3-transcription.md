# Deepgram Nova-3 Transcription

## SDK v5 is broken — use REST API

The `deepgram-sdk` v5.x completely restructured its API. `PrerecordedOptions` no longer exists as an import. The SDK exports hundreds of typed response objects but the client initialization signature changed too.

**Fix:** Skip the SDK entirely. The REST API is dead simple and stable:

```python
response = requests.post(
    "https://api.deepgram.com/v1/listen",
    params={"model": "nova-3", "language": "en", "smart_format": "true", "paragraphs": "true"},
    headers={"Authorization": f"Token {api_key}", "Content-Type": "audio/mpeg"},
    data=audio_data,
    timeout=300,
)
result = response.json()
transcript = result["results"]["channels"][0]["alternatives"][0]["paragraphs"]["transcript"]
```

## Keyterm prompting

Pass domain-specific vocabulary as repeated `keyterm` query params:

```python
keyterm_params = [("keyterm", term) for term in ["Vipassana", "Dzogchen", ...]]
requests.post(url, params=list(params.items()) + keyterm_params, ...)
```

- Max 500 tokens total across all keyterms
- Only works with Nova-3 English (not multilingual)
- Deepgram claims 625% improvement on domain-specific proper nouns

## Deepgram paragraphs vs manual post-processing

When `paragraphs=true`, Deepgram returns pre-structured text. Skip any manual paragraph-splitting heuristics — they'll create double-breaks. Only apply term corrections on top.

## Pricing (Feb 2026)

Nova-3: $0.0043/min (~$0.258/hr). $200 free credit on signup.

## Reference

Working implementation: `~/repos/waking-up-transcripts/download_and_transcribe.py`
