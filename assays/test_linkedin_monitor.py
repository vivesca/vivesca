"""Tests for effectors/linkedin-monitor — LinkedIn activity monitor."""
from __future__ import annotations

import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "linkedin-monitor"
    loader = SourceFileLoader("linkedin_monitor", str(module_path))
    spec = importlib.util.spec_from_loader("linkedin_monitor", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Unit tests: pure functions ───────────────────────────────────────────


class TestHashText:
    def test_deterministic(self):
        mod = _load_module()
        assert mod.hash_text("hello") == mod.hash_text("hello")

    def test_different_inputs_differ(self):
        mod = _load_module()
        assert mod.hash_text("foo") != mod.hash_text("bar")

    def test_length(self):
        mod = _load_module()
        assert len(mod.hash_text("anything")) == 16


class TestProfileSlug:
    def test_lowercase_and_dash(self):
        mod = _load_module()
        assert mod.profile_slug("John Doe") == "john-doe"

    def test_already_slug(self):
        mod = _load_module()
        assert mod.profile_slug("already-slug") == "already-slug"

    def test_uppercase(self):
        mod = _load_module()
        assert mod.profile_slug("ALLCAPS") == "allcaps"


class TestParseEvalResult:
    def test_valid_json_array(self):
        mod = _load_module()
        raw = json.dumps([
            {"text": "A" * 30, "timestamp": "2025-01-01", "url": ""},
        ])
        result = mod._parse_eval_result(raw)
        assert len(result) == 1
        assert result[0]["text"] == "A" * 30

    def test_empty_string(self):
        mod = _load_module()
        assert mod._parse_eval_result("") == []

    def test_double_encoded(self):
        mod = _load_module()
        inner = json.dumps([{"text": "B" * 30, "timestamp": "", "url": ""}])
        double = json.dumps(inner)  # double-wrapped
        result = mod._parse_eval_result(double)
        assert len(result) == 1

    def test_short_text_filtered(self):
        mod = _load_module()
        raw = json.dumps([{"text": "short", "timestamp": "", "url": ""}])
        assert mod._parse_eval_result(raw) == []

    def test_invalid_json(self):
        mod = _load_module()
        assert mod._parse_eval_result("not json at all") == []


class TestParseSnapshot:
    def test_extracts_long_lines(self):
        mod = _load_module()
        snapshot = "header\n" + "A" * 100 + "\n" + "B" * 100 + "\n"
        result = mod._parse_snapshot(snapshot)
        assert len(result) >= 1
        assert all("text" in p for p in result)

    def test_deduplicates(self):
        mod = _load_module()
        line = "X" * 100
        snapshot = line + "\n" + line + "\n"
        result = mod._parse_snapshot(snapshot)
        # Should deduplicate by first 80 chars
        keys = [p["text"][:80] for p in result]
        assert len(keys) == len(set(keys))

    def test_caps_at_20(self):
        mod = _load_module()
        lines = "\n".join(f"Line number {i} " + "Z" * 80 for i in range(50))
        result = mod._parse_snapshot(lines)
        assert len(result) <= 20

    def test_short_lines_ignored(self):
        mod = _load_module()
        snapshot = "short\nalso short\ntiny\n"
        assert mod._parse_snapshot(snapshot) == []


class TestIsAuthGated:
    def test_no_posts_with_auth_signal(self):
        mod = _load_module()
        assert mod.is_auth_gated([], "please sign in to continue") is True

    def test_no_posts_without_signal(self):
        mod = _load_module()
        assert mod.is_auth_gated([], "some normal content") is False

    def test_posts_present_not_gated(self):
        mod = _load_module()
        assert mod.is_auth_gated([{"text": "a post"}], "sign in") is False

    def test_authwall_signal(self):
        mod = _load_module()
        assert mod.is_auth_gated([], "authwall blocking page") is True


class TestFormatDigest:
    def test_basic_format(self):
        mod = _load_module()
        profile = {"name": "Jane Doe", "url": "https://linkedin.com/in/jane", "context": "VC"}
        posts = [
            {"text": "Exciting news about our Series A!", "timestamp": "2025-06-01", "url": "https://link"},
        ]
        result = mod.format_digest(profile, posts, new_count=1)
        assert "## Jane Doe" in result
        assert "**Context:** VC" in result
        assert "**New posts:** 1 of 1 seen" in result
        assert "### Post 1" in result
        assert "2025-06-01" in result
        assert "[View on LinkedIn](https://link)" in result

    def test_no_context(self):
        mod = _load_module()
        profile = {"name": "Bob", "url": "https://linkedin.com/in/bob"}
        posts = [{"text": "Hello world " * 5, "timestamp": "", "url": ""}]
        result = mod.format_digest(profile, posts, new_count=0)
        assert "**Context:**" not in result

    def test_no_timestamp(self):
        mod = _load_module()
        profile = {"name": "Alice", "url": "https://linkedin.com/in/alice"}
        posts = [{"text": "Some post content " * 5, "timestamp": "", "url": ""}]
        result = mod.format_digest(profile, posts, new_count=0)
        assert "### Post 1\n" in result


# ── Unit tests: seen post tracking ───────────────────────────────────────


class TestSeenTracking:
    def test_load_seen_empty(self, tmp_path, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")
        assert mod.load_seen("nobody") == set()

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")
        hashes = {"abc123", "def456"}
        mod.save_seen("test-slug", hashes)
        loaded = mod.load_seen("test-slug")
        assert loaded == hashes

    def test_load_seen_corrupt_json(self, tmp_path, monkeypatch):
        mod = _load_module()
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "bad.json").write_text("not valid json{")
        monkeypatch.setattr(mod, "CACHE_DIR", cache)
        assert mod.load_seen("bad") == set()


# ── Integration tests: main with mocking ─────────────────────────────────


class TestMainDryRun:
    def test_dry_run_no_profiles(self, monkeypatch, tmp_path):
        mod = _load_module()
        config_file = tmp_path / "linkedin-monitor.yaml"
        config_file.write_text("profiles: []\n")
        monkeypatch.setattr(mod, "CONFIG_PATH", config_file)
        monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog", "--dry-run"]))
        # Should not error, just print
        mod.main()

    def test_dry_run_with_profiles(self, monkeypatch, tmp_path, capsys):
        mod = _load_module()
        config_file = tmp_path / "linkedin-monitor.yaml"
        config_file.write_text(json.dumps({
            "profiles": [
                {"name": "Test User", "url": "https://linkedin.com/in/test"},
            ]
        }))
        monkeypatch.setattr(mod, "CONFIG_PATH", config_file)
        monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog", "--dry-run"]))
        mod.main()
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out

    def test_config_not_found(self, monkeypatch, tmp_path):
        mod = _load_module()
        monkeypatch.setattr(mod, "CONFIG_PATH", tmp_path / "nonexistent.yaml")
        monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog"]))
        with pytest.raises(SystemExit, match="1"):
            mod.main()


class TestFetchActivity:
    def test_fetch_activity_browser_open_fails(self, monkeypatch):
        mod = _load_module()
        monkeypatch.setattr(mod, "AGENT_BROWSER", "/nonexistent/ab")
        monkeypatch.setattr(mod, "_run", lambda *a, **kw: (False, "[error]"))
        monkeypatch.setattr(mod, "time", MagicMock())
        result = mod.fetch_activity("https://linkedin.com/in/test")
        assert result == []

    def test_fetch_activity_eval_returns_posts(self, monkeypatch):
        mod = _load_module()
        posts_json = json.dumps([
            {"text": "A" * 30, "timestamp": "2025-01-01", "url": ""},
        ])
        call_count = {"n": 0}

        def fake_run(cmd, timeout=30):
            call_count["n"] += 1
            # close → ok, open → ok, wait → ok, scroll → ok, eval → posts, close → ok
            if "eval" in cmd:
                return True, posts_json
            return True, "ok"

        monkeypatch.setattr(mod, "_run", fake_run)
        monkeypatch.setattr(mod, "time", MagicMock())
        result = mod.fetch_activity("https://linkedin.com/in/test")
        assert len(result) == 1
        assert result[0]["text"] == "A" * 30

    def test_fetch_activity_fallback_snapshot(self, monkeypatch):
        mod = _load_module()
        snapshot_text = "X" * 100 + "\n" + "Y" * 100 + "\n"

        def fake_run(cmd, timeout=30):
            if "eval" in cmd:
                return True, ""  # eval returns nothing
            if "snapshot" in cmd:
                return True, snapshot_text
            return True, "ok"

        monkeypatch.setattr(mod, "_run", fake_run)
        monkeypatch.setattr(mod, "time", MagicMock())
        result = mod.fetch_activity("https://linkedin.com/in/test")
        assert len(result) >= 1


class TestMainWithFetch:
    def test_main_writes_digest(self, monkeypatch, tmp_path):
        mod = _load_module()
        config_file = tmp_path / "linkedin-monitor.yaml"
        config_file.write_text(json.dumps({
            "profiles": [
                {"name": "Test User", "url": "https://linkedin.com/in/test"},
            ]
        }))
        output_dir = tmp_path / "output"
        monkeypatch.setattr(mod, "CONFIG_PATH", config_file)
        monkeypatch.setattr(mod, "OUTPUT_DIR", output_dir)
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog"]))
        monkeypatch.setattr(mod, "INTER_PROFILE_DELAY", 0)

        posts = [{"text": "A great post " * 10, "timestamp": "2025-06-01", "url": ""}]
        monkeypatch.setattr(mod, "fetch_activity", lambda url: posts)

        mod.main()
        digest_files = list(output_dir.glob("linkedin-activity-*.md"))
        assert len(digest_files) == 1
        content = digest_files[0].read_text()
        assert "Test User" in content

    def test_main_no_posts(self, monkeypatch, tmp_path):
        mod = _load_module()
        config_file = tmp_path / "linkedin-monitor.yaml"
        config_file.write_text(json.dumps({
            "profiles": [
                {"name": "Quiet User", "url": "https://linkedin.com/in/quiet"},
            ]
        }))
        output_dir = tmp_path / "output"
        monkeypatch.setattr(mod, "CONFIG_PATH", config_file)
        monkeypatch.setattr(mod, "OUTPUT_DIR", output_dir)
        monkeypatch.setattr(mod, "CACHE_DIR", tmp_path / "cache")
        monkeypatch.setattr(mod, "sys", MagicMock(argv=["prog"]))
        monkeypatch.setattr(mod, "INTER_PROFILE_DELAY", 0)
        monkeypatch.setattr(mod, "fetch_activity", lambda url: [])

        mod.main()
        content = (output_dir / f"linkedin-activity-{mod.datetime.now().strftime('%Y-%m-%d')}.md").read_text()
        assert "No posts extracted" in content
