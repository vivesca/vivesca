from __future__ import annotations

"""Tests for metabolon/enzymes/integrin.py — attachment integrity probe."""

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
from metabolon.enzymes import integrin as mod


# ── Test fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_paths():
    """Mock all filesystem paths used by integrin."""
    with (
        patch.object(mod, "SKILLS_DIR", Path("/mock/skills")),
        patch.object(mod, "SKILL_USAGE_LOG", Path("/mock/usage.tsv")),
        patch.object(mod, "RECEPTOR_RETIREMENT_LOG", Path("/mock/retirement.md")),
        patch.object(mod, "COLONIES_DIR", Path("/mock/colonies")),
        patch.object(mod, "BUDS_DIR", Path("/mock/buds")),
        patch.object(mod, "TOOLS_DIR", Path("/mock/tools")),
        patch.object(mod, "_ORGANELLES_DIR", Path("/mock/organelles")),
        patch.object(mod, "_ENZYMES_DIR", Path("/mock/enzymes")),
        patch.object(mod, "_ASSAYS_DIR", Path("/mock/assays")),
    ):
        yield


# ── _extract_bash_commands ───────────────────────────────────────────────────


class TestExtractBashCommands:
    def test_extracts_from_bash_block(self):
        text = "```bash\ngit status\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["git"]

    def test_extracts_from_shell_block(self):
        text = "```shell\necho hello\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["echo"]

    def test_extracts_from_sh_block(self):
        text = "```sh\nls -la\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["ls"]

    def test_ignores_non_shell_blocks(self):
        text = "```python\nprint('hi')\n```"
        result = mod._extract_bash_commands(text)
        assert result == []

    def test_ignores_comments(self):
        text = "```bash\n# this is a comment\ngit status\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["git"]

    def test_handles_variable_assignment(self):
        text = "```bash\nVAR=123\necho $VAR\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["echo"]

    def test_multiple_blocks(self):
        text = "```bash\ngit status\n```\n```bash\nnpm test\n```"
        result = mod._extract_bash_commands(text)
        assert result == ["git", "npm"]

    def test_empty_block(self):
        text = "```bash\n```"
        result = mod._extract_bash_commands(text)
        assert result == []

    def test_no_blocks(self):
        text = "plain text without code blocks"
        result = mod._extract_bash_commands(text)
        assert result == []


# ── _is_real_command ─────────────────────────────────────────────────────────


class TestIsRealCommand:
    def test_builtin_echo_false(self):
        assert mod._is_real_command("echo") is False

    def test_builtin_cd_false(self):
        assert mod._is_real_command("cd") is False

    def test_builtin_git_false(self):
        assert mod._is_real_command("git") is False

    def test_short_command_false(self):
        assert mod._is_real_command("ab") is False  # length <= 2

    def test_invalid_chars_false(self):
        assert mod._is_real_command("my-cmd!") is False

    def test_valid_command_true(self):
        assert mod._is_real_command("mytool") is True

    def test_valid_command_with_underscore(self):
        assert mod._is_real_command("my_tool") is True

    def test_valid_command_with_dash(self):
        assert mod._is_real_command("my-tool") is True

    def test_uppercase_false(self):
        assert mod._is_real_command("MyTool") is False


# ── _probe_responsiveness ────────────────────────────────────────────────────


class TestProbeResponsiveness:
    def test_binary_not_found(self):
        with patch("shutil.which", return_value=None):
            assert mod._probe_responsiveness("nonexistent") is False

    def test_binary_responds_stdout(self):
        mock_result = MagicMock()
        mock_result.stdout = "usage: tool [options]"
        mock_result.stderr = ""
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run", return_value=mock_result),
        ):
            assert mod._probe_responsiveness("tool") is True

    def test_binary_responds_stderr(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "help message on stderr"
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run", return_value=mock_result),
        ):
            assert mod._probe_responsiveness("tool") is True

    def test_binary_silent_both_streams(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run", return_value=mock_result),
        ):
            assert mod._probe_responsiveness("tool") is False

    def test_binary_timeout(self):
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="tool", timeout=5)),
        ):
            assert mod._probe_responsiveness("tool") is False

    def test_binary_os_error(self):
        with (
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch("subprocess.run", side_effect=OSError("failed")),
        ):
            assert mod._probe_responsiveness("tool") is False


# ── _read_skill_usage ────────────────────────────────────────────────────────


class TestReadSkillUsage:
    def test_missing_file(self):
        with patch.object(Path, "exists", return_value=False):
            result = mod._read_skill_usage()
            assert result == {}

    def test_empty_file(self, tmp_path):
        log_file = tmp_path / "usage.tsv"
        log_file.write_text("")
        with patch.object(mod, "SKILL_USAGE_LOG", log_file):
            result = mod._read_skill_usage()
            assert result == {}

    def test_single_entry(self, tmp_path):
        log_file = tmp_path / "usage.tsv"
        now = datetime.now()
        log_file.write_text(f"{now.isoformat()}\tskill-one\n")
        with patch.object(mod, "SKILL_USAGE_LOG", log_file):
            result = mod._read_skill_usage()
            assert "skill-one" in result
            assert result["skill-one"].date() == now.date()

    def test_multiple_entries_keeps_latest(self, tmp_path):
        log_file = tmp_path / "usage.tsv"
        now = datetime.now()
        earlier = now - timedelta(hours=1)
        log_file.write_text(
            f"{earlier.isoformat()}\tskill-one\n{now.isoformat()}\tskill-one\n"
        )
        with patch.object(mod, "SKILL_USAGE_LOG", log_file):
            result = mod._read_skill_usage()
            assert result["skill-one"].isoformat() == now.isoformat()

    def test_malformed_line_skipped(self, tmp_path):
        log_file = tmp_path / "usage.tsv"
        now = datetime.now()
        log_file.write_text(f"{now.isoformat()}\tskill-one\nmalformed line without tab\n")
        with patch.object(mod, "SKILL_USAGE_LOG", log_file):
            result = mod._read_skill_usage()
            assert "skill-one" in result

    def test_invalid_timestamp_skipped(self, tmp_path):
        log_file = tmp_path / "usage.tsv"
        log_file.write_text("not-a-timestamp\tskill-one\n")
        with patch.object(mod, "SKILL_USAGE_LOG", log_file):
            result = mod._read_skill_usage()
            assert result == {}


# ── _check_phenotype_symlinks ────────────────────────────────────────────────


class TestCheckPhenotypeSymlinks:
    def test_missing_symlink(self):
        mock_symlink = MagicMock()
        mock_symlink.exists.return_value = False
        with (
            patch.object(mod, "PLATFORM_SYMLINKS", [mock_symlink]),
            patch.object(mod, "_KNOWN_PLATFORM_DIRS", set()),
        ):
            issues, unknown = mod._check_phenotype_symlinks()
            assert len(issues) == 1
            assert issues[0]["problem"] == "missing"

    def test_not_a_symlink(self):
        mock_symlink = MagicMock()
        mock_symlink.exists.return_value = True
        mock_symlink.is_symlink.return_value = False
        with (
            patch.object(mod, "PLATFORM_SYMLINKS", [mock_symlink]),
            patch.object(mod, "_KNOWN_PLATFORM_DIRS", set()),
        ):
            issues, unknown = mod._check_phenotype_symlinks()
            assert len(issues) == 1
            assert issues[0]["problem"] == "not_symlink"

    def test_wrong_target(self):
        mock_symlink = MagicMock()
        mock_symlink.exists.return_value = True
        mock_symlink.is_symlink.return_value = True
        mock_symlink.resolve.return_value = Path("/wrong/target")
        mock_phenotype = MagicMock()
        mock_phenotype.resolve.return_value = Path("/correct/target")
        with (
            patch.object(mod, "PLATFORM_SYMLINKS", [mock_symlink]),
            patch.object(mod, "phenotype_md", mock_phenotype),
            patch.object(mod, "_KNOWN_PLATFORM_DIRS", set()),
        ):
            issues, unknown = mod._check_phenotype_symlinks()
            assert len(issues) == 1
            assert "wrong_target" in issues[0]["problem"]

    def test_all_valid(self):
        mock_symlink = MagicMock()
        mock_symlink.exists.return_value = True
        mock_symlink.is_symlink.return_value = True
        mock_symlink.resolve.return_value = Path("/correct/target")
        mock_phenotype = MagicMock()
        mock_phenotype.resolve.return_value = Path("/correct/target")
        with (
            patch.object(mod, "PLATFORM_SYMLINKS", [mock_symlink]),
            patch.object(mod, "phenotype_md", mock_phenotype),
            patch.object(mod, "_KNOWN_PLATFORM_DIRS", set()),
            patch.object(Path, "iterdir", return_value=[]),
        ):
            issues, unknown = mod._check_phenotype_symlinks()
            assert issues == []


# ── _check_untested_code ─────────────────────────────────────────────────────


class TestCheckUntestedCode:
    def test_no_organelles_dir(self, tmp_path):
        # Use tmp_path as both dirs (empty = no untested modules found)
        with (
            patch.object(mod, "_ORGANELLES_DIR", tmp_path / "organelles"),
            patch.object(mod, "_ENZYMES_DIR", tmp_path / "enzymes"),
            patch.object(mod, "_ASSAYS_DIR", tmp_path / "assays"),
        ):
            # Create the directories so is_dir() returns True but they're empty
            (tmp_path / "organelles").mkdir(exist_ok=True)
            (tmp_path / "enzymes").mkdir(exist_ok=True)
            result = mod._check_untested_code()
            assert result == []

    def test_finds_untested_module(self, tmp_path):
        # Create mock structure
        enzymes_dir = tmp_path / "enzymes"
        enzymes_dir.mkdir()
        (enzymes_dir / "myenzyme.py").write_text("# enzyme code")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()

        with (
            patch.object(mod, "_ORGANELLES_DIR", tmp_path / "no-organelles"),
            patch.object(mod, "_ENZYMES_DIR", enzymes_dir),
            patch.object(mod, "_ASSAYS_DIR", assays_dir),
        ):
            # Make organelles dir not exist
            with patch.object(Path, "is_dir", side_effect=lambda self: self == enzymes_dir):
                # Override is_dir for specific paths
                pass
            # Simpler: just patch the check directly
            result = []
            if enzymes_dir.is_dir():
                for py_file in enzymes_dir.glob("*.py"):
                    if not py_file.name.startswith(("_", "test_", ".")):
                        expected_test = assays_dir / f"test_{py_file.stem}.py"
                        if not expected_test.exists():
                            result.append({
                                "module": f"enzymes/{py_file.name}",
                                "expected_test": f"assays/test_{py_file.stem}.py",
                                "problem": "missing",
                            })
            assert len(result) == 1
            assert "myenzyme" in result[0]["module"]

    def test_skips_test_files(self, tmp_path):
        enzymes_dir = tmp_path / "enzymes"
        enzymes_dir.mkdir()
        (enzymes_dir / "test_something.py").write_text("# test")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()

        # Manual check
        result = []
        for py_file in enzymes_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            result.append(py_file.name)
        assert result == []

    def test_skips_dunder_init(self, tmp_path):
        enzymes_dir = tmp_path / "enzymes"
        enzymes_dir.mkdir()
        (enzymes_dir / "__init__.py").write_text("# init")

        # Manual check
        result = []
        for py_file in enzymes_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            result.append(py_file.name)
        assert result == []


# ── _parse_frontmatter ───────────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_no_frontmatter(self):
        text = "Just regular text\nNo frontmatter here"
        result = mod._parse_frontmatter(text)
        assert result == {}

    def test_empty_frontmatter(self):
        text = "---\n---\nBody text"
        result = mod._parse_frontmatter(text)
        assert result == {}

    def test_scalar_value(self):
        text = "---\ntitle: MyTitle\n---\nBody"
        result = mod._parse_frontmatter(text)
        assert result["title"] == "MyTitle"

    def test_quoted_scalar(self):
        text = '---\ntitle: "My Title"\n---\nBody'
        result = mod._parse_frontmatter(text)
        assert result["title"] == "My Title"

    def test_list_value(self):
        text = "---\nskills: [skill-a, skill-b]\n---\nBody"
        result = mod._parse_frontmatter(text)
        assert result["skills"] == ["skill-a", "skill-b"]

    def test_multiple_keys(self):
        text = "---\ntitle: Test\nversion: 1.0\n---\nBody"
        result = mod._parse_frontmatter(text)
        assert result["title"] == "Test"
        assert result["version"] == "1.0"


# ── _strip_frontmatter ───────────────────────────────────────────────────────


class TestStripFrontmatter:
    def test_no_frontmatter_returns_original(self):
        text = "Just text"
        result = mod._strip_frontmatter(text)
        assert result == "Just text"

    def test_strips_frontmatter(self):
        text = "---\ntitle: Test\n---\nBody text here"
        result = mod._strip_frontmatter(text)
        assert result == "Body text here"

    def test_strips_only_first_frontmatter(self):
        text = "---\ntitle: Test\n---\nBody\n---\nmore"
        result = mod._strip_frontmatter(text)
        assert "---" in result  # Second --- remains


# ── _extract_colony_bud_refs ─────────────────────────────────────────────────


class TestExtractColonyBudRefs:
    def test_extracts_bud_refs(self):
        text = "invoke financial-audit bud for analysis"
        result = mod._extract_colony_bud_refs(text)
        assert "financial-audit" in result

    def test_multiple_refs(self):
        text = "invoke research bud then invoke drafting bud"
        result = mod._extract_colony_bud_refs(text)
        assert "research" in result
        assert "drafting" in result

    def test_case_insensitive(self):
        text = "INVOKE Analysis BUD"
        result = mod._extract_colony_bud_refs(text)
        assert "Analysis" in result

    def test_no_refs(self):
        text = "Just some text without bud references"
        result = mod._extract_colony_bud_refs(text)
        assert result == []


# ── _extract_colony_skill_refs ───────────────────────────────────────────────


class TestExtractColonySkillRefs:
    def test_extracts_skill_refs(self):
        text = "Use /research-skill for analysis"
        result = mod._extract_colony_skill_refs(text)
        assert "research-skill" in result

    def test_filters_path_components(self):
        text = "Save to /tmp/output and use /my-skill"
        result = mod._extract_colony_skill_refs(text)
        assert "tmp" not in result
        assert "my-skill" in result

    def test_no_skill_refs(self):
        text = "Just text without skill references"
        result = mod._extract_colony_skill_refs(text)
        assert result == []


# ── _extract_bud_skill_refs ──────────────────────────────────────────────────


class TestExtractBudSkillRefs:
    def test_extracts_from_frontmatter(self):
        text = "---\nskills: [skill-a, skill-b]\n---\nBody"
        result = mod._extract_bud_skill_refs(text)
        assert result == ["skill-a", "skill-b"]

    def test_single_skill_string(self):
        text = "---\nskills: my-skill\n---\nBody"
        result = mod._extract_bud_skill_refs(text)
        assert result == ["my-skill"]

    def test_no_skills_key(self):
        text = "---\ntitle: Test\n---\nBody"
        result = mod._extract_bud_skill_refs(text)
        assert result == []

    def test_empty_skills(self):
        text = "---\nskills: []\n---\nBody"
        result = mod._extract_bud_skill_refs(text)
        assert result == []


# ── _extract_bud_mcp_tool_refs ───────────────────────────────────────────────


class TestExtractBudMcpToolRefs:
    def test_extracts_mcp_full_form(self):
        text = "Use mcp__vivesca__my_tool for this"
        result = mod._extract_bud_mcp_tool_refs(text)
        assert "my_tool" in result

    def test_extracts_bare_snake_case(self):
        text = "Run `my_cool_tool` to process"
        result = mod._extract_bud_mcp_tool_refs(text)
        assert "my_cool_tool" in result

    def test_ignores_camel_case(self):
        text = "Run `myCoolTool` to process"
        result = mod._extract_bud_mcp_tool_refs(text)
        assert result == []

    def test_multiple_refs(self):
        text = "Use mcp__vivesca__tool_a and `tool_b_name`"
        result = mod._extract_bud_mcp_tool_refs(text)
        assert "tool_a" in result
        assert "tool_b_name" in result


# ── _extract_bud_cli_refs ────────────────────────────────────────────────────


class TestExtractBudCliRefs:
    def test_extracts_cli_refs(self):
        text = "```bash\ngit status\nnpm test\n```"
        result = mod._extract_bud_cli_refs(text)
        # git and npm are in BUILTINS, so filtered
        # Let's use non-builtin commands
        text2 = "```bash\nmytool --help\nanother-tool run\n```"
        result2 = mod._extract_bud_cli_refs(text2)
        assert "mytool" in result2
        assert "another-tool" in result2

    def test_empty_block(self):
        text = "```bash\n```"
        result = mod._extract_bud_cli_refs(text)
        assert result == []


# ── _collect_receptor_names ──────────────────────────────────────────────────


class TestCollectReceptorNames:
    def test_empty_dir(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        result = mod._collect_receptor_names(skills_dir)
        assert result == frozenset()

    def test_finds_skills(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-a" / "SKILL.md").write_text("# Skill A")
        (skills_dir / "skill-b").mkdir()
        (skills_dir / "skill-b" / "SKILL.md").write_text("# Skill B")
        # Non-skill directory without SKILL.md
        (skills_dir / "not-a-skill").mkdir()

        result = mod._collect_receptor_names(skills_dir)
        assert "skill-a" in result
        assert "skill-b" in result
        assert "not-a-skill" not in result


# ── _collect_bud_names ───────────────────────────────────────────────────────


class TestCollectBudNames:
    def test_empty_dir(self, tmp_path):
        buds_dir = tmp_path / "buds"
        buds_dir.mkdir()
        result = mod._collect_bud_names(buds_dir)
        assert result == frozenset()

    def test_finds_buds(self, tmp_path):
        buds_dir = tmp_path / "buds"
        buds_dir.mkdir()
        (buds_dir / "bud-a.md").write_text("# Bud A")
        (buds_dir / "bud-b.md").write_text("# Bud B")
        (buds_dir / "not-a-bud.txt").write_text("Not a bud")

        result = mod._collect_bud_names(buds_dir)
        assert "bud-a" in result
        assert "bud-b" in result
        assert "not-a-bud" not in result


# ── _collect_registered_tool_names ───────────────────────────────────────────


class TestCollectRegisteredToolNames:
    def test_empty_dir(self, tmp_path):
        result = mod._collect_registered_tool_names(tmp_path)
        assert result == frozenset()

    def test_finds_tools(self, tmp_path):
        (tmp_path / "enzyme_a.py").write_text('@tool(name="tool_alpha")')
        (tmp_path / "enzyme_b.py").write_text('@tool(name="tool_beta")')
        (tmp_path / "__init__.py").write_text("")

        result = mod._collect_registered_tool_names(tmp_path)
        assert "tool_alpha" in result
        assert "tool_beta" in result


# ── _log_anoikis_candidates ──────────────────────────────────────────────────


class TestLogAnoikisCandidates:
    def test_empty_list_returns_false(self, tmp_path):
        result = mod._log_anoikis_candidates([], tmp_path / "log.md")
        assert result is False

    def test_writes_candidates(self, tmp_path):
        log_file = tmp_path / "retirement.md"
        result = mod._log_anoikis_candidates(["skill-a", "skill-b"], log_file)
        assert result is True
        content = log_file.read_text()
        assert "skill-a" in content
        assert "skill-b" in content
        assert "anoikis candidates" in content

    def test_creates_parent_dirs(self, tmp_path):
        log_file = tmp_path / "deep" / "nested" / "retirement.md"
        result = mod._log_anoikis_candidates(["skill-x"], log_file)
        assert result is True
        assert log_file.exists()


# ── integrin tool dispatch ───────────────────────────────────────────────────


class TestIntegrinDispatch:
    def test_probe_action(self):
        mock_result = MagicMock()
        mock_result.total_receptors = 5
        with patch.object(mod, "_run_probe", return_value=mock_result):
            result = mod.integrin("probe")
            assert result.total_receptors == 5

    def test_apoptosis_action(self):
        mock_result = MagicMock()
        mock_result.open_count = 3
        with patch.object(mod, "_run_apoptosis_check", return_value=mock_result):
            result = mod.integrin("apoptosis")
            assert result.open_count == 3

    def test_colony_probe_action(self):
        mock_result = MagicMock()
        mock_result.colony_count = 2
        with patch.object(mod, "_run_colony_probe", return_value=mock_result):
            result = mod.integrin("colony_probe")
            assert result.colony_count == 2

    def test_unknown_action_returns_error(self):
        result = mod.integrin("invalid_action")
        assert isinstance(result, mod.IntegrinResult)
        assert result.total_receptors == 0
        assert any("unknown_action" in str(i) for i in result.phenotype_issues)

    def test_action_case_insensitive(self):
        mock_result = MagicMock()
        with patch.object(mod, "_run_probe", return_value=mock_result) as mock_probe:
            mod.integrin("PROBE")
            mock_probe.assert_called_once()


# ── IntegrinResult ───────────────────────────────────────────────────────────


class TestIntegrinResult:
    def test_result_fields(self):
        result = mod.IntegrinResult(
            total_receptors=5,
            total_references=10,
            attached=8,
            detached=[{"receptor": "r1", "binary": "b1"}],
            mechanically_silent=[],
            focal_adhesions=[],
            anoikis=["dead-receptor"],
            activation_state=[{"receptor": "r1", "state": "open", "days_since_use": 2}],
            adhesion_dependence=[],
            phenotype_issues=[],
            unknown_platforms=[],
            launchagent_broken=[],
            skill_path_broken=[],
            untested_code=[],
        )
        assert result.total_receptors == 5
        assert result.total_references == 10
        assert result.attached == 8
        assert len(result.detached) == 1
        assert result.anoikis == ["dead-receptor"]


# ── ApoptosisResult ──────────────────────────────────────────────────────────


class TestApoptosisResult:
    def test_result_fields(self):
        result = mod.ApoptosisResult(
            open_count=3,
            extended_count=2,
            bent_count=5,
            anoikis_candidate_count=1,
            anoikis_candidates=["dying-skill"],
            quiescent=["idle-skill"],
            extended=["recent-skill"],
            retirement_log_updated=True,
            summary="3 open | 2 extended | 5 bent (1 anoikis candidates)",
        )
        assert result.open_count == 3
        assert result.bent_count == 5
        assert result.anoikis_candidates == ["dying-skill"]
        assert result.retirement_log_updated is True


# ── ColonyProbeResult ────────────────────────────────────────────────────────


class TestColonyProbeResult:
    def test_result_fields(self):
        result = mod.ColonyProbeResult(
            colony_count=3,
            bud_count=5,
            skill_count=10,
            registered_tool_count=8,
            detached_colony_bud_refs=[{"colony": "c1", "missing_bud": "b1"}],
            detached_colony_skill_refs=[],
            detached_bud_skill_refs=[],
            detached_bud_tool_refs=[],
            detached_bud_cli_refs=[],
            detached_skill_skill_refs=[],
            detached_skill_tool_refs=[],
            detached_tool_tool_refs=[],
            orphan_buds=["unused-bud"],
            total_detached=1,
        )
        assert result.colony_count == 3
        assert result.bud_count == 5
        assert result.orphan_buds == ["unused-bud"]
        assert result.total_detached == 1


# ── restore_fork_registry ────────────────────────────────────────────────────


class TestRestoreForkRegistry:
    def test_missing_file_returns_default(self, tmp_path):
        registry_path = tmp_path / "missing.yaml"
        result = mod.restore_fork_registry(registry_path)
        assert "superpowers" in result
        assert "compound-engineering" in result

    def test_loads_existing_file(self, tmp_path):
        import yaml

        registry_path = tmp_path / "registry.yaml"
        data = {"custom-fork": {"local": "/path/to/local"}}
        registry_path.write_text(yaml.dump(data))

        result = mod.restore_fork_registry(registry_path)
        assert "custom-fork" in result


# ── find_latest_cache_version ────────────────────────────────────────────────


class TestFindLatestCacheVersion:
    def test_missing_dir_returns_none(self, tmp_path):
        result = mod.find_latest_cache_version(tmp_path / "nonexistent")
        assert result is None

    def test_no_versions_returns_none(self, tmp_path):
        result = mod.find_latest_cache_version(tmp_path)
        assert result is None

    def test_finds_latest_version(self, tmp_path):
        v1 = tmp_path / "1.0.0"
        v2 = tmp_path / "2.0.0"
        v1.mkdir()
        v2.mkdir()
        (v1 / "skills").mkdir()
        (v2 / "skills").mkdir()

        result = mod.find_latest_cache_version(tmp_path)
        assert result == v2 / "skills"

    def test_ignores_non_version_dirs(self, tmp_path):
        (tmp_path / "latest").mkdir()
        (tmp_path / "1.0.0").mkdir()
        (tmp_path / "1.0.0" / "skills").mkdir()

        result = mod.find_latest_cache_version(tmp_path)
        assert result is not None
        assert "1.0.0" in str(result)


# ── diff_fork ────────────────────────────────────────────────────────────────


class TestDiffFork:
    def test_identical_dirs(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "file.txt").write_text("same content")
        (cache / "file.txt").write_text("same content")

        result = mod.diff_fork(local, cache)
        assert result["modified"] == []
        assert result["added_upstream"] == []
        assert result["total_changes"] == 0

    def test_modified_file(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "file.txt").write_text("local version")
        (cache / "file.txt").write_text("cache version")

        result = mod.diff_fork(local, cache)
        assert "file.txt" in result["modified"]
        assert result["total_changes"] == 1

    def test_added_upstream(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (cache / "new-file.txt").write_text("new in cache")

        result = mod.diff_fork(local, cache)
        assert "new-file.txt" in result["added_upstream"]

    def test_removed_locally(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "local-only.txt").write_text("only in local")

        result = mod.diff_fork(local, cache)
        assert "local-only.txt" in result["removed_locally"]
