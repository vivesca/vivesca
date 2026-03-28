#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    if len(sys.argv) < 3:
        print("Usage: safe_search.py <pattern> <path>")
        sys.exit(1)

    pattern = sys.argv[1]
    search_path = os.path.abspath(os.path.expanduser(sys.argv[2]))
    root_path = os.path.abspath(os.path.expanduser("~"))

    # Hard block on searching the root directly or its parents
    if search_path == root_path or search_path == "/Users/terry" or search_path == "/":
        print(f"ERROR: Searching the root directory '{search_path}' is PROHIBITED.")
        print("Reason: Performance bottleneck and context pollution.")
        print("Action: Specify a narrow sub-directory (e.g., 'bank-faq-chatbot', 'notes').")
        sys.exit(1)

    # Prevent searching directories known to be massive without further narrowing
    # (Example: searching ~/Library recursive is almost always a mistake)
    massive_dirs = ["/Users/terry/Library", "/Users/terry/Pictures", "/Users/terry/Downloads"]
    if search_path in [os.path.abspath(d) for d in massive_dirs]:
        print(f"ERROR: Directory '{search_path}' is too large for broad search.")
        print("Action: Narrow your search path (e.g., '~/Library/Application Support/app').")
        sys.exit(1)

    # Use ripgrep with smart exclusions and a 10s timeout
    cmd = [
        "rg", 
        "--max-columns", "500",
        "--max-results", "100",  # Don't drown the agent in matches
        "--glob", "!.Library/*",
        "--glob", "!.Trash/*",
        "--glob", "!*.log",
        "--glob", "!node_modules/*",
        pattern, 
        search_path
    ]
    try:
        subprocess.run(cmd, timeout=15)
    except subprocess.TimeoutExpired:
        print(f"ERROR: Search timed out after 15s on '{search_path}'.")
        print("Action: Narrow the search scope further.")
        sys.exit(1)
    except FileNotFoundError:

        print("ERROR: ripgrep (rg) is not installed. Falling back to grep...")
        subprocess.run(["grep", "-r", pattern, search_path])

if __name__ == "__main__":
    main()
