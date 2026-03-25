---
name: sag
description: ElevenLabs text-to-speech with mac-style say UX. Use when user wants spoken audio output or TTS.
user_invocable: false
github_url: https://github.com/steipete/sag
---

# sag

ElevenLabs TTS CLI with local playback.

## Prerequisites

- `sag` CLI installed: `brew install steipete/tap/sag`
- `ELEVENLABS_API_KEY` environment variable set

## Commands

### Basic Speech

```bash
sag "Hello there"
sag speak -v "Roger" "Hello"
```

### List Voices

```bash
sag voices
```

### Model Selection

```bash
# Default: eleven_v3 (expressive)
sag "Text"

# Stable multilingual
sag "Text" --model eleven_multilingual_v2

# Fast
sag "Text" --model eleven_flash_v2_5
```

## Pronunciation & Delivery

- Respell for clarity: "key-note" instead of "keynote"
- Add hyphens for compound words
- Use `--normalize auto` for numbers/units/URLs
- Use `--lang en|de|fr|...` for language bias

### v3 Audio Tags

Put at entrance of a line:
- `[whispers]`, `[shouts]`, `[sings]`
- `[laughs]`, `[starts laughing]`, `[sighs]`, `[exhales]`
- `[sarcastic]`, `[curious]`, `[excited]`, `[crying]`, `[mischievously]`

### Pauses (v3)

SSML `<break>` not supported in v3. Use:
- `[pause]`
- `[short pause]`
- `[long pause]`

### Example

```bash
sag "[whispers] keep this quiet. [short pause] ok?"
```

## Prompting Tips

```bash
sag prompting  # Model-specific tips
```
