def test_restore_goals(tmp_path):
    """Load goal configs from YAML directory."""
    from metabolon.tools.receptor import restore_goals

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    (goals_dir / "capco.yaml").write_text(
        "name: Do well at Capco\n"
        "phases:\n"
        "  - name: pre-joining\n"
        "    until: '2026-04-08'\n"
        "  - name: onboarding\n"
        "    until: '2026-05-08'\n"
        "  - name: delivery\n"
        "materials:\n"
        "  - path: ~/epigenome/chromatin/HSBC Flashcard Deck - 2026-03-19.md\n"
        "    type: flashcards\n"
        "    categories: [D1, D2, D3, D4, D5, D6, D7]\n"
        "  - path: ~/epigenome/chromatin/HSBC Delivery Readiness — Drill Map.md\n"
        "    type: drills\n"
    )

    goals = restore_goals(goals_dir)
    assert len(goals) == 1
    assert goals[0]["name"] == "Do well at Capco"
    assert len(goals[0]["phases"]) == 3
    assert len(goals[0]["materials"]) == 2


def test_current_phase_pre_joining():
    """Detects current phase based on date markers."""
    import datetime

    from metabolon.tools.receptor import current_phase

    phases = [
        {"name": "pre-joining", "until": "2026-04-08"},
        {"name": "onboarding", "until": "2026-05-08"},
        {"name": "delivery"},
    ]

    # Before Apr 8
    result = current_phase(phases, today=datetime.date(2026, 3, 22))
    assert result["name"] == "pre-joining"

    # After Apr 8, before May 8
    result = current_phase(phases, today=datetime.date(2026, 4, 15))
    assert result["name"] == "onboarding"

    # After May 8
    result = current_phase(phases, today=datetime.date(2026, 6, 1))
    assert result["name"] == "delivery"


def test_signal_store_append_and_read(tmp_path):
    """Signal store appends JSONL and reads back."""
    from metabolon.tools.receptor import ProprioceptiveStore

    store = ProprioceptiveStore(tmp_path / "signals.jsonl")
    store.append(
        goal="capco",
        material="HSBC Flashcard Deck",
        category="D1",
        score=2,
        drill_type="flashcard",
    )
    store.append(
        goal="capco",
        material="HSBC Flashcard Deck",
        category="D1",
        score=3,
        drill_type="flashcard",
    )

    signals = store.recall_all()
    assert len(signals) == 2
    assert signals[0]["score"] == 2
    assert signals[1]["score"] == 3
    assert "ts" in signals[0]


def test_signal_store_read_since(tmp_path):
    """Read signals since a given datetime."""
    import datetime

    from metabolon.tools.receptor import ProprioceptiveStore

    store = ProprioceptiveStore(tmp_path / "signals.jsonl")
    store.append(goal="capco", material="deck", category="D1", score=1, drill_type="flashcard")

    # All signals are recent, so read_since yesterday should return all
    yesterday = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    signals = store.recall_since(yesterday)
    assert len(signals) == 1


def test_decode_flashcard_deck(tmp_path):
    """Parses flashcard markdown into structured cards."""
    from metabolon.tools.receptor import decode_flashcard_deck

    deck = tmp_path / "deck.md"
    deck.write_text(
        "# HSBC Flashcard Deck\n\n"
        "## D1 — AI Risk Tiering Framework\n\n"
        "### Card 1 — D1 — Framework Recall\n"
        "**Q:** Name the five scoring dimensions.\n"
        "**A:** Decision Impact, Model Complexity, Data Sensitivity, Autonomy, Regulatory Exposure.\n\n"
        "### Card 2 — D1 — Key Figures\n"
        "**Q:** What are the three tiers?\n"
        "**A:** Tier 3 (5-7), Tier 2 (8-11), Tier 1 (12-15).\n\n"
        "## D2 — 2-Week Pilot Design\n\n"
        "### Card 9 — D2 — Key Figures\n"
        "**Q:** How many use cases in the pilot?\n"
        "**A:** 10-15 use cases, >80% alignment.\n"
    )

    cards = decode_flashcard_deck(deck)
    assert len(cards) == 3
    assert cards[0]["category"] == "D1"
    assert cards[0]["card_type"] == "Framework Recall"
    assert "five scoring dimensions" in cards[0]["question"]
    assert cards[2]["category"] == "D2"


def test_synthesize_signal_summary(tmp_path):
    """Builds a structured summary from goal config + signals."""
    import datetime

    from metabolon.tools.receptor import ProprioceptiveStore, synthesize_signal_summary

    store = ProprioceptiveStore(tmp_path / "signals.jsonl")
    store.append(goal="capco", material="deck", category="D1", score=3, drill_type="flashcard")
    store.append(goal="capco", material="deck", category="D1", score=3, drill_type="flashcard")
    store.append(goal="capco", material="deck", category="D2", score=1, drill_type="flashcard")

    goal = {
        "name": "Do well at Capco",
        "_file": str(tmp_path / "goals" / "capco.yaml"),
        "phases": [
            {"name": "pre-joining", "until": "2026-04-08"},
            {"name": "delivery"},
        ],
        "materials": [
            {
                "path": "~/epigenome/chromatin/deck.md",
                "type": "flashcards",
                "categories": ["D1", "D2", "D3"],
            },
        ],
    }

    summary = synthesize_signal_summary(goal, store, today=datetime.date(2026, 3, 22))
    assert summary["goal"] == "Do well at Capco"
    assert summary["phase"] == "pre-joining"
    assert summary["days_to_next_phase"] == 17
    assert "D1" in summary["categories"]
    assert summary["categories"]["D1"]["avg_score"] == 3.0
    assert summary["categories"]["D2"]["avg_score"] == 1.0
    assert "D3" in summary["categories"]
    assert summary["categories"]["D3"]["avg_score"] == 0  # never drilled


def test_proprioception_sense_no_goals(tmp_path, monkeypatch):
    """When no goals are configured, returns helpful message."""
    from metabolon.tools.receptor import proprioception_sense

    monkeypatch.setattr("metabolon.tools.receptor.GOALS_DIR", tmp_path / "empty")

    result = proprioception_sense()
    assert result.has_goal is False
    assert "no goals" in result.summary.lower()


def test_proprioception_sense_with_goal(tmp_path, monkeypatch):
    """With a configured goal, returns readiness summary."""
    from metabolon.tools.receptor import proprioception_sense

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    (goals_dir / "capco.yaml").write_text(
        "name: Do well at Capco\n"
        "phases:\n"
        "  - name: pre-joining\n"
        "    until: '2026-04-08'\n"
        "  - name: delivery\n"
        "materials:\n"
        "  - path: ~/epigenome/chromatin/deck.md\n"
        "    type: flashcards\n"
        "    categories: [D1, D2]\n"
    )

    signals_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.tools.receptor.GOALS_DIR", goals_dir)
    monkeypatch.setattr("metabolon.tools.receptor.SIGNALS_DIR", signals_dir)

    result = proprioception_sense()
    assert result.has_goal is True
    assert "Capco" in result.summary
    assert "pre-joining" in result.summary


def test_proprioception_drill(tmp_path, monkeypatch):
    """Records a drill signal and persists it."""
    from metabolon.tools.receptor import ProprioceptiveStore, proprioception_drill

    signals_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.tools.receptor.SIGNALS_DIR", signals_dir)

    result = proprioception_drill(
        goal="do-well-at-capco",
        category="D1",
        score=2,
        drill_type="flashcard",
        material="HSBC Flashcard Deck",
    )
    assert result.success is True

    store = ProprioceptiveStore(signals_dir / "do-well-at-capco-signals.jsonl")
    signals = store.recall_all()
    assert len(signals) == 1
    assert signals[0]["category"] == "D1"
    assert signals[0]["score"] == 2


def test_prep_sense_integration(tmp_path, monkeypatch):
    """Full flow: goal config -> record signals -> sense readiness."""
    from metabolon.tools.receptor import (
        proprioception_drill,
        proprioception_sense,
    )

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    (goals_dir / "capco.yaml").write_text(
        "name: Do well at Capco\n"
        "phases:\n"
        "  - name: pre-joining\n"
        "    until: '2026-04-08'\n"
        "  - name: delivery\n"
        "materials:\n"
        "  - path: ~/epigenome/chromatin/deck.md\n"
        "    type: flashcards\n"
        "    categories: [D1, D2, D3]\n"
    )

    signals_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.tools.receptor.GOALS_DIR", goals_dir)
    monkeypatch.setattr("metabolon.tools.receptor.SIGNALS_DIR", signals_dir)

    # Record some drills
    proprioception_drill(goal="do-well-at-capco", category="D1", score=3, material="deck")
    proprioception_drill(goal="do-well-at-capco", category="D1", score=3, material="deck")
    proprioception_drill(goal="do-well-at-capco", category="D2", score=1, material="deck")

    # Sense readiness
    result = proprioception_sense()
    assert result.has_goal is True
    assert "D3" in result.summary or any("D3" in str(g.get("weakest", [])) for g in result.goals)
    # D3 should be weakest (never drilled)
    assert result.goals[0]["weakest"][0] == "D3"
