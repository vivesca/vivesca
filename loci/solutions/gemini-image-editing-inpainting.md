# Gemini Image Editing / Nano Banana Inpainting

## What it is
Nano Banana is Google's image editing model, available via the Gemini API.
Great for text removal, object removal, and inpainting.

## Keychain
```bash
security find-generic-password -s "gemini-api-key-secrets" -w
```

## Available models (as of Mar 2026)
- `nano-banana-pro-preview` — best quality inpainting (used for text removal)
- `gemini-2.0-flash-exp-image-generation` — image generation
- `gemini-2.5-flash-image` — flash image model
- `gemini-3.1-flash-image-preview` — latest flash image preview

## Working Python snippet — text/object removal

```python
import urllib.request, json, base64

key = "YOUR_KEY"  # security find-generic-password -s "gemini-api-key-secrets" -w

with open('input.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "contents": [{"parts": [
        {"text": "Remove the bold white text 'FOCUS.' from the top of this image. Keep everything else exactly the same."},
        {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
    ]}],
    "generationConfig": {"responseModalities": ["image", "text"]}
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/nano-banana-pro-preview:generateContent?key={key}"
req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())

for part in result['candidates'][0]['content']['parts']:
    data = part.get('inlineData') or part.get('inline_data')  # API returns camelCase
    if data:
        with open('output.jpg', 'wb') as f:
            f.write(base64.b64decode(data['data']))
        break
```

## Gotchas
- Response uses `inlineData` (camelCase), not `inline_data` — check both
- `responseModalities: ["image", "text"]` required to get image output
- Model listing: `GET /v1beta/models?key=KEY`

## YouTube thumbnail workflow
1. `curl -o thumb.jpg "https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg"`
2. Call nano-banana-pro-preview with removal prompt
3. `scp result.jpg terry@100.111.84.117:~/Downloads/` (M3 via Tailscale)
