#!/usr/bin/env python3
"""Generate INDEX.md for docs/solutions/.

Categorizes files by subdirectory, extracts first meaningful line as description.
Run manually or via /monthly.
"""

import argparse
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SOLUTIONS = Path.home() / "docs" / "solutions"
INDEX = SOLUTIONS / "INDEX.md"


def extract_description(path: Path, max_len: int = 120) -> str:
    """Extract first non-heading, non-frontmatter line as description."""
    in_frontmatter = False
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter:
                    continue
                if not stripped or stripped.startswith("#"):
                    continue
                # Extract title from frontmatter-style lines
                if stripped.startswith("title:"):
                    return stripped[6:].strip().strip('"').strip("'")[:max_len]
                if stripped.startswith("module:") or stripped.startswith("category:"):
                    continue
                return stripped[:max_len]
    except (UnicodeDecodeError, PermissionError):
        pass
    return ""


def generate_index() -> str:
    """Generate markdown index content."""
    categories: dict[str, list[tuple[str, str, float, str]]] = defaultdict(list)

    for root, _dirs, files in os.walk(SOLUTIONS):
        for f in files:
            if not f.endswith(".md") or f == "INDEX.md" or f == "schema.md":
                continue
            full = Path(root) / f
            stat = full.stat()
            mtime = stat.st_mtime
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            rel = full.relative_to(SOLUTIONS)
            category = str(rel.parent) if rel.parent != Path(".") else "general"
            desc = extract_description(full)
            categories[category].append((str(rel), desc, mtime, date_str))

    lines = [
        "# Solutions KB Index",
        "",
        f"Auto-generated. {sum(len(v) for v in categories.values())} files across {len(categories)} categories.",
        "",
        "Re-generate: `python3 ~/scripts/generate-solutions-index.py`",
        "",
    ]

    # Sort categories: 'general' first, then alphabetical
    sorted_cats = sorted(categories.keys(), key=lambda c: ("" if c == "general" else c))

    for cat in sorted_cats:
        entries = sorted(categories[cat], key=lambda x: x[2], reverse=True)
        display = cat.replace("-", " ").replace("/", " / ").title() if cat != "general" else "General"
        lines.append(f"## {display} ({len(entries)})")
        lines.append("")
        for rel, desc, _mtime, date_str in entries:
            name = Path(rel).stem.replace("-", " ").replace("_", " ")
            if desc:
                lines.append(f"- **{name}** — {desc} ({date_str})")
            else:
                lines.append(f"- **{name}** ({date_str})")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate index for solutions KB")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing to file")
    args = parser.parse_args()

    content = generate_index()
    count = sum(1 for line in content.splitlines() if line.startswith("- "))

    if args.dry_run:
        print(content)
        print(f"\nDry run complete. {count} entries found.")
    else:
        INDEX.write_text(content)
        print(f"Generated {INDEX} ({count} entries)")
