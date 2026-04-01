"""Tests for metabolon.enzymes.integrin — attachment integrity probe.

Covers: pure extraction functions, I/O-bound probe/apoptosis/colony paths,
dispatch via integrin() tool, fork-diff utilities.
"""

from __future__ import annotations

import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.integrin import (
    ApoptosisResult,
    ColonyProbeResult,
    IntegrinResult,
    _extract_bash_commands,
    _extract_bud_cli_refs,
    _extract_bud_mcp_tool_refs,
    _extract_bud_skill_refs,
    _extract_colony_bud_refs,
    _extract_colony_skill_refs,
    _extract_skill_mcp_tool_refs,
    _extract_skill_skill_refs,
    _extract_tool_cross_imports,
    _is_real_command,
    _log_anoikis_candidates,
    _parse_frontmatter,
    _probe_responsiveness,
    _read_skill_usage,
    _run_apoptosis_check,
    _run_colony_probe,
    _run_probe,
    _strip_frontmatter,
    _collect_receptor_names,
    _collect_bud_names,
    _collect_registered_tool_names,
    diff_fork,
    find_latest_cache_version,
    integrin,
    restore_fork_registry,
)


# ── Pure: _extract_bash_commands ─────────────────────────────────────

class TestExtractBashCommands:
    def test_simple_bash_block(self):
        md = textwrap.dedent("""\
            ```bash
            curl -s http://example.com
            wget http://example.com
            ```
        """)
        assert _extract_bash_commands(md) == ["curl", "wget"]

    def test_shell_and_sh_blocks(self):
        md = "```shell\necho hi\n```\n```sh\nls -la\n```"
        assert _extract_bash_commands(md) == ["echo", "ls"]

    def test_skips_comments(self):
        md = "```bash\n# this is a comment\ngit status\n```"
        assert _extract_bash_commands(md) == ["git"]

    def test_skips_non_bash_blocks(self):
        md = "```python\nprint('hi')\n```"
        assert _extract_bash_commands(md) == []

    def test_variable_assignment_skips_varname(self):
        md = "```bash\nRESULT=$(jq '.field' file.json)\necho $RESULT\n```"
        cmds = _extract_bash_commands(md)
        # $() is not a command; after it, echo should appear
        assert "echo" in cmds

    def test_empty_string(self):
        assert _extract_bash_commands("") == []

    def test_unclosed_block(self):
        md = "```bash\ngit status"
        # No closing fence -> still in block, should extract
        assert "git" in _extract_bash_commands(md)

    def test_multiple_blocks(self):
        md = "```bash\nfoo\n```\n```bash\nbar\n```"
        assert _extract_bash_commands(md) == ["foo", "bar"]


# ── Pure: _is_real_command ───────────────────────────────────────────

class TestIsRealCommand:
    def test_builtin_excluded(self):
        for b in ("echo", "cd", "ls", "grep", "cat", "git"):
            assert not _is_real_command(b), f"{b} should be excluded"

    def test_real_command(self):
        assert _is_real_command("rg")
        assert _is_real_command("docker")
        assert _is_real_command("my-tool")

    def test_too_short(self):
        assert not _is_real_command("ab")  # len 2, excluded
        assert _is_real_command("abc")     # len 3, passes

    def test_uppercase_excluded(self):
        assert not _is_real_command("Docker")

    def test_flag_excluded(self):
        assert not _is_real_command("--help")
        assert not _is_real_command("-v")


# ── Pure: _parse_frontmatter ────────────────────────────────────────

class TestParseFrontmatter:
    def test_scalar(self):
        text = "---\nname: my-bud\n---\nbody"
        assert _parse_frontmatter(text) == {"name": "my-bud"}

    def test_list(self):
        text = "---\nskills: [alpha, beta, gamma]\n---\nbody"
        fm = _parse_frontmatter(text)
        assert fm["skills"] == ["alpha", "beta", "gamma"]

    def test_quoted_scalar(self):
        text = '---\nname: "my bud"\n---\nbody'
        fm = _parse_frontmatter(text)
        assert fm["name"] == "my bud"

    def test_single_quoted_scalar(self):
        text = "---\nname: 'my bud'\n---\nbody"
        fm = _parse_frontmatter(text)
        assert fm["name"] == "my bud"

    def test_no_frontmatter(self):
        assert _parse_frontmatter("no frontmatter here") == {}

    def test_empty_frontmatter(self):
        assert _parse_frontmatter("---\n---\nbody") == {}

    def test_multiple_keys(self):
        text = "---\nname: x\nrole: researcher\nskills: [a, b]\n---\n"
        fm = _parse_frontmatter(text)
        assert fm == {"name": "x", "role": "researcher", "skills": ["a", "b"]}


# ── Pure: _strip_frontmatter ────────────────────────────────────────

class TestStripFrontmatter:
    def test_strips_frontmatter(self):
        text = "---\nname: x\n---\nbody content"
        assert _strip_frontmatter(text) == "body content"

    def test_no_frontmatter_passthrough(self):
        text = "just body"
        assert _strip_frontmatter(text) == "just body"


# ── Pure: colony/bud/skill extraction helpers ────────────────────────

class TestExtractColonyBudRefs:
    def test_invokes(self):
        text = "---\n---\n- **audit**: invoke financial-audit bud"
        assert _extract_colony_bud_refs(text) == ["financial-audit"]

    def test_multiple(self):
        text = "---\n---\ninvoke alpha bud\ninvoke beta bud"
        assert _extract_colony_bud_refs(text) == ["alpha", "beta"]

    def test_no_refs(self):
        assert _extract_colony_bud_refs("---\n---\njust text") == []


class TestExtractColonySkillRefs:
    def test_skill_ref(self):
        text = "---\n---\nuse /my-skill for analysis"
        assert _extract_colony_skill_refs(text) == ["my-skill"]

    def test_filters_path_components(self):
        text = "---\n---\npath /tmp /docs /notes /home"
        assert _extract_colony_skill_refs(text) == []

    def test_multiple(self):
        text = "---\n---\n/alpha and /beta-skill"
        assert _extract_colony_skill_refs(text) == ["alpha", "beta-skill"]


class TestExtractBudSkillRefs:
    def test_from_frontmatter(self):
        text = "---\nskills: [alpha, beta]\n---\nbody"
        assert _extract_bud_skill_refs(text) == ["alpha", "beta"]

    def test_single_skill(self):
        text = "---\nskills: alpha\n---\nbody"
        assert _extract_bud_skill_refs(text) == ["alpha"]

    def test_no_skills(self):
        text = "---\nname: x\n---\nbody"
        assert _extract_bud_skill_refs(text) == []


class TestExtractBudMcpToolRefs:
    def test_full_mcp_ref(self):
        text = "---\n---\nuse mcp__vivesca__my_tool for X"
        assert _extract_bud_mcp_tool_refs(text) == ["my_tool"]

    def test_bare_snake_case(self):
        text = "---\n---\ncall `some_tool_name` in body"
        assert _extract_bud_mcp_tool_refs(text) == ["some_tool_name"]

    def test_no_refs(self):
        assert _extract_bud_mcp_tool_refs("---\n---\nplain text") == []


class TestExtractBudCliRefs:
    def test_extracts_from_bash_block(self):
        text = "---\n---\n```bash\ndocker ps\n```"
        refs = _extract_bud_cli_refs(text)
        assert "docker" in refs

    def test_excludes_builtins(self):
        text = "---\n---\n```bash\nls -la\ngit status\n```"
        refs = _extract_bud_cli_refs(text)
        assert "ls" not in refs
        assert "git" not in refs


class TestExtractSkillSkillRefs:
    def test_cross_ref(self):
        text = "---\n---\nuse /other-skill for help"
        assert _extract_skill_skill_refs(text) == ["other-skill"]

    def test_filters_paths(self):
        text = "---\n---\n/tmp /docs /notes"
        assert _extract_skill_skill_refs(text) == []


class TestExtractSkillMcpToolRefs:
    def test_full_mcp(self):
        text = "---\n---\ninvoke mcp__vivesca__probe_tool"
        assert _extract_skill_mcp_tool_refs(text) == ["probe_tool"]


# ── Pure: _extract_tool_cross_imports ────────────────────────────────

class TestExtractToolCrossImports:
    def test_finds_cross_imports(self, tmp_path):
        # tool_a.py imports from tool_b
        tool_a = tmp_path / "tool_a.py"
        tool_a.write_text("from metabolon.enzymes.tool_b import run_b\n")
        tool_b = tmp_path / "tool_b.py"
        tool_b.write_text("pass\n")

        edges = _extract_tool_cross_imports(tmp_path)
        assert len(edges) == 1
        assert edges[0]["source_tool"] == "tool_a"
        assert edges[0]["target_tool"] == "tool_b"
        assert edges[0]["symbol"] == "run_b"

    def test_skips_self_import(self, tmp_path):
        tool_a = tmp_path / "tool_a.py"
        tool_a.write_text("from metabolon.enzymes.tool_a import helper\n")
        assert _extract_tool_cross_imports(tmp_path) == []

    def test_skips_init(self, tmp_path):
        init = tmp_path / "__init__.py"
        init.write_text("from metabolon.enzymes.tool_b import x\n")
        # __init__ is skipped
        assert _extract_tool_cross_imports(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path):
        assert _extract_tool_cross_imports(tmp_path / "nope") == []


# ── I/O: _probe_responsiveness ───────────────────────────────────────

class TestProbeResponsiveness:
    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/docker")
    @patch("metabolon.enzymes.integrin.subprocess.run")
    def test_responsive(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(stdout="Usage: docker", stderr="", returncode=0)
        assert _probe_responsiveness("docker") is True

    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/docker")
    @patch("metabolon.enzymes.integrin.subprocess.run")
    def test_stderr_only_counts(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(stdout="", stderr="Usage", returncode=1)
        assert _probe_responsiveness("docker") is True

    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/broken")
    @patch("metabolon.enzymes.integrin.subprocess.run")
    def test_silent_binary(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        assert _probe_responsiveness("broken") is False

    @patch("metabolon.enzymes.integrin.shutil.which", return_value=None)
    def test_not_on_path(self, mock_which):
        assert _probe_responsiveness("nonexistent") is False

    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/slow")
    @patch("metabolon.enzymes.integrin.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="slow", timeout=5))
    def test_timeout(self, mock_run, mock_which):
        assert _probe_responsiveness("slow") is False

    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/x")
    @patch("metabolon.enzymes.integrin.subprocess.run", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_run, mock_which):
        assert _probe_responsiveness("x") is False


# ── I/O: _read_skill_usage ──────────────────────────────────────────

class TestReadSkillUsage:
    @patch("metabolon.enzymes.integrin.SKILL_USAGE_LOG")
    def test_parses_tsv(self, mock_log):
        mock_log.exists.return_value = True
        mock_log.read_text.return_value = (
            "2025-12-01T10:00:00\talpha\n"
            "2025-12-15T10:00:00\talpha\n"
            "2025-12-10T10:00:00\tbeta\n"
        )
        result = _read_skill_usage()
        assert result["alpha"] == datetime(2025, 12, 15, 10, 0, 0)
        assert result["beta"] == datetime(2025, 12, 10, 10, 0, 0)

    @patch("metabolon.enzymes.integrin.SKILL_USAGE_LOG")
    def test_missing_log(self, mock_log):
        mock_log.exists.return_value = False
        assert _read_skill_usage() == {}

    @patch("metabolon.enzymes.integrin.SKILL_USAGE_LOG")
    def test_malformed_line_skipped(self, mock_log):
        mock_log.exists.return_value = True
        mock_log.read_text.return_value = "bad-line\n2025-12-01T10:00:00\tgood\n"
        result = _read_skill_usage()
        assert "good" in result
        assert len(result) == 1

    @patch("metabolon.enzymes.integrin.SKILL_USAGE_LOG")
    def test_oserror_returns_empty(self, mock_log):
        mock_log.exists.return_value = True
        mock_log.read_text.side_effect = OSError("nope")
        assert _read_skill_usage() == {}


# ── I/O: _log_anoikis_candidates ────────────────────────────────────

class TestLogAnoikisCandidates:
    def test_writes_candidates(self, tmp_path):
        log = tmp_path / "retirement.md"
        result = _log_anoikis_candidates(["alpha", "beta"], retirement_log=log)
        assert result is True
        content = log.read_text()
        assert "alpha" in content
        assert "beta" in content
        assert "anoikis candidates" in content

    def test_empty_candidates_returns_false(self, tmp_path):
        log = tmp_path / "retirement.md"
        assert _log_anoikis_candidates([], retirement_log=log) is False

    def test_oserror_returns_false(self, tmp_path):
        log = tmp_path / "nonexistent" / "deep" / "retirement.md"
        # parent mkdir will succeed, but we'll make the open fail
        with patch("builtins.open", side_effect=OSError("nope")):
            assert _log_anoikis_candidates(["x"], retirement_log=log) is False


# ── I/O: _collect_receptor_names ────────────────────────────────────

class TestCollectReceptorNames:
    def test_collects_skill_dirs(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "SKILL.md").write_text("x")
        (tmp_path / "beta").mkdir()
        (tmp_path / "beta" / "SKILL.md").write_text("y")
        (tmp_path / "empty").mkdir()  # no SKILL.md
        result = _collect_receptor_names(tmp_path)
        assert result == frozenset({"alpha", "beta"})

    def test_nonexistent_dir(self, tmp_path):
        assert _collect_receptor_names(tmp_path / "nope") == frozenset()


class TestCollectBudNames:
    def test_collects_md_stems(self, tmp_path):
        (tmp_path / "audit.md").write_text("x")
        (tmp_path / "research.md").write_text("y")
        (tmp_path / "ignore.txt").write_text("z")
        assert _collect_bud_names(tmp_path) == frozenset({"audit", "research"})

    def test_nonexistent_dir(self, tmp_path):
        assert _collect_bud_names(tmp_path / "nope") == frozenset()


class TestCollectRegisteredToolNames:
    def test_finds_tool_decorator(self, tmp_path):
        py = tmp_path / "mytool.py"
        py.write_text('@tool(name="my_probe", description="x")\ndef my_probe(): pass')
        assert _collect_registered_tool_names(tmp_path) == frozenset({"my_probe"})

    def test_nonexistent_dir(self, tmp_path):
        assert _collect_registered_tool_names(tmp_path / "nope") == frozenset()


# ── I/O: _run_probe ─────────────────────────────────────────────────

class TestRunProbe:
    @patch("metabolon.enzymes.integrin._check_skill_paths", return_value=[])
    @patch("metabolon.enzymes.integrin._check_untested_code", return_value=[])
    @patch("metabolon.enzymes.integrin._check_launchagent_paths", return_value=[])
    @patch("metabolon.enzymes.integrin._check_phenotype_symlinks", return_value=([], []))
    @patch("metabolon.enzymes.integrin.SKILLS_DIR")
    def test_no_skills_dir(self, mock_skills, mock_pheno, mock_launch, mock_untested, mock_skill_paths):
        mock_skills.is_dir.return_value = False
        result = _run_probe()
        assert isinstance(result, IntegrinResult)
        assert result.total_receptors == 0
        assert result.total_references == 0

    @patch("metabolon.enzymes.integrin._probe_responsiveness", return_value=True)
    @patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/bin/docker")
    @patch("metabolon.enzymes.integrin._read_skill_usage", return_value={})
    @patch("metabolon.enzymes.integrin._check_skill_paths", return_value=[])
    @patch("metabolon.enzymes.integrin._check_untested_code", return_value=[])
    @patch("metabolon.enzymes.integrin._check_launchagent_paths", return_value=[])
    @patch("metabolon.enzymes.integrin._check_phenotype_symlinks", return_value=([], []))
    @patch("metabolon.enzymes.integrin.SKILLS_DIR")
    def test_with_skills(self, mock_skills, mock_pheno, mock_launch, mock_untested,
                         mock_skill_paths, mock_usage, mock_which, mock_probe):
        # Create a mock skill dir structure
        skill_dir = MagicMock()
        skill_dir.name = "my-skill"
        skill_dir.is_dir.return_value = True

        skill_file = MagicMock()
        skill_file.is_file.return_value = True
        skill_file.read_text.return_value = "```bash\ndocker ps\n```\n"

        skill_dir.__truediv__ = lambda self, key: skill_file if key == "SKILL.md" else Path(str(self) + "/" + key)
        # Also need to support iterdir on skill_dir for activation state scan
        mock_skills.iterdir.return_value = [skill_dir]
        mock_skills.is_dir.return_value = True

        # Also need the activation state loop to find skill dirs
        # That loop does: for receptor_dir in sorted(SKILLS_DIR.iterdir())
        # and checks receptor_dir / "SKILL.md"

        result = _run_probe()
        assert isinstance(result, IntegrinResult)
        assert result.total_receptors == 1
        assert result.total_references == 1
        assert result.attached == 1
        assert result.detached == []
        assert len(result.focal_adhesions) == 0  # valency=1, threshold >= 2


# ── I/O: _run_apoptosis_check ────────────────────────────────────────

class TestRunApoptosisCheck:
    @patch("metabolon.enzymes.integrin._log_anoikis_candidates", return_value=True)
    @patch("metabolon.enzymes.integrin._run_probe")
    def test_classifies_receptors(self, mock_probe, mock_log):
        mock_probe.return_value = IntegrinResult(
            total_receptors=3,
            total_references=3,
            attached=3,
            detached=[],
            mechanically_silent=[],
            focal_adhesions=[],
            anoikis=["dead-skill"],
            activation_state=[
                {"receptor": "active-skill", "state": "open", "days_since_use": 1},
                {"receptor": "aging-skill", "state": "extended", "days_since_use": 15},
                {"receptor": "dead-skill", "state": "bent", "days_since_use": 60},
                {"receptor": "idle-skill", "state": "bent", "days_since_use": 60},
            ],
            adhesion_dependence=[],
            phenotype_issues=[],
            unknown_platforms=[],
            launchagent_broken=[],
            skill_path_broken=[],
            untested_code=[],
        )
        result = _run_apoptosis_check()
        assert isinstance(result, ApoptosisResult)
        assert result.open_count == 1
        assert result.extended_count == 1
        assert result.bent_count == 2
        assert result.anoikis_candidate_count == 1
        assert result.anoikis_candidates == ["dead-skill"]
        assert result.quiescent == ["idle-skill"]
        assert result.extended == ["aging-skill"]
        assert result.retirement_log_updated is True

    @patch("metabolon.enzymes.integrin._log_anoikis_candidates", return_value=False)
    @patch("metabolon.enzymes.integrin._run_probe")
    def test_no_anoikis(self, mock_probe, mock_log):
        mock_probe.return_value = IntegrinResult(
            total_receptors=1,
            total_references=1,
            attached=1,
            detached=[],
            mechanically_silent=[],
            focal_adhesions=[],
            anoikis=[],
            activation_state=[
                {"receptor": "happy", "state": "open", "days_since_use": 0},
            ],
            adhesion_dependence=[],
            phenotype_issues=[],
            unknown_platforms=[],
            launchagent_broken=[],
            skill_path_broken=[],
            untested_code=[],
        )
        result = _run_apoptosis_check()
        assert result.anoikis_candidate_count == 0
        assert result.retirement_log_updated is False


# ── I/O: _run_colony_probe ──────────────────────────────────────────

class TestRunColonyProbe:
    def test_empty_dirs(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        for d in (colonies, buds, skills, tools):
            d.mkdir()

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert isinstance(result, ColonyProbeResult)
        assert result.colony_count == 0
        assert result.bud_count == 0
        assert result.skill_count == 0
        assert result.total_detached == 0

    def test_colony_with_missing_bud(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        colonies.mkdir()
        buds.mkdir()
        skills.mkdir()
        tools.mkdir()

        # Colony references a bud that doesn't exist
        (colonies / "audit-colony.md").write_text(
            "---\nname: audit\n---\ninvoke missing-bud bud\n"
        )

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert result.colony_count == 1
        assert len(result.detached_colony_bud_refs) == 1
        assert result.detached_colony_bud_refs[0]["missing_bud"] == "missing-bud"

    def test_bud_with_missing_skill(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        colonies.mkdir()
        buds.mkdir()
        skills.mkdir()
        tools.mkdir()

        (buds / "auditor.md").write_text(
            "---\nskills: [missing-skill]\n---\nbody\n"
        )

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert len(result.detached_bud_skill_refs) == 1
        assert result.detached_bud_skill_refs[0]["missing_skill"] == "missing-skill"

    def test_bud_with_missing_tool(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        colonies.mkdir()
        buds.mkdir()
        skills.mkdir()
        tools.mkdir()

        # Register a tool so we can detect a missing one
        (tools / "real_tool.py").write_text('@tool(name="real_tool")\ndef t(): pass')
        (buds / "worker.md").write_text(
            "---\n---\nuse mcp__vivesca__real_tool and mcp__vivesca__fake_tool\n"
        )

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert len(result.detached_bud_tool_refs) == 1
        assert result.detached_bud_tool_refs[0]["missing_tool"] == "fake_tool"

    def test_skill_with_missing_skill_crossref(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        colonies.mkdir()
        buds.mkdir()
        tools.mkdir()

        # Skill "alpha" exists
        alpha_dir = skills / "alpha"
        alpha_dir.mkdir()
        (alpha_dir / "SKILL.md").write_text("---\n---\nuse /missing-skill\n")

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert len(result.detached_skill_skill_refs) == 1
        assert result.detached_skill_skill_refs[0]["missing_skill"] == "missing-skill"

    def test_orphan_bud_detected(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        colonies.mkdir()
        buds.mkdir()
        skills.mkdir()
        tools.mkdir()

        (buds / "lonely.md").write_text("---\n---\nI have no colony")

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert "lonely" in result.orphan_buds

    def test_tool_cross_import_broken(self, tmp_path):
        colonies = tmp_path / "colonies"
        buds = tmp_path / "buds"
        skills = tmp_path / "skills"
        tools = tmp_path / "tools"
        for d in (colonies, buds, skills, tools):
            d.mkdir()

        # tool_a imports from nonexistent tool_b
        (tools / "tool_a.py").write_text("from metabolon.enzymes.tool_b import run_b\n")

        result = _run_colony_probe(
            colonies_dir=colonies,
            buds_dir=buds,
            skills_dir=skills,
            tools_dir=tools,
        )
        assert len(result.detached_tool_tool_refs) == 1
        assert result.detached_tool_tool_refs[0]["target_tool"] == "tool_b"


# ── Fork utilities ──────────────────────────────────────────────────

class TestRestoreForkRegistry:
    def test_loads_yaml(self, tmp_path):
        reg = tmp_path / "forks.yaml"
        reg.write_text("superpowers:\n  local: /path/to/local\n")
        result = restore_fork_registry(path=reg)
        assert "superpowers" in result

    def test_missing_returns_default(self, tmp_path):
        result = restore_fork_registry(path=tmp_path / "nope.yaml")
        assert "superpowers" in result  # default registry


class TestFindLatestCacheVersion:
    def test_finds_latest(self, tmp_path):
        v1 = tmp_path / "1.0.0"
        v2 = tmp_path / "2.1.0"
        v3 = tmp_path / "1.5.3"
        for v in (v1, v2, v3):
            (v / "skills").mkdir(parents=True)
        result = find_latest_cache_version(tmp_path)
        assert result == v2 / "skills"

    def test_no_versions(self, tmp_path):
        (tmp_path / "not-a-version").mkdir()
        assert find_latest_cache_version(tmp_path) is None

    def test_nonexistent_dir(self, tmp_path):
        assert find_latest_cache_version(tmp_path / "nope") is None

    def test_version_without_skills_dir(self, tmp_path):
        (tmp_path / "1.0.0").mkdir()  # no skills/ subdir
        assert find_latest_cache_version(tmp_path) is None


class TestDiffFork:
    def test_identical(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "file.txt").write_text("same")
        (cache / "file.txt").write_text("same")
        result = diff_fork(local, cache)
        assert result["modified"] == []
        assert result["added_upstream"] == []
        assert result["removed_locally"] == []
        assert result["total_changes"] == 0

    def test_modified(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "file.txt").write_text("v1")
        (cache / "file.txt").write_text("v2")
        result = diff_fork(local, cache)
        assert "file.txt" in result["modified"]

    def test_added_upstream(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (cache / "new.txt").write_text("new")
        result = diff_fork(local, cache)
        assert "new.txt" in result["added_upstream"]

    def test_removed_locally(self, tmp_path):
        local = tmp_path / "local"
        cache = tmp_path / "cache"
        local.mkdir()
        cache.mkdir()
        (local / "removed.txt").write_text("gone")
        result = diff_fork(local, cache)
        assert "removed.txt" in result["removed_locally"]


# ── integrin() dispatch ─────────────────────────────────────────────

class TestIntegrinDispatch:
    @patch("metabolon.enzymes.integrin._run_probe")
    def test_probe_action(self, mock_probe):
        mock_probe.return_value = IntegrinResult(
            total_receptors=0, total_references=0, attached=0,
            detached=[], mechanically_silent=[], focal_adhesions=[],
            anoikis=[], activation_state=[], adhesion_dependence=[],
            phenotype_issues=[], unknown_platforms=[], launchagent_broken=[],
            skill_path_broken=[], untested_code=[],
        )
        result = integrin(action="probe")
        assert isinstance(result, IntegrinResult)
        mock_probe.assert_called_once()

    @patch("metabolon.enzymes.integrin._run_apoptosis_check")
    def test_apoptosis_action(self, mock_apoptosis):
        mock_apoptosis.return_value = ApoptosisResult(
            open_count=0, extended_count=0, bent_count=0,
            anoikis_candidate_count=0, anoikis_candidates=[], quiescent=[],
            extended=[], retirement_log_updated=False, summary="",
        )
        result = integrin(action="apoptosis")
        assert isinstance(result, ApoptosisResult)
        mock_apoptosis.assert_called_once()

    @patch("metabolon.enzymes.integrin._run_colony_probe")
    def test_colony_probe_action(self, mock_colony):
        mock_colony.return_value = ColonyProbeResult(
            colony_count=0, bud_count=0, skill_count=0, registered_tool_count=0,
            detached_colony_bud_refs=[], detached_colony_skill_refs=[],
            detached_bud_skill_refs=[], detached_bud_tool_refs=[],
            detached_bud_cli_refs=[], detached_skill_skill_refs=[],
            detached_skill_tool_refs=[], detached_tool_tool_refs=[],
            orphan_buds=[], total_detached=0,
        )
        result = integrin(action="colony_probe")
        assert isinstance(result, ColonyProbeResult)
        mock_colony.assert_called_once()

    def test_unknown_action_returns_integrin_result(self):
        result = integrin(action="bogus")
        assert isinstance(result, IntegrinResult)
        assert result.phenotype_issues[0]["problem"] == "unknown_action:bogus"

    @patch("metabolon.enzymes.integrin._run_probe")
    def test_case_insensitive(self, mock_probe):
        mock_probe.return_value = IntegrinResult(
            total_receptors=0, total_references=0, attached=0,
            detached=[], mechanically_silent=[], focal_adhesions=[],
            anoikis=[], activation_state=[], adhesion_dependence=[],
            phenotype_issues=[], unknown_platforms=[], launchagent_broken=[],
            skill_path_broken=[], untested_code=[],
        )
        integrin(action="PROBE")
        mock_probe.assert_called_once()

    @patch("metabolon.enzymes.integrin._run_probe")
    def test_whitespace_stripped(self, mock_probe):
        mock_probe.return_value = IntegrinResult(
            total_receptors=0, total_references=0, attached=0,
            detached=[], mechanically_silent=[], focal_adhesions=[],
            anoikis=[], activation_state=[], adhesion_dependence=[],
            phenotype_issues=[], unknown_platforms=[], launchagent_broken=[],
            skill_path_broken=[], untested_code=[],
        )
        integrin(action="  probe  ")
        mock_probe.assert_called_once()
