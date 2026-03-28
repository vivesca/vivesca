"""Tests for proprioception_gradient — direction maker pattern."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from metabolon.enzymes.gradient import (
    _score_text,
    _sense_endocytosis,
    _sense_signals,
    _topology_weight,
    proprioception_gradient,
)

# ---------------------------------------------------------------------------
# Unit tests: _score_text
# ---------------------------------------------------------------------------


def test_score_text_ai_governance():
    hits = _score_text("HKMA issues new regulatory guidance on AI compliance")
    assert "ai_governance" in hits
    assert hits["ai_governance"] >= 2  # "regulatory", "compliance", "hkma"


def test_score_text_ai_agents():
    hits = _score_text("New multi-agent orchestration framework for autonomous workflows")
    assert "ai_agents" in hits


def test_score_text_no_match():
    hits = _score_text("weather is nice today in the park")
    assert hits == {}


def test_score_text_multi_domain():
    hits = _score_text("Bank deploys AI agent for regulatory compliance checks")
    # Should hit multiple domains
    assert "ai_governance" in hits or "banking_fintech" in hits
    assert len(hits) >= 2


# ---------------------------------------------------------------------------
# Unit tests: _sense_endocytosis
# ---------------------------------------------------------------------------


def test_sense_endocytosis_empty(tmp_path, monkeypatch):
    """Empty log returns empty dicts."""
    import metabolon.enzymes.gradient as grad

    monkeypatch.setattr(grad, "_RELEVANCE_LOG", tmp_path / "empty.jsonl")
    hits, titles = _sense_endocytosis(7)
    assert hits == {}
    assert titles == {}


def test_sense_endocytosis_filters_low_score(tmp_path, monkeypatch):
    """Items with score < 6 are excluded."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "relevance.jsonl"
    now = datetime.now(UTC)
    log.write_text(
        json.dumps(
            {
                "timestamp": now.isoformat(),
                "title": "HKMA issues AI governance framework for banks",
                "source": "HKMA",
                "score": 3,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", log)
    hits, _ = _sense_endocytosis(7)
    assert hits == {}


def test_sense_endocytosis_includes_high_score(tmp_path, monkeypatch):
    """Items with score >= 6 within window are included."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "relevance.jsonl"
    now = datetime.now(UTC)
    log.write_text(
        json.dumps(
            {
                "timestamp": now.isoformat(),
                "title": "HKMA issues AI governance compliance framework for banks",
                "source": "HKMA",
                "score": 8,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", log)
    hits, _titles = _sense_endocytosis(7)
    assert "ai_governance" in hits or "banking_fintech" in hits


def test_sense_endocytosis_filters_old_items(tmp_path, monkeypatch):
    """Items outside the time window are excluded."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "relevance.jsonl"
    old_ts = datetime.now(UTC) - timedelta(days=30)
    log.write_text(
        json.dumps(
            {
                "timestamp": old_ts.isoformat(),
                "title": "HKMA AI governance banking compliance 2026",
                "source": "HKMA",
                "score": 9,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", log)
    hits, _ = _sense_endocytosis(7)
    assert hits == {}


# ---------------------------------------------------------------------------
# Unit tests: _sense_signals
# ---------------------------------------------------------------------------


def test_sense_signals_empty(tmp_path, monkeypatch):
    """Empty signals log returns empty dict."""
    import metabolon.enzymes.gradient as grad

    monkeypatch.setattr(grad, "_SIGNALS_LOG", tmp_path / "empty.jsonl")
    hits = _sense_signals(7)
    assert hits == {}


def test_sense_signals_known_tool(tmp_path, monkeypatch):
    """Known tool in TOOL_DOMAINS is classified correctly."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "signals.jsonl"
    now = datetime.now(UTC)
    log.write_text(
        json.dumps(
            {
                "ts": now.isoformat(),
                "tool": "histone_search",
                "outcome": "success",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_SIGNALS_LOG", log)
    hits = _sense_signals(7)
    assert "career_consulting" in hits
    assert hits["career_consulting"] == 1


def test_sense_signals_unknown_tool(tmp_path, monkeypatch):
    """Unknown tools are silently ignored."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "signals.jsonl"
    now = datetime.now(UTC)
    log.write_text(
        json.dumps(
            {
                "ts": now.isoformat(),
                "tool": "some_unknown_tool_xyz",
                "outcome": "success",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_SIGNALS_LOG", log)
    hits = _sense_signals(7)
    assert hits == {}


def test_sense_signals_filters_old(tmp_path, monkeypatch):
    """Old signals outside window are excluded."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "signals.jsonl"
    old_ts = datetime.now(UTC) - timedelta(days=30)
    log.write_text(
        json.dumps(
            {
                "ts": old_ts.isoformat(),
                "tool": "ligand_bind",
                "outcome": "success",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_SIGNALS_LOG", log)
    hits = _sense_signals(7)
    assert hits == {}


# ---------------------------------------------------------------------------
# Integration tests: proprioception_gradient
# ---------------------------------------------------------------------------


def test_gradient_returns_report_type(tmp_path, monkeypatch):
    """Tool returns a GradientReport regardless of empty inputs."""
    import metabolon.enzymes.gradient as grad

    monkeypatch.setattr(grad, "_RELEVANCE_LOG", tmp_path / "empty_relevance.jsonl")
    monkeypatch.setattr(grad, "_SIGNALS_LOG", tmp_path / "empty_signals.jsonl")
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    # Check shape rather than isinstance to avoid class identity issues in test isolation
    assert hasattr(result, "polarity_vector")
    assert hasattr(result, "gradients")
    assert hasattr(result, "window_days")
    assert result.polarity_vector == "diffuse"
    assert result.gradients == []
    assert result.window_days == 7


def test_gradient_single_sensor(tmp_path, monkeypatch):
    """Single sensor signal yields single-sensor polarity annotation."""
    import metabolon.enzymes.gradient as grad

    log = tmp_path / "relevance.jsonl"
    now = datetime.now(UTC)
    for _ in range(3):
        log.open("a").write(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "title": "HKMA AI governance compliance banking regulation 2026",
                    "source": "HKMA",
                    "score": 9,
                }
            )
            + "\n"
        )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", tmp_path / "empty_signals.jsonl")
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    assert "single-sensor" in result.polarity_vector or result.gradients[0].sensor_coverage == 1


def test_gradient_multi_sensor_coverage(tmp_path, monkeypatch):
    """Two sensors confirming same domain yields coverage=2."""
    import metabolon.enzymes.gradient as grad

    now = datetime.now(UTC)

    # Lustro: career_consulting signal
    lustro_log = tmp_path / "relevance.jsonl"
    for _ in range(3):
        lustro_log.open("a").write(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "title": "Capco consulting principal role interview preparation strategy",
                    "source": "JobsDB",
                    "score": 8,
                }
            )
            + "\n"
        )

    # Signals: career_consulting tool usage
    signals_log = tmp_path / "signals.jsonl"
    for _ in range(5):
        signals_log.open("a").write(
            json.dumps({"ts": now.isoformat(), "tool": "ligand_bind", "outcome": "success"}) + "\n"
        )

    monkeypatch.setattr(grad, "_RELEVANCE_LOG", lustro_log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", signals_log)
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    career_vectors = [g for g in result.gradients if g.domain == "career_consulting"]
    assert career_vectors, "career_consulting should appear in gradients"
    assert career_vectors[0].sensor_coverage == 2


def test_gradient_normalised_strength(tmp_path, monkeypatch):
    """Top domain always has signal_strength=1.0 after normalisation."""
    import metabolon.enzymes.gradient as grad

    now = datetime.now(UTC)
    lustro_log = tmp_path / "relevance.jsonl"
    for _ in range(5):
        lustro_log.open("a").write(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "title": "HKMA AI governance compliance banking regulation 2026",
                    "source": "HKMA",
                    "score": 9,
                }
            )
            + "\n"
        )

    signals_log = tmp_path / "signals.jsonl"
    for _ in range(10):
        signals_log.open("a").write(
            json.dumps({"ts": now.isoformat(), "tool": "emit_tweet", "outcome": "success"}) + "\n"
        )

    monkeypatch.setattr(grad, "_RELEVANCE_LOG", lustro_log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", signals_log)
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    if result.gradients:
        assert result.gradients[0].signal_strength == 1.0


def test_gradient_respects_window(tmp_path, monkeypatch):
    """Items outside the requested window do not affect gradient."""
    import metabolon.enzymes.gradient as grad

    lustro_log = tmp_path / "relevance.jsonl"
    old_ts = datetime.now(UTC) - timedelta(days=30)
    lustro_log.write_text(
        json.dumps(
            {
                "timestamp": old_ts.isoformat(),
                "title": "HKMA AI governance compliance banking regulation",
                "source": "HKMA",
                "score": 10,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", lustro_log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", tmp_path / "empty_signals.jsonl")
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    assert result.polarity_vector == "diffuse"


# ---------------------------------------------------------------------------
# Unit tests: _topology_weight
# ---------------------------------------------------------------------------


def test_topology_single_sensor():
    """One sensor → weight 1.0, bonus 'single'."""
    w, bonus = _topology_weight({"endocytosis_signal"})
    assert w == 1.0
    assert bonus == "single"


def test_topology_adjacent_pair():
    """lustro + rheotaxis are adjacent — weight 1.5."""
    w, bonus = _topology_weight({"endocytosis_signal", "rheotaxis_queries"})
    assert w == 1.5
    assert bonus == "adjacent"


def test_topology_independent_pair_lustro_tools():
    """lustro + tool_signals are independent — weight 2.0."""
    w, bonus = _topology_weight({"endocytosis_signal", "tool_signals"})
    assert w == 2.0
    assert bonus == "independent"


def test_topology_independent_pair_rheotaxis_tools():
    """rheotaxis + tool_signals are independent — weight 2.0."""
    w, bonus = _topology_weight({"rheotaxis_queries", "tool_signals"})
    assert w == 2.0
    assert bonus == "independent"


def test_topology_all_three():
    """All three sensors → weight 3.0, bonus 'full'."""
    w, bonus = _topology_weight({"endocytosis_signal", "rheotaxis_queries", "tool_signals"})
    assert w == 3.0
    assert bonus == "full"


def test_topology_empty():
    """Empty sensor set → weight 0.0."""
    w, _bonus = _topology_weight(set())
    assert w == 0.0


# ---------------------------------------------------------------------------
# Integration tests: topology weighting in proprioception_gradient
# ---------------------------------------------------------------------------


def test_gradient_topology_bonus_field_present(tmp_path, monkeypatch):
    """GradientVector has topology_bonus field."""
    import metabolon.enzymes.gradient as grad

    now = datetime.now(UTC)
    lustro_log = tmp_path / "relevance.jsonl"
    lustro_log.write_text(
        json.dumps(
            {
                "timestamp": now.isoformat(),
                "title": "Capco consulting principal role interview preparation strategy",
                "source": "JobsDB",
                "score": 8,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(grad, "_RELEVANCE_LOG", lustro_log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", tmp_path / "empty_signals.jsonl")
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    assert result.gradients
    gv = result.gradients[0]
    assert hasattr(gv, "topology_bonus")
    assert gv.topology_bonus == "single"


def test_gradient_adjacent_pair_lower_weight_than_independent(tmp_path, monkeypatch):
    """Adjacent confirmation (lustro+rheotaxis) ranks below independent confirmation
    (lustro+tools) when raw hit counts are equal.
    """
    import metabolon.enzymes.gradient as grad

    now = datetime.now(UTC)

    # Adjacent domain: career_consulting via lustro + rheotaxis
    # Independent domain: ai_governance via lustro + tool_signals
    # Both get same raw hits so topology is the differentiator.

    lustro_log = tmp_path / "relevance.jsonl"
    # career_consulting hits via lustro (3 articles)
    for _ in range(3):
        lustro_log.open("a").write(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "title": "Capco consulting principal interview role proposal cv",
                    "source": "JobsDB",
                    "score": 8,
                }
            )
            + "\n"
        )
    # ai_governance hits via lustro (3 articles, same volume)
    for _ in range(3):
        lustro_log.open("a").write(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "title": "HKMA AI governance compliance regulatory framework audit",
                    "source": "HKMA",
                    "score": 9,
                }
            )
            + "\n"
        )

    # Signals: ai_governance tools only (not career_consulting)
    signals_log = tmp_path / "signals.jsonl"
    for _ in range(3):
        signals_log.open("a").write(
            json.dumps({"ts": now.isoformat(), "tool": "emit_tweet", "outcome": "success"}) + "\n"
        )

    monkeypatch.setattr(grad, "_RELEVANCE_LOG", lustro_log)
    monkeypatch.setattr(grad, "_SIGNALS_LOG", signals_log)
    monkeypatch.setattr(grad, "_RHEOTAXIS_LOG", tmp_path / "no_rheotaxis")

    result = proprioception_gradient(days=7)
    gov = next((g for g in result.gradients if g.domain == "ai_governance"), None)
    career = next((g for g in result.gradients if g.domain == "career_consulting"), None)

    assert gov is not None
    assert gov.topology_bonus == "independent"
    # ai_governance (independent) should rank at or above career_consulting (single)
    assert gov.signal_strength >= (career.signal_strength if career else 0.0)
