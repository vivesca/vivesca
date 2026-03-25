"""Ecdysis gather — weekly review context (was weekly).

Moulting: shed the old week, prepare the new.
Collects: next week calendar, TODO, Oura, spores/garden.
"""


def intake(as_json: bool = True) -> str:
    """Run ecdysis gather. Returns formatted string."""
    raise NotImplementedError("ecdysis gather not yet implemented — migrate from weekly")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Gather context for /ecdysis weekly review.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print(gather(as_json=args.json))


if __name__ == "__main__":
    main()
