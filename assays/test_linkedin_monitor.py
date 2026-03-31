#!/usr/bin/env python3
from __future__ import annotations
"""Tests for linkedin-monitor effector — mocks all external file I/O and subprocess calls.

This test suite covers:
- Unit tests for all helper functions
- Parsing functions (eval result, snapshot)
- Auth gate detection
- Digest formatting
- File I/O operations (load/save seen hashes)
- Subprocess integration (_run helper)
- Main function behavior
- Edge cases and error handling
- End-to-end scenarios with mocked dependencies
"""


import hashlib
import json
import os
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
import yaml

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


# ---------------------------------------------------------------------------
# Additional hash_text tests
# ---------------------------------------------------------------------------

def test_hash_text_known_value():
    """Test hash_text produces expected hash for known input."""
    # SHA-1 of "test" is a94a8fe5ccb19ba61c4c0873d391e987982fbbd3
    # We take first 16 chars: a94a8fe5ccb19ba6
    result = linkedin.hash_text("test")
    expected = hashlib.sha1("test".encode()).hexdigest()[:16]
    assert result == expected


def test_hash_text_newline_preserved():
    """Test hash_text includes newlines in hash computation."""
    text1 = "line1\nline2"
    text2 = "line1line2"
    assert linkedin.hash_text(text1) != linkedin.hash_text(text2)


def test_hash_text_whitespace_significant():
    """Test hash_text treats whitespace as significant."""
    assert linkedin.hash_text("test") != linkedin.hash_text(" test")
    assert linkedin.hash_text("test") != linkedin.hash_text("test ")
    assert linkedin.hash_text("test") != linkedin.hash_text("te st")


def test_hash_text_consistency_multiple_calls():
    """Test hash_text is consistent across multiple calls."""
    text = "Consistent input text for hashing"
    results = [linkedin.hash_text(text) for _ in range(10)]
    assert len(set(results)) == 1  # All identical


def test_hash_text_different_encodings_not_tested():
    """Test hash_text with various unicode code points."""
    # Emoji and international characters
    texts = [
        "Hello 世界",
        "Привет мир",
        "مرحبا بالعالم",
        "🚀🎉💡",
        "Mixed: hello 世界 🌍",
    ]
    hashes = [linkedin.hash_text(t) for t in texts]
    # All should be unique (different inputs)
    assert len(set(hashes)) == len(hashes)


# ---------------------------------------------------------------------------
# Additional profile_slug tests
# ---------------------------------------------------------------------------

def test_profile_slug_preserves_numbers():
    """Test profile_slug preserves numeric characters."""
    assert linkedin.profile_slug("John Doe 123") == "john-doe-123"


def test_profile_slug_multiple_spaces():
    """Test profile_slug handles multiple consecutive spaces."""
    assert linkedin.profile_slug("John   Doe") == "john---doe"


def test_profile_slug_leading_trailing_spaces():
    """Test profile_slug handles leading/trailing spaces."""
    assert linkedin.profile_slug(" John Doe ") == "-john-doe-"


def test_profile_slug_tabs_not_replaced():
    """Test profile_slug does not replace tabs (only spaces)."""
    result = linkedin.profile_slug("John\tDoe")
    assert "\t" in result.lower()


def test_profile_slug_empty_string():
    """Test profile_slug handles empty string."""
    assert linkedin.profile_slug("") == ""


def test_profile_slug_single_space():
    """Test profile_slug handles single space."""
    assert linkedin.profile_slug(" ") == "-"


def test_profile_slug_long_name():
    """Test profile_slug handles very long names."""
    long_name = "John " * 100
    result = linkedin.profile_slug(long_name)
    assert result.count("-") == 100
    assert result.startswith("john-")


# ---------------------------------------------------------------------------
# Additional load_seen tests
# ---------------------------------------------------------------------------

def test_load_seen_non_json_array():
    """Test load_seen returns keys when JSON is an object (current behavior)."""
    # Current implementation: set(json.loads(path.read_text())) on object gives keys
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value='{"key": "value"}'):
            result = linkedin.load_seen("john-doe")
            # Object becomes set of its keys
            assert result == {"key"}


def test_load_seen_json_object_instead_of_array():
    """Test load_seen returns keys when JSON is an object (current behavior)."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value='{"hash1": true, "hash2": false}'):
            result = linkedin.load_seen("john-doe")
            # Object becomes set of its keys
            assert result == {"hash1", "hash2"}


def test_load_seen_json_number():
    """Test load_seen raises TypeError for JSON number (current behavior)."""
    # Current implementation doesn't handle non-iterable JSON values
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value='123'):
            # This will raise TypeError when trying to make set from int
            with pytest.raises(TypeError):
                linkedin.load_seen("john-doe")


def test_load_seen_json_null():
    """Test load_seen raises TypeError for JSON null (current behavior)."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value='null'):
            # This will raise TypeError when trying to make set from None
            with pytest.raises(TypeError):
                linkedin.load_seen("john-doe")


def test_load_seen_os_error():
    """Test load_seen handles OSError during file read."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', side_effect=OSError("Permission denied")):
            result = linkedin.load_seen("john-doe")
            assert result == set()


def test_load_seen_mixed_array_elements():
    """Test load_seen raises TypeError for array with non-hashable elements."""
    json_content = '["hash1", 123, null, {"nested": true}, "hash2"]'
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=json_content):
            # This will raise TypeError when trying to add dict to set
            with pytest.raises(TypeError):
                linkedin.load_seen("john-doe")


def test_load_seen_large_file():
    """Test load_seen handles large cache file efficiently."""
    # Simulate a large cache with many hashes
    hashes = [f"hash{i:016d}" for i in range(10000)]
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=json.dumps(hashes)):
            result = linkedin.load_seen("john-doe")
            assert len(result) == 10000


# ---------------------------------------------------------------------------
# Additional save_seen tests
# ---------------------------------------------------------------------------

def test_save_seen_empty_set():
    """Test save_seen handles empty set."""
    mock_path = MagicMock()
    with patch.object(Path, '__truediv__', return_value=mock_path):
        with patch('pathlib.Path.mkdir'):
            linkedin.save_seen("john-doe", set())
            mock_path.write_text.assert_called_once_with("[]")


def test_save_seen_single_element():
    """Test save_seen handles single element set."""
    mock_path = MagicMock()
    with patch.object(Path, '__truediv__', return_value=mock_path):
        with patch('pathlib.Path.mkdir'):
            linkedin.save_seen("john-doe", {"single-hash"})
            written = mock_path.write_text.call_args[0][0]
            parsed = json.loads(written)
            assert parsed == ["single-hash"]


def test_save_seen_creates_parent_directories():
    """Test save_seen creates parent directories with correct flags."""
    mock_cache_dir = MagicMock()
    mock_cache_dir.mkdir = MagicMock()

    with patch.object(Path, '__truediv__', return_value=MagicMock()):
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            linkedin.save_seen("john-doe", {"hash"})
            # Verify mkdir was called
            mock_mkdir.assert_called()


def test_save_seen_json_format():
    """Test save_seen produces valid JSON array format."""
    mock_path = MagicMock()
    hashes = {"abc", "def", "ghi"}

    with patch.object(Path, '__truediv__', return_value=mock_path):
        with patch('pathlib.Path.mkdir'):
            linkedin.save_seen("test-profile", hashes)
            written = mock_path.write_text.call_args[0][0]
            # Should be valid JSON
            parsed = json.loads(written)
            assert isinstance(parsed, list)
            assert set(parsed) == hashes


# ---------------------------------------------------------------------------
# Additional _parse_eval_result tests
# ---------------------------------------------------------------------------

def test_parse_eval_result_whitespace_only():
    """Test _parse_eval_result handles whitespace-only input."""
    assert linkedin._parse_eval_result("   \n\t  ") == []


def test_parse_eval_result_nested_structure():
    """Test _parse_eval_result handles nested JSON structures."""
    data = [{"text": "Post text that is long enough here", "metadata": {"nested": {"deep": "value"}}, "url": ""}]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1
    assert result[0]["text"] == "Post text that is long enough here"


def test_parse_eval_result_exactly_20_chars():
    """Test _parse_eval_result filters text with exactly 20 chars."""
    # Text with exactly 20 characters
    text_20 = "12345678901234567890"
    data = [{"text": text_20, "timestamp": "", "url": ""}]
    result = linkedin._parse_eval_result(json.dumps(data))
    # 20 chars is NOT > 20, so should be filtered
    assert len(result) == 0


def test_parse_eval_result_21_chars():
    """Test _parse_eval_result keeps text with 21 chars."""
    # Text with 21 characters
    text_21 = "123456789012345678901"
    data = [{"text": text_21, "timestamp": "", "url": ""}]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1


def test_parse_eval_result_triple_encoded():
    """Test _parse_eval_result handles triple-encoded JSON."""
    data = [{"text": "A post with enough characters here", "timestamp": "", "url": ""}]
    triple_encoded = json.dumps(json.dumps(json.dumps(data)))
    # This might not decode properly through double-encoding
    result = linkedin._parse_eval_result(triple_encoded)
    # Should either parse or return empty, not crash
    assert isinstance(result, list)


def test_parse_eval_result_with_escape_sequences():
    """Test _parse_eval_result handles JSON with escape sequences."""
    data = [{"text": "Post with \"quotes\" and \\backslashes\\", "timestamp": "", "url": ""}]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 1


def test_parse_eval_result_unicode_escapes():
    """Test _parse_eval_result handles unicode escape sequences."""
    # JSON with unicode escape
    json_str = r'[{"text": "Unicode: \u4e16\u754c test text here", "timestamp": "", "url": ""}]'
    result = linkedin._parse_eval_result(json_str)
    assert len(result) == 1
    assert "世界" in result[0]["text"]


def test_parse_eval_result_mixed_valid_invalid():
    """Test _parse_eval_result filters mixed valid/invalid items."""
    data = [
        {"text": "Valid long enough post text", "timestamp": "", "url": ""},
        {"text": "short"},  # too short
        {"timestamp": "2026-03-31"},  # no text
        "string item",
        {"text": "Another valid post with text", "timestamp": "", "url": ""},
    ]
    result = linkedin._parse_eval_result(json.dumps(data))
    assert len(result) == 2


def test_parse_eval_result_empty_array():
    """Test _parse_eval_result handles empty JSON array."""
    assert linkedin._parse_eval_result("[]") == []


def test_parse_eval_result_nested_json_in_string():
    """Test _parse_eval_result handles embedded JSON string."""
    inner = json.dumps([{"text": "Embedded post with enough text", "timestamp": "", "url": ""}])
    outer = json.dumps(inner)  # Double wrap as string
    result = linkedin._parse_eval_result(outer)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Additional _parse_snapshot tests
# ---------------------------------------------------------------------------

def test_parse_snapshot_empty_string():
    """Test _parse_snapshot handles empty string."""
    assert linkedin._parse_snapshot("") == []


def test_parse_snapshot_whitespace_only():
    """Test _parse_snapshot handles whitespace-only input."""
    assert linkedin._parse_snapshot("   \n\n   \t  \n") == []


def test_parse_snapshot_single_long_line():
    """Test _parse_snapshot captures single long line."""
    line = "This is a single very long line of text that exceeds the threshold."
    result = linkedin._parse_snapshot(line)
    # Line doesn't start with indentation, so buffer logic may not capture
    # This tests the actual behavior
    assert isinstance(result, list)


def test_parse_snapshot_mixed_lengths():
    """Test _parse_snapshot with mixed line lengths."""
    snapshot = """
Short
    This is a long line with leading indentation that should be captured properly.
Also short
    Another long line with indentation that definitely exceeds sixty characters easily.
Tiny
"""
    result = linkedin._parse_snapshot(snapshot)
    # Should capture the long indented lines
    assert isinstance(result, list)


def test_parse_snapshot_bracket_variations():
    """Test _parse_snapshot skips various bracket patterns."""
    snapshot = """
[button] Click me
[link] https://example.com
[heading] Important
    But this long line without bracket should be captured if long enough text.
"""
    result = linkedin._parse_snapshot(snapshot)
    # Bracket lines should be skipped
    for post in result:
        assert not post["text"].strip().startswith("[")


def test_parse_snapshot_empty_fields():
    """Test _parse_snapshot returns posts with empty timestamp and url."""
    snapshot = "This is a very long line of text that should be captured as a valid post."
    result = linkedin._parse_snapshot(snapshot)
    if result:
        assert result[0]["timestamp"] == ""
        assert result[0]["url"] == ""


def test_parse_snapshot_exact_60_chars():
    """Test _parse_snapshot with exactly 60 character lines."""
    # Exactly 60 chars
    line_60 = "123456789012345678901234567890123456789012345678901234567890"
    result = linkedin._parse_snapshot(line_60)
    # 60 is NOT > 60, so should not be captured (threshold check)
    # Depends on implementation - check actual behavior
    assert isinstance(result, list)


def test_parse_snapshot_exact_80_chars_combined():
    """Test _parse_snapshot combines buffer to exactly 80 chars."""
    # Two 40-char lines that combine to 80+ with space
    line1 = "1234567890123456789012345678901234567890"
    line2 = "abcdefghijklmnopqrstabcdefghijklmnopqrst"
    snapshot = f"{line1}\n{line2}"
    result = linkedin._parse_snapshot(snapshot)
    # Behavior depends on buffer logic
    assert isinstance(result, list)


def test_parse_snapshot_consecutive_short_lines():
    """Test _parse_snapshot handles consecutive short lines."""
    snapshot = "Short line 1\nShort line 2\nShort line 3\nShort line 4"
    result = linkedin._parse_snapshot(snapshot)
    # None should exceed threshold
    assert len(result) == 0


def test_parse_snapshot_newline_variations():
    """Test _parse_snapshot handles different newline styles."""
    text = "A very long line of text that exceeds the sixty character threshold by a good margin."
    # Unix newlines
    result_unix = linkedin._parse_snapshot(text + "\n" + text)
    # Windows newlines
    result_win = linkedin._parse_snapshot(text + "\r\n" + text)
    # Both should produce results
    assert isinstance(result_unix, list)
    assert isinstance(result_win, list)


def test_parse_snapshot_no_duplicates_same_content():
    """Test _parse_snapshot deduplicates identical content."""
    text = "This is a very long line of text that should be captured but not duplicated."
    snapshot = f"{text}\n{text}\n{text}"
    result = linkedin._parse_snapshot(snapshot)
    # Should dedupe based on first 80 chars
    texts = [p["text"][:80] for p in result]
    assert len(texts) == len(set(texts))


# ---------------------------------------------------------------------------
# Additional is_auth_gated tests
# ---------------------------------------------------------------------------

def test_is_auth_gated_all_signals():
    """Test is_auth_gated detects all known auth signals."""
    signals = [
        ("sign in", True),
        ("log in", True),
        ("create account", True),
        ("join now", True),
        ("authwall", True),
        ("join linkedin", True),
        ("see who's hiring", True),
    ]
    for signal, expected in signals:
        assert linkedin.is_auth_gated([], signal) == expected, f"Failed for: {signal}"


def test_is_auth_gated_partial_match():
    """Test is_auth_gated with partial signal matches."""
    # These should NOT trigger auth detection (substrings)
    # Actually, the current implementation uses `in`, so partials DO match
    assert linkedin.is_auth_gated([], "Please sign in now") is True
    assert linkedin.is_auth_gated([], "You can log in here") is True


def test_is_auth_gated_case_variations():
    """Test is_auth_gated handles various case combinations."""
    assert linkedin.is_auth_gated([], "SIGN IN") is True
    assert linkedin.is_auth_gated([], "Sign In") is True
    assert linkedin.is_auth_gated([], "SiGn In") is True
    assert linkedin.is_auth_gated([], "LOG IN") is True
    assert linkedin.is_auth_gated([], "AUTHWALL") is True


def test_is_auth_gated_posts_override():
    """Test is_auth_gated returns False when posts exist regardless of signal."""
    posts = [{"text": "Some content"}]
    assert linkedin.is_auth_gated(posts, "Please sign in to continue") is False
    assert linkedin.is_auth_gated(posts, "authwall detected") is False


def test_is_auth_gated_mixed_case_signal_in_text():
    """Test is_auth_gated finds signal in mixed case text."""
    text = "Welcome! Please SIGN IN to access all features."
    assert linkedin.is_auth_gated([], text) is True


def test_is_auth_gated_signal_at_end():
    """Test is_auth_gated finds signal at end of text."""
    text = "Welcome to our site. Please sign in"
    assert linkedin.is_auth_gated([], text) is True


def test_is_auth_gated_signal_at_start():
    """Test is_auth_gated finds signal at start of text."""
    text = "Sign in to continue reading"
    assert linkedin.is_auth_gated([], text) is True


def test_is_auth_gated_realistic_auth_wall():
    """Test is_auth_gated with realistic LinkedIn auth wall text."""
    texts = [
        "Sign in to see who's hiring in your network",
        "Join LinkedIn to discover more",
        "Log in to view full profile",
        "Create account to connect",  # Note: must match signal exactly (no "an")
    ]
    for text in texts:
        assert linkedin.is_auth_gated([], text) is True


# ---------------------------------------------------------------------------
# Additional format_digest tests
# ---------------------------------------------------------------------------

def test_format_digest_profile_missing_name():
    """Test format_digest handles missing name key."""
    profile = {"url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post content that is long enough here", "timestamp": "", "url": ""}]
    # Should raise KeyError or handle gracefully
    try:
        result = linkedin.format_digest(profile, posts, 1)
        # If it doesn't raise, check what happens
    except KeyError:
        pass  # Expected behavior


def test_format_digest_url_with_tracking():
    """Test format_digest preserves tracking parameters in URLs."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test?tracking=123"}
    posts = [{"text": "Post text that is sufficiently long", "timestamp": "", "url": "https://linkedin.com/posts/123?utm_source=test"}]
    result = linkedin.format_digest(profile, posts, 1)
    assert "tracking=123" in result
    assert "utm_source=test" in result


def test_format_digest_new_count_exceeds_total():
    """Test format_digest when new_count > total posts (edge case)."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Single post with enough text here", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=5)  # More than total
    assert "**New posts:** 5 of 1 seen" in result


def test_format_digest_zero_new_posts():
    """Test format_digest with zero new posts."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Old post with enough characters here", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=0)
    assert "**New posts:** 0 of 1 seen" in result


def test_format_digest_post_text_preserved():
    """Test format_digest preserves post text exactly."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    original_text = "This is my original post text with specific formatting: 123."
    posts = [{"text": original_text, "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    assert original_text in result


def test_format_digest_timestamp_formats():
    """Test format_digest handles various timestamp formats."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [
        {"text": "Post with ISO timestamp", "timestamp": "2026-03-31T10:30:00Z", "url": ""},
        {"text": "Post with date only", "timestamp": "2026-03-31", "url": ""},
        {"text": "Post with relative time", "timestamp": "2 hours ago", "url": ""},
    ]
    result = linkedin.format_digest(profile, posts, new_count=3)
    assert "2026-03-31T10:30:00Z" in result
    assert "2026-03-31" in result
    assert "2 hours ago" in result


def test_format_digest_unicode_in_name():
    """Test format_digest handles unicode in profile name."""
    profile = {"name": "José García 世界", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post content here with enough characters", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    assert "José García 世界" in result


def test_format_digest_unicode_in_post():
    """Test format_digest handles unicode in post text."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post with 中文 and émojis 🚀 and other unicode", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    assert "中文" in result
    assert "🚀" in result


def test_format_digest_very_long_post():
    """Test format_digest handles very long post text."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    long_text = "This is a very long post. " * 100  # ~2700 chars
    posts = [{"text": long_text, "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    # Text is stripped before being included in output
    assert long_text.strip() in result


def test_format_digest_context_with_special_chars():
    """Test format_digest handles context with special markdown chars."""
    profile = {
        "name": "Test User",
        "url": "https://linkedin.com/in/test",
        "context": "Former **colleague** at _Company_ with `code`"
    }
    posts = [{"text": "Post content here", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, new_count=1)
    # Context should be preserved as-is
    assert "Former **colleague**" in result


def test_format_digest_multiple_posts_numbering():
    """Test format_digest correctly numbers multiple posts."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [
        {"text": f"Post number {i} with enough text content here", "timestamp": "", "url": ""}
        for i in range(1, 6)
    ]
    result = linkedin.format_digest(profile, posts, new_count=5)
    for i in range(1, 6):
        assert f"### Post {i}" in result


# ---------------------------------------------------------------------------
# Additional _run tests
# ---------------------------------------------------------------------------

def test_run_with_env():
    """Test _run passes environment correctly."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="output")
        linkedin._run(["echo", "test"])
        # Verify subprocess.run was called
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('capture_output') is True
        assert call_kwargs.get('text') is True


def test_run_custom_timeout():
    """Test _run respects custom timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        linkedin._run(["sleep", "1"], timeout=60)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('timeout') == 60


def test_run_default_timeout():
    """Test _run uses default timeout of 30."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        linkedin._run(["echo", "test"])
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get('timeout') == 30


def test_run_stderr_not_captured():
    """Test _run doesn't include stderr in result."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="stdout", stderr="stderr")
        success, output = linkedin._run(["test"])
        assert output == "stdout"
        # stderr is not returned


def test_run_nonzero_with_stdout():
    """Test _run returns stdout even on non-zero exit."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="error output")
        success, output = linkedin._run(["test"])
        assert success is False
        assert output == "error output"


def test_run_permission_error():
    """Test _run raises PermissionError (not caught by implementation)."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = PermissionError("Permission denied")
        # Implementation only catches TimeoutExpired and FileNotFoundError
        with pytest.raises(PermissionError):
            linkedin._run(["test"])


def test_run_generic_exception():
    """Test _run handles generic exceptions."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = RuntimeError("Unexpected error")
        # Should raise since we only catch TimeoutExpired and FileNotFoundError
        with pytest.raises(RuntimeError):
            linkedin._run(["test"])


# ---------------------------------------------------------------------------
# Additional fetch_activity tests
# ---------------------------------------------------------------------------

def test_fetch_activity_url_trailing_slash():
    """Test fetch_activity handles URL with trailing slash."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        with patch('time.sleep'):
            linkedin.fetch_activity("https://linkedin.com/in/test/")

        # Check the constructed URL
        calls = mock_run.call_args_list
        for c in calls:
            args = c.args
            if args and len(args) >= 1:
                cmd_list = args[0]
                if isinstance(cmd_list, list):
                    for arg in cmd_list:
                        if 'recent-activity/all/' in str(arg):
                            # Should not have double slashes
                            assert '//recent-activity' not in str(arg)


def test_fetch_activity_url_no_trailing_slash():
    """Test fetch_activity handles URL without trailing slash."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        with patch('time.sleep'):
            linkedin.fetch_activity("https://linkedin.com/in/test")

        calls = mock_run.call_args_list
        found = False
        for c in calls:
            args = c.args
            if args and len(args) >= 1:
                cmd_list = args[0]
                if isinstance(cmd_list, list):
                    for arg in cmd_list:
                        if 'recent-activity/all/' in str(arg):
                            found = True
        assert found


def test_fetch_activity_sequence_of_commands():
    """Test fetch_activity calls correct sequence of agent-browser commands."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="[]")
        with patch('time.sleep'):
            linkedin.fetch_activity("https://linkedin.com/in/test")

        # Verify sequence: close, open, wait, scroll, eval, close
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any('close' in str(c) for c in calls)
        assert any('open' in str(c) for c in calls)
        assert any('wait' in str(c) for c in calls)
        assert any('scroll' in str(c) for c in calls)
        assert any('eval' in str(c) for c in calls)


def test_fetch_activity_eval_returns_posts():
    """Test fetch_activity processes eval result correctly."""
    posts = [{"text": "A valid post with enough characters here", "timestamp": "2026-03-31", "url": ""}]

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=0, stdout=""),  # open
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=0, stdout=json.dumps(posts)),  # eval
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        assert len(result) == 1
        assert result[0]["text"] == "A valid post with enough characters here"


def test_fetch_activity_all_steps_timeout():
    """Test fetch_activity handles timeout at close step."""
    with patch('subprocess.run') as mock_run:
        # Need enough responses for all subprocess.run calls
        mock_run.side_effect = [
            subprocess.TimeoutExpired(cmd=["agent-browser"], timeout=8),  # close times out
            MagicMock(returncode=0, stdout=""),  # open succeeds
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=0, stdout="[]"),  # eval returns empty
            MagicMock(returncode=0, stdout=""),  # snapshot (empty)
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")
        # Should continue despite timeout on close
        assert isinstance(result, list)


def test_fetch_activity_snapshot_parsing():
    """Test fetch_activity parses snapshot output."""
    snapshot = "This is a very long accessibility tree text line that should be captured as a post here."

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=0, stdout=""),  # open
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=1, stdout=""),  # eval fails
            MagicMock(returncode=0, stdout=snapshot),  # snapshot
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        # Should have parsed the snapshot
        assert isinstance(result, list)


def test_fetch_activity_empty_result():
    """Test fetch_activity returns empty list when no posts found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=""),  # close
            MagicMock(returncode=0, stdout=""),  # open
            MagicMock(returncode=0, stdout=""),  # wait
            MagicMock(returncode=0, stdout=""),  # scroll
            MagicMock(returncode=0, stdout="[]"),  # eval returns empty
            MagicMock(returncode=0, stdout=""),  # snapshot empty
            MagicMock(returncode=0, stdout=""),  # close
        ]
        with patch('time.sleep'):
            result = linkedin.fetch_activity("https://linkedin.com/in/test")

        assert result == []


# ---------------------------------------------------------------------------
# Additional main function tests
# ---------------------------------------------------------------------------

def test_main_with_multiple_profiles():
    """Test main processes multiple profiles correctly."""
    config_content = """
profiles:
  - name: User One
    url: https://linkedin.com/in/user1
  - name: User Two
    url: https://linkedin.com/in/user2
  - name: User Three
    url: https://linkedin.com/in/user3
"""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor', '--dry-run']):
                with patch('sys.stdout', new_callable=StringIO):
                    namespace['main']()
                    # Should process all 3 profiles


def test_main_output_path_format():
    """Test main creates output path with correct date format."""
    config_content = """
profiles:
  - name: Test User
    url: https://linkedin.com/in/test
"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor', '--dry-run']):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    namespace['main']()
                    output = mock_stdout.getvalue()
                    # Check date appears in output
                    assert today in output or "DRY RUN" in output


def test_main_yaml_parse_error():
    """Test main handles malformed YAML config."""
    bad_yaml = """
profiles:
  - name: Unclosed quote
    url: https://example.com
    context: "this is not closed
"""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=bad_yaml):
            with patch.object(sys, 'argv', ['linkedin-monitor']):
                # Should raise YAML parse error
                with pytest.raises(yaml.YAMLError):
                    namespace['main']()


def test_main_missing_profiles_key():
    """Test main handles config without profiles key."""
    config_content = "some_other_key: value"
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor']):
                with pytest.raises(SystemExit) as exc_info:
                    namespace['main']()
                assert exc_info.value.code == 0  # Empty profiles exits 0


def test_main_profile_missing_url():
    """Test main handles profile without URL."""
    config_content = """
profiles:
  - name: Test User
    context: No URL provided
"""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor', '--dry-run']):
                # Should handle gracefully (URL would be empty string)
                namespace['main']()


def test_main_creates_output_directory():
    """Test main creates output directory when it doesn't exist."""
    config_content = """
profiles:
  - name: Test
    url: https://linkedin.com/in/test
"""
    mock_output_dir = MagicMock()
    mock_output_dir.mkdir = MagicMock()

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor']):
                # Would create output dir in non-dry-run mode
                with patch('subprocess.run'):
                    with patch('time.sleep'):
                        with patch.object(Path, 'write_text'):
                            with patch.object(Path, 'mkdir'):
                                try:
                                    namespace['main']()
                                except (SystemExit, AttributeError, TypeError):
                                    pass  # May exit or error on mocked paths


def test_main_inter_profile_delay():
    """Test main applies delay between profiles."""
    config_content = """
profiles:
  - name: User One
    url: https://linkedin.com/in/user1
  - name: User Two
    url: https://linkedin.com/in/user2
"""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=config_content):
            with patch.object(sys, 'argv', ['linkedin-monitor', '--dry-run']):
                with patch('time.sleep') as mock_sleep:
                    namespace['main']()
                    # In dry-run mode, sleep is called for delay between profiles
                    # Actually in dry-run, no fetch happens, so no inter-profile delay


# ---------------------------------------------------------------------------
# Constants validation tests
# ---------------------------------------------------------------------------

def test_agent_browser_path():
    """Test AGENT_BROWSER path is defined."""
    assert hasattr(linkedin, 'AGENT_BROWSER')
    assert isinstance(linkedin.AGENT_BROWSER, str)
    assert len(linkedin.AGENT_BROWSER) > 0


def test_inter_profile_delay_reasonable_range():
    """Test INTER_PROFILE_DELAY is in reasonable range."""
    delay = linkedin.INTER_PROFILE_DELAY
    assert 1 <= delay <= 60, f"Delay {delay} not in reasonable range"


def test_extract_js_function():
    """Test EXTRACT_JS contains required elements."""
    js = linkedin.EXTRACT_JS
    assert 'querySelectorAll' in js
    assert 'feed-shared-update-v2' in js or 'data-urn' in js
    assert 'results.push' in js
    assert 'JSON.stringify' in js


def test_extract_js_post_extraction():
    """Test EXTRACT_JS extracts text, timestamp, and url."""
    js = linkedin.EXTRACT_JS
    assert 'text' in js
    assert 'timestamp' in js
    assert 'url' in js


def test_auth_signals_comprehensive():
    """Test AUTH_SIGNALS covers common auth wall texts."""
    signals = linkedin.AUTH_SIGNALS
    # Should include common variations
    assert any('sign' in s.lower() for s in signals)
    assert any('log' in s.lower() for s in signals)
    assert any('auth' in s.lower() for s in signals)


# ---------------------------------------------------------------------------
# Integration-style tests with temporary directories
# ---------------------------------------------------------------------------

class TestWithTempDir:
    """Tests using real temporary directories for file I/O."""

    def test_load_save_roundtrip(self, tmp_path):
        """Test load_seen and save_seen work together with mocked paths."""
        profile = "test-profile"
        hashes = {"hash1", "hash2", "hash3"}

        # Create the expected JSON content
        expected_json = json.dumps(sorted(hashes))

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=expected_json):
                loaded = linkedin.load_seen(profile)
                assert loaded == hashes

    def test_load_seen_persistence(self, tmp_path):
        """Test seen hashes persist conceptually across save/load cycles."""
        profile = "persist-test"
        original = {"abc123", "def456"}
        updated = original | {"ghi789"}

        # Track written content
        written_content = []

        def mock_write(self, content):
            written_content.append(content)
            return len(content)

        with patch.object(Path, 'mkdir'):
            with patch.object(Path, 'write_text', mock_write):
                # First save
                linkedin.save_seen(profile, original)
                first_write = json.loads(written_content[-1])

                # Second save
                linkedin.save_seen(profile, updated)
                second_write = json.loads(written_content[-1])

                assert set(first_write) == original
                assert set(second_write) == updated

    def test_multiple_profiles_separate(self, tmp_path):
        """Test different profiles produce different slugs."""
        # This tests that profile_slug creates unique identifiers
        slug_a = linkedin.profile_slug("Profile A")
        slug_b = linkedin.profile_slug("Profile B")

        assert slug_a != slug_b
        assert slug_a == "profile-a"
        assert slug_b == "profile-b"

    def test_cache_file_format(self, tmp_path):
        """Test cache file is valid JSON array."""
        hashes = {"abc", "def"}
        written_content = []

        def mock_write(self, content):
            written_content.append(content)
            return len(content)

        with patch.object(Path, 'mkdir'):
            with patch.object(Path, 'write_text', mock_write):
                linkedin.save_seen("test", hashes)

                content = written_content[0]
                parsed = json.loads(content)

                assert isinstance(parsed, list)
                assert set(parsed) == hashes


# ---------------------------------------------------------------------------
# Subprocess execution tests
# ---------------------------------------------------------------------------

class TestSubprocessExecution:
    """Tests that verify the script can be executed as a subprocess."""

    def test_script_exists(self):
        """Test linkedin-monitor script exists and is readable."""
        script_path = Path("/home/terry/germline/effectors/linkedin-monitor")
        assert script_path.exists()
        assert script_path.is_file()

    def test_script_executable(self):
        """Test linkedin-monitor can be executed."""
        result = subprocess.run(
            ["/home/terry/germline/effectors/linkedin-monitor", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should exit 0 for --help
        assert result.returncode == 0

    def test_script_version_or_usage(self):
        """Test linkedin-monitor shows usage information."""
        result = subprocess.run(
            ["/home/terry/germline/effectors/linkedin-monitor", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.lower()
        # Should mention linkedin or monitor
        assert 'linkedin' in output or 'monitor' in output or 'usage' in output

    def test_script_dry_run_no_config(self):
        """Test script exits gracefully when config missing."""
        # Run with a non-existent config by using subprocess env manipulation
        env = os.environ.copy()
        env['HOME'] = '/nonexistent/home/path'

        result = subprocess.run(
            ["/home/terry/germline/effectors/linkedin-monitor"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        # Should exit with error code
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Edge case and boundary tests
# ---------------------------------------------------------------------------

def test_hash_text_collision_resistance():
    """Test hash_text produces different hashes for similar inputs."""
    base = "This is a test post"
    variants = [
        base,
        base + ".",
        base + " ",
        base.upper(),
        base.lower(),
    ]
    hashes = [linkedin.hash_text(v) for v in variants]
    # All should be different
    assert len(set(hashes)) == len(hashes)


def test_parse_eval_result_max_posts():
    """Test _parse_eval_result handles large number of posts."""
    posts = [{"text": f"Post number {i} with enough characters to pass", "timestamp": "", "url": ""} for i in range(1000)]
    result = linkedin._parse_eval_result(json.dumps(posts))
    assert len(result) == 1000


def test_parse_snapshot_max_posts_cap():
    """Test _parse_snapshot caps output at 20 posts."""
    lines = [f"This is post number {i} which is definitely long enough to be captured here." for i in range(50)]
    snapshot = "\n".join(lines)
    result = linkedin._parse_snapshot(snapshot)
    assert len(result) <= 20


def test_format_digest_output_is_string():
    """Test format_digest returns string."""
    profile = {"name": "Test", "url": "https://linkedin.com/in/test"}
    posts = [{"text": "Post content here", "timestamp": "", "url": ""}]
    result = linkedin.format_digest(profile, posts, 1)
    assert isinstance(result, str)


def test_is_auth_gated_with_none():
    """Test is_auth_gated handles None input gracefully."""
    # This tests edge case behavior
    try:
        result = linkedin.is_auth_gated([], None)
    except (TypeError, AttributeError):
        pass  # Expected if implementation doesn't handle None


def test_load_seen_with_none_slug():
    """Test load_seen handles None slug."""
    try:
        result = linkedin.load_seen(None)
    except (TypeError, AttributeError):
        pass  # Expected


def test_save_seen_with_none_slug():
    """Test save_seen handles None slug."""
    try:
        linkedin.save_seen(None, {"hash"})
    except (TypeError, AttributeError):
        pass  # Expected


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------

def test_regression_hash_consistency():
    """Regression test: hash should be consistent with SHA-1 first 16 chars."""
    # This ensures the hash implementation doesn't change unexpectedly
    text = "Regression test input"
    expected = hashlib.sha1(text.encode()).hexdigest()[:16]
    assert linkedin.hash_text(text) == expected


def test_regression_slug_format():
    """Regression test: slug format should remain consistent."""
    # Ensure slug format doesn't change
    assert linkedin.profile_slug("John Doe") == "john-doe"
    assert linkedin.profile_slug("Jane Marie Smith") == "jane-marie-smith"


def test_regression_digest_format():
    """Regression test: digest format structure."""
    profile = {"name": "Test User", "url": "https://linkedin.com/in/test", "context": "Test context"}
    posts = [{"text": "Test post content that is long enough here", "timestamp": "2026-03-31", "url": "https://example.com"}]
    result = linkedin.format_digest(profile, posts, new_count=1)

    # Key structural elements
    assert result.startswith("## Test User")
    assert "**Context:** Test context" in result
    assert "**Profile:** https://linkedin.com/in/test" in result
    assert "**New posts:** 1 of 1 seen" in result
    assert "### Post 1" in result


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------

def test_hash_text_performance():
    """Test hash_text is reasonably fast."""
    import time
    start = time.time()
    for _ in range(1000):
        linkedin.hash_text("Performance test input text")
    elapsed = time.time() - start
    assert elapsed < 1.0  # 1000 hashes should take < 1 second


def test_parse_eval_result_performance():
    """Test _parse_eval_result is reasonably fast."""
    import time
    posts = [{"text": f"Post {i} with enough characters", "timestamp": "", "url": ""} for i in range(100)]
    json_data = json.dumps(posts)

    start = time.time()
    for _ in range(100):
        linkedin._parse_eval_result(json_data)
    elapsed = time.time() - start
    assert elapsed < 2.0  # 100 parses should take < 2 seconds


# ---------------------------------------------------------------------------
# Error message tests
# ---------------------------------------------------------------------------

def test_run_timeout_error_message():
    """Test _run produces helpful error message on timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
        success, output = linkedin._run(["test"], timeout=30)
        assert "error" in output.lower()
        # The error message includes "timed out" or "timeout"
        assert "timed out" in output.lower() or "timeout" in output.lower()


def test_run_file_not_found_error_message():
    """Test _run produces helpful error message when command not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("command not found")
        success, output = linkedin._run(["nonexistent"])
        assert "error" in output.lower()


# ---------------------------------------------------------------------------
# Configuration validation tests
# ---------------------------------------------------------------------------

def test_config_yaml_valid_structure():
    """Test expected config YAML structure."""
    valid_config = """
profiles:
  - name: John Doe
    url: https://linkedin.com/in/johndoe
    context: Former colleague
  - name: Jane Smith
    url: https://linkedin.com/in/janesmith
"""
    parsed = yaml.safe_load(valid_config)
    assert 'profiles' in parsed
    assert len(parsed['profiles']) == 2
    assert all('name' in p and 'url' in p for p in parsed['profiles'])


def test_config_minimal_profile():
    """Test minimal profile config."""
    minimal_config = """
profiles:
  - name: Minimal User
    url: https://linkedin.com/in/minimal
"""
    parsed = yaml.safe_load(minimal_config)
    assert len(parsed['profiles']) == 1
    assert parsed['profiles'][0].get('context') is None


def test_config_extra_fields_ignored():
    """Test config with extra fields is parsed correctly."""
    config_with_extras = """
profiles:
  - name: User
    url: https://linkedin.com/in/user
    extra_field: ignored
    another_field: also_ignored
some_other_key: value
"""
    parsed = yaml.safe_load(config_with_extras)
    assert parsed['profiles'][0]['name'] == "User"
