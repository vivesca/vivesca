---
name: fingo
description: Rust CLI for AI image generation and editing via Gemini. Use when generating or editing images from the terminal.
user_invocable: true
disable-model-invocation: true
---

# fingo

Rust CLI for AI image generation and editing via Google Gemini / Nano Banana.

Crate: https://crates.io/crates/fingo
Repo: https://github.com/terry-li-hm/fingo
Source: ~/code/fingo

## Install

```bash
cargo install fingo
```

## Key management

```bash
fingo key save <api-key>     # saves to keychain: gemini-api-key-secrets / gemini
fingo key show               # prints masked key (first 8 + last 4)
```

Keychain service name: `gemini-api-key-secrets`

## Commands

```bash
# Text-to-image generation
fingo gen "a sunset over HK harbour" -o ~/Desktop/out.png

# Edit image with prompt
fingo edit input.jpg "add dramatic lighting" -o output.jpg

# Remove / inpaint
fingo remove input.jpg "remove the text overlay in the top left" -o clean.jpg

# List available image models
fingo models
```

## Default models

- **gen**: `gemini-2.0-flash-exp-image-generation`
- **edit / remove**: `nano-banana-pro-preview`

Override with `-m <model>`.

## Default output

`./fingo-out.jpg` in the current directory. Extension auto-corrects to match the response MIME type (e.g. `-o out.jpg` saves as `out.png` if the API returns PNG). The printed path is always the actual saved path — check that, not the flag you passed.

## API details

- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- Auth: `x-goog-api-key` header (NOT query param — key never appears in logs)
- Required config: `generationConfig: { responseModalities: ["image", "text"] }`
- Response field: `inlineData` (camelCase) — handled transparently by serde alias

## Gotchas

- **finishReason check**: API returns `finishReason` (not an error HTTP status) when generation is blocked (e.g. safety). fingo checks this and surfaces a clear error message.
- **Nano Banana excels at inpainting** — prompt-based removal works without a mask file. Describe the thing to remove and it handles it.
- **gemini-2.0-flash-exp-image-generation** is the gen model; nano-banana-pro-preview is the edit model. Don't mix them up.
- **`fingo models`** lists all image-capable models if you want to find alternatives.
- **Key in keychain account `"gemini"`** — not your username. This is intentional for portability.
- **Short API keys**: mask_api_key handles keys shorter than 12 chars gracefully (no overlap).
