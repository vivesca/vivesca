"""sporulation — garden publishing for terryli.hm (formerly publish CLI).

Endosymbiosis: Python script (vivesca/effectors/publish) → Python organelle.
The original script was a standalone CLI wrapping Astro's chromatin sync workflow.
This organelle exposes the same operations as direct Python functions, eliminating
the subprocess hop that emit_publish previously required.

Sporulation is the biological process of forming spores for dispersal — apt for
publishing garden posts into the world.

Core functions: new, list_posts, publish, revise, push, index.
"""

import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from metabolon.locus import blog_published, terryli_hm

PUBLISHED_DIR = blog_published
INDEX_PATH = terryli_hm
SYNC_SCRIPT = Path.home() / "code" / "blog" / "sync-from-chromatin.sh"


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _to_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9\s\-_]", "", title.lower())
    slug = re.sub(r"[\s\-_]+", "-", slug).strip("-")
    return slug


def _parse_frontmatter(content: str) -> dict | None:
    if not content.startswith("---\n"):
        return None
    try:
        end = content.index("---", 4)
    except ValueError:
        return None
    if end < 0:
        return None
    fm_text = content[4:end]
    fm: dict = {}
    for line in fm_text.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            if key.strip() == "tags":
                val = [
                    t.strip().strip('"').strip("'")
                    for t in val.strip("[]").split(",")
                    if t.strip()
                ]
            elif val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            fm[key.strip()] = val
    fm["_body_offset"] = end + 4  # after closing ---\n
    return fm


def _scan_content(content: str) -> list[str]:
    """Check for sensitive content before publishing."""
    warnings = []
    patterns = [
        (r"\$[0-9]", "exact dollar figure"),
        (r"HKD\s*[0-9]", "exact HKD figure"),
        (r"[0-9]+\s*million\b", "exact million figure"),
        (r"(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][a-z]+", "named individual"),
        (
            r'(?i)(password|api.?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9+/=_\-]{8,}',
            "possible credential",
        ),
    ]
    for pat, label in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            snippet = content[m.start() : m.end() + 30].strip()
            warnings.append(f'[sensitive] {label} -- "{snippet}..."')
    return warnings


def germinate_post(title: str) -> dict:
    """Create a new draft garden post with frontmatter scaffold.

    Args:
        title: Human-readable post title.

    Returns:
        {"path": "/abs/path/to/slug.md", "slug": "slug", "created": True}
        or {"error": "message"}
    """
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    slug = _to_slug(title)
    path = PUBLISHED_DIR / f"{slug}.md"
    if path.exists():
        return {"error": f"File already exists: {path}"}
    content = (
        f'---\ntitle: "{title}"\ndescription: ""\n'
        f"pubDatetime: {_now_iso()}\ndraft: true\ntags: []\n---\n\n"
    )
    path.write_text(content)
    return {"path": str(path), "slug": slug, "created": True}


def dormant_posts() -> list[dict]:
    """List all posts in the published directory.

    Returns:
        [{"slug": "...", "title": "...", "date": "YYYY-MM-DD", "draft": bool, "words": N}, ...]
    """
    if not PUBLISHED_DIR.exists():
        return []
    posts = []
    for p in sorted(PUBLISHED_DIR.glob("*.md")):
        content = p.read_text()
        fm = _parse_frontmatter(content)
        if not fm:
            continue
        body = content[fm.get("_body_offset", 0) :]
        words = len(body.split())
        slug = p.stem
        date = str(fm.get("pubDatetime", "")).split("T")[0]
        draft = bool(fm.get("draft"))
        title = fm.get("title", slug)
        posts.append({"slug": slug, "title": title, "date": date, "draft": draft, "words": words})
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def publish(slug: str, push: bool = False) -> dict:
    """Publish a draft post by setting draft: false.

    Args:
        slug: Post filename stem (without .md).
        push: If True, run sync script after publishing.

    Returns:
        {"published": True, "title": "...", "warnings": [...]}
        or {"error": "message"} or {"already_published": True}
    """
    path = PUBLISHED_DIR / f"{slug}.md"
    if not path.exists():
        return {"error": f"No post found: {slug}.md"}
    content = path.read_text()
    fm = _parse_frontmatter(content)
    if not fm:
        return {"error": "Failed to parse frontmatter"}
    if not fm.get("draft"):
        return {"already_published": True, "slug": slug}
    warnings = _scan_content(content)
    new_content = content.replace("draft: true", "draft: false")
    path.write_text(new_content)
    result: dict = {
        "published": True,
        "title": fm.get("title", slug),
        "slug": slug,
        "warnings": warnings,
    }
    if push:
        push_result = propagate_site()
        result["push"] = push_result
    return result


def mutate_post(slug: str, note: str) -> dict:
    """Record a revision note and update modDatetime on a post.

    Args:
        slug: Post filename stem.
        note: Short description of the revision.

    Returns:
        {"revised": True, "title": "...", "note": "..."} or {"error": "message"}
    """
    path = PUBLISHED_DIR / f"{slug}.md"
    if not path.exists():
        return {"error": f"No post found: {slug}.md"}
    content = path.read_text()
    fm = _parse_frontmatter(content)
    if not fm:
        return {"error": "Failed to parse frontmatter"}

    lines = content.splitlines()
    now = _now_iso()
    pub_idx = next((i for i, ln in enumerate(lines) if ln.startswith("pubDatetime:")), 0)
    note_idx = next((i for i, ln in enumerate(lines) if ln.startswith("revisionNote:")), None)

    if note_idx is not None:
        lines[note_idx] = f'revisionNote: "{note}"'
    else:
        lines.insert(pub_idx + 1, f'revisionNote: "{note}"')

    # Recalculate after possible insert
    mod_idx_new = next((i for i, ln in enumerate(lines) if ln.startswith("modDatetime:")), None)
    if mod_idx_new is not None:
        lines[mod_idx_new] = f"modDatetime: {now}"
    else:
        pub_idx_new = next((i for i, ln in enumerate(lines) if ln.startswith("pubDatetime:")), 0)
        lines.insert(pub_idx_new + 1, f"modDatetime: {now}")

    path.write_text("\n".join(lines) + "\n")
    return {"revised": True, "title": fm.get("title", slug), "slug": slug, "note": note}


def propagate_site() -> dict:
    """Run sync-from-chromatin.sh to deploy the Astro blog.

    Returns:
        {"pushed": True, "url": "https://terryli.hm"} or {"error": "message"}
    """
    if not SYNC_SCRIPT.exists():
        return {"error": f"Sync script not found: {SYNC_SCRIPT}"}
    result = subprocess.run(["bash", str(SYNC_SCRIPT)], capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip() or f"exit {result.returncode}"
        return {"error": f"Sync failed: {err}"}
    return {"pushed": True, "url": "https://terryli.hm"}


def catalog() -> dict:
    """Regenerate the terryli.hm.md garden index from published posts.

    Returns:
        {"indexed": N, "path": "/abs/path/to/terryli.hm.md"}
    """
    posts = []
    if PUBLISHED_DIR.exists():
        for p in sorted(PUBLISHED_DIR.glob("*.md")):
            content = p.read_text()
            fm = _parse_frontmatter(content)
            if not fm or fm.get("draft"):
                continue
            slug = p.stem
            title = fm.get("title", slug)
            pub = fm.get("pubDatetime", "")
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [tags] if tags else []
            date_str = str(pub).split("T")[0] if pub else ""
            if not pub or not fm.get("description"):
                continue  # skip invalid frontmatter
            posts.append((slug, title, date_str, tags))

    posts.sort(key=lambda x: x[2], reverse=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "---",
        "title: terryli.hm garden index",
        f"updated: {now_str}",
        "---",
        "",
        "# terryli.hm",
        "",
        f"Personal garden at [terryli.hm](https://terryli.hm). {len(posts)} posts.",
        f"*Auto-generated {now_str} -- do not edit manually.*",
        "",
        "## All posts (recent first)",
        "",
    ]
    for slug, title, date, tags in posts:
        tag_str = "  " + ", ".join(f"`{t}`" for t in tags[:3]) if tags else ""
        lines.append(f"- {date} -- [[Writing/Blog/Published/{slug}|{title}]]{tag_str}")
    lines.append("")
    lines.append("## By topic")
    lines.append("")
    groups: dict[str, list] = {}
    for slug, title, date, tags in posts:
        for tag in tags:
            groups.setdefault(tag, []).append((slug, title, date))
    for tag in sorted(groups):
        lines.append(f"### {tag}")
        for slug, title, _ in sorted(groups[tag], key=lambda x: x[2], reverse=True):
            lines.append(f"- [[Writing/Blog/Published/{slug}|{title}]]")
        lines.append("")

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(lines) + "\n")
    return {"indexed": len(posts), "path": str(INDEX_PATH)}
