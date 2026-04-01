from __future__ import annotations

"""Tests for metabolon.lysin.cli — click CLI with mocked fetch/format."""

from unittest.mock import patch

from click.testing import CliRunner

from metabolon.lysin.cli import main
from metabolon.lysin.fetch import BioArticle


def _article(**overrides):
    """Build a BioArticle with sensible defaults."""
    defaults = dict(
        title="TP53",
        definition="Tumor protein p53.",
        mechanism="Acts as a tumor suppressor.",
        url="https://www.uniprot.org/uniprotkb/P04637",
        sections=[],
        sources=["UniProt"],
    )
    defaults.update(overrides)
    return BioArticle(**defaults)


# ── happy path: basic text output ──────────────────────────────────────────

@patch("metabolon.lysin.cli.format_text", return_value="TEXT-OUT")
@patch("metabolon.lysin.cli.fetch_summary")
def test_basic_text_output(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 0
    assert result.output.strip() == "TEXT-OUT"
    mock_fetch.assert_called_once_with("TP53")
    mock_fmt.assert_called_once()
    # full=False because --full not passed
    assert mock_fmt.call_args[1]["full"] is False


# ── happy path: JSON output ────────────────────────────────────────────────

@patch("metabolon.lysin.cli.format_json", return_value='{"title":"TP53"}')
@patch("metabolon.lysin.cli.fetch_summary")
def test_json_output(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--json"])
    assert result.exit_code == 0
    assert result.output.strip() == '{"title":"TP53"}'
    mock_fmt.assert_called_once()
    assert mock_fmt.call_args[1]["full"] is False


# ── --full flag triggers fetch_sections ─────────────────────────────────────

@patch("metabolon.lysin.cli.format_text", return_value="FULL-TEXT")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "Function", "text": "details"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_flag_fetches_sections(mock_fetch, mock_sections, mock_fmt):
    article = _article(sections=[])
    mock_fetch.return_value = article
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full"])
    assert result.exit_code == 0
    mock_sections.assert_called_once_with("TP53")
    assert article.sections == [{"title": "Function", "text": "details"}]
    assert mock_fmt.call_args[1]["full"] is True


# ── --full + --json together ───────────────────────────────────────────────

@patch("metabolon.lysin.cli.format_json", return_value='{"title":"TP53","sections":[...]}')
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "X", "text": "Y"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_and_json_together(mock_fetch, mock_sections, mock_fmt):
    mock_fetch.return_value = _article(sections=[])
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full", "--json"])
    assert result.exit_code == 0
    mock_sections.assert_called_once()
    assert mock_fmt.call_args[1]["full"] is True


# ── LookupError → stderr message, exit 1 ───────────────────────────────────

@patch("metabolon.lysin.cli.fetch_summary", side_effect=LookupError("nope"))
def test_lookup_error(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["ZZZZZ"])
    assert result.exit_code == 1
    assert "Not found: nope" in (result.stderr or result.output)


# ── Generic Exception → stderr message, exit 1 ─────────────────────────────

@patch("metabolon.lysin.cli.fetch_summary", side_effect=RuntimeError("boom"))
def test_generic_error(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 1
    assert "Error: boom" in (result.stderr or result.output)


# ── --full without --json still calls format_text (not format_json) ────────

@patch("metabolon.lysin.cli.format_text", return_value="FULL")
@patch("metabolon.lysin.cli.format_json")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_uses_format_text_not_json(mock_fetch, mock_sec, mock_json, mock_text):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full"])
    assert result.exit_code == 0
    mock_text.assert_called_once()
    mock_json.assert_not_called()


# ── --json without --full does not call fetch_sections ─────────────────────

@patch("metabolon.lysin.cli.format_json", return_value="{}")
@patch("metabolon.lysin.cli.fetch_sections")
@patch("metabolon.lysin.cli.fetch_summary")
def test_json_without_full_skips_sections(mock_fetch, mock_sec, mock_json):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--json"])
    assert result.exit_code == 0
    mock_sec.assert_not_called()


# ─-- no term argument → click error (exit 2) ──────────────────────────────

def test_missing_term_argument():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    # Click shows usage on missing required arg
    assert "Missing argument" in result.output or "Usage" in result.output


# ── format_json/full=True is passed through when both flags set ────────────

@patch("metabolon.lysin.cli.format_json", return_value="{}")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "S", "text": "T"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_format_json_receives_full_true(mock_fetch, mock_sec, mock_json):
    mock_fetch.return_value = _article(sections=[])
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full", "--json"])
    assert result.exit_code == 0
    call_kwargs = mock_json.call_args
    assert call_kwargs[1]["full"] is True


# ── sections are set on article before formatting ──────────────────────────

@patch("metabolon.lysin.cli.format_text", return_value="ok")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "A", "text": "B"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_sections_mutate_article_before_format(mock_fetch, mock_sec, mock_fmt):
    article = _article(sections=[])
    mock_fetch.return_value = article
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full"])
    assert result.exit_code == 0
    # The article passed to format_text should have the fetched sections
    formatted_article = mock_fmt.call_args[0][0]
    assert formatted_article.sections == [{"title": "A", "text": "B"}]
