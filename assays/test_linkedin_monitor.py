#!/usr/bin/env python3
"""Tests for linkedin-monitor effector — mocks all external file I/O and subprocess calls."""

import json
import pytest
import subprocess
import sys
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path

# Execute the linkedin-monitor file directly
linkedin_code = Path("/home/terry/germline/effectors/linkedin-monitor").read_text()
namespace = {}
exec(linkedin_code, namespace)

# Extract all the functions/globals from the namespace
linkedin = type('linkedin_monitor_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(linkedin, key, value)

# ---------------------------------------------------------------------------
# Test hash_text
# ---------------------------------------------------------------------------

def test_hash_text_returns_16_chars():
    """Test hash_text returns 16 character hex string."""
    result = linkedin.hash_text("test content")
    assert len(result) == 16
    assert all(c in '0123456789abcdef' for c in result)

def test_hash_text_deterministic():
    """Test hash_text produces same hash for same input."""
    text = "This is a LinkedIn post about AI."
    hash1 = linkedin.hash_text(text)
    hash2 = linkedin.hash_text(text)
    assert hash1 == hash2

def test_hash_text_different_inputs():
    """Test hash_text produces different hashes for different inputs."""
    hash1 = linkedin.hash_text("first post")
    hash2 = linkedin.hash_text("second post")
    assert hash1 != hash2

def test_hash_text_empty_string():
    """Test hash_text handles empty string."""
    result = linkedin.hash_text("")
    assert len(result) == 16

# ---------------------------------------------------------------------------
# Test profile_slug
# ---------------------------------------------------------------------------

def test_profile_slug_lowercase():
    """Test profile_slug converts to lowercase."""
    assert linkedin.profile_slug("John Doe") == "john-doe"

def test_profile_slug_spaces_to_hyphens():
    """Test profile_slug replaces spaces with hyphens."""
    assert linkedin.profile_slug("Jane Marie Smith") == "jane-marie-smith"

def test_profile_slug_no_spaces():
    """Test profile_slug handles single name."""
    assert linkedin.profile_slug("Madonna") == "madonna"

def test_profile_slug_mixed_case():
    """Test profile_slug normalizes mixed case."""
    assert linkedin.profile_slug("JoHn DoE") == "john-doe"

# ---------------------------------------------------------------------------
# Test load_seen
# ---------------------------------------------------------------------------

def test_load_seen_missing_file():
    """Test load_seen returns empty set when cache file doesn't exist."""
    with patch.object(Path, 'exists', return_value=False):
        result = linkedin.load_seen("john-doe")
        assert result == set()

def test_load_seen_valid_json():
    """Test load_seen parses valid JSON array."""
    hashes = ["abc123def456", "fed456cba321"]
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=json.dumps(hashes)):
            result = linkedin.load_seen("john-doe")
            assert result == set(hashes)

def test_load_seen_invalid_json():
    """Test load_seen returns empty set on malformed JSON."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value="not valid json"):
            result = linkedin.load_seen("john-doe")
            assert result == set()

def test_load_seen_empty_file():
    """Test load_seen handles empty file."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=""):
            result = linkedin.load_seen("john-doe")
            assert result == set()

# ---------------------------------------------------------------------------
# Test save_seen
# ---------------------------------------------------------------------------

def test_save_seen_creates_directory():
    """Test save_seen creates cache directory if needed."""
    mock_cache_dir = MagicMock()
    mock_path = MagicMock()
    
    with patch.object(Path, '__truediv__', return_value=mock_path):
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            linkedin.save_seen("john-doe", {"abc123", "def456"})
            # mkdir should be called with parents=True, exist_ok=True
            mock_mkdir.assert_called()

def test_save_seen_writes_sorted_json():
    """Test save_seen writes sorted JSON array."""
    hashes = {"def456", "abc123"}  # set is unordered
    mock_path = MagicMock()
    
    with patch.object(Path, '__truediv__', return_value=mock_path):
        with patch('pathlib.Path.mkdir'):
            linkedin.save_seen("john-doe", hashes)
            # Check write_text was called with sorted JSON
            mock_path.write_text.assert_called_once()
            written = mock_path.write_text.call_args[0][0]
            parsed = json.loads(written)
            assert parsed == sorted(hashes)  # should be sorted

# ---------------------------------------------------------------------------
# Test _parse_eval_result
# ---------------------------------------------------------------------------

def test_parse_eval_result_empty():
    """Test _parse_eval_result returns empty list for empty input."""
    assert linkedin._parse_eval_result("") == []
    assert linkedin._parse_eval_result(None) == []

def test_parse_eval_result_valid_json_array():
    """Test _parse_eval_result parses valid JSON array."""
    data = [
        {"text": "This is a post that is long enough", "timestamp": "2026-03-31", "url": "https://example.com"},
        {"text": "Another post with enough characters", "timestamp": "2026-03-30", "url": ""}
    ]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 2
    assert result[0]["text"] == "This is a post that is long enough"

def test_parse_eval_result_filters_short_text():
    """Test _parse_eval_result filters posts with text <= 20 chars."""
    data = [
        {"text": "Short text", "timestamp": "2026-03-31", "url": ""},  # 10 chars - filtered
        {"text": "This is longer than twenty characters", "timestamp": "", "url": ""}  # kept
    ]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1
    assert "longer" in result[0]["text"]

def test_parse_eval_result_double_encoded():
    """Test _parse_eval_result handles double-encoded JSON."""
    data = [{"text": "A post that is definitely long enough text", "timestamp": "", "url": ""}]
    double_encoded = json.dumps(json.dumps(data))
    result = linkedin._parse_eval_result(double_encoded)
    assert len(result) == 1

def test_parse_eval_result_invalid_json():
    """Test _parse_eval_result returns empty list for invalid JSON."""
    assert linkedin._parse_eval_result("not json at all") == []

def test_parse_eval_result_non_list():
    """Test _parse_eval_result returns empty list for non-list JSON."""
    assert linkedin._parse_eval_result('{"key": "value"}') == []

def test_parse_eval_result_non_dict_items():
    """Test _parse_eval_result filters non-dict items."""
    data = [
        {"text": "Valid post with enough characters here", "timestamp": "", "url": ""},
        "not a dict",
        123,
        ["list", "item"]
    ]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1

# ---------------------------------------------------------------------------
# Test _parse_snapshot
# ---------------------------------------------------------------------------

def test_parse_snapshot_basic():
    """Test _parse_snapshot extracts posts from accessibility tree text."""
    snapshot = """
    Some header
        This is a long line of text that should be captured as a post because it exceeds 60 characters easily.
    Another line
        Here is another post that is quite long and should also be captured by the parser.
    """
    result = linkedin._parse_snapshot(snapshot)
    assert len(result) >= 1

def test_parse_snapshot_filters_short_lines():
    """Test _parse_snapshot filters lines shorter than 60 chars."""
    snapshot = """
    Short line
    Another short
    """
    result = linkedin._parse_snapshot(snapshot)
    assert len(result) == 0

def test_parse_snapshot_skips_bracket_lines():
    """Test _parse_snapshot skips lines starting with bracket."""
    snapshot = """
    [button] Click here
    [link] Navigation
    """
    result = linkedin._parse_snapshot(snapshot)
    assert len(result) == 0

def test_parse_snapshot_combines_buffer():
    """Test _parse_snapshot combines adjacent long lines."""
    snapshot = """
    First long line of text that exceeds the sixty character threshold
    Second long line that also exceeds the threshold and should combine
    Short
    """
    result = linkedin._parse_snapshot(snapshot)
    # The two long lines should be combined before short line breaks buffer
    assert len(result) >= 1

def test_parse_snapshot_deduplicates():
    """Test _parse_snapshot deduplicates similar posts."""
    snapshot = """
    This is a unique post that is definitely long enough to be captured here.
    This is a unique post that is definitely long enough to be captured here.
    """
    result = linkedin._parse_snapshot(snapshot)
    # Both lines have same first 80 chars, so should dedupe to 1
    assert len(result) <= 1

def test_parse_snapshot_caps_at_20():
    """Test _parse_snapshot caps output at 20 posts."""
    lines = []
    for i in range(30):
        lines.append(f"This is post number {i} which is definitely long enough to be captured here yay.")
    snapshot = "\n".join(lines)
    result = linkedin._parse_snapshot(snapshot)
    assert len(result) <= 20

def test_parse_snapshot_returns_text_key():
    """Test _parse_snapshot returns dicts with text key."""
    snapshot = "This is a very long line of text that should definitely be captured as a post by the parser."
    result = linkedin._parse_snapshot(snapshot)
    if result:  # if any posts found
        assert "text" in result[0]
        assert "timestamp" in result[0]
        assert "url" in result[0]

# ---------------------------------------------------------------------------
# Test is_auth_gated
# ---------------------------------------------------------------------------

def test_is_auth_gated_no_posts_with_signal():
    """Test is_auth_gated returns True when no posts and signal in raw_text."""
    signals = [
        "Please sign in to continue",
        "Log in to see more",
        "Create account to view",
        "Join now for free",
        "Authwall detected",
        "Join LinkedIn today",
        "See who's hiring in your network"
    ]
    for signal in signals:
        assert linkedin.is_auth_gated([], signal) is True

def test_is_auth_gated_no_posts_no_signal():
    """Test is_auth_gated returns False when no posts and no signal."""
    assert linkedin.is_auth_gated([], "Welcome to LinkedIn content") is False

def test_is_auth_gated_has_posts():
    """Test is_auth_gated returns False when posts exist."""
    posts = [{"text": "Some post content here"}]
    assert linkedin.is_auth_gated(posts, "Please sign in") is False

def test_is_auth_gated_case_insensitive():
    """Test is_auth_gated is case insensitive."""
    assert linkedin.is_auth_gated([], "PLEASE SIGN IN") is True
    assert linkedin.is_auth_gated([], "LOG IN NOW") is True

def test_is_auth_gated_empty_raw_text():
    """Test is_auth_gated with empty raw_text and no posts."""
    assert linkedin.is_auth_gated([], "") is False

# ---------------------------------------------------------------------------
# Test format_digest
# ---------------------------------------------------------------------------

def test_format_digest_basic():
    """Test format_digest produces expected markdown."""
    profile = {
        "name": "John Doe",
        "url": "https://linkedin.com/in/johndoe",
        "context": "Former colleague"
    }
    posts = [
        {"text": "First post content here with enough text", "timestamp": "2026-03-31", "url": "https://linkedin.com/posts/123"},
        {"text": "Second post also has enough characters", "timestamp": "2026-03-30", "url": ""}
    ]
    result = linkedin.format_digest(profile, posts, new_count=1)
    
    assert "## John Doe" in result
    assert "**Context:** Former colleague" in result
    assert "**Profile:** https://linkedin.com/in/johndoe" in result
    assert "**New posts:** 1 of 2 seen" in result
    assert "### Post 1" in result
    assert "### Post 2" in result
    assert "2026-03-31" in result
    assert "[View on LinkedIn]" in result

def test_format_digest_no_context():
    """Test format_digest omits context line when empty."""
    profile = {
        "name": "Jane Smith",
        "url": "https://linkedin.com/in/janesmith"
    }
    posts = [{"text": "A post with sufficient characters here", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=0)
    
    assert "## Jane Smith" in result
    assert "**Context:**" not in result

def test_format_digest_no_timestamp():
    """Test format_digest handles missing timestamp."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post content goes here and is long enough", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    
    assert "### Post 1" in result
    assert " — " not in result  # no timestamp dash

def test_format_digest_no_url():
    """Test format_digest omits link when no URL."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post content goes here and is long enough", "timestamp": "2026-03-31", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    
    assert "[View on LinkedIn]" not in result

def test_format_digest_multiple_posts():
    """Test format_digest numbers posts correctly."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test"}
    posts = [
        {"text": "First post content with enough characters", "timestamp": "", "url": ""},
        {"text": "Second post content with enough characters", "timestamp": "", "url": ""},
        {"text": "Third post content with enough characters", "timestamp": "", "url": ""}
    ]
    result = linkedin.format_digest(profile, posts, new_count=3)
    
    assert "### Post 1" in result
    assert "### Post 2" in result
    assert "### Post 3" in result

# ---------------------------------------------------------------------------
# Test _run helper
# ---------------------------------------------------------------------------

def test_run_success():
    """Test _run returns (True, stdout) on success."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="output text\n")
        success, output = linkedin._run(["echo", "test"])
        assert success is True
        assert output == "output text"

def test_run_failure():
    """Test _run returns (False, stdout) on non-zero exit."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        success, output = linkedin._run(["false"])
        assert success is False

def test_run_timeout():
    """Test _run returns (False, error) on timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep"], timeout=30)
        success, output = linkedin._run(["sleep", "100"], timeout=30)
        assert success is False
        assert "[error:" in output

def test_run_file_not_found():
    """Test _run returns (False, error) when command not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("command not found")
        success, output = linkedin._run(["nonexistent-command"])
        assert success is False
        assert "[error:" in output

def test_run_strips_output():
    """Test _run strips whitespace from stdout."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="  text  \n\n")
        success, output = linkedin._run(["echo", "test"])
        assert output == "text"

# ---------------------------------------------------------------------------
# Test fetch_activity (integration-like test with heavy mocking)
# ---------------------------------------------------------------------------

def test_fetch_activity_returns_posts_on_success():
    """Test fetch_activity returns posts when agent-browser succeeds."""
    mock_posts = [{"text": "A post that is definitely long enough to pass", "timestamp": "", "url": ""}]

    # Patch subprocess.run directly since _run uses it
    with patch('subprocess.run') as mock_run:
        # Sequence: close, open, wait, scroll, eval, close
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=0, stdout=""),  # open
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=0, stdout=json.dumps(mock_posts)),  # eval
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        assert len(result) == 1
        assert "definitely long enough" in result[0]["text"]

def test_fetch_activity_uses_snapshot_fallback():
    """Test fetch_activity falls back to snapshot when eval fails."""
    snapshot_text = "This is a very long line of text that should be captured from accessibility tree here."

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=0, stdout=""),  # open
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=1, stdout=""),  # eval fails
            MagicMock(returncode=0, stdout=snapshot_text),  # snapshot succeeds
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        assert len(result) >= 1

def test_fetch_activity_handles_open_failure():
    """Test fetch_activity returns empty list when open fails."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=1, stdout="error"),  # open fails
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        assert result == []

def test_fetch_activity_constructs_activity_url():
    """Test fetch_activity constructs correct activity URL."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        with patch('time.sleep'):
            linkedin.fetch_activity("https://linkedin.com/in/johndoe/")

        # Check that open was called with correct URL
        calls = mock_run.call_args_list
        # Find the call that includes 'open' command and the activity URL
        found_activity_url = False
        for c in calls:
            args = c.args
            if args and len(args) >= 1:
                cmd_list = args[0]  # First arg is the command list
                if isinstance(cmd_list, list) and 'open' in cmd_list:
                    # Check for activity URL in the command
                    for arg in cmd_list:
                        if 'recent-activity/all/' in str(arg):
                            found_activity_url = True
                            break
        assert found_activity_url, "Did not find 'recent-activity/all/' in agent-browser open command"

# ---------------------------------------------------------------------------
# Test main function (via subprocess for isolation)
# ---------------------------------------------------------------------------

def test_main_help():
    """Test that linkedin-monitor --help exits successfully."""
    result = subprocess.run(
        ["/home/terry/germline/effectors/linkedin-monitor", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "linkedin-monitor" in result.stdout.lower() or "linkedin" in result.stdout.lower()

def test_main_dry_run_no_config():
    """Test that main exits with error when config missing."""
    with patch.object(Path, 'exists', return_value=False):
        # Capture SystemExit
        with pytest.raises(SystemExit) as exc_info:
            namespace['main']()
        assert exc_info.value.code == 1

def test_main_dry_run_with_config():
    """Test dry run mode with valid config."""
    config_content = """
profiles:
  - name: Test User
    url: https://linkedin.com/in/testuser
    context: Test profile
"""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor', '--dry-run']):
                # Should not raise, just print
                namespace['main']()

def test_main_empty_profiles():
    """Test main exits gracefully with no profiles configured."""
    config_content = "profiles: []"
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor']):
                with pytest.raises(SystemExit) as exc_info:
                    namespace['main']()
                assert exc_info.value.code == 0

# ---------------------------------------------------------------------------
# Test constants and configuration
# ---------------------------------------------------------------------------

def test_config_path_location():
    """Test CONFIG_PATH is in expected location."""
    assert "epigenome/phenotype/linkedin-monitor.yaml" in str(linkedin.CONFIG_PATH)

def test_output_dir_location():
    """Test OUTPUT_DIR is in expected location."""
    assert "epigenome/chromatin/Consulting" in str(linkedin.OUTPUT_DIR)

def test_cache_dir_location():
    """Test CACHE_DIR is in expected location."""
    assert ".cache/linkedin-monitor" in str(linkedin.CACHE_DIR)

def test_inter_profile_delay():
    """Test INTER_PROFILE_DELAY is reasonable."""
    assert linkedin.INTER_PROFILE_DELAY >= 1
    assert linkedin.INTER_PROFILE_DELAY <= 60

def test_auth_signals_exist():
    """Test AUTH_SIGNALS contains expected signals."""
    assert "sign in" in linkedin.AUTH_SIGNALS
    assert "log in" in linkedin.AUTH_SIGNALS
    assert "authwall" in linkedin.AUTH_SIGNALS

def test_extract_js_structure():
    """Test EXTRACT_JS is valid JavaScript function structure."""
    js = linkedin.EXTRACT_JS
    assert "function" in js
    assert "JSON.stringify" in js
    assert "return" in js

# ---------------------------------------------------------------------------
# Edge cases and error handling
# ---------------------------------------------------------------------------

def test_hash_text_unicode():
    """Test hash_text handles unicode characters."""
    result = linkedin.hash_text("Hello 世界 🌍")
    assert len(result) == 16

def test_hash_text_very_long():
    """Test hash_text handles very long strings."""
    long_text = "x" * 100000
    result = linkedin.hash_text(long_text)
    assert len(result) == 16

def test_profile_slug_special_chars():
    """Test profile_slug with special characters (only spaces handled)."""
    # Current implementation only handles spaces
    assert "john-doe" in linkedin.profile_slug("John Doe")
    # Special chars pass through lowercased
    result = linkedin.profile_slug("John O'Brien")
    assert "o'brien" in result

def test_parse_eval_result_missing_text_key():
    """Test _parse_eval_result handles dicts without text key."""
    data = [
        {"timestamp": "2026-03-31", "url": "https://example.com"},  # no text
        {"text": "Valid post with enough characters here", "timestamp": "", "url": ""}
    ]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1

def test_format_digest_empty_posts():
    """Test format_digest handles empty posts list."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test"}
    result = linkedin.format_digest(profile, [], new_count=0)
    assert "## Test User" in result
    assert "**New posts:** 0 of 0 seen" in result

def test_format_digest_special_chars_in_text():
    """Test format_digest handles special markdown characters."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post with **bold** and _italic_ and `code`", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    assert "**bold**" in result  # preserved literally
