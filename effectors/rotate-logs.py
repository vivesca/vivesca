#!/usr/bin/env python3
"""Truncate cron logs to last N lines. Runs weekly via cron."""

import argparse
from pathlib import Path

LOG_DIR = Path.home() / "logs"
DEFAULT_KEEP = 200


def main():
    parser = argparse.ArgumentParser(
        description="Truncate log files to last N lines.",
    )
    parser.add_argument(
        "-d", "--dir", type=Path, default=LOG_DIR,
        help=f"Log directory (default: {LOG_DIR})",
    )
    parser.add_argument(
        "-n", "--keep", type=int, default=DEFAULT_KEEP,
        help=f"Lines to keep per file (default: {DEFAULT_KEEP})",
    )
    args = parser.parse_args()

    log_dir = args.dir
    if not log_dir.is_dir():
        print(f"No log directory: {log_dir}")
        return

    for log in log_dir.glob("*.log"):
        try:
            lines = log.read_text().splitlines()
            if len(lines) > args.keep:
                log.write_text("\n".join(lines[-args.keep:]) + "\n")
        except OSError:
            pass


if __name__ == "__main__":
    main()
