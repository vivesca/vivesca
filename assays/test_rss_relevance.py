from __future__ import annotations

"""Tests for relevance.py"""


from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import json

import pytest

from metabolon.organelles.endocytosis_rss.relevance import (
    _normalize_score_payload,
    _keyword_score,
    _read_jsonl,
    receptor_signal_ratio,
    record_affinity,
    record_recycling,
    top_cargo,
    affinity_stats,
    BATCH_SIZE,
)


class TestNormalizeScorePayload:
    """Tests for score payload normalization"""

    def test_normalizes_valid_payload(self):
        """Valid payload returned as-is with clamped score"""
        payload = {"score": 8, "banking_angle": "Banks need this", "talking_point": "Ask about it"}
        result = _normalize_score_payload(payload)
        assert result["score"] == 8
        assert result["banking_angle"] == "Banks need this"
        assert result["talking_point"] == "Ask about it"

    def test_clamps_scores_outside_range(self):
        """Clamps scores to 1-10 range"""
        assert _normalize_score_payload({"score": 0})["score"] == 1
        assert _normalize_score_payload({"score": 15})["score"] == 10
        assert _normalize_score_payload({"score": -5})["score"] == 1

    def test_handles_non_numeric_score(self):
        """Non-numeric score → 0 → clamped to 1"""
        result = _normalize_score_payload({"score": "not a number"})
        assert result["score"] == 1

    def test_provides_defaults_for_missing_fields(self):
        """Missing fields get N/A"""
        result = _normalize_score_payload({})
        assert result["banking_angle"] == "N/A"
        assert result["talking_point"] == "N/A"


class TestKeywordScore:
    """Tests for keyword-based scoring fallback"""

    def test_high_keywords_increase_score(self):
        """High importance keywords add 2 each"""
        title = "HKMA announces new AI regulatory framework for banks"
        summary = "The Hong Kong Monetary Authority published new compliance requirements for AI in banking"
        result = _keyword_score(title, summary)
        # Should have high score due to 'hkma', 'bank', 'banking', 'regulatory', 'compliance'
        assert result["score"] > 5

    def test_low_keywords_decrease_score(self):
        """Consumer/low relevance keywords decrease score"""
        title = "New AI smartphone photo filter released"
        summary = "The new consumer app is available for download on app stores"
        result = _keyword_score(title, summary)
        # Starts at 2 → gets -1 due to 'consumer' → 1
        assert result["score"] == 1

    def test_returns_default_even_with_no_keywords(self):
        """Returns at least 1"""
        result = _keyword_score("Random article", "Something about something else")
        assert 1 <= result["score"] <= 10


class TestReadJsonl:
    """Tests for JSONL reading"""

    def test_reads_valid_jsonl(self):
        """Reads valid JSONL with one dict per line"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(json.dumps({"a": 1}) + "\n")
            f.write(json.dumps({"b": 2}) + "\n")
            f.write("\n")  # empty line skipped
            f.write(json.dumps({"c": 3}) + "\n")
        path = Path(f.name)
        try:
            result = _read_jsonl(path)
            assert len(result) == 3
            assert result[0]["a"] == 1
            assert result[1]["b"] == 2
            assert result[2]["c"] == 3
        finally:
            path.unlink(missing_ok=True)

    def test_returns_empty_for_missing_file(self):
        """Missing file → empty list"""
        result = _read_jsonl(Path("/does/not/exist"))
        assert result == []

    def test_skips_bad_json_lines(self):
        """Skips invalid JSON lines"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(json.dumps({"a": 1}) + "\n")
            f.write("not valid json\n")
            f.write(json.dumps({"c": 3}) + "\n")
        path = Path(f.name)
        try:
            result = _read_jsonl(path)
            assert len(result) == 2
        finally:
            path.unlink(missing_ok=True)


class TestRecordAffinity:
    """Tests for affinity logging"""

    def test_record_affinity_appends(self):
        """Appends entry to log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "affinity.jsonl"
            # Monkeypatch the global AFFINITY_LOG for this test
            from metabolon.organelles.endocytosis_rss import relevance
            original = relevance.AFFINITY_LOG
            try:
                relevance.AFFINITY_LOG = path
                item = {
                    "timestamp": "2024-03-15T10:30:00Z",
                    "title": "Test Article",
                    "source": "Test Source",
                }
                scores = {"score": 8, "banking_angle": "Test", "talking_point": "Test"}
                record_affinity(item, scores)
                assert path.exists()
                lines = path.read_text().splitlines()
                assert len(lines) == 1
                data = json.loads(lines[0])
                assert data["title"] == "Test Article"
                assert data["score"] == 8
            finally:
                relevance.AFFINITY_LOG = original

class TestRecordRecycling:
    """Tests for recycling (engagement) logging"""

    def test_record_recycling_appends(self):
        """Appends engagement entry to log"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "recycling.jsonl"
            from metabolon.organelles.endocytosis_rss import relevance
            original = relevance.RECYCLING_LOG
            try:
                relevance.RECYCLING_LOG = path
                record_recycling("Test Article Title")
                assert path.exists()
                lines = path.read_text().splitlines()
                assert len(lines) == 1
                data = json.loads(lines[0])
                assert data["title"] == "Test Article Title"
                assert "timestamp" in data
            finally:
                relevance.RECYCLING_LOG = original


class TestReceptorSignalRatio:
    """Tests for signal-to-noise ratio calculation"""

    def test_returns_1_when_fewer_than_five_items(self):
        """<5 items → return 1.0 (no downregulation)"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            for i in range(3):
                f.write(json.dumps({
                    "source": "TestSource",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "score": 6 + i,
                }) + "\n")
        from metabolon.organelles.endocytosis_rss import relevance
        path = Path(f.name)
        original = relevance.AFFINITY_LOG
        try:
            relevance.AFFINITY_LOG = path
            ratio = receptor_signal_ratio("TestSource")
            assert ratio == 1.0
        finally:
            relevance.AFFINITY_LOG = original
            path.unlink()

    def test_calculates_correct_ratio(self):
        """Correctly computes fraction of items >=5"""
        now = datetime.now(UTC)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            scores = [8, 7, 5, 2, 6]  # 4/5 >=5
            for score in scores:
                f.write(json.dumps({
                    "source": "TestSource",
                    "timestamp": now.isoformat(),
                    "score": score,
                }) + "\n")
        from metabolon.organelles.endocytosis_rss import relevance
        path = Path(f.name)
        original = relevance.AFFINITY_LOG
        try:
            relevance.AFFINITY_LOG = path
            ratio = receptor_signal_ratio("TestSource", window_days=30)
            assert abs(ratio - 4/5) < 0.0001
        finally:
            relevance.AFFINITY_LOG = original
            path.unlink()


class TestAffinityStats:
    """Tests for affinity statistics"""

    def test_returns_insufficient_when_empty(self):
        """Empty data → insufficient status"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            pass  # empty
        from metabolon.organelles.endocytosis_rss import relevance
        affinity_path = Path(f.name)
        recycling_path = Path(f.name + ".recycling")
        recycling_path.write_text("", encoding="utf-8")
        original_aff = relevance.AFFINITY_LOG
        original_rec = relevance.RECYCLING_LOG
        try:
            relevance.AFFINITY_LOG = affinity_path
            relevance.RECYCLING_LOG = recycling_path
            stats = affinity_stats()
            assert stats["status"] == "insufficient_data"
        finally:
            relevance.AFFINITY_LOG = original_aff
            relevance.RECYCLING_LOG = original_rec
            affinity_path.unlink()
            recycling_path.unlink()


class TestTopCargo:
    """Tests for top cargo retrieval by score"""

    def test_returns_highest_scored_recent(self):
        """Returns highest-scored recent items sorted descending"""
        now = datetime.now(UTC)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            # Three items: one old (filtered out), two recent
            old_date = (now - timedelta(days=14)).isoformat()
            recent_date1 = (now - timedelta(days=1)).isoformat()
            recent_date2 = (now - timedelta(days=2)).isoformat()
            f.write(json.dumps({"timestamp": old_date, "score": "10", "title": "Old"}) + "\n")
            f.write(json.dumps({"timestamp": recent_date1, "score": "5", "title": "Mid"}) + "\n")
            f.write(json.dumps({"timestamp": recent_date2, "score": "9", "title": "High"}) + "\n")
        from metabolon.organelles.endocytosis_rss import relevance
        path = Path(f.name)
        original = relevance.AFFINITY_LOG
        try:
            relevance.AFFINITY_LOG = path
            items = top_cargo(limit=10, days=7)
            # Only the two recent, sorted highest first
            assert len(items) == 2
            assert items[0]["title"] == "High"
            assert items[1]["title"] == "Mid"
        finally:
            relevance.AFFINITY_LOG = original
            path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
