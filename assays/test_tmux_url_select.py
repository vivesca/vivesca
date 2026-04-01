#!/usr/bin/env python3
"""Tests for the tmux-url-select.sh effector."""

from __future__ import annotations

import base64
import contextlib
import os
import subprocess
from pathlib import Path

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parent.parent / "effectors" / "tmux-url-select.sh"
BUFFER_PATH = Path("/tmp/tmux-url-buffer")


def run_effector(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the shell effector as an external process."""
    return subprocess.run(
        [str(EFFECTOR_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=5,
    )


@contextlib.contextmanager
def temporary_buffer(content: str | None):
    """Temporarily replace the tmux URL buffer and restore it afterwards."""
    original_content = BUFFER_PATH.read_text() if BUFFER_PATH.exists() else None
    try:
        if content is None:
            if BUFFER_PATH.exists():
                BUFFER_PATH.unlink()
        else:
            BUFFER_PATH.write_text(content)
        yield
    finally:
        if original_content is None:
            if BUFFER_PATH.exists():
                BUFFER_PATH.unlink()
        else:
            BUFFER_PATH.write_text(original_content)


def build_mock_env(
    tmp_path: Path,
    *,
    selection_mode: str = "first",
    selected_url: str = "",
) -> tuple[dict[str, str], Path, Path]:
    """Create mock fzf and tmux binaries and prepend them to PATH."""
    fzf_input_path = tmp_path / "fzf_input.txt"
    fzf_args_path = tmp_path / "fzf_args.txt"
    tmux_calls_path = tmp_path / "tmux_calls.txt"

    mock_fzf = tmp_path / "fzf"
    mock_fzf.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                f'printf "%s\\n" "$@" > "{fzf_args_path}"',
                f'cat > "{fzf_input_path}"',
                'case "${FZF_SELECTION_MODE:-first}" in',
                '  first)',
                f'    head -n 1 "{fzf_input_path}"',
                "    ;;",
                '  constant)',
                '    printf "%s\\n" "${FZF_SELECTED_URL}"',
                "    ;;",
                '  none)',
                "    exit 0",
                "    ;;",
                "esac",
            ]
        )
        + "\n"
    )
    mock_fzf.chmod(0o755)

    mock_tmux = tmp_path / "tmux"
    mock_tmux.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                f'printf "%s\\n" "$*" >> "{tmux_calls_path}"',
            ]
        )
        + "\n"
    )
    mock_tmux.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    env["FZF_SELECTION_MODE"] = selection_mode
    env["FZF_SELECTED_URL"] = selected_url
    return env, fzf_input_path, tmux_calls_path


def extract_fzf_input(tmp_path: Path, buffer_content: str) -> list[str]:
    """Run the effector and return the URLs passed into fzf."""
    env, fzf_input_path, _ = build_mock_env(tmp_path, selection_mode="none")
    with temporary_buffer(buffer_content):
        result = run_effector(env=env)
    assert result.returncode == 0
    assert fzf_input_path.exists()
    return fzf_input_path.read_text().splitlines()


def extract_osc52_payload(stdout: str) -> str:
    """Extract the raw OSC 52 payload from stdout."""
    prefix = "\x1b]52;c;"
    start = stdout.index(prefix) + len(prefix)
    end = stdout.index("\x07", start)
    return stdout[start:end]


def test_tmux_url_select_script_exists():
    assert EFFECTOR_PATH.exists()
    assert EFFECTOR_PATH.is_file()


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_flags(flag: str):
    result = run_effector(flag)
    assert result.returncode == 0
    assert "Usage: tmux-url-select.sh" in result.stdout
    assert "Interactively select a URL" in result.stdout
    assert "fzf" in result.stdout


def test_no_urls_when_buffer_missing():
    with temporary_buffer(None):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_no_urls_when_buffer_empty():
    with temporary_buffer(""):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_no_urls_when_buffer_has_only_text():
    with temporary_buffer("hello world\njust text\nstill no links\n"):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_selected_url_emits_osc52_and_tmux_message(tmp_path: Path):
    env, _, tmux_calls_path = build_mock_env(tmp_path, selection_mode="first")
    selected_url = "https://example.com/page1"
    with temporary_buffer(
        "\n".join(
            [
                f"Check {selected_url}",
                "Also https://example.com/page2",
                f"Duplicate {selected_url}",
            ]
        )
        + "\n"
    ):
        result = run_effector(env=env)

    assert result.returncode == 0
    assert "\x1b]52;c;" in result.stdout
    assert "\x07" in result.stdout
    assert base64.b64decode(extract_osc52_payload(result.stdout)).decode() == selected_url
    tmux_calls = tmux_calls_path.read_text()
    assert "display-message" in tmux_calls
    assert selected_url in tmux_calls


def test_duplicate_urls_are_removed_before_fzf(tmp_path: Path):
    urls_seen = extract_fzf_input(
        tmp_path,
        "\n".join(
            [
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page1",
                "https://example.com/page3",
                "https://example.com/page2",
            ]
        )
        + "\n",
    )
    assert urls_seen == [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]


def test_fzf_cancel_emits_no_osc52(tmp_path: Path):
    env, _, tmux_calls_path = build_mock_env(tmp_path, selection_mode="none")
    with temporary_buffer("https://example.com\n"):
        result = run_effector(env=env)
    assert result.returncode == 0
    assert "\x1b]52;c;" not in result.stdout
    assert not tmux_calls_path.exists()


def test_http_urls_are_supported(tmp_path: Path):
    urls_seen = extract_fzf_input(tmp_path, "Go to http://plain.example.org/foo\n")
    assert urls_seen == ["http://plain.example.org/foo"]


@pytest.mark.parametrize(
    ("buffer_content", "expected_url"),
    [
        ("https://example.com/path page2 other\n", "https://example.com/path"),
        ("link <https://example.com/a>b\n", "https://example.com/a"),
        ("see (https://example.com/x) next\n", "https://example.com/x"),
        ('href="https://example.com/z" more\n', "https://example.com/z"),
    ],
)
def test_url_extraction_stops_at_delimiters(
    tmp_path: Path,
    buffer_content: str,
    expected_url: str,
):
    urls_seen = extract_fzf_input(tmp_path, buffer_content)
    assert urls_seen == [expected_url]


def test_fzf_receives_expected_flags(tmp_path: Path):
    env, _, _ = build_mock_env(tmp_path, selection_mode="none")
    fzf_args_path = tmp_path / "fzf_args.txt"
    with temporary_buffer("https://example.com\n"):
        result = run_effector(env=env)
    assert result.returncode == 0
    args = fzf_args_path.read_text().splitlines()
    assert args == ["--reverse", "--prompt=Copy URL: ", "--no-info"]


def test_constant_fzf_selection_is_copied_even_if_not_first_match(tmp_path: Path):
    selected_url = "https://selected.example.com/test"
    env, _, tmux_calls_path = build_mock_env(
        tmp_path,
        selection_mode="constant",
        selected_url=selected_url,
    )
    with temporary_buffer(
        "\n".join(
            [
                "Visit http://first.example.com for more info",
                "Check https://second.example.org/path?q=1",
            ]
        )
        + "\n"
    ):
        result = run_effector(env=env)

    assert result.returncode == 0
    assert base64.b64decode(extract_osc52_payload(result.stdout)).decode() == selected_url
    assert selected_url in tmux_calls_path.read_text()


def test_osc52_sequence_format(tmp_path: Path):
    """OSC 52 must be \\033]52;c;<base64>\\a exactly."""
    url = "https://example.com/osc-test"
    env, _, _ = build_mock_env(tmp_path, selection_mode="first")
    with temporary_buffer(f"{url}\n"):
        result = run_effector(env=env)

    assert result.returncode == 0
    expected_b64 = base64.b64encode(url.encode()).decode()
    assert f"\x1b]52;c;{expected_b64}\x07" in result.stdout


def test_multiple_urls_on_one_line(tmp_path: Path):
    """All URLs on a single line should be extracted."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "Check https://a.com and https://b.com then http://c.net\n",
    )
    assert urls_seen == [
        "https://a.com",
        "https://b.com",
        "http://c.net",
    ]


def test_url_with_query_string_and_fragment(tmp_path: Path):
    """URLs with ?, =, &, # characters should be preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://example.com/search?q=hello+world&lang=en#results\n",
    )
    assert urls_seen == [
        "https://example.com/search?q=hello+world&lang=en#results",
    ]


def test_url_stops_at_single_quote(tmp_path: Path):
    """The grep regex excludes single-quote characters from URLs."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "link=https://example.com/path'next\n",
    )
    assert urls_seen == ["https://example.com/path"]


def test_tmux_display_message_includes_url(tmp_path: Path):
    """tmux display-message should contain 'Copied: <url>'."""
    url = "https://example.com/msg-test"
    env, _, tmux_calls_path = build_mock_env(tmp_path, selection_mode="first")
    with temporary_buffer(f"{url}\n"):
        result = run_effector(env=env)

    assert result.returncode == 0
    tmux_output = tmux_calls_path.read_text()
    assert f"display-message Copied: {url}" in tmux_output


def test_single_url_in_buffer(tmp_path: Path):
    """A buffer with exactly one URL should pass it to fzf."""
    urls_seen = extract_fzf_input(tmp_path, "https://solo.example.org/only\n")
    assert urls_seen == ["https://solo.example.org/only"]


def test_url_with_trailing_parenthesis(tmp_path: Path):
    """URL inside parentheses should not include the closing paren."""
    urls_seen = extract_fzf_input(tmp_path, "(https://example.com/paren)\n")
    assert urls_seen == ["https://example.com/paren"]


# ── Additional coverage tests ────────────────────────────────────────────


def test_url_with_port_number(tmp_path: Path):
    """URLs with explicit port numbers should be preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "Connect to https://example.com:8443/secure\n",
    )
    assert urls_seen == ["https://example.com:8443/secure"]


def test_url_with_percent_encoding(tmp_path: Path):
    """URLs with percent-encoded characters should be preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://example.com/search?q=hello%20world&page=1\n",
    )
    assert urls_seen == ["https://example.com/search?q=hello%20world&page=1"]


def test_url_at_start_of_line(tmp_path: Path):
    """URL at the very beginning of a line is extracted."""
    urls_seen = extract_fzf_input(tmp_path, "https://example.com/start-of-line\n")
    assert urls_seen == ["https://example.com/start-of-line"]


def test_url_at_end_of_line_no_trailing_newline(tmp_path: Path):
    """URL at end of buffer without trailing newline is still extracted."""
    urls_seen = extract_fzf_input(tmp_path, "See https://example.com/end")
    assert urls_seen == ["https://example.com/end"]


def test_url_with_path_segments(tmp_path: Path):
    """URLs with deep paths and multiple segments are preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://example.com/a/b/c/d/e/f/g.html\n",
    )
    assert urls_seen == ["https://example.com/a/b/c/d/e/f/g.html"]


def test_url_with_trailing_greater_than(tmp_path: Path):
    """URL followed by > (e.g. in HTML or markdown) stops before >."""
    urls_seen = extract_fzf_input(tmp_path, "<https://example.com/link>\n")
    assert urls_seen == ["https://example.com/link"]


def test_url_with_double_quote_delimiter(tmp_path: Path):
    """URL followed by double-quote stops before the quote."""
    urls_seen = extract_fzf_input(
        tmp_path,
        'src="https://example.com/image.png" alt="test"\n',
    )
    assert urls_seen == ["https://example.com/image.png"]


def test_buffer_with_only_whitespace(tmp_path: Path):
    """Buffer containing only whitespace produces no URLs."""
    with temporary_buffer("   \n\t  \n   \n"):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_buffer_with_mixed_text_and_urls(tmp_path: Path):
    """URLs are extracted from lines that also contain non-URL text."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "Deploy https://app.example.com/v2 to production, see https://docs.example.com/deploy\n",
    )
    assert urls_seen == [
        "https://app.example.com/v2",
        "https://docs.example.com/deploy",
    ]


def test_very_long_url(tmp_path: Path):
    """Very long URLs (>1000 chars) are extracted intact."""
    long_path = "a" * 1000
    urls_seen = extract_fzf_input(
        tmp_path,
        f"https://example.com/{long_path}\n",
    )
    assert len(urls_seen) == 1
    assert urls_seen[0] == f"https://example.com/{long_path}"


def test_url_with_plus_sign(tmp_path: Path):
    """URLs with + in query strings are preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://example.com/search?q=foo+bar+baz\n",
    )
    assert urls_seen == ["https://example.com/search?q=foo+bar+baz"]


def test_url_with_colon_in_path(tmp_path: Path):
    """URLs should stop at spaces (first stop character)."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://example.com/path more text\n",
    )
    assert urls_seen == ["https://example.com/path"]


def test_no_urls_buffer_with_at_symbols(tmp_path: Path):
    """Text with @ symbols but no http(s) should not produce URLs."""
    with temporary_buffer("user@host.com another@domain.org\n"):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_https_only_not_ftp_or_other_schemes(tmp_path: Path):
    """Only http and https schemes are extracted, not ftp, ssh etc."""
    with temporary_buffer("ftp://files.example.com/data ssh://host.example.com\n"):
        result = run_effector()
    assert result.returncode == 0
    assert "No URLs found in pane" in result.stdout


def test_url_with_underscore_and_hyphen(tmp_path: Path):
    """URLs with underscores and hyphens in domain/path are preserved."""
    urls_seen = extract_fzf_input(
        tmp_path,
        "https://my-site.example.com/path_to/page_1\n",
    )
    assert urls_seen == ["https://my-site.example.com/path_to/page_1"]


def test_empty_fzf_selection_produces_no_output(tmp_path: Path):
    """When fzf outputs an empty line, no OSC 52 or tmux message is emitted."""
    env, _, tmux_calls_path = build_mock_env(tmp_path, selection_mode="none")
    # Override mock to output empty string
    mock_fzf = tmp_path / "fzf"
    mock_fzf.write_text("#!/bin/bash\necho ''\n")
    mock_fzf.chmod(0o755)
    with temporary_buffer("https://example.com\n"):
        result = run_effector(env=env)
    assert result.returncode == 0
    assert "\x1b]52;c;" not in result.stdout


def test_osc52_base64_encoding_of_special_chars(tmp_path: Path):
    """OSC 52 payload correctly base64-encodes URLs with special characters."""
    url = "https://example.com/search?q=hello%20world&lang=en#results"
    env, _, _ = build_mock_env(tmp_path, selection_mode="first")
    with temporary_buffer(f"{url}\n"):
        result = run_effector(env=env)
    assert result.returncode == 0
    decoded = base64.b64decode(extract_osc52_payload(result.stdout)).decode()
    assert decoded == url


def test_buffer_with_many_duplicate_urls_deduped(tmp_path: Path):
    """Many duplicate URLs across multiple lines are deduplicated."""
    buffer = "\n".join(
        [
            "See https://example.com/page",
            "Also check https://example.com/page",
            "And https://example.com/page again",
            "Plus https://example.com/other",
            "Back to https://example.com/other",
        ]
    ) + "\n"
    urls_seen = extract_fzf_input(tmp_path, buffer)
    assert urls_seen == [
        "https://example.com/page",
        "https://example.com/other",
    ]


def test_url_exits_zero_when_no_urls(tmp_path: Path):
    """Script exits 0 (not error) when no URLs are found."""
    with temporary_buffer("just some text\n"):
        result = run_effector()
    assert result.returncode == 0


def test_buffer_with_trailing_angle_bracket_url(tmp_path: Path):
    """URL followed by > character (e.g. markdown autolink) is trimmed."""
    urls_seen = extract_fzf_input(tmp_path, "<https://example.com/autolink>\n")
    assert urls_seen == ["https://example.com/autolink"]
