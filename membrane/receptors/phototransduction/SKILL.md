---
name: phototransduction
description: Reconstruct documents from photos as structured markdown. Use when user shares photos of slides, papers, or screens and wants them captured as text. "OCR this", "reconstruct from photos", "transcribe these slides", "photo to markdown".
triggers:
  - photos of documents
  - OCR
  - reconstruct from photos
  - transcribe slides
  - photo to markdown
  - document from camera
tools: [rhodopsin.py, Read, Write, Bash, Edit]
epistemics: []
---

# Phototransduction

Convert photos of documents (slides, papers, screens) into structured markdown with frontmatter.

Biology: phototransduction converts absorbed photons into molecular signals. Here: photos → structured internal text.

## When to use

- User took photos of a presentation, Word doc, or screen
- User wants document content captured as searchable, linkable markdown
- User says "OCR", "reconstruct", "transcribe slides", "photo to markdown"

## Procedure

### 1. Acquire photos

```bash
# From macOS Photos by date
rhodopsin.py today
rhodopsin.py date 2026-04-18
rhodopsin.py recent 30

# Export as JPEG (handles HEIC conversion)
rhodopsin.py export UUID1 UUID2 UUID3...
```

If photos are on the local machine already (e.g., `/tmp/`), skip to step 2.

If accessing via SSH to Mac, use `rhodopsin.py` on the Mac side or AppleScript export.

### 2. Auto-rotate (CRITICAL)

**Always rotate images to correct orientation before reading.** This was the single biggest source of transcription errors — reading rotated text produces garbled output that looks plausible but is substantially wrong.

```bash
# On macOS: sips auto-rotates based on EXIF
sips --rotate 0 image.jpg  # applies EXIF rotation metadata

# Or detect and rotate explicitly
sips -g pixelWidth -g pixelHeight -g orientation image.jpg
# If orientation != 1, rotate:
sips --rotate 90 image.jpg   # or 180, 270 as needed

# On Linux (ImageMagick):
convert image.jpg -auto-orient image_rotated.jpg

# Batch rotate all:
for f in *.jpg; do convert "$f" -auto-orient "$f"; done
```

### 3. Identify document boundaries

Photos may cover multiple documents. Before reading, scan all images to identify clusters:

- Check timestamps — bursts with gaps indicate different documents
- Check visual style — different templates, orientations, or formats
- Note page numbers if visible (e.g., "p 3 of 7")

Group photos by document. Process each document separately.

### 4. Read and reconstruct

Read images in order. For each page:

1. Read the image with the Read tool
2. Transcribe ALL visible text — don't paraphrase or summarize
3. Preserve structure: headings, bullets, tables, numbered lists
4. Note anything unclear with `[?]` markers
5. If text is dense or hard to read, flag for Apple OCR verification

**Key lesson:** Dense rotated text is where errors concentrate. If photos were taken at an angle or the document was displayed sideways on screen, even after rotation the text quality may be poor. Flag these pages for user verification via Apple Live Text (camera OCR on iPhone/iPad is more accurate than model vision on rotated photos).

### 5. Structure as markdown

Write the reconstructed document with frontmatter:

```markdown
---
title: "Document Title (reconstruction)"
date: YYYY-MM-DD
type: deliverable|reference
author: Original Author
source: Photos taken YYYY-MM-DD HH:MM TZ
original_format: Word document|PowerPoint deck, N pages/slides
status: reconstructed
pii: false
tags: [relevant, tags]
---

# Document Title

[reconstructed content]

---

**Related:**
- [[linked-document-1]] — relationship
- [[linked-document-2]] — relationship
```

### 6. Verify with Apple OCR

For any page where confidence is low (rotated text, dense paragraphs, small fonts):

1. Ask the user to open the photo on their iPhone/iPad
2. Use Apple Live Text (long-press on text in Photos app) to copy the text
3. User pastes the OCR text into the conversation
4. Compare against reconstruction and fix discrepancies

**This step is not optional for dense text pages.** Model vision on rotated/angled photos produces plausible but wrong text — errors that look like bad writing rather than bad OCR.

### 7. Save and interlink

- Save to `~/epigenome/chromatin/immunity/` (private, not public)
- Add frontmatter with source provenance
- Add `**Related:**` wikilinks to connected documents
- Commit to epigenome repo and push

## Anti-patterns (learned 2026-04-18)

1. **Never read rotated images without rotating first.** The model produces fluent-sounding but wrong text. "Phishing is a single system" was actually "What is missing is the operating model."

2. **Never assume transcription errors are the author's writing problems.** Review comments based on bad OCR waste everyone's time. Verify before critiquing.

3. **Never substitute numbers from other sources.** "86 in pilot, 1,319 in ideation" came from a different document — the actual text said "66 in pilot, 162 in POC." Keep transcription and analysis separate.

4. **Check for missing pages.** Count page numbers if visible. Compare photo count vs page count. One index off = one missing page.

5. **Duplicate photos of the same page exist.** Different angles, zoom levels. Don't double-count as separate pages.

## CLI enhancement needed

`rhodopsin.py export` should auto-rotate based on EXIF orientation. Currently it converts HEIC→JPEG but doesn't fix rotation. Add `sips --rotate 0` (which applies EXIF metadata) after conversion.
