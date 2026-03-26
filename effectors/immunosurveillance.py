#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Weekly cargo audit sweep across all Rust projects in ~/code/.
Audits root workspace once, then standalone projects individually.
Sends a Telegram notification via deltos if any RUSTSEC advisories are found.
"""

import subprocess
from pathlib import Path

CODE_DIR = Path.home() / "code"
CARGO_AUDIT = Path.home() / ".cargo/bin/cargo-audit"


def find_rust_projects() -> list[Path]:
    """Return standalone projects (those with their own Cargo.lock)."""
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


def main():
    vulnerable = []

    # Audit root workspace (covers workspace members like exauro, porta, etc.)
    root_lock = CODE_DIR / "Cargo.lock"
    if root_lock.exists():
        ok, output = run_audit(CODE_DIR)
        if not ok and has_rustsec(output):
            vulnerable.append(("workspace-root", output.strip()))

    # Audit standalone projects
    projects = find_rust_projects()
    for project in projects:
        ok, output = run_audit(project)
        if not ok and has_rustsec(output):
            vulnerable.append((project.name, output.strip()))

    total = len(projects) + (1 if root_lock.exists() else 0)

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


if __name__ == "__main__":
    main()
