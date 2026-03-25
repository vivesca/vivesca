#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Add 8 missing GARP LO-gap topics to FSRS state JSON."""

import json
import time

STATE_FILE = "/Users/terry/code/epigenome/chromatin/.garp-fsrs-state.json"

NEW_TOPICS = [
    "M3-fairness-tradeoffs",  # Impossibility theorem, trade-off logic
    "M2-cross-validation",  # CV + bootstrapping + grid search
    "M2-ols-nls-mle",  # OLS vs NLS vs MLE methods
    "M2-data-cleaning",  # Data cleaning + preparation techniques
    "M2-categorical-encoding",  # One-hot, label, ordinal encoding
    "M2-train-val-test-split",  # Train/validation/test splits
    "M2-genai-evaluation",  # Evaluating GenAI/LLM outputs (BLEU, ROUGE, human eval)
    "M2-nlp-evaluation",  # NLP model evaluation factors
]


def fresh_card(card_id: int) -> str:
    """New card with no review history — will appear as due immediately."""
    return json.dumps(
        {
            "card_id": card_id,
            "state": 0,
            "step": None,
            "stability": 0.0,
            "difficulty": 0.0,
            "due": "2026-03-10T00:00:00+00:00",
            "last_review": None,
        }
    )


def main():
    with open(STATE_FILE) as f:
        raw = f.read()

    # Handle double-encoded JSON
    data = json.loads(raw)
    if isinstance(data, str):
        data = json.loads(data)

    cards = data.get("cards", {})
    existing = set(cards.keys())

    added = []
    skipped = []

    base_id = int(time.time() * 1000)
    for i, topic in enumerate(NEW_TOPICS):
        if topic in existing:
            skipped.append(topic)
            continue
        cards[topic] = fresh_card(base_id + i)
        added.append(topic)

    data["cards"] = cards

    # Re-encode in same format as original (double-encoded)
    inner = json.dumps(data, ensure_ascii=False)
    outer = json.dumps(inner, ensure_ascii=False)

    with open(STATE_FILE, "w") as f:
        f.write(outer)

    print(f"Added {len(added)} topics:")
    for t in added:
        print(f"  + {t}")
    if skipped:
        print(f"\nSkipped {len(skipped)} (already exist):")
        for t in skipped:
            print(f"  = {t}")
    print(f"\nTotal cards: {len(cards)}")


if __name__ == "__main__":
    main()
