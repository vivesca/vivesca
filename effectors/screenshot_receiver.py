#!/usr/bin/env python3
"""
Minimal webhook endpoint for receiving iPhone screenshots via iOS Shortcuts.

Receives multipart POST uploads, saves with rotation (keeps last 5),
serves the latest via GET.

Run:
    uv run --with fastapi --with uvicorn --with python-multipart \
        python3 ~/germline/effectors/screenshot_receiver.py

Endpoints:
    POST /screenshot  - Upload a screenshot (multipart form, field: "file")
    GET  /latest      - Serve the most recent screenshot
    GET  /list        - List all stored screenshots (JSON)
    GET  /health      - Health check
"""

import shutil
import time
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse

STORAGE_DIR = Path("/tmp/screenshots")
STORAGE_DIR.mkdir(exist_ok=True)
MAX_SCREENSHOTS = 5
LATEST_SYMLINK = STORAGE_DIR / "latest.png"

app = FastAPI(title="Screenshot Receiver")


def _rotate() -> None:
    """Keep only the newest MAX_SCREENSHOTS files."""
    files = sorted(STORAGE_DIR.glob("screenshot_*.png"), key=lambda p: p.stat().st_mtime)
    while len(files) > MAX_SCREENSHOTS:
        files.pop(0).unlink()


def _update_symlink(target: Path) -> None:
    """Point the 'latest' symlink at the newest file."""
    if LATEST_SYMLINK.is_symlink() or LATEST_SYMLINK.exists():
        LATEST_SYMLINK.unlink()
    LATEST_SYMLINK.symlink_to(target)


@app.post("/screenshot")
async def upload_screenshot(file: UploadFile = File(...)):
    timestamp = int(time.time() * 1000)
    filename = f"screenshot_{timestamp}.png"
    filepath = STORAGE_DIR / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    _rotate()
    _update_symlink(filepath)

    return JSONResponse(
        {
            "status": "ok",
            "filename": filename,
            "path": str(filepath),
            "size_bytes": filepath.stat().st_size,
        }
    )


@app.get("/latest")
async def get_latest():
    if not LATEST_SYMLINK.exists():
        return JSONResponse({"error": "no screenshots yet"}, status_code=404)
    return FileResponse(
        LATEST_SYMLINK,
        media_type="image/png",
        filename="latest.png",
    )


@app.get("/list")
async def list_screenshots():
    files = sorted(STORAGE_DIR.glob("screenshot_*.png"), key=lambda p: p.stat().st_mtime)
    return JSONResponse(
        {
            "count": len(files),
            "files": [{"name": f.name, "size_bytes": f.stat().st_size} for f in files],
        }
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7755)
