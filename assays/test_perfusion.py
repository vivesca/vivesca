"""Tests for perfusion — north star coverage measurement."""

from unittest.mock import patch
from metabolon.perfusion import (
    north_star_names,
    coverage_map,
    least_perfused,
    ischaemic_stars,
    perfusion_report,
    _ROUTABLE_STARS,
    _LOW_LEVERAGE_SHAPES,
)


def test_north_star_names_no_file(tmp_path):
    with patch("metabolon.perfusion.NORTH_STAR_FILE", tmp_path / "nope.md"):
        assert north_star_names() == []


def test_north_star_names_parses(tmp_path):
    f = tmp_path / "ns.md"
    f.write_text("# North Stars\n\n## Build a career\n\n## Protect health\n\n## Meta\nignored\n")
    with patch("metabolon.perfusion.NORTH_STAR_FILE", f):
        names = north_star_names()
        assert "Build a career" in names
        assert "Protect health" in names
        assert "Meta" not in names


def test_coverage_map_empty(tmp_path):
    ns = tmp_path / "ns.md"
    ns.write_text("## Star A\n")
    with patch("metabolon.perfusion.NORTH_STAR_FILE", ns), \
         patch("metabolon.perfusion.CARDIAC_LOG", tmp_path / "nope.md"), \
         patch("metabolon.perfusion.Path.home", return_value=tmp_path):
        cov = coverage_map()
        assert cov == {"Star A": 0}


def test_routable_stars_defined():
    assert len(_ROUTABLE_STARS) >= 3


def test_low_leverage_shapes():
    assert "Protect health" in _LOW_LEVERAGE_SHAPES


def test_least_perfused_none(tmp_path):
    with patch("metabolon.perfusion.NORTH_STAR_FILE", tmp_path / "nope.md"):
        assert least_perfused() is None


def test_ischaemic_stars(tmp_path):
    ns = tmp_path / "ns.md"
    ns.write_text("## Star A\n## Star B\n")
    with patch("metabolon.perfusion.NORTH_STAR_FILE", ns), \
         patch("metabolon.perfusion.CARDIAC_LOG", tmp_path / "nope.md"), \
         patch("metabolon.perfusion.Path.home", return_value=tmp_path):
        result = ischaemic_stars(threshold=1)
        assert "Star A" in result


def test_perfusion_report(tmp_path):
    ns = tmp_path / "ns.md"
    ns.write_text("## Build a career worth having\n")
    with patch("metabolon.perfusion.NORTH_STAR_FILE", ns), \
         patch("metabolon.perfusion.CARDIAC_LOG", tmp_path / "nope.md"), \
         patch("metabolon.perfusion.Path.home", return_value=tmp_path), \
         patch("metabolon.perfusion.record_event"):
        report = perfusion_report()
        assert "coverage" in report
        assert "ischaemic" in report
        assert "tropism" in report
