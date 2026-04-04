
"""Merchant categorisation via YAML prefix map."""


from pathlib import Path

import yaml


def restore_categories(path: Path) -> dict[str, str]:
    """Load merchant -> category map from YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def categorise(merchant: str, categories: dict[str, str]) -> str:
    """Match merchant name against category map (case-insensitive prefix).

    First match wins. Returns 'Uncategorised' if no match.
    """
    upper = merchant.upper()
    for prefix, category in categories.items():
        if upper.startswith(prefix.upper()):
            return category
    return "Uncategorised"
