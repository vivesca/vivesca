from __future__ import annotations

"""Tests for x-feed-to-endocytosis — fetch X feed via bird CLI and cache articles."""

import hashlib
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load():
    """Load x-feed-to-endocytosis by exec-ing its Python body."""
    source = open(Path.home() / "germline" / "effectors" / "x-feed-to-endocytosis").read()
    ns: dict = {"__name__": "x_feed_to_endocytosis"}
    exec(source, ns)
    return ns


_mod = _load()
main = _mod["main"]
CACHE_DIR = _mod["CACHE_DIR"]
COUNT = _mod["COUNT"]
MIN_TEXT_LENGTH = _mod["MIN_TEXT_LENGTH"]


@contextmanager
def _cache_dir(target: Path):
    """Temporarily swap CACHE_DIR in the exec'd namespace."""
    original = _mod["CACHE_DIR"]
    _mod["CACHE_DIR"] = target
    try:
        yield
    finally:
        _mod["CACHE_DIR"] = original


# ── helper: build a fake tweet ──────────────────────────────────────


def _tweet(
    text="A" * 150,
    handle="testuser",
    name="Test User",
    url="https://x.com/testuser/status/123",
    date="Mon Jan 01 12:00:00 +0000 2025",
    quoted_tweet=None,
):
    t = {
        "text": text,
        "author": {"handle": handle, "name": name},
        "url": url,
        "date": date,
    }
    if quoted_tweet is not None:
        t["quoted_tweet"] = quoted_tweet
    return t


def _mock_run(stdout_json, returncode=0):
    """Return a mock subprocess.run result."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout_json
    m.stderr = ""
    return m


# ── constants / module loading ───────────────────────────────────────


def test_module_loads():
    """Module loads and exposes expected constants."""
    assert COUNT == 20
    assert MIN_TEXT_LENGTH == 100
    assert str(CACHE_DIR).endswith(".cache/endocytosis-articles")


def test_cache_dir_under_home():
    """CACHE_DIR is under the user's home directory."""
    assert Path.home() / ".cache" / "endocytosis-articles" == CACHE_DIR


# ── bird CLI failure ─────────────────────────────────────────────────


def test_bird_failure_exits():
    """main exits 1 when bird CLI returns non-zero."""
    with patch("subprocess.run", return_value=_mock_run("", returncode=1)):
        with patch("sys.argv", ["x-feed-to-endocytosis"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


# ── single tweet saved ────────────────────────────────────────────────


def test_single_tweet_saved(tmp_path):
    """A long-enough tweet is saved as a JSON cache file."""
    tweet = _tweet()
    tweets_json = json.dumps([tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1

    record = json.loads(files[0].read_text())
    assert record["source"] == "X Feed (For You)"
    assert record["tier"] == 1
    assert record["link"] == tweet["url"]
    assert "Test User" in record["title"]
    assert "@testuser" in record["title"]


# ── short tweet skipped ──────────────────────────────────────────────


def test_short_tweet_skipped(tmp_path):
    """Tweets shorter than MIN_TEXT_LENGTH are skipped."""
    short_tweet = _tweet(text="hi")
    tweets_json = json.dumps([short_tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert list(tmp_path.glob("*.json")) == []


# ── duplicate not overwritten ─────────────────────────────────────────


def test_duplicate_not_overwritten(tmp_path):
    """An already-cached tweet is not re-written."""
    tweet = _tweet()
    tweets_json = json.dumps([tweet])

    # Pre-create the file so it already exists
    text = tweet["text"]
    title_hash = hashlib.sha256(text[:200].encode()).hexdigest()[:8]
    filename = f"2025-01-01_x-feed_{title_hash}.json"
    existing = tmp_path / filename
    existing.write_text('{"old": true}')

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    record = json.loads(existing.read_text())
    assert record == {"old": True}


# ── quoted tweet appended ─────────────────────────────────────────────


def test_quoted_tweet_appended(tmp_path):
    """Quoted tweet text is appended to the main text."""
    tweet = _tweet(text="B" * 120, quoted_tweet={"text": "C" * 120})
    tweets_json = json.dumps([tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text())
    assert "C" * 10 in record["summary"]


# ── date parsing ──────────────────────────────────────────────────────


def test_date_parsing(tmp_path):
    """Tweet date is parsed into YYYY-MM-DD format for the filename."""
    tweet = _tweet(date="Wed Mar 15 09:30:00 +0000 2025")
    tweets_json = json.dumps([tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    files = list(tmp_path.glob("2025-03-15_*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text())
    assert record["date"] == "2025-03-15"


def test_bad_date_uses_today(tmp_path):
    """Bad/missing date falls back to today's date."""
    tweet = _tweet(date="not-a-date")
    tweets_json = json.dumps([tweet])
    today_str = datetime.now(UTC).strftime("%Y-%m-%d")

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert len(list(tmp_path.glob(f"{today_str}_*.json"))) == 1


def test_missing_date_uses_today(tmp_path):
    """Missing date field falls back to today's date."""
    tweet = _tweet()
    del tweet["date"]
    tweets_json = json.dumps([tweet])
    today_str = datetime.now(UTC).strftime("%Y-%m-%d")

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert len(list(tmp_path.glob(f"{today_str}_*.json"))) == 1


# ── single object (non-list) response ────────────────────────────────


def test_single_object_response(tmp_path):
    """A single tweet object (not a list) is handled correctly."""
    tweet = _tweet()
    tweets_json = json.dumps(tweet)  # no list wrapper

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert len(list(tmp_path.glob("*.json"))) == 1


# ── mixed long and short tweets ───────────────────────────────────────


def test_mixed_tweets(tmp_path, capsys):
    """Only long-enough tweets are saved; summary printed to stderr."""
    long_tweet = _tweet(text="A" * 150, handle="longuser")
    short_tweet = _tweet(text="hi", handle="shortuser")
    tweets_json = json.dumps([long_tweet, short_tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert len(list(tmp_path.glob("*.json"))) == 1

    captured = capsys.readouterr()
    assert "1 saved" in captured.err
    assert "1 skipped" in captured.err
    assert "2 total" in captured.err


# ── subprocess.run called with correct args ───────────────────────────


def test_subprocess_called_correctly(tmp_path):
    """subprocess.run is called with bird home --count 20 --json."""
    tweets_json = json.dumps([_tweet()])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)) as mock_run:
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd == ["bird", "home", "--count", "20", "--json"]
    assert mock_run.call_args[1]["capture_output"] is True
    assert mock_run.call_args[1]["timeout"] == 60


# ── cache dir created if missing ──────────────────────────────────────


def test_cache_dir_created(tmp_path):
    """CACHE_DIR is created with parents if it doesn't exist."""
    deep_dir = tmp_path / "nested" / "dir"
    tweet = _tweet()
    tweets_json = json.dumps([tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(deep_dir):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    assert deep_dir.exists()
    assert len(list(deep_dir.glob("*.json"))) == 1


# ── record has all expected fields ────────────────────────────────────


def test_record_fields(tmp_path):
    """Saved record contains all required fields."""
    tweet = _tweet()
    tweets_json = json.dumps([tweet])

    with patch("subprocess.run", return_value=_mock_run(tweets_json)):
        with _cache_dir(tmp_path):
            with patch("sys.argv", ["x-feed-to-endocytosis"]):
                main()

    record = json.loads(next(iter(tmp_path.glob("*.json"))).read_text())
    for key in ("title", "date", "source", "tier", "link", "summary", "text", "fetched_at"):
        assert key in record, f"missing key: {key}"
    # fetched_at should be a valid ISO timestamp
    datetime.fromisoformat(record["fetched_at"])
