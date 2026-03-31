#!/usr/bin/env python3
"""
Rename ASIN-named Kindle extract files to proper titles.
Run after overnight queue extraction.

Usage: python3 rename-kindle-asins.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

BOOKS_DIR = Path.home() / "notes" / "Books"

ASIN_TO_TITLE = {
    "B00CNQ2NTK": "Awakenings",
    "B0041OT9W6": "The Diary of a Young Girl",
    "B004DEPH3E": "The Rise of Theodore Roosevelt",
    "B004R1Q296": "A Distant Mirror",
    "B00AK78PH8": "Lincoln at Gettysburg",
    "B004QWZ5SA": "A Beautiful Mind",
    "B07MXPQJ9G": "No Visible Bruises",
    "B00768D5BK": "Connections",
    "B0CZ79RMWL": "The Outermost House",
    "B000FC0O1I": "Ernest Hemingway on Writing",
    "B08FGV64B1": "Four Thousand Weeks",
    "B075HYVP7C": "Skin in the Game",
    "B0B1BTJLJN": "Outlive",
    "B0CM8TRWK3": "Co-Intelligence",
    "B0BCF78T14": "Excellent Advice for Living",
    "B07FB1NPNY": "Naked Economics",
    "B0B9SH82C2": "A Brief History of Intelligence",
    "B09QMHZ5KW": "The Abyss - Nuclear Crisis Cuba 1962",
}

def main():
    parser = argparse.ArgumentParser(
        description="Rename ASIN-named Kindle extract files to proper titles."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be renamed without doing it.")
    args = parser.parse_args()

    renamed = 0
    for asin, title in ASIN_TO_TITLE.items():
        src = BOOKS_DIR / f"{asin}.md"
        dst = BOOKS_DIR / f"{title}.md"
        if src.exists():
            if dst.exists():
                print(f"SKIP (dest exists): {asin} → {title}.md")
            else:
                print(f"{'[dry-run] ' if args.dry_run else ''}Rename: {asin}.md → {title}.md")
                if not args.dry_run:
                    src.rename(dst)
                renamed += 1

    print(f"\n{'Would rename' if args.dry_run else 'Renamed'} {renamed} files.")


if __name__ == "__main__":
    main()
