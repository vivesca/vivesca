"""garden — blog publishing pipeline (formerly sarcio).

Endosymbiosis: Rust binary -> Python organelle.
Manages Markdown posts in ~/epigenome/chromatin/Garden Posts/.
Syncs to terryli.hm via ~/code/blog/sync-from-vault.sh.
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

VAULT_DIR = Path.home() / "epigenome" / "chromatin" / "Garden Posts"
INDEX_PATH = Path.home() / "epigenome" / "chromatin" / "terryli.hm.md"
SYNC_SCRIPT = Path.home() / "code" / "blog" / "sync-from-vault.sh"
BASE_URL = "https://terryli.hm/posts"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _to_slug(title: str) -> str:
    slug = ""
    for c in title.lower():
        if c.isascii() and c.isalnum():
            slug += c
        elif c in (" ", "-", "_"):
            if not slug.endswith("-"):
                slug += "-"
    return slug.rstrip("-")


def _parse_frontmatter(content: str) -> tuple[dict, str] | None:
    """Parse YAML frontmatter. Returns (frontmatter_dict, body) or None."""
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---\n", 4)
    if end == -1:
        return None
    fm_str = content[4:end]
    body = content[end + 5:]
    fm = yaml.safe_load(fm_str)
    return fm, body


def _write_frontmatter(fm: dict, body: str) -> str:
    """Serialize frontmatter + body back to string."""
    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm_str}---\n{body}"


def scan_content(content: str) -> list[str]:
    """Content guardrails — scan for sensitive data before publishing."""
    warnings = []

    financial_patterns = [
        (r"\$[0-9]", "exact dollar figure"),
        (r"HKD\s*[0-9]", "exact HKD figure"),
        (r"[0-9]+\s*million\b", "exact million figure"),
        (r"[0-9]+\s*billion\b", "exact billion figure"),
        (r"[0-9]+%\s+(margin|profit|revenue|salary|budget)", "exact percentage with financial context"),
    ]
    for pat, label in financial_patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            snippet = content[m.start():min(m.end() + 30, len(content))].strip()
            warnings.append(f"[sensitive] {label} -- \"{snippet}...\"")

    name_re = re.compile(r"(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][a-z]+")
    m = name_re.search(content)
    if m:
        snippet = content[m.start():min(m.end() + 20, len(content))].strip()
        warnings.append(f'[sensitive] named individual -- "{snippet}"')

    cred_re = re.compile(
        r'(?i)(password|api.?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9+/=_\-]{8,}'
    )
    if cred_re.search(content):
        warnings.append("[sensitive] possible credential value in content")

    offensive = ["fuck", "shit", "cunt", "asshole", "nigger", "faggot"]
    lower = content.lower()
    for word in offensive:
        if word in lower:
            warnings.append(f'[offensive] word "{word}" found')

    return warnings


def new(title: str) -> tuple[str, Path]:
    """Create a new draft post. Returns (slug, path)."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    slug = _to_slug(title)
    path = VAULT_DIR / f"{slug}.md"
    if path.exists():
        raise ValueError(f"File already exists: {path}")

    fm = {
        "title": title,
        "description": "",
        "pubDatetime": _now_iso(),
        "draft": True,
        "tags": [],
    }
    content = _write_frontmatter(fm, "\n")
    path.write_text(content)
    return slug, path


def publish(slug: str, force: bool = False) -> str:
    """Publish a draft post. Returns the title. Raises on guardrail warnings unless force=True."""
    path = VAULT_DIR / f"{slug}.md"
    if not path.exists():
        raise ValueError(f"No post found: {slug}.md")

    content = path.read_text()
    parsed = _parse_frontmatter(content)
    if not parsed:
        raise ValueError("Failed to parse frontmatter")

    fm, body = parsed
    if not fm.get("draft", False):
        return fm.get("title", slug)

    warnings = scan_content(content)
    if warnings and not force:
        raise ValueError(
            "Content scan warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
        )

    fm["draft"] = False
    path.write_text(_write_frontmatter(fm, body))
    return fm.get("title", slug)


def revise(slug: str, note: str) -> str:
    """Update modDatetime and revisionNote. Returns title."""
    path = VAULT_DIR / f"{slug}.md"
    if not path.exists():
        raise ValueError(f"No post found: {slug}.md")

    content = path.read_text()
    parsed = _parse_frontmatter(content)
    if not parsed:
        raise ValueError("Failed to parse frontmatter")

    fm, body = parsed
    fm["modDatetime"] = _now_iso()
    fm["revisionNote"] = note
    path.write_text(_write_frontmatter(fm, body))
    return fm.get("title", slug)


def list_posts() -> list[dict]:
    """List all posts with metadata."""
    posts = []
    if not VAULT_DIR.exists():
        return posts

    for path in sorted(VAULT_DIR.glob("*.md")):
        content = path.read_text()
        parsed = _parse_frontmatter(content)
        if not parsed:
            continue
        fm, body = parsed
        posts.append({
            "slug": path.stem,
            "title": fm.get("title", path.stem),
            "pubDatetime": str(fm.get("pubDatetime", "")),
            "draft": fm.get("draft", False),
            "tags": fm.get("tags") or [],
            "words": len(body.split()),
        })

    posts.sort(key=lambda p: p["pubDatetime"], reverse=True)
    return posts


def push() -> str:
    """Run sync script to publish to terryli.hm."""
    if not SYNC_SCRIPT.exists():
        raise ValueError(f"Sync script not found: {SYNC_SCRIPT}")

    r = subprocess.run(
        ["bash", str(SYNC_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise ValueError(f"Sync failed: {r.stderr.strip()}")
    return "Live at https://terryli.hm"


def index() -> int:
    """Regenerate garden index. Returns post count."""
    posts = []
    if VAULT_DIR.exists():
        for path in VAULT_DIR.glob("*.md"):
            content = path.read_text()
            parsed = _parse_frontmatter(content)
            if not parsed:
                continue
            fm, _ = parsed
            if fm.get("draft", False):
                continue
            posts.append({
                "slug": path.stem,
                "title": fm.get("title", path.stem),
                "pubDatetime": fm.get("pubDatetime", ""),
                "tags": fm.get("tags", []),
            })

    posts.sort(key=lambda p: p["pubDatetime"], reverse=True)
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

    for p in posts:
        date = p["pubDatetime"].split("T")[0] if p["pubDatetime"] else "--"
        tags = p.get("tags", [])
        tag_str = "  " + ", ".join(f"`{t}`" for t in tags[:3]) if tags else ""
        wikilink = f"[[Writing/Blog/Published/{p['slug']}|{p['title']}]]"
        lines.append(f"- {date} -- {wikilink}{tag_str}")

    lines.append("")
    lines.append("## By topic")
    lines.append("")

    groups: dict[str, list[dict]] = {}
    for p in posts:
        for tag in p.get("tags", []):
            groups.setdefault(tag, []).append(p)

    for tag in sorted(groups):
        lines.append(f"### {tag}")
        for p in sorted(groups[tag], key=lambda x: x["pubDatetime"], reverse=True):
            lines.append(f"- [[Writing/Blog/Published/{p['slug']}|{p['title']}]]")
        lines.append("")

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(lines) + "\n")
    return len(posts)


def _cli() -> None:
    """CLI entry point (drop-in replacement for Rust sarcio)."""
    import argparse

    parser = argparse.ArgumentParser(prog="sarcio", description="Garden CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list")
    p_new = sub.add_parser("new")
    p_new.add_argument("title")
    p_pub = sub.add_parser("publish")
    p_pub.add_argument("slug")
    p_pub.add_argument("--push", action="store_true")
    p_rev = sub.add_parser("revise")
    p_rev.add_argument("slug")
    p_rev.add_argument("--note", required=True)
    sub.add_parser("index")
    sub.add_parser("push")

    args = parser.parse_args()

    if args.cmd == "new":
        slug, path = new(args.title)
        print(f"Created {path} (draft)")
    elif args.cmd == "list":
        for p in list_posts():
            draft = "(draft)" if p["draft"] else ""
            date = p["pubDatetime"].split("T")[0] if p["pubDatetime"] else "--"
            print(f"{p['slug']:30s} {p['title'][:40]:40s} {date:12s} {draft:8s} {p['words']}w")
    elif args.cmd == "publish":
        title = publish(args.slug, force=True)
        print(f"Published: {title}")
        if args.push:
            print(push())
    elif args.cmd == "revise":
        title = revise(args.slug, args.note)
        print(f"Revised: {title} -- {args.note}")
    elif args.cmd == "index":
        count = index()
        print(f"Index updated -- {count} posts")
    elif args.cmd == "push":
        print(push())
    else:
        parser.print_help()
