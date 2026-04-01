from __future__ import annotations

"""Tests for pinocytosis/photoreception — morning brief context gather."""

import pytest

from metabolon.pinocytosis.photoreception import intake, main


# ── intake tests ───────────────────────────────────────────────────────


def test_pinocytosis_photoreception_intake_raises_not_implemented():
    """intake() raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        intake()
    assert "photoreception gather not yet implemented" in str(exc_info.value)


def test_pinocytosis_photoreception_intake_as_json_parameter():
    """intake() accepts as_json parameter (even though it raises)."""
    with pytest.raises(NotImplementedError):
        intake(as_json=True)
    with pytest.raises(NotImplementedError):
        intake(as_json=False)


def test_intake_send_weather_parameter():
    """intake() accepts send_weather parameter (even though it raises)."""
    with pytest.raises(NotImplementedError):
        intake(as_json=True, send_weather=True)
    with pytest.raises(NotImplementedError):
        intake(as_json=False, send_weather=False)


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
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake", mock_intake
    )
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
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake", mock_intake
    )
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
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake", mock_intake
    )
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
    monkeypatch.setattr(
        "metabolon.pinocytosis.photoreception.intake", mock_intake
    )
    main()
    assert called["as_json"] is True
    assert called["send_weather"] is True
