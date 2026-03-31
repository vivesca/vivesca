#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Weekly cargo audit sweep across all Rust projects in ~/code/.
Audits root workspace once, then standalone projects individually.
Sends a Telegram notification via deltos if any RUSTSEC advisories are found.

Runs as a LaunchAgent: com.terry.immunosurveillance

Usage:
    immunosurveillance.py              # run the audit sweep
    immunosurveillance.py --health     # check LaunchAgent + binary health
    immunosurveillance.py --dry-run    # show what would be audited
"""

import argparse
import subprocess
import sys
from pathlib import Path

CODE_DIR = Path.home() / "code"
CARGO_AUDIT = Path.home() / ".cargo/bin/cargo-audit"
LAUNCH_AGENT_NAME = "com.terry.immunosurveillance"
PLIST_PATH = Path.home() / "Library/LaunchAgents" / f"{LAUNCH_AGENT_NAME}.plist"


def find_rust_projects() -> list[Path]:
    """Return standalone projects (those with their own Cargo.lock)."""
    if not CODE_DIR.exists():
        return []
    return sorted(
        p.parent for p in CODE_DIR.glob("*/Cargo.toml") if (p.parent / "Cargo.lock").exists()
    )


def run_audit(cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [str(CARGO_AUDIT), "audit", "--quiet"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def has_rustsec(output: str) -> bool:
    return "RUSTSEC-" in output


def check_health() -> bool:
    """Verify LaunchAgent plist and cargo-audit binary are in place.

    Returns True if everything is healthy, False otherwise.
    """
    ok = True

    # Check cargo-audit binary
    if CARGO_AUDIT.exists():
        print(f"  ✓ cargo-audit found at {CARGO_AUDIT}")
    else:
        print(f"  ✗ cargo-audit missing at {CARGO_AUDIT}", file=sys.stderr)
        ok = False

    # Check LaunchAgent plist (macOS only)
    if PLIST_PATH.parent.exists():
        if PLIST_PATH.exists():
            print(f"  ✓ LaunchAgent plist found at {PLIST_PATH}")
            # Try to verify it's loaded via launchctl
            try:
                result = subprocess.run(
                    ["launchctl", "list", LAUNCH_AGENT_NAME],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    print(f"  ✓ LaunchAgent '{LAUNCH_AGENT_NAME}' is loaded")
                else:
                    print(
                        f"  ✗ LaunchAgent '{LAUNCH_AGENT_NAME}' not loaded",
                        file=sys.stderr,
                    )
                    ok = False
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # launchctl not available (non-macOS) — skip silently
                pass
        else:
            print(f"  ✗ LaunchAgent plist missing at {PLIST_PATH}", file=sys.stderr)
            ok = False
    else:
        # Not on macOS — LaunchAgent check is N/A
        print("  ~/Library/LaunchAgents not found (non-macOS), plist check skipped")

    # Check ~/code exists
    if CODE_DIR.exists():
        print(f"  ✓ code directory found at {CODE_DIR}")
    else:
        print(f"  ✗ code directory missing at {CODE_DIR}", file=sys.stderr)
        ok = False

    return ok


def run_sweep(dry_run: bool = False) -> None:
    """Run the cargo-audit sweep across all Rust projects."""
    vulnerable = []

    root_lock = CODE_DIR / "Cargo.lock"
    projects = find_rust_projects()
    total = len(projects) + (1 if root_lock.exists() else 0)

    if dry_run:
        print(f"Targets ({total}):")
        if root_lock.exists():
            print(f"  [workspace-root] {CODE_DIR}")
        for p in projects:
            print(f"  [{p.name}] {p}")
        return

    # Audit root workspace (covers workspace members like exauro, porta, etc.)
    if root_lock.exists():
        ok, output = run_audit(CODE_DIR)
        if not ok and has_rustsec(output):
            vulnerable.append(("workspace-root", output.strip()))

    # Audit standalone projects
    for project in projects:
        ok, output = run_audit(project)
        if not ok and has_rustsec(output):
            vulnerable.append((project.name, output.strip()))

    if not vulnerable:
        print(f"cargo-audit: all {total} targets clean")
        return

    lines = [f"cargo audit: {len(vulnerable)}/{total} targets have vulnerabilities\n"]
    for name, output in vulnerable:
        lines.append(f"[{name}]")
        for line in output.splitlines():
            if any(
                k in line for k in ("RUSTSEC-", "error[", "ID:", "Crate:", "Version:", "Date:")
            ):
                lines.append(f"  {line.strip()}")
        lines.append("")

    message = "\n".join(lines)
    print(message)

    from metabolon.organelles.secretory_vesicle import secrete_text

    secrete_text(message, html=False, label="Cargo Audit")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Weekly cargo audit sweep for Rust projects in ~/code/.",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check LaunchAgent plist, cargo-audit binary, and code directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show audit targets without running cargo-audit.",
    )
    args = parser.parse_args(argv)

    if args.health:
        if check_health():
            print("\nAll checks passed.")
        else:
            print("\nSome checks failed.", file=sys.stderr)
            sys.exit(1)
        return

    run_sweep(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
