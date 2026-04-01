from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from metabolon.lysin.cli import main
from metabolon.lysin.fetch import BioArticle


def _article(**overrides):
    """Build a sample BioArticle with sensible defaults."""
    base = dict(
        title="TP53",
        definition="Tumor protein p53.",
        mechanism="TP53 encodes a tumor suppressor.",
        url="https://www.uniprot.org/uniprotkb/P04637",
        sections=[],
        sources=["UniProt"],
    )
    base.update(overrides)
    return BioArticle(**base)


# ── happy path ──────────────────────────────────────────────────────────────

@patch("metabolon.lysin.cli.format_text", return_value="formatted-text")
@patch("metabolon.lysin.cli.fetch_summary")
def test_basic_text_output(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with("TP53")
    mock_fmt.assert_called_once()
    assert result.output.strip() == "formatted-text"


@patch("metabolon.lysin.cli.format_text", return_value="formatted-full")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "Fn", "text": "details"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_flag_fetches_sections(mock_fetch, mock_sections, mock_fmt):
    article = _article()
    mock_fetch.return_value = article
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full"])
    assert result.exit_code == 0
    mock_sections.assert_called_once_with(article.title)
    # format_text should be called with full=True
    mock_fmt.assert_called_once()
    call_kwargs = mock_fmt.call_args
    assert call_kwargs[1].get("full") is True or call_kwargs[0][1] is True


@patch("metabolon.lysin.cli.format_json", return_value='{"title":"TP53"}')
@patch("metabolon.lysin.cli.fetch_summary")
def test_json_flag(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--json"])
    assert result.exit_code == 0
    mock_fmt.assert_called_once()
    assert result.output.strip() == '{"title":"TP53"}'


@patch("metabolon.lysin.cli.format_json", return_value='{"title":"TP53","sections":[]}')
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "Fn", "text": "details"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_and_json_flags(mock_fetch, mock_sections, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["TP53", "--full", "--json"])
    assert result.exit_code == 0
    mock_sections.assert_called_once()
    mock_fmt.assert_called_once()


# ── error handling ──────────────────────────────────────────────────────────

@patch("metabolon.lysin.cli.fetch_summary", side_effect=LookupError("nothing found"))
def test_lookup_error(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["ZZZZZ"])
    assert result.exit_code == 1
    assert "Not found: nothing found" in (result.stderr or result.output)


@patch("metabolon.lysin.cli.fetch_summary", side_effect=RuntimeError("network down"))
def test_generic_exception(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 1
    assert "Error: network down" in (result.stderr or result.output)


# ── no extra flags behavior ─────────────────────────────────────────────────

@patch("metabolon.lysin.cli.format_text", return_value="out")
@patch("metabolon.lysin.cli.fetch_summary")
def test_no_flags_does_not_fetch_sections(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["apoptosis"])
    assert result.exit_code == 0
    # fetch_summary called, but fetch_sections should NOT be imported/called
    # (verify format_text called with full=False)
    call_kwargs = mock_fmt.call_args
    assert call_kwargs[1].get("full") is not True


@patch("metabolon.lysin.cli.format_text", return_value="out")
@patch("metabolon.lysin.cli.fetch_summary")
def test_term_passed_verbatim(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, ["BRCA1"])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with("BRCA1")
