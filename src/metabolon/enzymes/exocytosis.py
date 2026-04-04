"""exocytosis — publish to terryli.hm garden.

Tools:
  exocytosis -- create a new post in secretome
  exocytosis_push -- sync secretome to Astro and deploy
"""

import subprocess
from pathlib import Path

from fastmcp.tools.function_tool import tool

SECRETOME = Path.home() / "epigenome" / "chromatin" / "secretome"
PUBLISH = Path.home() / "germline" / "effectors" / "publish"


@tool()
async def exocytosis(title: str, content: str, tags: str = "", description: str = "") -> str:
    """Create a new blog post in secretome. Does NOT deploy -- call exocytosis_push after.

    Args:
        title: Post title
        content: Post body (markdown, no frontmatter)
        tags: Comma-separated tags (e.g. "banking, ai-governance")
        description: One-line description for SEO/social
    """
    import re
    from datetime import UTC, datetime

    slug = re.sub(r"[^a-z0-9\s\-_]", "", title.lower())
    slug = re.sub(r"[\s\-_]+", "-", slug).strip("-")
    path = SECRETOME / f"{slug}.md"

    if path.exists():
        return f"Post already exists: {path}"

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    tag_str = "[" + ", ".join(tag_list) + "]" if tag_list else "[]"

    frontmatter = (
        f'---\ntitle: "{title}"\n'
        f'description: "{description}"\n'
        f"publishDate: {now}\n"
        f"draft: false\n"
        f"tags: {tag_str}\n"
        f"---\n\n"
    )

    SECRETOME.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter + content + "\n")
    return f"Created {path.name} ({len(content.split())} words). Call exocytosis_push to deploy."


@tool()
async def exocytosis_push() -> str:
    """Sync all new/updated posts from secretome to Astro repo, commit, and push to deploy."""
    result = subprocess.run(
        [str(PUBLISH), "push"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return f"Push failed: {output}"
    return output or "Nothing to sync"
