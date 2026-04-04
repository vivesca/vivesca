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


# ── argument validation ──────────────────────────────────────────────────────


def test_no_term_shows_usage_error():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Usage" in result.output


def test_lysin_cli_help_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "term" in result.output.lower()
    assert "--full" in result.output
    assert "--json" in result.output


# ── section assignment ───────────────────────────────────────────────────────


@patch("metabolon.lysin.cli.format_text", return_value="formatted-full")
@patch("metabolon.lysin.cli.fetch_sections", return_value=[{"title": "Fn", "text": "details"}])
@patch("metabolon.lysin.cli.fetch_summary")
def test_full_flag_sets_sections_on_article(mock_fetch, mock_sections, mock_fmt):
    article = _article()
    mock_fetch.return_value = article
    runner = CliRunner()
    runner.invoke(main, ["TP53", "--full"])
    # The article object returned by fetch_summary should have its .sections
    # updated to the return value of fetch_sections
    assert article.sections == [{"title": "Fn", "text": "details"}]


@patch("metabolon.lysin.cli.format_json", return_value="{}")
@patch("metabolon.lysin.cli.fetch_summary")
def test_json_without_full_does_not_call_fetch_sections(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    with patch("metabolon.lysin.cli.fetch_sections") as mock_secs:
        result = runner.invoke(main, ["TP53", "--json"])
    assert result.exit_code == 0
    mock_secs.assert_not_called()
    # format_json should be called with full=False
    mock_fmt.assert_called_once()
    assert mock_fmt.call_args[1].get("full") is not True


# ── multi-word / special terms ───────────────────────────────────────────────


@patch("metabolon.lysin.cli.format_text", return_value="out")
@patch("metabolon.lysin.cli.fetch_summary")
def test_multi_word_term(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article(title="apoptosis pathway")
    runner = CliRunner()
    result = runner.invoke(main, ["apoptosis pathway"])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with("apoptosis pathway")


@patch("metabolon.lysin.cli.format_text", return_value="out")
@patch("metabolon.lysin.cli.fetch_summary")
def test_empty_string_term(mock_fetch, mock_fmt):
    mock_fetch.return_value = _article()
    runner = CliRunner()
    result = runner.invoke(main, [""])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with("")


# ── format function receives correct article ─────────────────────────────────


@patch("metabolon.lysin.cli.format_text", return_value="out")
@patch("metabolon.lysin.cli.fetch_summary")
def test_format_text_receives_article_object(mock_fetch, mock_fmt):
    art = _article(title="EGFR", definition="Epidermal growth factor receptor.")
    mock_fetch.return_value = art
    runner = CliRunner()
    result = runner.invoke(main, ["EGFR"])
    assert result.exit_code == 0
    # format_text is called with the article as first positional arg
    assert mock_fmt.call_args[0][0] is art


@patch("metabolon.lysin.cli.format_json", return_value="{}")
@patch("metabolon.lysin.cli.fetch_summary")
def test_format_json_receives_article_object(mock_fetch, mock_fmt):
    art = _article(title="MYC")
    mock_fetch.return_value = art
    runner = CliRunner()
    result = runner.invoke(main, ["MYC", "--json"])
    assert result.exit_code == 0
    assert mock_fmt.call_args[0][0] is art


# ── error message content ────────────────────────────────────────────────────


@patch("metabolon.lysin.cli.fetch_summary", side_effect=LookupError("FOOBAR not found"))
def test_lookup_error_message_contains_term(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["FOOBAR"])
    assert result.exit_code == 1
    output = result.stderr or result.output
    assert "Not found" in output
    assert "FOOBAR not found" in output


@patch("metabolon.lysin.cli.fetch_summary", side_effect=ConnectionError("timeout"))
def test_connection_error_exit_1(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 1
    output = result.stderr or result.output
    assert "Error: timeout" in output


@patch("metabolon.lysin.cli.fetch_summary", side_effect=ValueError("bad data"))
def test_value_error_exit_1(mock_fetch):
    runner = CliRunner()
    result = runner.invoke(main, ["TP53"])
    assert result.exit_code == 1
    assert "Error: bad data" in (result.stderr or result.output)
