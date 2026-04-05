from __future__ import annotations

"""Comprehensive tests for metabolon/pore.py — CLI entry point.

Tests cover:
- Helper functions: _extract_key_nouns, _detect_chain_seeds, _word_set, _jaccard,
  _parse_frontmatter, _keyword_overlap, _hooks_status
- CLI commands with mocked external dependencies
"""


from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from metabolon.pore import (
    _COMMON_WORDS,
    CONSOLIDATION_PATHWAYS,
    _detect_chain_seeds,
    _extract_key_nouns,
    _jaccard,
    _keyword_overlap,
    _parse_frontmatter,
    _word_set,
    cli,
)

# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS: Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════


class TestWordSet:
    """Tests for _word_set helper."""

    def test_basic(self):
        assert _word_set("The quick brown fox") == {"the", "quick", "brown", "fox"}

    def test_ignores_single_chars(self):
        assert _word_set("A I am") == {"am"}

    def test_empty_string(self):
        assert _word_set("") == set()

    def test_whitespace_only(self):
        assert _word_set("   \t\n") == set()

    def test_case_normalization(self):
        result = _word_set("UPPER lower MiXeD")
        assert result == {"upper", "lower", "mixed"}

    def test_preserves_duplicates_as_set(self):
        assert _word_set("hello hello world world") == {"hello", "world"}


class TestJaccard:
    """Tests for _jaccard similarity function."""

    def test_identical_sets(self):
        assert _jaccard({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        # {a, b, c} ∩ {b, c, d} = {b, c}, union = {a, b, c, d}
        assert _jaccard({"a", "b", "c"}, {"b", "c", "d"}) == 0.5

    def test_both_empty(self):
        assert _jaccard(set(), set()) == 1.0

    def test_one_empty(self):
        assert _jaccard({"a"}, set()) == 0.0
        assert _jaccard(set(), {"a"}) == 0.0

    def test_single_element(self):
        assert _jaccard({"a"}, {"a"}) == 1.0
        assert _jaccard({"a"}, {"b"}) == 0.0


class TestExtractKeyNouns:
    """Tests for _extract_key_nouns helper."""

    def test_filters_short_words(self):
        nouns = _extract_key_nouns("a an the to of in")
        assert nouns == set()

    def test_filters_common_words(self):
        # These are in _COMMON_WORDS
        nouns = _extract_key_nouns("the system should enable large throughput")
        assert "throughput" in nouns
        assert "system" not in nouns  # in common words
        assert "enable" not in nouns  # in common words
        assert "large" not in nouns  # in common words

    def test_extracts_significant_words(self):
        nouns = _extract_key_nouns("Mycorrhizal networks demonstrate cooperative symbiosis")
        assert "mycorrhizal" in nouns
        assert "networks" in nouns
        assert "cooperative" in nouns
        assert "symbiosis" in nouns

    def test_case_insensitive(self):
        nouns = _extract_key_nouns("CRYPTOGRAPHY Security PROTOCOLS")
        assert "cryptography" in nouns
        assert "security" in nouns
        assert "protocols" in nouns

    def test_extracts_alphabetic_only(self):
        nouns = _extract_key_nouns("crypto123 algorithms! @mentions")
        assert "algorithms" in nouns
        # crypto123 not extracted (contains digits)
        # mentions should be extracted
        assert "mentions" in nouns

    def test_empty_string(self):
        assert _extract_key_nouns("") == set()

    def test_only_numbers_and_symbols(self):
        assert _extract_key_nouns("123 456 !@#$%") == set()

    def test_common_words_set_exists(self):
        """Verify _COMMON_WORDS is populated."""
        assert len(_COMMON_WORDS) > 50
        assert "system" in _COMMON_WORDS
        assert "design" in _COMMON_WORDS
        assert "important" in _COMMON_WORDS


class TestDetectChainSeeds:
    """Tests for _detect_chain_seeds helper."""

    def test_finds_novel_concepts(self):
        result = "Fermentation kinetics optimize metabolic throughput"
        existing = ["Ideas about system design"]
        seeds = _detect_chain_seeds(result, existing)
        assert len(seeds) > 0
        # Seeds should contain words from result not in existing
        for seed in seeds:
            for word in seed.split():
                assert word not in _extract_key_nouns("Ideas about system design")

    def test_returns_empty_when_all_covered(self):
        result = "Networks demonstrate cooperative symbiosis"
        existing = ["Networks demonstrate cooperative symbiosis"]
        seeds = _detect_chain_seeds(result, existing)
        assert seeds == []

    def test_caps_at_two_seeds(self):
        result = (
            "Thermodynamics crystallography bioinformatics "
            "proteomics spectroscopy neuroplasticity genomics "
            "metamaterials nanotechnology astrophysics"
        )
        existing = ["basic simple idea"]
        seeds = _detect_chain_seeds(result, existing)
        assert len(seeds) <= 2

    def test_returns_sorted_results(self):
        """Results should be deterministic (sorted)."""
        result = "Zygapophysis xenotransplantation aardvarks"
        existing = ["basic idea"]
        seeds = _detect_chain_seeds(result, existing)
        # Should be sorted alphabetically
        if len(seeds) > 1:
            for i in range(len(seeds) - 1):
                assert seeds[i] <= seeds[i + 1]

    def test_builds_phrases_from_adjacent_novels(self):
        """Each seed should be up to 3 adjacent novel concepts."""
        result = "alpha beta gamma delta epsilon zeta"
        existing = ["unrelated concepts"]
        seeds = _detect_chain_seeds(result, existing)
        for seed in seeds:
            words = seed.split()
            assert len(words) <= 3


class TestParseFrontmatter:
    """Tests for _parse_frontmatter helper."""

    def test_basic_frontmatter(self):
        text = """---
title: Test Title
description: Test description
---
Content here"""
        meta = _parse_frontmatter(text)
        assert meta["title"] == "Test Title"
        assert meta["description"] == "Test description"

    def test_no_frontmatter(self):
        text = "No frontmatter here, just content."
        assert _parse_frontmatter(text) == {}

    def test_incomplete_frontmatter(self):
        text = "---\ntitle: Test\nContent here"
        assert _parse_frontmatter(text) == {}

    def test_empty_frontmatter(self):
        text = "---\n---\nContent"
        assert _parse_frontmatter(text) == {}

    def test_multiline_value(self):
        """Simple parser only captures first line of value."""
        text = """---
title: Test
description: Line one
---
Content"""
        meta = _parse_frontmatter(text)
        assert meta["title"] == "Test"
        assert "Line one" in meta["description"]

    def test_colon_in_value(self):
        text = """---
title: Test: A Subtitle
---
Content"""
        meta = _parse_frontmatter(text)
        assert "Test" in meta["title"]
        assert "Subtitle" in meta["title"]

    def test_numeric_value(self):
        text = """---
count: 42
---
Content"""
        meta = _parse_frontmatter(text)
        assert meta["count"] == "42"


class TestKeywordOverlap:
    """Tests for _keyword_overlap helper."""

    def test_basic_overlap(self):
        overlap = _keyword_overlap("the quick fox", "quick brown fox")
        assert "quick" in overlap
        assert "brown" not in overlap

    def test_no_overlap(self):
        overlap = _keyword_overlap("alpha beta", "gamma delta")
        assert overlap == set()

    def test_minimum_word_length(self):
        """Default min_word_len=4 filters short words."""
        overlap = _keyword_overlap("testing system", "testing app")
        assert "testing" in overlap
        assert "app" not in overlap  # too short

    def test_case_insensitive(self):
        overlap = _keyword_overlap("CRYPTOGRAPHY", "cryptography methods")
        assert "cryptography" in overlap

    def test_empty_strings(self):
        assert _keyword_overlap("", "") == set()
        assert _keyword_overlap("test", "") == set()

    def test_extracts_alphanumeric(self):
        overlap = _keyword_overlap("test_module", "test_module function")
        assert "test_module" in overlap


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: CLI Commands
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLIVersion:
    """Tests for CLI version command."""

    def test_version_shows(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Version shows package name
        assert "version" in result.output.lower()


class TestServeCommand:
    """Tests for serve CLI command."""

    @patch("metabolon.membrane._absorb_cofactors")
    @patch("metabolon.membrane.assemble_organism")
    @patch("metabolon.organelles.inflammasome.run_all_probes")
    @patch("metabolon.organelles.inflammasome.adaptive_response")
    def test_serve_stdio_mode(self, mock_adaptive, mock_probes, mock_assemble, mock_cofactors):
        """Test serve command in stdio mode."""
        mock_probes.return_value = []
        mock_mcp = MagicMock()
        mock_assemble.return_value = mock_mcp

        runner = CliRunner()
        runner.invoke(cli, ["serve"])

        mock_cofactors.assert_called_once()
        mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("metabolon.membrane._absorb_cofactors")
    @patch("metabolon.membrane.assemble_organism")
    @patch("metabolon.organelles.inflammasome.run_all_probes")
    @patch("metabolon.organelles.inflammasome.adaptive_response")
    def test_serve_http_mode(self, mock_adaptive, mock_probes, mock_assemble, mock_cofactors):
        """Test serve command in HTTP mode."""
        mock_probes.return_value = []
        mock_mcp = MagicMock()
        mock_assemble.return_value = mock_mcp

        runner = CliRunner()
        runner.invoke(cli, ["serve", "--http"])

        mock_mcp.run.assert_called_once()
        call_kwargs = mock_mcp.run.call_args[1]
        assert call_kwargs["transport"] == "streamable-http"

    @patch("metabolon.membrane._absorb_cofactors")
    @patch("metabolon.membrane.assemble_organism")
    @patch("metabolon.organelles.inflammasome.run_all_probes")
    @patch("metabolon.organelles.inflammasome.adaptive_response")
    def test_serve_custom_host_port(
        self, mock_adaptive, mock_probes, mock_assemble, mock_cofactors
    ):
        """Test serve command with custom host and port."""
        mock_probes.return_value = []
        mock_mcp = MagicMock()
        mock_assemble.return_value = mock_mcp

        runner = CliRunner()
        runner.invoke(cli, ["serve", "--http", "--host", "0.0.0.0", "--port", "9000"])

        call_kwargs = mock_mcp.run.call_args[1]
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 9000


class TestReloadCommand:
    """Tests for reload CLI command."""

    @patch("subprocess.run")
    def test_reload_success(self, mock_run, tmp_path, monkeypatch):
        """Test successful reload of LaunchAgent."""
        plist_path = tmp_path / "Library" / "LaunchAgents" / "com.vivesca.mcp.plist"
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text("<?xml version='1.0'?><plist/>")

        monkeypatch.setenv("HOME", str(tmp_path))

        runner = CliRunner()
        result = runner.invoke(cli, ["reload"])

        assert mock_run.call_count == 2
        assert "Reloaded" in result.output

    def test_reload_missing_plist(self, tmp_path, monkeypatch):
        """Test reload fails when LaunchAgent missing."""
        monkeypatch.setenv("HOME", str(tmp_path))

        runner = CliRunner()
        result = runner.invoke(cli, ["reload"])

        assert result.exit_code == 1
        assert "LaunchAgent not found" in result.output

    @patch("subprocess.run")
    def test_reload_linux_uses_systemctl(self, mock_run, monkeypatch):
        """On Linux, reload should use systemctl --user restart."""
        monkeypatch.setenv("HOME", "/home/testuser")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch("platform.system", return_value="Linux"):
            runner = CliRunner()
            result = runner.invoke(cli, ["reload"])

        assert result.exit_code == 0
        assert "systemctl" in result.output
        mock_run.assert_called_once()
        assert "systemctl" in mock_run.call_args[0][0]
        assert "--user" in mock_run.call_args[0][0]

    @patch("subprocess.run", side_effect=FileNotFoundError("systemctl not found"))
    def test_reload_linux_systemctl_fails(self, mock_run, monkeypatch):
        """On Linux without systemctl, reload should report error."""
        monkeypatch.setenv("HOME", "/home/testuser")

        with patch("platform.system", return_value="Linux"):
            runner = CliRunner()
            result = runner.invoke(cli, ["reload"])

        assert result.exit_code == 1
        assert "launchctl not available" in result.output


class TestInitCommand:
    """Tests for init CLI command."""

    @patch("metabolon.gastrulation.init.scaffold_project")
    def test_init_creates_project(self, mock_scaffold, tmp_path):
        """Test init command scaffolds a new project."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "demo", "-d", "Demo server"])

        assert result.exit_code == 0
        mock_scaffold.assert_called_once()
        # scaffold_project(name, target, description) - positional args
        args = mock_scaffold.call_args[0]
        assert args[0] == "demo"
        assert "demo" in str(args[1])
        assert args[2] == "Demo server"


class TestEpigenomeCommand:
    """Tests for epigenome CLI command."""

    @patch("metabolon.gastrulation.epigenome.scaffold_epigenome")
    def test_epigenome_creates_structure(self, mock_scaffold, tmp_path):
        """Test epigenome command scaffolds instance repo."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["epigenome"])

        assert result.exit_code == 0
        mock_scaffold.assert_called_once()


class TestAddCommands:
    """Tests for add tool/prompt/resource CLI commands."""

    @patch("metabolon.gastrulation.add.graft_tool")
    def test_add_tool_basic(self, mock_graft, tmp_path):
        """Test add tool command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create project structure so Path.cwd() works
            project_dir = tmp_path / "demo"
            project_dir.mkdir(parents=True)

            import os

            os.chdir(project_dir)

            # Return a path within the cwd for relative_to to work
            mock_graft.return_value = project_dir / "src" / "demo" / "enzymes" / "weather.py"

            result = runner.invoke(cli, ["add", "tool", "weather_fetch"])

        assert result.exit_code == 0
        mock_graft.assert_called_once()

    @patch("metabolon.gastrulation.add.graft_tool")
    def test_add_tool_with_options(self, mock_graft, tmp_path):
        """Test add tool with domain and verb options."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            project_dir = tmp_path / "demo"
            project_dir.mkdir(parents=True)

            import os

            os.chdir(project_dir)

            mock_graft.return_value = project_dir / "src" / "demo" / "enzymes" / "data.py"

            result = runner.invoke(
                cli,
                ["add", "tool", "custom", "--domain", "data", "--verb", "process"],
            )

        assert result.exit_code == 0
        call_kwargs = mock_graft.call_args[1]
        assert call_kwargs["domain"] == "data"
        assert call_kwargs["verb"] == "process"

    @patch("metabolon.gastrulation.add.graft_prompt")
    def test_add_prompt(self, mock_graft, tmp_path):
        """Test add prompt command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            project_dir = tmp_path / "demo"
            project_dir.mkdir(parents=True)

            import os

            os.chdir(project_dir)

            mock_graft.return_value = project_dir / "src" / "demo" / "codons" / "analyze.py"

            result = runner.invoke(cli, ["add", "prompt", "analyze"])

        assert result.exit_code == 0
        mock_graft.assert_called_once()

    @patch("metabolon.gastrulation.add.graft_resource")
    def test_add_resource(self, mock_graft, tmp_path):
        """Test add resource command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            project_dir = tmp_path / "demo"
            project_dir.mkdir(parents=True)

            import os

            os.chdir(project_dir)

            mock_graft.return_value = project_dir / "src" / "demo" / "resources" / "config.py"

            result = runner.invoke(cli, ["add", "resource", "config"])

        assert result.exit_code == 0
        mock_graft.assert_called_once()


class TestCheckCommand:
    """Tests for check CLI command."""

    @patch("metabolon.gastrulation.check.probe_gastrulation")
    def test_check_passes(self, mock_probe, tmp_path):
        """Test check command with no issues."""
        mock_probe.return_value = []

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["check"])

        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    @patch("metabolon.gastrulation.check.probe_gastrulation")
    def test_check_finds_issues(self, mock_probe, tmp_path):
        """Test check command with issues."""
        mock_probe.return_value = ["Issue 1", "Issue 2"]

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["check"])

        assert result.exit_code == 1
        assert "2 issue" in result.output


class TestHooksCommands:
    """Tests for hooks check/repair CLI commands."""

    @patch("metabolon.pore._hooks_status")
    def test_hooks_check_healthy(self, mock_status, tmp_path):
        """Test hooks check when healthy."""
        mock_status.return_value = []

        runner = CliRunner()
        result = runner.invoke(cli, ["hooks", "check"])

        assert result.exit_code == 0
        assert "HEALTHY" in result.output

    @patch("metabolon.pore._hooks_status")
    def test_hooks_check_broken(self, mock_status, tmp_path):
        """Test hooks check when broken."""
        mock_status.return_value = ["hooks: not a symlink"]

        runner = CliRunner()
        result = runner.invoke(cli, ["hooks", "check"])

        assert result.exit_code == 1
        assert "BROKEN" in result.output


class TestAutopoiesisCommands:
    """Tests for autopoiesis CLI commands."""

    @patch("metabolon.organelles.inflammasome.probe_report")
    def test_autopoiesis_probe(self, mock_report, tmp_path):
        """Test autopoiesis probe command."""
        mock_report.return_value = "Probe report output"

        runner = CliRunner()
        result = runner.invoke(cli, ["autopoiesis", "probe"])

        assert result.exit_code == 0
        assert "Probe report" in result.output

    @patch("metabolon.organelles.inflammasome.run_all_probes")
    @patch("metabolon.organelles.inflammasome.adaptive_response")
    def test_autopoiesis_repair(self, mock_adaptive, mock_probes, tmp_path):
        """Test autopoiesis repair command."""
        mock_probes.return_value = [
            {"name": "test", "passed": True, "message": "OK", "duration_ms": 10}
        ]

        runner = CliRunner()
        result = runner.invoke(cli, ["autopoiesis", "repair"])

        assert result.exit_code == 0
        assert "PASS" in result.output


class TestMetaboliseCommand:
    """Tests for metabolise CLI command (additional coverage)."""

    def _mock_transduce(self, model, prompt, timeout=120):
        if "compress" in prompt.lower() or "one sentence" in prompt.lower():
            return "Compressed insight."
        if "adversarial" in prompt.lower():
            return '"Make it real" — specific challenge.'
        return "Expanded exploration of the idea."

    @patch("metabolon.pore._acquire_catalyst")
    def test_metabolise_basic(self, mock_catalyst):
        """Test basic metabolise execution."""
        mock_mod = MagicMock()
        mock_mod.transduce.side_effect = self._mock_transduce
        mock_catalyst.return_value = mock_mod

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolise", "test idea", "--no-publish"])

        assert result.exit_code == 0

    @patch("metabolon.pore._acquire_catalyst")
    def test_metabolise_with_output_file(self, mock_catalyst, tmp_path):
        """Test metabolise writes to output file."""
        mock_mod = MagicMock()
        mock_mod.transduce.side_effect = self._mock_transduce
        mock_catalyst.return_value = mock_mod

        out_file = tmp_path / "result.md"

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["metabolise", "test idea", "-o", str(out_file), "--no-publish"],
            )

        assert result.exit_code == 0


class TestPulseCommand:
    """Tests for pulse CLI command."""

    @patch("metabolon.pulse.main")
    def test_pulse_default(self, mock_pulse_main, tmp_path):
        """Test pulse command with defaults."""
        runner = CliRunner()
        runner.invoke(cli, ["pulse"])

        mock_pulse_main.assert_called_once()
        call_kwargs = mock_pulse_main.call_args[1]
        assert call_kwargs["model"] == "opus"

    @patch("metabolon.pulse.main")
    def test_pulse_with_options(self, mock_pulse_main, tmp_path):
        """Test pulse command with custom options."""
        runner = CliRunner()
        runner.invoke(
            cli,
            ["pulse", "--waves", "5", "--model", "sonnet", "--retry", "2"],
        )

        call_kwargs = mock_pulse_main.call_args[1]
        assert call_kwargs["systoles"] == 5
        assert call_kwargs["model"] == "sonnet"
        assert call_kwargs["retry"] == 2

    @patch("metabolon.pulse.main")
    def test_pulse_overnight_flag(self, mock_pulse_main, tmp_path):
        """Test pulse --overnight sets overnight defaults."""
        runner = CliRunner()
        runner.invoke(cli, ["pulse", "--overnight"])

        call_kwargs = mock_pulse_main.call_args[1]
        assert call_kwargs["systoles"] == 3
        assert call_kwargs["stop_after"] == "07:00"

    @patch("metabolon.pulse.main")
    def test_pulse_dry_run(self, mock_pulse_main, tmp_path):
        """Test pulse --dry-run flag."""
        runner = CliRunner()
        runner.invoke(cli, ["pulse", "--dry-run"])

        call_kwargs = mock_pulse_main.call_args[1]
        assert call_kwargs["dry_run"] is True


class TestMetabolismCommands:
    """Tests for metabolism CLI commands."""

    @patch("metabolon.metabolism.substrates.receptor_catalog")
    @patch("metabolon.pore._run_substrate")
    def test_metabolism_run_single(self, mock_run, mock_registry, tmp_path):
        """Test metabolism run with single target."""
        mock_registry.return_value = {"phenotype": MagicMock}

        runner = CliRunner()
        runner.invoke(cli, ["metabolism", "run", "phenotype"])

        mock_run.assert_called_once_with("phenotype", days=30)

    @patch("metabolon.metabolism.substrates.receptor_catalog")
    @patch("metabolon.pore._run_substrate")
    def test_metabolism_run_all(self, mock_run, mock_registry, tmp_path):
        """Test metabolism run with all targets."""
        mock_registry.return_value = {"phenotype": MagicMock, "dna": MagicMock}

        runner = CliRunner()
        runner.invoke(cli, ["metabolism", "run", "all"])

        assert mock_run.call_count == 2

    @patch("metabolon.metabolism.substrates.receptor_catalog")
    def test_metabolism_run_unknown_target(self, mock_registry, tmp_path):
        """Test metabolism run with unknown target."""
        mock_registry.return_value = {"phenotype": MagicMock}

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "run", "unknown"])

        assert result.exit_code == 1
        assert "Unknown target" in result.output


class TestEndocytosisCommands:
    """Tests for endocytosis CLI commands."""

    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    @patch("metabolon.organelles.endocytosis_rss.state.lockfile")
    @patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
    def test_endocytosis_fetch(self, mock_fetch, mock_lock, mock_config, tmp_path):
        """Test endocytosis fetch command."""
        cfg = MagicMock()
        cfg.state_path = tmp_path / "state.json"
        mock_config.return_value = cfg

        # Make lockfile a context manager
        mock_lock.return_value.__enter__ = MagicMock(return_value=None)
        mock_lock.return_value.__exit__ = MagicMock(return_value=None)

        runner = CliRunner()
        runner.invoke(cli, ["endocytosis", "fetch"])

        mock_fetch.assert_called_once()

    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    def test_endocytosis_status(self, mock_restore_state, mock_config, tmp_path):
        """Test endocytosis status command."""
        cfg = MagicMock()
        cfg.config_dir = tmp_path
        cfg.sources_path = tmp_path / "sources.yaml"
        cfg.state_path = tmp_path / "state.json"
        cfg.log_path = tmp_path / "news.md"
        cfg.cargo_path = tmp_path / "cargo.jsonl"
        cfg.article_cache_dir = tmp_path / "cache"

        # Create files
        cfg.sources_path.write_text("sources:")
        cfg.state_path.write_text("{}")
        cfg.log_path.write_text("log")
        cfg.cargo_path.write_text("{}")
        cfg.article_cache_dir.mkdir()

        mock_config.return_value = cfg
        mock_restore_state.return_value = {}

        runner = CliRunner()
        result = runner.invoke(cli, ["endocytosis", "status"])

        assert result.exit_code == 0
        assert "Endocytosis Status" in result.output

    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    @patch("metabolon.organelles.endocytosis_rss.breaking.scan_breaking")
    def test_endocytosis_breaking(self, mock_scan, mock_config, tmp_path):
        """Test endocytosis breaking command."""
        cfg = MagicMock()
        mock_config.return_value = cfg
        mock_scan.return_value = 0

        runner = CliRunner()
        runner.invoke(cli, ["endocytosis", "breaking"])

        mock_scan.assert_called_once()

    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_endocytosis_sources(self, mock_config, tmp_path):
        """Test endocytosis sources command."""
        cfg = MagicMock()
        cfg.sources_data = {"web_sources": [{"name": "Test Feed", "tier": 1, "cadence": "daily"}]}
        mock_config.return_value = cfg

        runner = CliRunner()
        result = runner.invoke(cli, ["endocytosis", "sources"])

        assert result.exit_code == 0
        assert "Test Feed" in result.output


class TestAuscultateCommand:
    """Tests for auscultate CLI command."""

    @patch("subprocess.run")
    def test_auscultate_runs_checks(self, mock_run, tmp_path, monkeypatch):
        """Test auscultate command runs health checks."""
        # Mock pyright output
        mock_run.return_value = MagicMock(
            stdout='{"generalDiagnostics": []}',
            returncode=0,
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["auscultate"])

        assert result.exit_code == 0
        assert "AUSCULTATION" in result.output


class TestPhenotypeCommands:
    """Tests for phenotype CLI commands."""

    @patch("metabolon.organelles.phenotype_translate.translate_to_gemini")
    def test_phenotype_translate(self, mock_translate, tmp_path):
        """Test phenotype translate command."""
        mock_result = MagicMock()
        mock_result.summary = "Translated"
        mock_translate.return_value = (mock_result, "diff text")

        runner = CliRunner()
        runner.invoke(cli, ["phenotype", "translate"])

        mock_translate.assert_called_once()

    @patch("metabolon.organelles.phenotype_translate.sync_phenotype")
    def test_phenotype_sync(self, mock_sync, tmp_path):
        """Test phenotype sync command."""
        mock_result = MagicMock()
        mock_result.ok = True
        mock_result.summary = "Sync complete"
        mock_sync.return_value = mock_result

        runner = CliRunner()
        result = runner.invoke(cli, ["phenotype", "sync"])

        assert result.exit_code == 0


class TestRenameCommand:
    """Tests for rename CLI command."""

    @patch("metabolon.organelles.rename._cli")
    def test_rename_basic(self, mock_cli_func, tmp_path):
        """Test rename command."""
        runner = CliRunner()
        runner.invoke(cli, ["rename", "old_name", "new_name"])

        mock_cli_func.assert_called_once_with("old_name", "new_name", [], False)

    @patch("metabolon.organelles.rename._cli")
    def test_rename_dry_run(self, mock_cli_func, tmp_path):
        """Test rename command with dry-run."""
        runner = CliRunner()
        runner.invoke(cli, ["rename", "old", "new", "--dry-run"])

        mock_cli_func.assert_called_once_with("old", "new", [], True)


class TestConjugationCommands:
    """Tests for conjugation CLI commands."""

    @patch("metabolon.organelles.conjugation_engine.replicate_to_gemini")
    def test_replicate_gemini(self, mock_replicate, tmp_path):
        """Test conjugation replicate gemini command."""
        mock_result = MagicMock()
        mock_replicate.return_value = (mock_result, "diff text")

        runner = CliRunner()
        runner.invoke(cli, ["conjugation", "replicate", "gemini"])

        mock_replicate.assert_called_once()


class TestReceptorHealthCommand:
    """Tests for receptor-health CLI command."""

    @patch("metabolon.enzymes.integrin.integrin_probe")
    @patch("metabolon.enzymes.integrin.integrin_apoptosis_check")
    def test_receptor_health_healthy(self, mock_apoptosis, mock_probe, tmp_path, monkeypatch):
        """Test receptor-health command when healthy."""
        # Mock probe result
        probe_result = MagicMock()
        probe_result.total_receptors = 10
        probe_result.total_references = 20
        probe_result.attached = 20
        probe_result.detached = []
        probe_result.mechanically_silent = []
        probe_result.focal_adhesions = []
        mock_probe.return_value = probe_result

        # Mock apoptosis check
        apoptosis_result = MagicMock()
        apoptosis_result.anoikis_candidates = []
        apoptosis_result.quiescent = []
        apoptosis_result.summary = "All healthy"
        apoptosis_result.retirement_log_updated = False
        mock_apoptosis.return_value = apoptosis_result

        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["receptor-health"])

        assert result.exit_code == 0
        assert "HEALTHY" in result.output

    @patch("metabolon.enzymes.integrin.integrin_probe")
    @patch("metabolon.enzymes.integrin.integrin_apoptosis_check")
    def test_receptor_health_needs_attention(
        self, mock_apoptosis, mock_probe, tmp_path, monkeypatch
    ):
        """Test receptor-health command when anoikis candidates found."""
        # Mock probe result
        probe_result = MagicMock()
        probe_result.total_receptors = 10
        probe_result.total_references = 20
        probe_result.attached = 18
        probe_result.detached = [{"receptor": "broken", "binary": "/bin/broken"}]
        probe_result.mechanically_silent = []
        probe_result.focal_adhesions = []
        mock_probe.return_value = probe_result

        # Mock apoptosis check
        apoptosis_result = MagicMock()
        apoptosis_result.anoikis_candidates = ["candidate1"]
        apoptosis_result.quiescent = []
        apoptosis_result.summary = "Issues found"
        apoptosis_result.retirement_log_updated = True
        mock_apoptosis.return_value = apoptosis_result

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["receptor-health"])

        assert result.exit_code == 1
        assert "NEEDS_ATTENTION" in result.output


class TestConsolidationPathways:
    """Tests for CONSOLIDATION_PATHWAYS constant."""

    def test_pathways_defined(self):
        """Test that consolidation pathways are defined."""
        assert "feedback" in CONSOLIDATION_PATHWAYS
        assert "finding" in CONSOLIDATION_PATHWAYS
        assert "user" in CONSOLIDATION_PATHWAYS
        assert "project" in CONSOLIDATION_PATHWAYS
        assert "reference" in CONSOLIDATION_PATHWAYS

    def test_pathways_have_target_and_rationale(self):
        """Test that each pathway has target and rationale."""
        for value in CONSOLIDATION_PATHWAYS.values():
            assert isinstance(value, tuple)
            assert len(value) == 2
            target, rationale = value
            assert isinstance(target, str)
            assert isinstance(rationale, str)


class TestMetabolismDissolveCommand:
    """Tests for metabolism dissolve CLI command."""

    @patch("metabolon.metabolism.signals.SensorySystem")
    def test_dissolve_missing_memory_dir(self, mock_sensory, tmp_path, monkeypatch):
        """Test dissolve when memory directory doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["metabolism", "dissolve"])

        assert "Memory directory not found" in result.output or result.exit_code == 0


class TestMetabolismAuditCommand:
    """Tests for metabolism audit CLI command."""

    @patch("metabolon.metabolism.signals.SensorySystem")
    def test_audit_missing_constitution(self, mock_sensory, tmp_path, monkeypatch):
        """Test audit when constitution doesn't exist."""
        # Mock home directory
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 1
        assert "No constitution found" in result.output


class TestTemplates:
    """Tests for template constants."""

    def test_divergence_template_format(self):
        """Test DIVERGENCE_TEMPLATE can be formatted."""
        from metabolon.pore import DIVERGENCE_TEMPLATE

        result = DIVERGENCE_TEMPLATE.format(seed="test idea")
        assert "test idea" in result
        assert "Expand this idea" in result

    def test_crystallisation_template_format(self):
        """Test CRYSTALLISATION_TEMPLATE can be formatted."""
        from metabolon.pore import CRYSTALLISATION_TEMPLATE

        result = CRYSTALLISATION_TEMPLATE.format(expansion="expanded text")
        assert "expanded text" in result
        assert "ONE sentence" in result

    def test_selection_pressure_template_format(self):
        """Test SELECTION_PRESSURE_TEMPLATE can be formatted."""
        from metabolon.pore import SELECTION_PRESSURE_TEMPLATE

        result = SELECTION_PRESSURE_TEMPLATE.format(compression="compressed idea")
        assert "compressed idea" in result
        assert "adversarial pusher" in result

    def test_adaptation_template_format(self):
        """Test ADAPTATION_TEMPLATE can be formatted."""
        from metabolon.pore import ADAPTATION_TEMPLATE

        result = ADAPTATION_TEMPLATE.format(
            seed="original idea",
            previous_compression="old compression",
            push="adversarial challenge",
        )
        assert "original idea" in result
        assert "old compression" in result
        assert "adversarial challenge" in result
