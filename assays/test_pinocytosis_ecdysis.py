from __future__ import annotations

"""Tests for pinocytosis/ecdysis — weekly review context gather."""

import pytest

from metabolon.pinocytosis.ecdysis import intake, main


# ── intake tests ───────────────────────────────────────────────────────


def test_pinocytosis_ecdysis_intake_raises_not_implemented():
    """intake() raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        intake()
    assert "ecdysis gather not yet implemented" in str(exc_info.value)


def test_pinocytosis_ecdysis_intake_as_json_parameter():
    """intake() accepts as_json parameter (even though it raises)."""
    with pytest.raises(NotImplementedError):
        intake(as_json=True)
    with pytest.raises(NotImplementedError):
        intake(as_json=False)


# ── main CLI tests ─────────────────────────────────────────────────────


def test_pinocytosis_ecdysis_main_calls_intake_with_default_args(monkeypatch, capsys):
    """main() calls intake with default arguments."""
    called = {}

    def mock_intake(as_json=True):
        called["as_json"] = as_json
        return "ecdysis output"

    import sys

    monkeypatch.setattr(sys, "argv", ["ecdysis"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.ecdysis.intake", mock_intake
    )
    main()
    captured = capsys.readouterr()
    # --json flag not passed, so as_json is False (default from argparse action="store_true")
    assert called["as_json"] is False
    assert "ecdysis output" in captured.out


def test_pinocytosis_ecdysis_main_with_json_flag(monkeypatch, capsys):
    """main() --json passes as_json=True to intake."""
    called = {}

    def mock_intake(as_json=True):
        called["as_json"] = as_json
        return "json output"

    import sys

    monkeypatch.setattr(sys, "argv", ["ecdysis", "--json"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.ecdysis.intake", mock_intake
    )
    main()
    assert called["as_json"] is True


def test_pinocytosis_ecdysis_main_without_json_flag(monkeypatch, capsys):
    """main() without --json still calls intake with as_json default."""
    called = {}

    def mock_intake(as_json=True):
        called["as_json"] = as_json
        return "output"

    import sys

    monkeypatch.setattr(sys, "argv", ["ecdysis"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.ecdysis.intake", mock_intake
    )
    main()
    # Default is True when --json is not passed
    assert called["as_json"] is False
