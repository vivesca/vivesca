#!/usr/bin/env python3
"""
Wrapper for rm -rf that blocks deletion of protected paths.
Usage: safe_rm.py <path> [<path2> ...]
"""
import argparse
import os
import sys

PROTECTED_PATHS = [
    # Critical - not backed up anywhere
    "~/.ssh",
    "~/.gnupg",
    # Prevent nuking everything
    "~",
    "/",
]

def is_protected(path: str) -> bool:
    """Check if path is protected or is a parent of protected paths."""
    abs_path = os.path.abspath(os.path.expanduser(path))

    for protected in PROTECTED_PATHS:
        protected_abs = os.path.abspath(os.path.expanduser(protected))
        # Block if trying to delete a protected path or its parent
        if abs_path == protected_abs:
            return True
        # Block if trying to delete a parent of a protected path
        if protected_abs.startswith(abs_path + "/"):
            return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: safe_rm.py <path> [<path2> ...]")
        sys.exit(1)

    paths = sys.argv[1:]

    for path in paths:
        if is_protected(path):
            abs_path = os.path.abspath(os.path.expanduser(path))
            print(f"❌ BLOCKED: '{abs_path}' is a protected path.")
            print("Protected paths cannot be deleted via rm -rf.")
            print("If you really need to delete this, do it manually in the terminal.")
            sys.exit(1)

    # All paths safe - print them for the caller to use
    for path in paths:
        print(os.path.abspath(os.path.expanduser(path)))
    sys.exit(0)

if __name__ == "__main__":
    main()
