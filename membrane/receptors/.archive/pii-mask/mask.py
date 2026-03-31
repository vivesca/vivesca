from __future__ import annotations

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "guardrails-ai>=0.6.0",
#     "presidio-analyzer>=2.2.0",
#     "presidio-anonymizer>=2.2.0",
# ]
# ///
"""
PII Masking Utility using Guardrails AI

Masks sensitive information before sending prompts to external LLMs.
Uses Microsoft Presidio under the hood for entity recognition.

Usage:
    # Mask text from stdin
    echo "Call me at 6187 2354" | uv run mask.py

    # Mask text from argument
    uv run mask.py "My email is terry@example.com"

    # Dry-run mode (show what would be masked)
    uv run mask.py --dry-run "My SSN is 123-45-6789"

    # Custom entities only
    uv run mask.py --entities "PHONE_NUMBER,EMAIL_ADDRESS" "Contact: 852-6187-2354"

    # As a module
    from mask import mask_pii
    masked = mask_pii("My phone is 6187 2354")
"""

import argparse
import sys

# Default PII entities to detect and mask
DEFAULT_ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "PERSON",  # Names
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "LOCATION",  # Addresses
    "DATE_TIME",  # Dates that might be identifying
    "NRP",  # Nationality, religious, political groups
    "URL",  # URLs that might contain PII
]

# Hong Kong specific patterns (Presidio doesn't have HK-specific)
HK_PATTERNS = {
    "HK_PHONE": r"\+?852[-\s]?\d{4}[-\s]?\d{4}",
    "HK_ID": r"[A-Z]{1,2}\d{6}\([0-9A]\)",  # HKID format: A123456(7)
}


def mask_pii(
    text: str,
    entities: list[str] | None = None,
    dry_run: bool = False,
) -> str | dict:
    """
    Mask PII in text using Presidio analyzer and anonymizer.

    Args:
        text: Input text to mask
        entities: List of entity types to detect (default: common PII)
        dry_run: If True, return dict with original, masked, and findings

    Returns:
        Masked text string, or dict with details if dry_run=True
    """
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    entities = entities or DEFAULT_ENTITIES

    # Initialize engines
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    # Add HK-specific recognizers
    for name, pattern in HK_PATTERNS.items():
        hk_recognizer = PatternRecognizer(
            supported_entity=name,
            patterns=[Pattern(name=name, regex=pattern, score=0.9)],
        )
        analyzer.registry.add_recognizer(hk_recognizer)
        entities.append(name)

    # Analyze text for PII
    results = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
    )

    if dry_run:
        # Return detailed findings
        findings = []
        for result in results:
            findings.append(
                {
                    "type": result.entity_type,
                    "text": text[result.start : result.end],
                    "score": result.score,
                    "start": result.start,
                    "end": result.end,
                }
            )

        # Still anonymize to show result
        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})},
        )

        return {
            "original": text,
            "masked": anonymized.text,
            "findings": findings,
            "count": len(findings),
        }

    # Anonymize with replacement markers
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})},
    )

    return anonymized.text


def main():
    parser = argparse.ArgumentParser(
        description="Mask PII in text before sending to external LLMs"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to mask (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be masked without masking",
    )
    parser.add_argument(
        "--entities",
        type=str,
        help="Comma-separated list of entity types to detect",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (useful for piping)",
    )
    args = parser.parse_args()

    # Get text from argument or stdin
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Error: No text provided. Pass as argument or pipe to stdin.", file=sys.stderr)
        sys.exit(1)

    # Parse entities if provided
    entities = None
    if args.entities:
        entities = [e.strip().upper() for e in args.entities.split(",")]

    # Mask the text
    result = mask_pii(text, entities=entities, dry_run=args.dry_run)

    # Output
    if args.dry_run or args.json:
        import json

        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"masked": result}))
    else:
        print(result)


if __name__ == "__main__":
    main()
