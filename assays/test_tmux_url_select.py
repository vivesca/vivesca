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
