from __future__ import annotations

"""Comprehensive tests for metabolon.organelles.talking_points.

Covers: TalkingPoint, TalkingPointCard, _scan_consulting_assets,
_score_relevance, generate_talking_points — all external I/O mocked.
"""

from datetime import datetime
from unittest.mock import patch

from metabolon.organelles.talking_points import (
    TalkingPoint,
    TalkingPointCard,
    _scan_consulting_assets,
    _score_relevance,
    generate_talking_points,
)

# ---------------------------------------------------------------------------
# TalkingPoint.to_markdown
# ---------------------------------------------------------------------------


class TestTalkingPointToMarkdown:
    def test_all_fields_present(self):
        tp = TalkingPoint(
            thesis="AI cuts costs",
            evidence="30% reduction in ops spend",
            positioning="Frame as efficiency play",
            source_asset="policy-ai.md",
            relevance_score=0.8,
        )
        md = tp.to_markdown()
        assert "**AI cuts costs**" in md
        assert "30% reduction" in md
        assert "Frame as efficiency play" in md
        assert "policy-ai.md" in md

    def test_default_relevance_score(self):
        tp = TalkingPoint(thesis="T", evidence="E", positioning="P", source_asset="a.md")
        assert tp.relevance_score == 0.0

    def test_multiline_format_structure(self):
        tp = TalkingPoint(thesis="Thesis", evidence="Ev", positioning="Pos", source_asset="s.md")
        md = tp.to_markdown()
        lines = md.split("\n")
        assert lines[0].startswith("**")
        assert lines[1].strip().startswith("Evidence:")
        assert lines[2].strip().startswith("Position:")
        assert lines[3].strip().startswith("Source:")


# ---------------------------------------------------------------------------
# TalkingPointCard.to_markdown
# ---------------------------------------------------------------------------


class TestTalkingPointCardToMarkdown:
    def _make_card(self, **overrides):
        defaults = dict(
            client="Acme Corp",
            meeting_context="Quarterly review",
            points=[],
            generated_at="2026-04-01 09:00",
        )
        defaults.update(overrides)
        return TalkingPointCard(**defaults)

    def test_header_contains_client_and_context(self):
        card = self._make_card()
        md = card.to_markdown()
        assert "# Talking Points: Acme Corp" in md
        assert "**Context:** Quarterly review" in md
        assert "**Generated:** 2026-04-01 09:00" in md

    def test_empty_points_still_produces_header(self):
        card = self._make_card(points=[])
        md = card.to_markdown()
        assert "# Talking Points:" in md
        assert "##" not in md  # no numbered point headings

    def test_multiple_points_numbered(self):
        pts = [
            TalkingPoint(thesis=f"Point {i}", evidence="e", positioning="p", source_asset="s.md")
            for i in range(3)
        ]
        card = self._make_card(points=pts)
        md = card.to_markdown()
        assert "## 1. Point 0" in md
        assert "## 2. Point 1" in md
        assert "## 3. Point 2" in md

    def test_point_fields_rendered(self):
        pts = [TalkingPoint(thesis="Th", evidence="Ev", positioning="Po", source_asset="file.md")]
        card = self._make_card(points=pts)
        md = card.to_markdown()
        assert "- **Evidence:** Ev" in md
        assert "- **Position:** Po" in md
        assert "- **Source:** `file.md`" in md

    def test_default_points_factory(self):
        card = TalkingPointCard(client="X", meeting_context="Y")
        assert card.points == []


# ---------------------------------------------------------------------------
# _scan_consulting_assets
# ---------------------------------------------------------------------------


class TestScanConsultingAssets:
    def test_returns_empty_when_dir_missing(self, tmp_path):
        fake_dir = tmp_path / "nope"
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", fake_dir):
            assert _scan_consulting_assets() == []

    def test_scans_all_four_subdirs(self, tmp_path):
        subdirs = ["Policies", "Architectures", "Use Cases", "Experiments"]
        for sd in subdirs:
            d = tmp_path / sd
            d.mkdir()
            (d / f"{sd.replace(' ', '_')}.md").write_text(
                f"# {sd} doc\n\nSome content here that is long enough."
            )
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert len(assets) == 4
        titles = {a["title"] for a in assets}
        assert "Policies doc" in titles

    def test_ignores_non_md_files(self, tmp_path):
        d = tmp_path / "Policies"
        d.mkdir()
        (d / "readme.md").write_text("# Readme\n\nContent.")
        (d / "data.json").write_text("{}")
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert len(assets) == 1
        assert assets[0]["filename"] == "readme.md"

    def test_extracts_domain_from_content(self, tmp_path):
        d = tmp_path / "Policies"
        d.mkdir()
        (d / "gov.md").write_text("# Governance\ndomain: fintech\n\nMore content.")
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert len(assets) == 1
        assert assets[0]["domain"] == "fintech"

    def test_stem_used_as_title_when_no_heading(self, tmp_path):
        d = tmp_path / "Architectures"
        d.mkdir()
        (d / "no_heading.md").write_text("Just plain text with no heading at all.")
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert assets[0]["title"] == "no_heading"

    def test_type_derived_from_subdir(self, tmp_path):
        d = tmp_path / "Experiments"
        d.mkdir()
        (d / "exp1.md").write_text("# Exp1\n\nContent here.")
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert assets[0]["type"] == "experiment"

    def test_content_preview_capped(self, tmp_path):
        d = tmp_path / "Policies"
        d.mkdir()
        long_body = "x" * 1000
        (d / "long.md").write_text(f"# Long\n\n{long_body}")
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert len(assets[0]["content_preview"]) == 500

    def test_skips_unreadable_file_gracefully(self, tmp_path):
        d = tmp_path / "Policies"
        d.mkdir()
        bad = d / "bad.md"
        bad.write_text("# Bad\nContent.")
        bad.chmod(0o000)
        try:
            with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
                assets = _scan_consulting_assets()
            assert assets == []
        finally:
            bad.chmod(0o644)

    def test_missing_subdir_skipped(self, tmp_path):
        d = tmp_path / "Policies"
        d.mkdir()
        (d / "a.md").write_text("# A\nContent.")
        # Only Policies exists, the other 3 are absent
        with patch("metabolon.organelles.talking_points.CONSULTING_DIR", tmp_path):
            assets = _scan_consulting_assets()
        assert len(assets) == 1


# ---------------------------------------------------------------------------
# _score_relevance
# ---------------------------------------------------------------------------


class TestScoreRelevance:
    def _asset(self, **kw):
        defaults = {"content_preview": "", "title": "", "domain": ""}
        defaults.update(kw)
        return defaults

    def test_zero_when_no_signals(self):
        asset = self._asset(content_preview="cooking pasta", title="Recipe", domain="food")
        score = _score_relevance(asset, "HSBC", "AI governance review")
        assert score < 0.15

    def test_client_name_match_adds_03(self):
        asset = self._asset(content_preview="HSBC banking platform overview")
        score = _score_relevance(asset, "HSBC", "general meeting")
        assert score >= 0.3

    def test_context_keyword_overlap(self):
        asset = self._asset(
            content_preview="governance framework for artificial intelligence oversight"
        )
        score = _score_relevance(asset, "Acme", "AI governance review")
        # "governance" and "artificial" and "intelligence" should overlap
        assert score > 0.1

    def test_domain_match_adds_02(self):
        asset = self._asset(domain="AI governance")
        score = _score_relevance(asset, "Acme", "discussing AI governance strategies")
        # domain words "AI" and "governance" in context
        assert score >= 0.2

    def test_fs_client_bonus(self):
        # Client has FS signal, content has banking keywords
        asset = self._asset(content_preview="banking regulatory compliance framework")
        score = _score_relevance(asset, "HSBC", "unrelated topic xyz")
        # No client match (HSBC not in content), no context overlap, no domain
        # but FS bonus: "hsbc" triggers, content has "banking" and "regulatory"
        assert score >= 0.1

    def test_no_fs_bonus_for_non_fs_client(self):
        asset = self._asset(content_preview="banking regulatory compliance framework")
        score = _score_relevance(asset, "Acme", "unrelated topic xyz")
        assert score < 0.1

    def test_score_capped_at_1(self):
        asset = self._asset(
            content_preview="HSBC " + "governance " * 100,
            title="HSBC governance banking financial regulatory HKMA compliance",
            domain="HSBC banking governance",
        )
        score = _score_relevance(
            asset, "HSBC", "HSBC governance banking financial regulatory HKMA compliance"
        )
        assert score <= 1.0

    def test_threshold_below_01(self):
        asset = self._asset(
            content_preview="random text nothing relevant", title="Misc", domain="other"
        )
        score = _score_relevance(asset, "UnknownClient", "completely unrelated agenda")
        assert score < 0.1


# ---------------------------------------------------------------------------
# generate_talking_points
# ---------------------------------------------------------------------------


class TestGenerateTalkingPoints:
    def _mock_asset(self, title="Test Asset", content_preview="", domain="", filename="asset.md"):
        return {
            "path": f"/fake/{filename}",
            "title": title,
            "type": "policy",
            "domain": domain,
            "content_preview": content_preview,
            "filename": filename,
        }

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_returns_card_with_correct_client_and_context(self, mock_scan):
        mock_scan.return_value = []
        card = generate_talking_points("Acme", "quarterly sync")
        assert card.client == "Acme"
        assert card.meeting_context == "quarterly sync"
        assert card.points == []

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_empty_assets_gives_empty_points(self, mock_scan):
        mock_scan.return_value = []
        card = generate_talking_points("X", "Y")
        assert card.points == []

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_filters_low_score_assets(self, mock_scan):
        mock_scan.return_value = [
            self._mock_asset(title="Irrelevant", content_preview="cooking pasta"),
        ]
        card = generate_talking_points("HSBC", "AI governance")
        assert len(card.points) == 0

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_includes_relevant_assets_as_points(self, mock_scan):
        mock_scan.return_value = [
            self._mock_asset(
                title="AI Governance Policy",
                content_preview="# AI Governance\n\nThis policy covers regulatory compliance for AI systems in banking.",
                filename="ai_gov.md",
            ),
        ]
        card = generate_talking_points("HSBC", "AI governance review")
        assert len(card.points) >= 1
        assert card.points[0].thesis == "AI Governance Policy"
        assert card.points[0].relevance_score > 0.1
        assert card.points[0].source_asset == "ai_gov.md"

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_respects_max_points(self, mock_scan):
        assets = [
            self._mock_asset(
                title=f"Asset {i}",
                content_preview=f"HSBC relevant content about governance {i} " * 10,
                domain="governance",
                filename=f"a{i}.md",
            )
            for i in range(10)
        ]
        mock_scan.return_value = assets
        card = generate_talking_points("HSBC", "AI governance review", max_points=3)
        assert len(card.points) <= 3

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_generated_at_is_populated(self, mock_scan):
        mock_scan.return_value = []
        card = generate_talking_points("X", "Y")
        assert card.generated_at != ""
        # Should be parseable as a datetime
        dt = datetime.strptime(card.generated_at, "%Y-%m-%d %H:%M")
        assert dt.year == 2026

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_evidence_extracted_from_paragraph(self, mock_scan):
        long_para = (
            "This is the first substantive paragraph that should be long enough "
            "to pass the fifty character threshold and be used as evidence for "
            "the talking point that we are generating here in this test."
        )
        mock_scan.return_value = [
            self._mock_asset(
                title="Test",
                content_preview=f"# Heading\n\n{long_para}\n\nShort\n\nAlso short.",
                filename="t.md",
            ),
        ]
        # Make it relevant
        card = generate_talking_points("Test", "first substantive paragraph")
        assert len(card.points) >= 1
        assert "first substantive paragraph" in card.points[0].evidence

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_positioning_includes_client_and_type(self, mock_scan):
        mock_scan.return_value = [
            self._mock_asset(
                title="Relevant Doc",
                content_preview="HSBC relevant governance content " * 10,
                domain="governance",
                filename="doc.md",
            ),
        ]
        card = generate_talking_points("HSBC", "AI governance review")
        assert len(card.points) >= 1
        assert "HSBC" in card.points[0].positioning
        assert "policy" in card.points[0].positioning

    @patch("metabolon.organelles.talking_points._scan_consulting_assets")
    def test_points_sorted_by_score_descending(self, mock_scan):
        mock_scan.return_value = [
            self._mock_asset(
                title="Low",
                content_preview="governance content for testing",
                domain="",
                filename="low.md",
            ),
            self._mock_asset(
                title="High",
                content_preview="HSBC banking governance regulatory compliance framework",
                domain="HSBC banking",
                filename="high.md",
            ),
        ]
        card = generate_talking_points("HSBC", "banking governance", max_points=10)
        if len(card.points) >= 2:
            assert card.points[0].relevance_score >= card.points[1].relevance_score
