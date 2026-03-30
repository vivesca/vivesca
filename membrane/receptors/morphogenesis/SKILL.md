---
name: morphogenesis
description: Generate images via Gemini image models (Nano Banana Pro, Imagen). "generate image", "draw"
user_invocable: true
triggers:
  - morphogenesis
  - generate image
  - draw me
  - nano banana
  - imagen
  - coloring page
context: fork
epistemics: [create]
model: sonnet
---

# morphogenesis -- image generation via Gemini

Generate images using Google's Gemini image models. Template → form.

## Available models

| Model ID | Name | Best for |
|---|---|---|
| `nano-banana-pro-preview` | Nano Banana Pro | General image gen + editing, highest quality |
| `gemini-2.5-flash-image` | Flash Image | Fast drafts, cheaper |
| `gemini-3.1-flash-image-preview` | Flash 3.1 Image | Newer flash variant |
| `imagen-4.0-generate-001` | Imagen 4.0 | Photo-realistic |
| `imagen-4.0-ultra-generate-001` | Imagen 4.0 Ultra | Highest quality photo |
| `imagen-4.0-fast-generate-001` | Imagen 4.0 Fast | Quick photo gen |

Default: `nano-banana-pro-preview` (best all-round).

## Generation pattern

```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY") or os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="nano-banana-pro-preview",
    contents=PROMPT,
    config=types.GenerateContentConfig(
        response_modalities=["image", "text"],
    )
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        with open(OUTPUT_PATH, "wb") as f:
            f.write(part.inline_data.data)
```

## Requires

- `google-genai` Python package (`pip3 install google-genai`)
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` env var

## Workflow

1. Clarify what the user wants (subject, style, purpose).
2. Craft a detailed prompt — style, composition, color constraints, format.
3. Generate 2-4 variations with different prompts.
4. Show all to user via `Read` tool, let them pick.
5. Save final to `~/Desktop/` for immediate use.
6. Archive to chromatin if the user wants to keep it.

## Prompt tips

- **Coloring pages:** "Black and white line art only, no shading, no grey tones, pure white background, bold outlines, large enclosed areas"
- **Age-appropriate:** Specify target age for complexity level
- **No text in image:** Gemini struggles with text rendering — add text separately
- **Aspect ratio:** Specify "portrait" or "landscape" and paper size
- **Style keywords:** kawaii, photorealistic, watercolor, pencil sketch, flat vector, isometric
