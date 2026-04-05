"""Tests for metabolon.pinocytosis.photoreception — module structure and CLI."""

from __future__ import annotations

import json

from metabolon.pinocytosis.photoreception import intake, main

# ── module structure ──────────────────────────────────────────────────


def test_module_exports_intake():
    """Module exposes an intake callable."""
    assert callable(intake)


def test_module_exports_main():
    """Module exposes a main callable."""
    assert callable(main)


def test_intake_has_expected_param_names():
    """intake() signature has as_json and send_weather parameters."""
    import inspect

    sig = inspect.signature(intake)
    params = list(sig.parameters)
    assert "as_json" in params
    assert "send_weather" in params


def test_intake_default_values():
    """intake() defaults: as_json=True, send_weather=False."""
    import inspect

    sig = inspect.signature(intake)
    assert sig.parameters["as_json"].default is True
    assert sig.parameters["send_weather"].default is False


# ── intake behaviour ─────────────────────────────────────────────────


def test_intake_returns_json_by_default(monkeypatch):
    """intake(as_json=True) returns valid JSON with expected section keys."""
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_context",
        lambda **kw: {
            "date": {"iso": "2026-04-05", "datetime": "2026-04-05 08:00 HKT"},
            "todo": {"available": True, "items": []},
            "now": {"available": True, "raw": "facts here"},
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
        lambda: {"label": "Weather", "ok": True, "content": "28C sunny"},
    )
    result = intake(as_json=True)
    parsed = json.loads(result)
    assert "datetime" in parsed
    assert "sleep" in parsed


def test_intake_text_mode(monkeypatch):
    """intake(as_json=False) returns a text brief."""
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_context",
        lambda **kw: {
            "date": {"iso": "2026-04-05", "datetime": "2026-04-05 08:00 HKT"},
            "todo": {"available": False, "error": "skipped"},
            "now": {"available": False, "error": "skipped"},
            "calendar": {"available": False},
            "budget": {"available": False, "error": "skipped"},
        },
    )
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_sleep",
        lambda: {"label": "Sleep", "ok": False, "content": "unavailable"},
    )
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake_weather",
        lambda: {"label": "Weather", "ok": False, "content": "unavailable"},
    )
    result = intake(as_json=False)
    assert "PHOTORECEPTION MORNING BRIEF" in result


# ── main CLI ─────────────────────────────────────────────────────────


def test_main_prints_intake_result(monkeypatch, capsys):
    """main() prints whatever intake() returns."""
    monkeypatch.setattr("sys.argv", ["photoreception"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake",
        lambda **kw: "briefing: sunny, 72F",
    )
    main()
    assert "briefing: sunny, 72F" in capsys.readouterr().out


def test_main_no_args_calls_intake_with_defaults(monkeypatch):
    """main() without flags passes default as_json=False, send_weather=False."""
    captured = {}

    def track_intake(as_json=True, send_weather=False):
        captured.update(as_json=as_json, send_weather=send_weather)
        return "ok"

    monkeypatch.setattr("sys.argv", ["photoreception"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", track_intake)
    main()
    assert captured["as_json"] is False
    assert captured["send_weather"] is False


def test_main_json_and_send_flags(monkeypatch, capsys):
    """main() --json --send forwards both flags to intake()."""
    captured = {}

    def track_intake(as_json=True, send_weather=False):
        captured.update(as_json=as_json, send_weather=send_weather)
        return "ok"

    monkeypatch.setattr("sys.argv", ["photoreception", "--json", "--send"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", track_intake)
    main()
    assert captured["as_json"] is True
    assert captured["send_weather"] is True


def test_main_only_send_flag(monkeypatch):
    """main() --send alone sets send_weather=True, as_json=False."""
    captured = {}

    def track_intake(as_json=True, send_weather=False):
        captured.update(as_json=as_json, send_weather=send_weather)
        return "ok"

    monkeypatch.setattr("sys.argv", ["photoreception", "--send"])
    monkeypatch.setattr("metabolon.pinocytosis.photoreception.intake", track_intake)
    main()
    assert captured["as_json"] is False
    assert captured["send_weather"] is True
