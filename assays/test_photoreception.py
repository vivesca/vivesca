"""Tests for metabolon.pinocytosis.photoreception — module structure and CLI."""

from __future__ import annotations

import pytest

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


def test_intake_raises_not_implemented():
    """intake() raises NotImplementedError until implemented."""
    with pytest.raises(NotImplementedError, match="photoreception gather"):
        intake()


def test_intake_error_with_all_param_combinations():
    """intake raises NotImplementedError regardless of parameter values."""
    combos = [
        dict(as_json=True, send_weather=False),
        dict(as_json=False, send_weather=True),
        dict(as_json=True, send_weather=True),
        dict(as_json=False, send_weather=False),
    ]
    for kwargs in combos:
        with pytest.raises(NotImplementedError):
            intake(**kwargs)


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
