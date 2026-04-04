"""Tests for respiration — metabolic conversion efficiency."""

from unittest.mock import patch

from metabolon.respiration import (
    _count_converted,
    _count_ejected,
    _count_stale,
    ejection_fraction,
)


def test_ejection_fraction_no_file(tmp_path):
    fake = tmp_path / "Praxis.md"
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert ejection_fraction() == -1.0


def test_ejection_fraction_no_ejected(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [ ] some non-terry item\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert ejection_fraction() == -1.0


def test_ejection_fraction_all_converted(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text(
        "- [x] agent:terry review memo (done)\n- [x] agent:terry check report (completed)\n"
    )
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert ejection_fraction() == 1.0


def test_ejection_fraction_partial(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [x] agent:terry done\n- [ ] agent:terry pending\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        ef = ejection_fraction()
        assert ef == 0.5


def test_count_ejected_zero(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("no special items here\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_ejected() == 0


def test_count_ejected_counts(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [ ] agent:terry review\n- [ ] agent:terry check\n- other line\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_ejected() == 2


def test_count_converted(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [x] agent:terry done\n- [ ] agent:terry pending\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_converted() == 1


def test_count_converted_multiple_signals(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [x] agent:terry done\n- agent:terry completed\n- agent:terry resolved\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_converted() == 3


def test_count_stale_old_item(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [ ] agent:terry old task 2020-01-01\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_stale(days=7) == 1


def test_count_stale_recent_item(tmp_path):
    fake = tmp_path / "Praxis.md"
    fake.write_text("- [ ] agent:terry new task 2099-01-01\n")
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_stale(days=7) == 0


def test_count_stale_no_file(tmp_path):
    fake = tmp_path / "nonexistent.md"
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_stale() == 0


def test_count_ejected_no_file(tmp_path):
    fake = tmp_path / "nonexistent.md"
    with patch("metabolon.respiration.PRAXIS_FILE", fake):
        assert _count_ejected() == 0
