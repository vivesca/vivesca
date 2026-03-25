"""Photoreception gather — morning brief context.

Sensing light: first input of the day.
Collects: weather, sleep (Oura), calendar, health signals.
"""


def intake(as_json: bool = True, send_weather: bool = False) -> str:
    """Run photoreception gather. Returns formatted string."""
    raise NotImplementedError("photoreception gather not yet implemented")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Gather context for morning brief.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send weather to Tara.")
    args = parser.parse_args()
    print(intake(as_json=args.json, send_weather=args.send))


if __name__ == "__main__":
    main()
