---
name: pdf-extract
description: Extract text from PDFs with OCR fallback. Use when the user needs PDF text or OCR from scanned documents.
user_invocable: true
---

# PDF Extract

Extract text from PDFs, including large and image-based (scanned) documents.

## When to Use

- PDF too large to read directly (>20MB)
- Image-based/scanned PDFs that need OCR
- Salary guides, reports, research papers
- Any PDF where standard tools fail

## Usage

```
/pdf-extract <path-or-url> [--local]
```

Examples:
```
/pdf-extract /tmp/salary_guide.pdf
/pdf-extract https://example.com/report.pdf
/pdf-extract document.pdf --local   # Force local OCR, skip API
```

## How It Works

1. **Try LlamaParse first** (cloud API) — best quality, handles tables well
2. **Try pymupdf4llm** (local) — fast, good for text-based PDFs
3. **Fall back to local OCR** — PyMuPDF + pytesseract for image-based PDFs
4. **Output to file** — saves to `/tmp/<filename>.md`

## Quality Comparison (tested on 46MB salary guide)

| Method | Output | Table Quality | Speed |
|--------|--------|---------------|-------|
| LlamaParse | 189K chars | Proper markdown tables | ~30s |
| Local OCR | 140K chars | Plain text, some errors | ~2min |

LlamaParse is significantly better for structured documents with tables.

## Implementation

Script: `pdf_extract.py` in this directory.

```bash
uv run ~/skills/pdf-extract/pdf_extract.py <pdf-path-or-url> [output-path] [--local]
```

## API Key

LlamaParse requires an API key. Set the environment variable:
```bash
export LLAMA_CLOUD_API_KEY=your-key-here
```

Without the API key, the script falls back to local extraction (pymupdf4llm → OCR).

Free tier: 1000 pages/day. Get key at https://cloud.llamaindex.ai

## Requirements

For local fallback (OCR):
- **tesseract**: `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Ubuntu)

All Python deps handled by `uv run` inline metadata.

## Output

- Markdown file at `/tmp/<original-filename>.md`
- Or specify custom output path as second argument

## Notes

- LlamaParse handles tables, forms, and structured docs very well
- Use `--local` flag to skip API and force local processing
- Local OCR is slower but works offline and doesn't use API credits
