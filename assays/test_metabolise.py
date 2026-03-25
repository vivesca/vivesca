"""Tests for the metabolise command — cross-model idea metabolism engine."""

from unittest.mock import patch

from click.testing import CliRunner

from metabolon.pore import (
    _detect_chain_seeds,
    _extract_key_nouns,
    _jaccard,
    _word_set,
    cli,
)

# ── Unit tests for similarity helpers ────────────────────────────────


def test_word_set_basic():
    assert _word_set("The quick brown fox") == {"the", "quick", "brown", "fox"}


def test_word_set_ignores_short():
    assert _word_set("A I go") == {"go"}


def test_jaccard_identical():
    assert _jaccard({"a", "b", "c"}, {"a", "b", "c"}) == 1.0


def test_jaccard_disjoint():
    assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_partial():
    # {a, b, c} & {b, c, d} = {b, c}, union = {a, b, c, d}
    assert _jaccard({"a", "b", "c"}, {"b", "c", "d"}) == 0.5


def test_jaccard_empty():
    assert _jaccard(set(), set()) == 1.0


# ── Convergence detection ────────────────────────────────────────────


def _mock_query_converges(model, prompt, timeout=120):
    """Always returns the same compression — should converge on round 2."""
    if "compress" in prompt.lower() or "one sentence" in prompt.lower():
        return "Ideas metabolise through adversarial compression cycles."
    if "adversarial pusher" in prompt.lower():
        return '"Make it real" — What concrete mechanism drives the compression?'
    return "This is an expanded exploration of the seed idea across multiple dimensions."


def test_convergence_detected():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(cli, ["metabolise", "test idea", "--rounds", "5"])

    assert result.exit_code == 0
    assert "Converged" in result.output


# ── Max rounds limit ─────────────────────────────────────────────────


_round_counter = 0

# Deliberately non-overlapping word sets to ensure <0.6 Jaccard each round
_DIVERGENT_COMPRESSIONS = [
    "Quantum entanglement reveals cryptographic protocols beneath particle wavefunctions.",
    "Mycorrhizal networks demonstrate cooperative resource allocation through fungal symbiosis.",
    "Tectonic subduction zones regulate planetary carbon sequestration via mantle convection.",
    "Linguistic recursion enables infinite semantic compositionality from finite phonological inventory.",
    "Fermentation kinetics optimize metabolic throughput under anaerobic thermodynamic constraints.",
]


def _mock_query_diverges(model, prompt, timeout=120):
    """Returns different compressions each time — never converges."""
    global _round_counter
    if "compress" in prompt.lower() or "one sentence" in prompt.lower():
        result = _DIVERGENT_COMPRESSIONS[_round_counter % len(_DIVERGENT_COMPRESSIONS)]
        _round_counter += 1
        return result
    if "adversarial pusher" in prompt.lower():
        return '"Just this?" — The scope ignores critical adjacent dimensions.'
    return "An expanded exploration of many different ideas and dimensions."


def test_max_rounds_stops():
    global _round_counter
    _round_counter = 0
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_diverges
        result = runner.invoke(cli, ["metabolise", "test idea", "--rounds", "3"])

    assert result.exit_code == 0
    assert "Result:" in result.output
    # Should not say "Converged" since ideas diverge each round
    assert "Converged" not in result.output


# ── Output file writing ──────────────────────────────────────────────


def test_output_file_written(tmp_path):
    out_file = tmp_path / "result.md"
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(cli, ["metabolise", "test idea", "-o", str(out_file)])

    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "metabolise" in content.lower() or "compression" in content.lower()


def test_no_output_file_without_flag():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(cli, ["metabolise", "test idea"])

    assert result.exit_code == 0
    assert "Written to" not in result.output


# ── Graceful error handling ──────────────────────────────────────────


def _mock_query_fails_on_expand(model, prompt, timeout=120):
    """Fails on expansion calls."""
    if "exploring an idea" in prompt.lower() or "go deeper" in prompt.lower():
        raise RuntimeError("Model unavailable")
    return "Some response"


def test_model_error_handled_gracefully():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_fails_on_expand
        result = runner.invoke(cli, ["metabolise", "test idea"])

    assert result.exit_code == 0
    assert "ERROR" in result.output


def _mock_query_fails_on_push(model, prompt, timeout=120):
    """Works for expand/compress, fails on push."""
    if "adversarial pusher" in prompt.lower():
        raise RuntimeError("Pusher model down")
    if "compress" in prompt.lower() or "one sentence" in prompt.lower():
        return "The essential insight about the idea."
    return "Expanded exploration of the idea across many dimensions."


def test_push_error_handled_gracefully():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_fails_on_push
        result = runner.invoke(cli, ["metabolise", "test idea", "--rounds", "3"])

    assert result.exit_code == 0
    assert "ERROR" in result.output
    # Should still have produced at least round 1's compression
    assert "Result:" in result.output


# ── Header and output format ─────────────────────────────────────────


def test_output_format():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(
            cli,
            [
                "metabolise",
                "test idea",
                "--expander",
                "gemini",
                "--pusher",
                "claude",
            ],
        )

    assert result.exit_code == 0
    assert "Metabolise: test idea" in result.output
    assert "Expander: gemini" in result.output
    assert "Pusher: claude" in result.output
    assert "Round 1 [gemini]:" in result.output


# ── Custom model options ─────────────────────────────────────────────


def test_custom_models():
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(
            cli,
            [
                "metabolise",
                "test idea",
                "--expander",
                "deepseek",
                "--pusher",
                "haiku",
            ],
        )

    assert result.exit_code == 0
    assert "Expander: deepseek" in result.output
    assert "Pusher: haiku" in result.output


# ── Chain detection helpers ─────────────────────────────────────────


def test_extract_key_nouns_filters_short_and_common():
    nouns = _extract_key_nouns("the system should enable large throughput")
    # "the" too short, "system"/"enable"/"large" are common words
    assert "throughput" in nouns
    assert "system" not in nouns
    assert "enable" not in nouns
    assert "large" not in nouns


def test_extract_key_nouns_extracts_significant():
    nouns = _extract_key_nouns("Mycorrhizal networks demonstrate cooperative symbiosis")
    assert "mycorrhizal" in nouns
    assert "networks" in nouns
    assert "cooperative" in nouns
    assert "symbiosis" in nouns
    assert "demonstrate" in nouns


def test_detect_chain_seeds_finds_novel_concepts():
    result = "Fermentation kinetics optimize metabolic throughput under anaerobic constraints."
    existing = ["Ideas about system design and architecture"]
    seeds = _detect_chain_seeds(result, existing)
    assert len(seeds) > 0
    # Seeds should contain words from the result, not from existing
    for s in seeds:
        words = s.split()
        for w in words:
            assert w not in _extract_key_nouns("Ideas about system design and architecture")


def test_detect_chain_seeds_returns_empty_when_all_covered():
    result = "Networks demonstrate cooperative symbiosis"
    existing = ["Networks demonstrate cooperative symbiosis and more"]
    seeds = _detect_chain_seeds(result, existing)
    assert seeds == []


def test_detect_chain_seeds_caps_at_two():
    result = (
        "Thermodynamics crystallography bioinformatics "
        "proteomics spectroscopy neuroplasticity genomics "
        "metamaterials nanotechnology astrophysics"
    )
    existing = ["basic simple idea"]
    seeds = _detect_chain_seeds(result, existing)
    assert len(seeds) <= 2


def test_no_chain_flag_accepted():
    """The --no-chain flag should be accepted without error."""
    runner = CliRunner()
    with patch("metabolon.pore._acquire_catalyst") as mock_llm_mod:
        mock_mod = mock_llm_mod.return_value
        mock_mod.query.side_effect = _mock_query_converges
        result = runner.invoke(cli, ["metabolise", "test idea", "--no-chain"])

    assert result.exit_code == 0
    assert "Converged" in result.output
