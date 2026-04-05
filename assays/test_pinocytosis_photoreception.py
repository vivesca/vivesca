from __future__ import annotations

"""Tests for pinocytosis/photoreception — morning brief context gather."""

import json

from metabolon.pinocytosis.photoreception import intake, main

# ── intake tests ───────────────────────────────────────────────────────


def _stub_context(monkeypatch):
    """Patch all external dependencies so intake() runs in isolation."""
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_context",
        lambda **kw: {
            "date": {"iso": "2026-04-05", "datetime": "2026-04-05 08:00 HKT"},
            "todo": {"available": True, "items": []},
            "now": {"available": True, "raw": "facts"},
            "calendar": {"available": True, "raw": "10:00 Standup"},
            "budget": {"available": True, "raw": "ok"},
        },
    )
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_sleep",
        lambda: {"label": "Sleep", "ok": True, "content": "Sleep: 80"},
    )
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_weather",
        lambda: {"label": "Weather", "ok": True, "content": "28C"},
    )


def test_pinocytosis_photoreception_intake_returns_json(monkeypatch):
    """intake(as_json=True) returns valid JSON with expected keys."""
    _stub_context(monkeypatch)
    result = intake(as_json=True)
    parsed = json.loads(result)
    assert "datetime" in parsed
    assert "sleep" in parsed


def test_pinocytosis_photoreception_intake_text_mode(monkeypatch):
    """intake(as_json=False) returns a readable text brief."""
    _stub_context(monkeypatch)
    result = intake(as_json=False)
    assert "PHOTORECEPTION MORNING BRIEF" in result


# ── main CLI tests ─────────────────────────────────────────────────────


def test_pinocytosis_photoreception_main_calls_intake_with_default_args(monkeypatch, capsys):
    """main() calls intake with default arguments."""
    called = {}

    def mock_intake(as_json=True, send_weather=False):
        called["as_json"] = as_json
        called["send_weather"] = send_weather
        return "photoreception output"

    import sys

    monkeypatch.setattr(sys, "argv", ["photoreception"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", mock_intake)
    main()
    captured = capsys.readouterr()
    # --json flag not passed, so as_json is False (default from argparse action="store_true")
    assert called["as_json"] is False
    assert called["send_weather"] is False
    assert "photoreception output" in captured.out


def test_pinocytosis_photoreception_main_with_json_flag(monkeypatch, capsys):
    """main() --json passes as_json=True to intake."""
    called = {}

    def mock_intake(as_json=True, send_weather=False):
        called["as_json"] = as_json
        return "json output"

    import sys

    monkeypatch.setattr(sys, "argv", ["photoreception", "--json"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", mock_intake)
    main()
    assert called["as_json"] is True


def test_main_with_send_flag(monkeypatch, capsys):
    """main() --send passes send_weather=True to intake."""
    called = {}

    def mock_intake(as_json=True, send_weather=False):
        called["send_weather"] = send_weather
        return "output"

    import sys

    monkeypatch.setattr(sys, "argv", ["photoreception", "--send"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", mock_intake)
    main()
    assert called["send_weather"] is True


def test_main_with_both_flags(monkeypatch, capsys):
    """main() handles both --json and --send flags."""
    called = {}

    def mock_intake(as_json=True, send_weather=False):
        called["as_json"] = as_json
        called["send_weather"] = send_weather
        return "output"

    import sys

    monkeypatch.setattr(sys, "argv", ["photoreception", "--json", "--send"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", mock_intake)
    main()
    assert called["as_json"] is True
    assert called["send_weather"] is True
