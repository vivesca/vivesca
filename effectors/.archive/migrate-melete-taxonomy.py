#!/usr/bin/env python3
from __future__ import annotations

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
migrate-melete-taxonomy.py — Migrate melete FSRS state from 37-topic taxonomy to 64-topic taxonomy.

Usage:
    uv run ~/germline/effectors/migrate-melete-taxonomy.py --dry-run   # preview only
    uv run ~/germline/effectors/migrate-melete-taxonomy.py             # write changes

Rules:
  - Splits: first replacement inherits old card state; additional replacements start fresh
  - Renames / stable topics: preserve state as-is under new ID
  - New topics (no prior card): add with default FSRS state
  - Old topics not in any new taxonomy entry: warn and keep (do not delete)
  - Idempotent: running twice is safe (new IDs won't match old IDs)
"""

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

STATE_FILE = Path.home() / "epigenome/chromatin/.garp-fsrs-state.json"
BACKUP_DIR = Path.home() / "tmp"

# ── Default FSRS state for a brand-new card ───────────────────────────────


def today_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def fresh_card(topic_id: str) -> dict:
    """Default FSRS state for a card that has never been reviewed."""
    import time

    card_id = int(time.time() * 1000) + abs(hash(topic_id)) % 1000
    return {
        "card_id": card_id,
        "state": 0,  # New
        "step": None,
        "stability": 1.0,
        "difficulty": 5.0,
        "due": today_utc_iso(),
        "last_review": today_utc_iso(),
    }


# ── Taxonomy mapping ──────────────────────────────────────────────────────
#
# Format:
#   SPLITS[old_id] = [new_id_1, new_id_2, ...]
#       new_id_1 inherits old card state
#       new_id_2..N start fresh
#
#   RENAMES[old_id] = new_id
#       direct 1:1 rename, state preserved
#
#   STABLE = set of old IDs whose new ID is identical (kept as-is)
#
#   NEW_TOPICS = list of brand-new topic IDs (no prior card)
#
# Source: ~/epigenome/chromatin/GARP RAI Topic Taxonomy.md (Summary section)

SPLITS: dict[str, list[str]] = {
    "M1-classical-ai": [
        "M1-gofai-characteristics",
        "M1-specific-vs-general-ai",
    ],
    "M2-intro-tools": [
        "M2-data-types",
        "M2-ml-vs-econometrics",
    ],
    "M2-data-prep": [
        "M2-normalization-scaling",
        "M2-standardization-scaling",
    ],
    "M2-clustering": [
        "M2-kmeans-clustering",
        "M2-hierarchical-clustering",
        "M2-dbscan-density",
    ],
    "M2-model-estimation": [
        "M2-bias-variance-tradeoff",
        "M2-gradient-descent",
        "M2-lasso-regularization",
        "M2-ridge-regularization",
        "M2-elastic-net",
    ],
    "M2-model-eval": [
        "M2-confusion-matrix-metrics",
        "M2-roc-auc",
    ],
    "M2-neural-networks": [
        "M2-neural-net-architecture",
        "M2-autoencoders",
    ],
    "M2-semi-supervised": [
        "M2-semi-supervised-assumptions",
        "M2-self-training",
        "M2-co-training",
    ],
    "M2-semi-rl": [
        "M2-rl-value-functions",
        "M2-rl-exploration-exploitation",
    ],
    "M2-nlp-genai": [
        "M2-nlp-word2vec",
        "M2-llm-transformers",
        "M2-llm-prompting-temperature",
    ],
    "M2-regression-classification": [
        "M2-decision-trees-ensembles",
        "M2-knn-classifier",
        "M2-svm-classifier",
    ],
    "M3-fairness-measures": [
        "M3-demographic-parity",
        "M3-predictive-rate-parity",
        "M3-equal-opportunity",
        "M3-equalized-odds",
        "M3-individual-fairness",
    ],
    "M3-xai": [
        "M3-interpretability-explainability",
        "M3-xai-shap",
        "M3-xai-lime",
    ],
    "M3-autonomy-safety": [
        "M3-automation-bias",
        "M3-manipulation-opaqueness",
    ],
    "M3-reputational-existential": [
        "M3-reputational-risk",
        "M3-existential-global-risks",
    ],
    "M4-ethical-frameworks": [
        "M4-consequentialism",
        "M4-deontology",
        "M4-virtue-ethics",
        "M4-practical-ethics",
    ],
    # M5-data-governance is both kept AND gains a new split sibling
    "M5-data-governance": [
        "M5-data-governance",  # inherits — same ID
        "M5-data-compliance",  # fresh
    ],
    "M5-implementation": [
        "M5-pen-and-paper-tasks",
        "M5-use-test",
        "M5-model-adaptation",
    ],
    # M5-model-changes-review is both kept AND gains a new split sibling
    "M5-model-changes-review": [
        "M5-model-changes-review",  # inherits — same ID
        "M5-model-monitoring",  # fresh
    ],
}

# Pure renames: old → new, 1:1, full state transfer
# The taxonomy renamed some old IDs without splitting them.
RENAMES: dict[str, str] = {
    "M3-bias-unfairness": "M3-bias-taxonomy",
    "M3-genai-risks": "M3-genai-risk-taxonomy",
    "M3-global-challenges": "M3-xai-challenges",  # repurposed: XAI challenges card
    "M2-econometric": "M2-linear-regression",  # econometric card → first of two new supervised econometric cards
    "M2-nlp-traditional": "M2-nlp-pipeline",
    "M4-privacy-cybersecurity": "M4-privacy-practices",
}

# Topics whose ID is unchanged — state passes through as-is
# Note: M3-genai-risk-taxonomy is NOT listed here; it is handled via RENAMES above.
STABLE: set[str] = {
    "M1-ai-risks",
    "M1-ml-types",
    "M4-ethics-principles",
    "M4-bias-discrimination",
    "M4-governance-challenges",
    "M4-regulatory",
    "M5-model-governance",
    "M5-model-risk-roles",
    "M5-model-dev-testing",
    "M5-model-validation",
    "M5-genai-governance",
    "M5-governance-recommendations",
}

# Completely new topics — no prior card at all
NEW_TOPICS: list[str] = [
    # Noted explicitly as "New (no prior card)" in taxonomy
    "M2-pca-dimensionality",
    "M2-rl-monte-carlo-td",
    "M3-sensitivity-specificity",
    "M4-justice-principle",
    # LO cross-check gaps added 2026-03-10
    "M2-ssl-transductive-inductive",
    "M2-rl-value-vs-policy",
    "M2-naive-bayes",
    "M2-rnn-lstm",
    "M2-agentic-vs-genai",
    "M2-llm-context-stateless",
    "M5-model-result-misinterpretation",
    # Additional new IDs that come from econometric split (logistic-lda is genuinely new)
    "M2-logistic-lda",
    "M2-stepwise-feature-selection",
]

# ── Core migration logic ──────────────────────────────────────────────────


def load_state(path: Path) -> dict:
    with open(path) as f:
        raw = json.load(f)
    # cards values are double-serialized JSON strings — parse each one
    parsed_cards: dict[str, dict] = {}
    for topic_id, value in raw.get("cards", {}).items():
        if isinstance(value, str):
            parsed_cards[topic_id] = json.loads(value)
        elif isinstance(value, dict):
            parsed_cards[topic_id] = value
        else:
            raise ValueError(f"Unexpected card type for {topic_id}: {type(value)}")
    return {
        "cards": parsed_cards,
        "review_log": raw.get("review_log", []),
    }


def serialize_state(state: dict) -> dict:
    """Re-encode cards as JSON strings to match melete's expected format."""
    encoded_cards = {}
    for topic_id, card in state["cards"].items():
        encoded_cards[topic_id] = json.dumps(card, separators=(",", ":"))
    return {
        "cards": encoded_cards,
        "review_log": state["review_log"],
    }


def run_migration(old_cards: dict[str, dict], dry_run: bool) -> tuple[dict[str, dict], list[str]]:
    """
    Returns (new_cards, warnings).
    new_cards: topic_id -> card dict
    """
    new_cards: dict[str, dict] = {}
    warnings: list[str] = []

    # Track which old IDs have been handled
    handled_old: set[str] = set()

    # Counters for summary
    stats = {
        "migrated_splits": 0,
        "migrated_renames": 0,
        "preserved_stable": 0,
        "added_fresh": 0,
    }

    # 1. Process splits
    print("\n=== SPLITS ===")
    for old_id, new_ids in SPLITS.items():
        if old_id not in old_cards:
            warnings.append(
                f"SPLIT source not found in state: {old_id} — skipping split, new topics will be fresh"
            )
            for new_id in new_ids:
                card = fresh_card(new_id)
                new_cards[new_id] = card
                stats["added_fresh"] += 1
                print(f"  [FRESH] {new_id}  (split source {old_id} missing)")
            handled_old.add(old_id)
            continue

        old_card = old_cards[old_id]
        handled_old.add(old_id)

        for i, new_id in enumerate(new_ids):
            if i == 0:
                # First inherits old state, with updated card_id slot preserved
                inherited = dict(old_card)
                new_cards[new_id] = inherited
                stats["migrated_splits"] += 1
                print(
                    f"  [INHERIT] {old_id} -> {new_id}"
                    f"  (stability={old_card['stability']:.2f}, difficulty={old_card['difficulty']:.2f})"
                )
            else:
                card = fresh_card(new_id)
                new_cards[new_id] = card
                stats["added_fresh"] += 1
                print(f"  [FRESH]   {old_id} -> {new_id}")

    # 2. Process renames
    print("\n=== RENAMES ===")
    for old_id, new_id in RENAMES.items():
        if old_id not in old_cards:
            warnings.append(
                f"RENAME source not found in state: {old_id} — adding {new_id} as fresh"
            )
            new_cards[new_id] = fresh_card(new_id)
            stats["added_fresh"] += 1
            print(f"  [FRESH]  {old_id} -> {new_id}  (source missing)")
        else:
            new_cards[new_id] = dict(old_cards[old_id])
            stats["migrated_renames"] += 1
            print(f"  [RENAME] {old_id} -> {new_id}")
        handled_old.add(old_id)

    # 3. Preserve stable topics (same ID)
    print("\n=== STABLE (same ID, preserved) ===")
    for topic_id in STABLE:
        if topic_id in old_cards:
            new_cards[topic_id] = dict(old_cards[topic_id])
            handled_old.add(topic_id)
            stats["preserved_stable"] += 1
            print(f"  [KEEP]  {topic_id}")
        else:
            # Not in old state yet — will be handled as new below if in NEW_TOPICS,
            # or warn if completely unaccounted for.
            print(f"  [SKIP]  {topic_id}  (not in current state — will be fresh)")

    # 4. Add genuinely new topics
    print("\n=== NEW TOPICS (fresh) ===")
    for topic_id in NEW_TOPICS:
        if topic_id not in new_cards:
            new_cards[topic_id] = fresh_card(topic_id)
            stats["added_fresh"] += 1
            print(f"  [NEW]   {topic_id}")
        else:
            print(f"  [SKIP]  {topic_id}  (already mapped from split/rename)")

    # 5. Warn about old topics not handled
    print("\n=== UNHANDLED OLD TOPICS ===")
    unhandled = set(old_cards.keys()) - handled_old
    if unhandled:
        for old_id in sorted(unhandled):
            msg = f"Old topic not mapped to any new taxonomy entry: {old_id} — KEPT as-is"
            warnings.append(msg)
            new_cards[old_id] = dict(old_cards[old_id])
            print(f"  [WARN/KEEP] {old_id}")
    else:
        print("  (none — all old topics accounted for)")

    # Print stats
    print(f"\n{'=' * 60}")
    print("Migration summary:")
    print(f"  Old topics:              {len(old_cards)}")
    print(f"  Split (inheriting):      {stats['migrated_splits']}")
    print(f"  Renamed:                 {stats['migrated_renames']}")
    print(f"  Preserved (stable):      {stats['preserved_stable']}")
    print(f"  Added fresh:             {stats['added_fresh']}")
    print(f"  Unhandled (kept+warned): {len(unhandled)}")
    print(f"  New total topics:        {len(new_cards)}")

    return new_cards, warnings


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Migrate melete FSRS state to the new 64-topic taxonomy."
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview migration without writing any files.",
    )
    args = parser.parse_args()

    dry_run: bool = args.dry_run

    if dry_run:
        print("DRY RUN MODE — no files will be written.\n")
    else:
        print("LIVE MODE — will write backup and update state file.\n")

    # Load current state
    print(f"Reading state from: {STATE_FILE}")
    state = load_state(STATE_FILE)
    old_cards = state["cards"]
    review_log = state["review_log"]
    print(f"Loaded {len(old_cards)} existing cards, {len(review_log)} review log entries.")

    # Run migration logic
    new_cards, warnings = run_migration(old_cards, dry_run=dry_run)

    # Print warnings
    if warnings:
        print(f"\n{'=' * 60}")
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")

    # Idempotency check: if all new IDs already present, nothing to do
    old_ids = set(old_cards.keys())
    new_ids = set(new_cards.keys())
    if new_ids == old_ids and not warnings:
        print("\n[IDEMPOTENT] State already matches target taxonomy — no changes needed.")
        if not dry_run:
            print("No file written.")
        return

    if dry_run:
        print(f"\n{'=' * 60}")
        print("DRY RUN complete. No files were written.")
        print(
            f"Would produce {len(new_cards)} topics ({len(new_cards) - len(old_cards):+d} from current {len(old_cards)})."
        )
        return

    # Backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    backup_path = BACKUP_DIR / f"garp-fsrs-backup-{date_str}.json"
    print(f"\nBacking up to: {backup_path}")
    shutil.copy2(STATE_FILE, backup_path)
    print("Backup written.")

    # Write new state
    new_state = {
        "cards": {},
        "review_log": review_log,
    }
    # Re-encode cards as double-serialized JSON strings
    for topic_id, card in new_cards.items():
        new_state["cards"][topic_id] = json.dumps(card, separators=(",", ":"))

    with open(STATE_FILE, "w") as f:
        json.dump(new_state, f, indent=2)
    print(f"State written to: {STATE_FILE}")
    print(f"Migration complete: {len(old_cards)} -> {len(new_cards)} topics.")


if __name__ == "__main__":
    main()
