#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Chromatin Decay Report - Find orphan and stale notes.

Orphan: No incoming wikilinks from other notes.
Stale: Not mentioned in daily notes for 30+ days (if tracking exists).
Cold: Has access_count but last_accessed > 30 days ago.
"""

import argparse
import os
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

CHROMATIN_PATH = Path.home() / "notes"
DAILY_NOTES_PATH = CHROMATIN_PATH / "memory"
EXCLUDE_PATTERNS = ["Archive/", "templates/", ".obsidian/"]

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown."""
    if not content.startswith("---"):
        return {}
    try:
        end = content.index("---", 3)
        return yaml.safe_load(content[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}

def find_wikilinks(content: str) -> set[str]:
    """Extract all [[wikilinks]] from content."""
    # Match [[link]] or [[link|alias]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    return set(re.findall(pattern, content))

def should_exclude(path: Path) -> bool:
    """Check if path should be excluded."""
    path_str = str(path)
    return any(ex in path_str for ex in EXCLUDE_PATTERNS)

def main():
    parser = argparse.ArgumentParser(
        description="Chromatin Decay Report — find orphan and stale notes."
    )
    parser.parse_args([])

    print("Chromatin Decay Report")
    print("=" * 50)

    # Collect all notes and their incoming links
    notes = {}  # path -> {frontmatter, incoming_links}
    all_links = defaultdict(set)  # target -> set of sources

    for md_file in CHROMATIN_PATH.rglob("*.md"):
        if should_exclude(md_file):
            continue

        rel_path = md_file.relative_to(CHROMATIN_PATH)
        note_name = md_file.stem

        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        frontmatter = parse_frontmatter(content)
        notes[note_name] = {
            "path": rel_path,
            "frontmatter": frontmatter,
            "incoming": set()
        }

        # Track outgoing links
        for link in find_wikilinks(content):
            # Normalize link (handle subpaths)
            link_name = link.split("/")[-1].split("#")[0]
            all_links[link_name].add(note_name)

    # Assign incoming links
    for target, sources in all_links.items():
        if target in notes:
            notes[target]["incoming"] = sources

    # Find orphans (no incoming links, excluding daily notes)
    orphans = []
    for name, data in notes.items():
        # Skip daily notes and hub files
        if re.match(r"\d{4}-\d{2}-\d{2}", name):
            continue
        if name in ["CLAUDE", "TODO", "Active Pipeline", "Job Hunting", "Contact Index"]:
            continue
        if len(data["incoming"]) == 0:
            orphans.append((name, data["path"]))

    # Find cold notes (access tracking shows > 30 days)
    cold = []
    today = datetime.now()
    for name, data in notes.items():
        fm = data["frontmatter"]
        if "last_accessed" in fm:
            try:
                last = datetime.strptime(str(fm["last_accessed"]), "%Y-%m-%d")
                days_ago = (today - last).days
                if days_ago > 30:
                    cold.append((name, days_ago, data["path"]))
            except ValueError:
                pass

    # Report
    print(f"\n📋 Total notes indexed: {len(notes)}")

    print(f"\n🔗 ORPHANS (no incoming links): {len(orphans)}")
    print("   These notes aren't linked from anywhere else.")
    for name, path in sorted(orphans)[:20]:
        print(f"   - {path}")
    if len(orphans) > 20:
        print(f"   ... and {len(orphans) - 20} more")

    print(f"\n❄️  COLD NOTES (last accessed > 30 days): {len(cold)}")
    for name, days, path in sorted(cold, key=lambda x: -x[1]):
        print(f"   - {path} ({days} days ago)")

    # Find notes with access tracking
    tracked = [(n, d) for n, d in notes.items() if "access_count" in d["frontmatter"]]
    print(f"\n📊 Notes with access tracking: {len(tracked)}")
    for name, data in tracked:
        fm = data["frontmatter"]
        print(f"   - {name}: count={fm.get('access_count', 0)}, last={fm.get('last_accessed', 'N/A')}")

if __name__ == "__main__":
    main()
