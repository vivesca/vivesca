"""Polarization gather — overnight flywheel preflight (was copia).

Establishing cell polarity before division: which direction to grow.
Collects: consumption check, guard status, north stars.
"""


def intake(as_json: bool = True) -> str:
    """Run polarization preflight gather. Returns formatted string."""
    raise NotImplementedError("polarization gather not yet implemented — stub — not yet implemented")


def guard(action: str = "status") -> str:
    """Control the polarization guard file (on/off/status)."""
    raise NotImplementedError("polarization guard not yet implemented")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Gather context for /polarization overnight flywheel.")
    sub = parser.add_subparsers(dest="command")

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--json", action="store_true")

    guard_cmd = sub.add_parser("guard")
    guard_cmd.add_argument("action", nargs="?", default="status", choices=["on", "off", "status"])

    args = parser.parse_args()
    if args.command == "guard":
        print(guard(action=args.action))
    else:
        print(gather(as_json=getattr(args, "json", True)))


if __name__ == "__main__":
    main()
