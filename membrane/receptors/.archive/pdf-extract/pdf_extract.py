from __future__ import annotations

# /// script
# dependencies = ["llama-parse", "pymupdf4llm", "pymupdf", "pytesseract", "pillow"]
# ///

"""
PDF Extract - Extract text from PDFs including large/image-based documents.

Usage:
    uv run pdf_extract.py <pdf-path-or-url> [output-path] [--local]

Options:
    --local    Force local OCR instead of LlamaParse API

Examples:
    uv run pdf_extract.py /tmp/salary_guide.pdf
    uv run pdf_extract.py https://example.com/report.pdf
    uv run pdf_extract.py document.pdf --local
"""

import os
import sys
import tempfile
import urllib.parse
import urllib.request

# LlamaParse API key - get from https://cloud.llamaindex.ai
# Set LLAMA_CLOUD_API_KEY env var to enable cloud parsing
LLAMA_PARSE_API_KEY = os.environ.get("LLAMA_CLOUD_API_KEY")


def download_if_url(source):
    """Download PDF if source is a URL, return local path."""
    if source.startswith(("http://", "https://")):
        print("Downloading from URL...")
        filename = os.path.basename(source.split("?")[0]) or "document.pdf"
        filename = urllib.parse.unquote(filename) if "%" in filename else filename
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        local_path = os.path.join(tempfile.gettempdir(), filename)
        urllib.request.urlretrieve(source, local_path)
        print(f"Downloaded to: {local_path}")
        return local_path
    return source


def extract_with_llamaparse(pdf_path):
    """Extract using LlamaParse cloud API."""
    try:
        from llama_parse import LlamaParse

        parser = LlamaParse(api_key=LLAMA_PARSE_API_KEY, result_type="markdown", verbose=True)

        print("Uploading to LlamaParse...")
        documents = parser.load_data(pdf_path)

        # Combine all document chunks
        full_text = "\n\n".join([doc.text for doc in documents])
        return full_text
    except Exception as e:
        print(f"LlamaParse failed: {e}")
        return None


def extract_with_pymupdf4llm(pdf_path):
    """Try fast local extraction with pymupdf4llm."""
    try:
        import pymupdf4llm

        md_text = pymupdf4llm.to_markdown(pdf_path)
        return md_text
    except Exception as e:
        print(f"pymupdf4llm failed: {e}")
        return None


def extract_with_ocr(pdf_path):
    """Fall back to local OCR for image-based PDFs."""
    import io

    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image

    print("Using local OCR extraction...")
    doc = fitz.open(pdf_path)
    full_text = []
    total_pages = len(doc)

    print(f"Processing {total_pages} pages with OCR...")

    for page_num in range(total_pages):
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(img)
        full_text.append(f"--- Page {page_num + 1} ---\n{text}")

        if (page_num + 1) % 10 == 0 or page_num + 1 == total_pages:
            print(f"  Processed {page_num + 1}/{total_pages} pages...")

    doc.close()
    return "\n\n".join(full_text)


def is_extraction_valid(text, min_chars=500):
    """Check if extraction produced meaningful content."""
    if not text:
        return False
    cleaned = "".join(text.split())
    return len(cleaned) > min_chars


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run pdf_extract.py <pdf-path-or-url> [output-path] [--local]")
        print("\nOptions:")
        print("  --local    Force local OCR instead of LlamaParse API")
        print("\nExamples:")
        print("  uv run pdf_extract.py /tmp/salary_guide.pdf")
        print("  uv run pdf_extract.py https://example.com/report.pdf")
        print("  uv run pdf_extract.py document.pdf --local")
        sys.exit(1)

    # Parse arguments
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_local = "--local" in sys.argv

    source = args[0]
    pdf_path = download_if_url(source)

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"File size: {file_size_mb:.1f} MB")

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base_name = base_name.replace("%20", "_").replace(" ", "_")
    output_path = args[1] if len(args) > 1 else f"/tmp/{base_name}.md"

    print(f"Extracting: {pdf_path}")
    print(f"Output: {output_path}")

    text = None

    if not use_local and LLAMA_PARSE_API_KEY:
        # Try LlamaParse first (cloud API)
        print("\n[1/3] Trying LlamaParse (cloud API)...")
        text = extract_with_llamaparse(pdf_path)

        if is_extraction_valid(text):
            print("LlamaParse extraction successful.")
        else:
            print("LlamaParse extraction insufficient.")
            text = None

    if not text:
        # Try pymupdf4llm (fast local)
        print("\n[2/3] Trying pymupdf4llm (local)...")
        text = extract_with_pymupdf4llm(pdf_path)

        if is_extraction_valid(text):
            print("pymupdf4llm extraction successful.")
        else:
            print("pymupdf4llm extraction insufficient, PDF likely image-based.")
            text = None

    if not text:
        # Fall back to OCR (slow but reliable for images)
        print("\n[3/3] Falling back to local OCR...")
        text = extract_with_ocr(pdf_path)

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\n✓ Done! Output written to: {output_path}")
    print(f"  Total characters: {len(text):,}")

    preview = text[:500].replace("\n", " ")[:200]
    print(f"  Preview: {preview}...")


if __name__ == "__main__":
    main()
