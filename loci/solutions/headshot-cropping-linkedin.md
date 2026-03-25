# Headshot Cropping for LinkedIn

## The Problem

LinkedIn displays profile photos as a square upload, shown as a circle. Cropping a portrait headshot to a square requires balancing face prominence, hair visibility, and professional context (suit/shoulders). The rule-of-thirds (eyes at 33%) is designed for rectangular frames and doesn't translate directly to circular crops.

## Council-Validated Guidelines (Feb 2026)

Source: `~/code/vivesca-terry/chromatin/Decisions/LLM Council - LinkedIn Photo Crop - 2026-02-15.md`

### Key Numbers

- **Eyes at 38% from top** (not 33% rule-of-thirds) — adapted for circular geometry
- **Face fills 39-49%** of frame depending on hair volume
- **Headroom above hair: 4-6%** of frame — just enough, no dead space
- **Shoulders/tie visible** in lower portion for professional context

### The Arc Problem

Styled hair needs clearance not just at 12 o'clock (top center) but at **10 and 2 o'clock positions** where the circle curves inward. This is the #1 cause of hair clipping that looks fine in the square but clips in the circle.

**Arc Test:** Preview the circular crop. If hair touches or clips at the 10/2 o'clock positions, zoom out until there's a small gap.

### The Core Tension

With voluminous/styled hair, you can't have both:
- Eyes at exactly 38%, AND
- Face filling 49%+

Hair volume forces a larger frame. Accept 39% face fill — the dark background corners get clipped by the circle, making the face appear larger than the percentage suggests.

### What NOT to Do

- Don't center the face vertically — loses shoulder context, looks like a selfie crop
- Don't chase the tie knot — at 100px circle in feeds, it's illegible pixels
- Don't follow rule-of-thirds strictly (33%) — it's for rectangular frames
- Don't lighten/edit the background gradient — scope creep

## Technical Setup

### MediaPipe Face Landmarker (Python)

```bash
uv pip install mediapipe opencv-python-headless
```

**API note (v0.10.32+):** Uses `mp.tasks` API, NOT the legacy `mp.solutions`. The old `mp.solutions.face_mesh` doesn't exist anymore.

```python
import mediapipe as mp

# Download model (one-time, ~3.7MB)
model_path = '/tmp/face_landmarker_v2_with_blendshapes.task'
urllib.request.urlretrieve(
    'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
    model_path
)

# Detect
options = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
    running_mode=mp.tasks.vision.RunningMode.IMAGE,
    num_faces=1
)
with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
    mp_image = mp.Image.create_from_file('photo.jpg')
    result = landmarker.detect(mp_image)
    landmarks = result.face_landmarks[0]  # 478 landmarks
```

### Key Landmarks

- `landmarks[10]` — forehead top
- `landmarks[152]` — chin bottom
- `landmarks[33]` — left eye outer
- `landmarks[263]` — right eye outer
- `min(ys)` / `max(ys)` — face mesh bounding box (does NOT include hair)

### Hair Allowance

MediaPipe mesh stops at the forehead — hair must be estimated:
- **Normal hair:** 35% of face_height above forehead
- **Styled/voluminous hair:** 55% of face_height above forehead
- Always verify visually — hair volume varies significantly

### Crop Calculation

```python
eye_y = (landmarks[33].y + landmarks[263].y) / 2 * h
hair_top = face_top - face_height * 0.55  # styled hair

# Solve for crop_size: eyes at 38%, hair visible with 120px buffer
crop_size = int((eye_y - hair_top + 120) / 0.38)
crop_y = int(eye_y - crop_size * 0.38)
crop_x = int(face_center_x - crop_size / 2)
```

### Circle Preview

Generate a circular preview to verify before uploading:

```python
from PIL import Image, ImageDraw
mask = Image.new('L', (800, 800), 0)
ImageDraw.Draw(mask).ellipse((0, 0, 799, 799), fill=255)
circle = Image.new('RGB', (800, 800), (255, 255, 255))
circle.paste(resized, mask=mask)
circle.resize((200, 200)).save('circle-preview.jpg')
```

## Lesson Learned

Don't guess pixel coordinates for face positioning — measure with face detection first, crop once. Manual estimation was consistently off by 400-680px, causing 6 failed iterations before we switched to MediaPipe.

## Output Specs for LinkedIn

- **Upload:** 1000x1000px JPEG, quality 92 (under 8MB limit, ~180KB)
- **Full res archive:** Keep at native resolution for future re-crops
- **Format:** JPEG (not PNG — smaller file, LinkedIn compresses anyway)

## Files

- Source headshots: `~/code/vivesca-terry/chromatin/assets/headshots/`
- Council transcript: `~/code/vivesca-terry/chromatin/Decisions/LLM Council - LinkedIn Photo Crop - 2026-02-15.md`
