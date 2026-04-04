#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Safe grep wrapper — searches with ripgrep and guards against massive directories."
    )
    parser.add_argument("pattern", help="Search pattern")
    parser.add_argument("path", help="Directory to search in")
    args = parser.parse_args()

    search_path = Path(args.path).expanduser().resolve()
    home_path = Path.home().resolve()

    # Hard block on searching the root directly or home directory
    if search_path == home_path or str(search_path) == "/":
        print(f"ERROR: Searching the root directory '{search_path}' is PROHIBITED.")
        print("Reason: Performance bottleneck and context pollution.")
        print("Action: Specify a narrow sub-directory (e.g., 'bank-faq-chatbot', 'notes').")
        sys.exit(1)

    # Prevent searching directories known to be massive without further narrowing
    massive_dirs = [home_path / d for d in ["Library", "Pictures", "Downloads"]]
    if search_path in massive_dirs:
        print(f"ERROR: Directory '{search_path}' is too large for broad search.")
        print("Action: Narrow your search path (e.g., '~/Library/Application Support/app').")
        sys.exit(1)

    # Use ripgrep with smart exclusions and a 10s timeout
    cmd = [
        "rg",
        "--max-columns",
        "500",
        "--max-count",
        "100",  # Don't drown the agent in matches
        "--glob",
        "!Library/**",
        "--glob",
        "!.Trash/**",
        "--glob",
        "!*.log",
        "--glob",
        "!node_modules/**",
        args.pattern,
        str(search_path),
    ]
    try:
        subprocess.run(cmd, timeout=15)
    except subprocess.TimeoutExpired:
        print(f"ERROR: Search timed out after 15s on '{search_path}'.")
        print("Action: Narrow the search scope further.")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: ripgrep (rg) is not installed. Falling back to grep...")
        subprocess.run(["grep", "-r", args.pattern, search_path], timeout=60)


if __name__ == "__main__":
    main()
