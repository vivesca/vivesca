#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-slugify",
# ]
# ///
"""
Archive web articles to Obsidian with local images.

Usage:
    python archive.py --url "https://example.com/article" --content "markdown content"
    python archive.py --url "https://example.com/article"  # fetches via Jina
"""

import argparse
import asyncio
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from slugify import slugify

ARCHIVE_DIR = Path.home() / "notes" / "Archive"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def get_headers_for_url(url: str) -> dict:
    """Get appropriate headers based on image URL domain."""
    headers = {"User-Agent": USER_AGENT}

    if "xhscdn.com" in url or "xiaohongshu.com" in url:
        headers["Referer"] = "https://www.xiaohongshu.com/"
    elif "mmbiz.qpic.cn" in url or "weixin.qq.com" in url:
        headers["Referer"] = "https://mp.weixin.qq.com/"

    return headers


def extract_image_urls(content: str) -> list[tuple[str, str]]:
    """Extract image URLs from markdown. Returns list of (full_match, url)."""
    patterns = [
        # Standard markdown: ![alt](url)
        (r"!\[[^\]]*\]\(([^)]+)\)", 1),
        # HTML img tags: <img src="url">
        (r'<img[^>]+src=["\']([^"\']+)["\']', 1),
    ]

    results = []
    seen_urls = set()

    for pattern, group in patterns:
        for match in re.finditer(pattern, content):
            url = match.group(group)
            # Skip data URIs and local paths
            if url.startswith(("data:", "./", "/", "images/")):
                continue
            if url not in seen_urls:
                seen_urls.add(url)
                results.append((match.group(0), url))

    return results


def extract_title(content: str) -> str | None:
    """Extract title from markdown content."""
    # Skip YAML frontmatter
    content_no_frontmatter = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Try Jina format first: "Title: xxx"
    match = re.search(r"^Title:\s*(.+)$", content_no_frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Try H1 markdown: "# Title"
    match = re.search(r"^#\s+(.+)$", content_no_frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Try underlined H1: "Title\n====="
    match = re.search(r"^(.+)\n=+\s*$", content_no_frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return None


def get_extension(url: str, content_type: str | None) -> str:
    """Determine file extension from URL or content-type."""
    # Try URL first
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"):
        return ext

    # Try content-type
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0])
        if guessed:
            return guessed

    # Default
    return ".jpg"


async def download_image(client: httpx.AsyncClient, url: str, dest: Path) -> bool:
    """Download an image to destination. Returns True on success."""
    try:
        headers = get_headers_for_url(url)
        response = await client.get(url, headers=headers, follow_redirects=True, timeout=30)
        response.raise_for_status()

        # Determine extension
        content_type = response.headers.get("content-type")
        ext = get_extension(url, content_type)

        # Update destination with correct extension
        dest = dest.with_suffix(ext)
        dest.write_bytes(response.content)

        return True, dest
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return False, None


async def archive_article(
    url: str,
    content: str,
    title: str | None = None,
) -> Path:
    """Archive article with local images. Returns path to saved file."""

    # Extract or use provided title
    if not title:
        title = extract_title(content)
    if not title:
        # Fallback: use URL path
        title = urlparse(url).path.split("/")[-1] or "untitled"

    # Create output directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title, max_length=50)
    output_dir = ARCHIVE_DIR / f"{date_str}_{slug}"
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Extract and download images
    image_matches = extract_image_urls(content)

    if image_matches:
        print(f"Downloading {len(image_matches)} images...")

        async with httpx.AsyncClient() as client:
            for i, (full_match, img_url) in enumerate(image_matches, 1):
                img_name = f"img_{i:02d}"
                img_dest = images_dir / img_name

                success, final_path = await download_image(client, img_url, img_dest)

                if success and final_path:
                    # Replace URL with local path
                    relative_path = f"./images/{final_path.name}"
                    if full_match.startswith("!"):
                        # Markdown image
                        new_match = re.sub(r"\([^)]+\)", f"({relative_path})", full_match)
                    else:
                        # HTML img
                        new_match = re.sub(
                            r'src=["\'][^"\']+["\']', f'src="{relative_path}"', full_match
                        )
                    content = content.replace(full_match, new_match)
                    print(f"  [{i}/{len(image_matches)}] Downloaded: {final_path.name}")

    # Build frontmatter
    now = datetime.now().astimezone()
    frontmatter = f"""---
title: "{title}"
source: "{url}"
archived: "{now.isoformat()}"
---

"""

    # Remove existing frontmatter if present
    content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Save content
    output_file = output_dir / "content.md"
    output_file.write_text(frontmatter + content)

    print(f"\nArchived to: {output_file}")
    return output_file


async def fetch_via_jina(url: str) -> str:
    """Fetch content using Jina Reader."""
    async with httpx.AsyncClient() as client:
        jina_url = f"https://r.jina.ai/{url}"
        response = await client.get(
            jina_url,
            headers={"Accept": "text/markdown", "User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=60,
        )
        response.raise_for_status()
        return response.text


async def main():
    parser = argparse.ArgumentParser(description="Archive web articles with local images")
    parser.add_argument("--url", required=True, help="Source URL of the article")
    parser.add_argument("--content", help="Markdown content (if not provided, fetches via Jina)")
    parser.add_argument("--title", help="Article title (extracted from content if not provided)")

    args = parser.parse_args()

    content = args.content
    if not content:
        print("Fetching content via Jina Reader...")
        content = await fetch_via_jina(args.url)

    await archive_article(args.url, content, args.title)


if __name__ == "__main__":
    asyncio.run(main())
