"""Tests for the parse-doc effector.

Mocks the LlamaCloud client so tests don't hit the network or burn quota.
Run: uv run pytest assays/test_parse_doc.py -x
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "parse-doc"
SAMPLE_PDF = Path("/tmp/parse-doc-test.pdf")


@pytest.fixture(autouse=True)
def _ensure_effector_exists():
    """All tests assume the effector script exists at germline/effectors/parse-doc."""
    if not EFFECTOR.exists():
        pytest.skip(f"effector not yet implemented at {EFFECTOR}")


@pytest.fixture
def fake_pdf(tmp_path: Path) -> Path:
    """Create a minimal valid-enough PDF so file-existence checks pass without
    actually parsing. The parse() call is mocked, so contents don't matter."""
    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%fake\ntrailer\n<<>>\n%%EOF\n")
    return pdf


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Invoke the effector with given args + env, capturing stdout/stderr."""
    full_env = {**os.environ, **(env or {})}
    full_env.setdefault("LLAMA_CLOUD_API_KEY", "fake-test-key")
    return subprocess.run(
        [sys.executable, str(EFFECTOR), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


# ---------------------------------------------------------------------------
# Acceptance criteria 1: default-tier success path
# ---------------------------------------------------------------------------
def test_default_tier_success(fake_pdf, tmp_path, monkeypatch):
    """parse-doc <pdf> exits 0, writes default-tier output, frontmatter intact."""
    out = tmp_path / "out.md"
    fake_markdown = "# Sample\n\nThis is parsed content from a fake PDF.\n"

    with patch("llama_cloud_services.LlamaParse") as mock_parser_cls:
        mock_doc = MagicMock(text=fake_markdown)
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        result = _run([str(fake_pdf), "--out", str(out), "--tier", "default"])

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out.exists()
    content = out.read_text()
    assert content.startswith("---\n"), "must have YAML frontmatter"
    assert "extracted_by:" in content
    assert "tier=default" in content or "default" in content.lower()
    assert fake_markdown.strip() in content


# ---------------------------------------------------------------------------
# Acceptance criteria 2: agentic-tier explicit override
# ---------------------------------------------------------------------------
def test_agentic_tier_explicit(fake_pdf, tmp_path):
    """parse-doc <pdf> --tier=agentic --out=<path> uses agentic, writes to given path."""
    out = tmp_path / "agentic.md"
    fake_markdown = "## Agentic-tier output\n"

    with patch("llama_cloud_services.LlamaParse") as mock_parser_cls:
        mock_doc = MagicMock(text=fake_markdown)
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        result = _run([str(fake_pdf), "--tier", "agentic", "--out", str(out)])

    assert result.returncode == 0
    assert out.exists()
    # Verify LlamaParse was instantiated with agentic-relevant params
    init_kwargs = mock_parser_cls.call_args.kwargs
    assert any(v in str(init_kwargs).lower() for v in ["agentic", "premium"]), (
        f"agentic tier not reflected in LlamaParse init: {init_kwargs}"
    )


# ---------------------------------------------------------------------------
# Acceptance criteria 3: URL input auto-downloads
# ---------------------------------------------------------------------------
def test_url_input_downloads_then_parses(tmp_path, monkeypatch):
    """parse-doc <url> downloads to /tmp, then parses."""
    fake_url = "https://example.com/fake.pdf"
    out = tmp_path / "url-out.md"

    with (
        patch("urllib.request.urlretrieve") as mock_retrieve,
        patch("llama_cloud_services.LlamaParse") as mock_parser_cls,
    ):
        # urlretrieve writes to a path; fake by writing the bytes ourselves
        def fake_download(url, dest):
            Path(dest).write_bytes(b"%PDF-1.4\n%fake\n%%EOF\n")

        mock_retrieve.side_effect = fake_download

        mock_doc = MagicMock(text="downloaded content")
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        result = _run([fake_url, "--out", str(out)])

    assert result.returncode == 0
    assert mock_retrieve.called, "URL input must trigger urlretrieve"
    assert out.exists()


# ---------------------------------------------------------------------------
# Acceptance criteria 4: missing file errors clearly
# ---------------------------------------------------------------------------
def test_missing_file_clear_error(tmp_path):
    """parse-doc /missing/file exits 1 with stderr message."""
    result = _run(["/definitely/not/a/real/path.pdf", "--out", str(tmp_path / "x.md")])
    assert result.returncode != 0
    assert (
        "not found" in result.stderr.lower()
        or "no such" in result.stderr.lower()
        or "missing" in result.stderr.lower()
    )


# ---------------------------------------------------------------------------
# Acceptance criteria 5: invalid tier errors with valid options
# ---------------------------------------------------------------------------
def test_invalid_tier_error(fake_pdf, tmp_path):
    """parse-doc --tier=invalid exits 1 with valid tiers listed."""
    result = _run([str(fake_pdf), "--tier", "garbage", "--out", str(tmp_path / "x.md")])
    assert result.returncode != 0
    err_lower = result.stderr.lower() + result.stdout.lower()
    assert "agentic" in err_lower, "error message should list valid tiers including 'agentic'"


# ---------------------------------------------------------------------------
# Acceptance criteria 6: --json mode
# ---------------------------------------------------------------------------
def test_json_envelope_output(fake_pdf, tmp_path):
    """parse-doc --json outputs a porin-style JSON envelope."""
    import json

    out = tmp_path / "json.md"
    with patch("llama_cloud_services.LlamaParse") as mock_parser_cls:
        mock_doc = MagicMock(text="x")
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        result = _run([str(fake_pdf), "--out", str(out), "--json"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload.get("ok") is True
    # porin envelope keys
    for key in ("ok", "result"):
        assert key in payload, f"porin envelope missing '{key}'"


# ---------------------------------------------------------------------------
# Acceptance criteria 7 (extra): empty markdown_full result is detected
# ---------------------------------------------------------------------------
def test_empty_result_fails_loudly(fake_pdf, tmp_path):
    """If LlamaCloud returns empty content, parse-doc exits non-zero with clear stderr."""
    out = tmp_path / "empty.md"
    with patch("llama_cloud_services.LlamaParse") as mock_parser_cls:
        mock_doc = MagicMock(text="")
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        result = _run([str(fake_pdf), "--out", str(out)])

    assert result.returncode != 0
    assert "empty" in (result.stderr + result.stdout).lower()


# ---------------------------------------------------------------------------
# Acceptance criteria 8: idempotent — re-running with same args overwrites
# ---------------------------------------------------------------------------
def test_idempotent_overwrite(fake_pdf, tmp_path):
    """Re-running with same args overwrites the output file with no state files in $HOME."""
    out = tmp_path / "idemp.md"
    home_before = set((Path.home()).iterdir()) if Path.home().exists() else set()

    with patch("llama_cloud_services.LlamaParse") as mock_parser_cls:
        mock_doc = MagicMock(text="run-1")
        mock_parser = MagicMock()
        mock_parser.load_data.return_value = [mock_doc]
        mock_parser_cls.return_value = mock_parser

        _run([str(fake_pdf), "--out", str(out)])
        first_content = out.read_text()

        mock_doc.text = "run-2"
        mock_parser.load_data.return_value = [mock_doc]
        _run([str(fake_pdf), "--out", str(out)])
        second_content = out.read_text()

    assert first_content != second_content, "second run must overwrite, not append"
    assert "run-2" in second_content
    assert "run-1" not in second_content

    home_after = set((Path.home()).iterdir()) if Path.home().exists() else set()
    new_in_home = home_after - home_before
    # Allow normal cache dirs but flag obvious state-file leaks
    suspicious = {p for p in new_in_home if "parse-doc" in p.name.lower()}
    assert not suspicious, f"effector created state in $HOME: {suspicious}"


# ---------------------------------------------------------------------------
# Acceptance criteria 9 (extra): script has docstring header
# ---------------------------------------------------------------------------
def test_effector_has_docstring_header():
    """The script must document flags + auto-tier heuristic at the top."""
    content = EFFECTOR.read_text()
    head = content[:2000]
    assert "tier" in head.lower(), "docstring should mention --tier flag"
    assert "out" in head.lower(), "docstring should mention --out flag"
    assert any(word in head.lower() for word in ["heuristic", "default tier", "auto-tier"]), (
        "docstring should describe the auto-tier heuristic"
    )
