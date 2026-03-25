"""Tests for integrin_colony_probe -- reference integrity across the dependency web."""

from __future__ import annotations

from pathlib import Path

import pytest

from metabolon.tools.integrin import (
    ColonyProbeResult,
    _collect_bud_names,
    _collect_receptor_names,
    _collect_registered_tool_names,
    _extract_bud_cli_refs,
    _extract_bud_mcp_tool_refs,
    _extract_bud_skill_refs,
    _extract_colony_bud_refs,
    _extract_colony_skill_refs,
    _extract_skill_mcp_tool_refs,
    _extract_skill_skill_refs,
    _extract_tool_cross_imports,
    _parse_frontmatter,
    integrin_colony_probe,
)


# -- Fixtures ----------------------------------------------------------------


def _make_colony(colonies_dir: Path, name: str, body: str) -> Path:
    f = colonies_dir / f"{name}.md"
    f.write_text(body)
    return f


def _make_bud(buds_dir: Path, name: str, content: str) -> Path:
    f = buds_dir / f"{name}.md"
    f.write_text(content)
    return f


def _make_skill(skills_dir: Path, name: str, content: str = "") -> Path:
    d = skills_dir / name
    d.mkdir(parents=True, exist_ok=True)
    f = d / "SKILL.md"
    f.write_text(content or f"---\nname: {name}\n---\n\nSome skill content.\n")
    return f


def _make_tool_module(tools_dir: Path, name: str, tool_names: list[str], imports: str = "") -> Path:
    tools_dir.mkdir(parents=True, exist_ok=True)
    tool_defs = "\n".join(
        f'@tool(name="{t}")\ndef {t}(): pass\n' for t in tool_names
    )
    content = f'from fastmcp.tools import tool\n{imports}\n{tool_defs}'
    f = tools_dir / f"{name}.py"
    f.write_text(content)
    return f


def _scaffold(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Return (colonies_dir, buds_dir, skills_dir, tools_dir)."""
    colonies = tmp_path / "colonies"
    buds = tmp_path / "agents"
    skills = tmp_path / "receptors"
    tools = tmp_path / "tools"
    for d in (colonies, buds, skills, tools):
        d.mkdir()
    return colonies, buds, skills, tools


# -- Unit: _parse_frontmatter ------------------------------------------------


class TestParseFrontmatter:
    def test_empty_text(self):
        assert _parse_frontmatter("no frontmatter here") == {}

    def test_simple_scalar(self):
        text = "---\nname: my-skill\n---\nBody.\n"
        fm = _parse_frontmatter(text)
        assert fm["name"] == "my-skill"

    def test_list_value(self):
        text = '---\nskills: ["histology", "cytometry"]\n---\nBody.\n'
        fm = _parse_frontmatter(text)
        assert fm["skills"] == ["histology", "cytometry"]

    def test_single_item_list(self):
        text = '---\nskills: ["homeostasis"]\n---\nBody.\n'
        fm = _parse_frontmatter(text)
        assert fm["skills"] == ["homeostasis"]

    def test_quoted_scalar(self):
        text = '---\nmodel: "opus"\n---\nBody.\n'
        fm = _parse_frontmatter(text)
        assert fm["model"] == "opus"


# -- Unit: _extract_colony_bud_refs ------------------------------------------


class TestExtractColonyBudRefs:
    def test_extracts_invoke_bud_pattern(self):
        text = "## Workers\n- **financial-audit**: invoke financial-audit bud — cashflow\n"
        refs = _extract_colony_bud_refs(text)
        assert "financial-audit" in refs

    def test_multiple_buds(self):
        text = (
            "- **health-audit**: invoke health-audit bud\n"
            "- **system-patrol**: invoke system-patrol bud\n"
        )
        refs = _extract_colony_bud_refs(text)
        assert "health-audit" in refs
        assert "system-patrol" in refs

    def test_no_bud_references(self):
        text = "## Workers\n- **researcher**: gather evidence\n"
        refs = _extract_colony_bud_refs(text)
        assert refs == []

    def test_ignores_frontmatter_name(self):
        text = "---\nname: monthly-review\n---\n- **financial-audit**: invoke financial-audit bud\n"
        refs = _extract_colony_bud_refs(text)
        assert refs == ["financial-audit"]
        assert "monthly-review" not in refs


# -- Unit: _extract_colony_skill_refs ----------------------------------------


class TestExtractColonySkillRefs:
    def test_extracts_slash_skill(self):
        text = "Trigger: /ecdysis monthly\n"
        refs = _extract_colony_skill_refs(text)
        assert "ecdysis" in refs

    def test_ignores_file_paths(self):
        text = "See /Users/terry/vivesca/receptors/ for details.\n"
        refs = _extract_colony_skill_refs(text)
        assert "Users" not in refs

    def test_no_skill_refs(self):
        text = "No slash refs here.\n"
        assert _extract_colony_skill_refs(text) == []


# -- Unit: _extract_bud_skill_refs -------------------------------------------


class TestExtractBudSkillRefs:
    def test_list_skills(self):
        text = '---\nname: biopsy\nskills: ["histology"]\n---\nBody.\n'
        assert _extract_bud_skill_refs(text) == ["histology"]

    def test_multiple_skills(self):
        text = '---\nskills: ["homeostasis", "cytometry"]\n---\nBody.\n'
        refs = _extract_bud_skill_refs(text)
        assert "homeostasis" in refs
        assert "cytometry" in refs

    def test_no_skills_key(self):
        text = "---\nname: gradient-sense\nmodel: sonnet\n---\nBody.\n"
        assert _extract_bud_skill_refs(text) == []

    def test_empty_skills_list(self):
        text = "---\nskills: []\n---\nBody.\n"
        assert _extract_bud_skill_refs(text) == []


# -- Unit: _extract_bud_mcp_tool_refs ----------------------------------------


class TestExtractBudMcpToolRefs:
    def test_mcp_full_pattern(self):
        text = "Use mcp__vivesca__histone_search to find notes.\n"
        refs = _extract_bud_mcp_tool_refs(text)
        assert "histone_search" in refs

    def test_multiple_mcp_tools(self):
        text = (
            "Call mcp__vivesca__histone_search and mcp__vivesca__chemotaxis_search.\n"
        )
        refs = _extract_bud_mcp_tool_refs(text)
        assert "histone_search" in refs
        assert "chemotaxis_search" in refs

    def test_bare_backtick_tool(self):
        text = "Run `integrin_probe` to check health.\n"
        refs = _extract_bud_mcp_tool_refs(text)
        assert "integrin_probe" in refs

    def test_ignores_non_snake_case(self):
        text = "Run `grep` or `ls` here.\n"
        refs = _extract_bud_mcp_tool_refs(text)
        assert "grep" not in refs
        assert "ls" not in refs


# -- Unit: _extract_bud_cli_refs ---------------------------------------------


class TestExtractBudCliRefs:
    def test_extracts_commands_from_bash_blocks(self):
        text = "Do this:\n```bash\npytest tests/\n```\n"
        refs = _extract_bud_cli_refs(text)
        assert "pytest" in refs

    def test_ignores_builtins(self):
        text = "```bash\necho hello\ncd /tmp\n```\n"
        refs = _extract_bud_cli_refs(text)
        assert "echo" not in refs
        assert "cd" not in refs


# -- Unit: _extract_skill_skill_refs -----------------------------------------


class TestExtractSkillSkillRefs:
    def test_slash_skill_ref(self):
        text = "---\nname: biopsy\n---\nFollow the /histology skill precisely.\n"
        refs = _extract_skill_skill_refs(text)
        assert "histology" in refs

    def test_ignores_frontmatter(self):
        text = "---\nname: test\n---\nUse /other-skill here.\n"
        refs = _extract_skill_skill_refs(text)
        assert "test" not in refs
        assert "other-skill" in refs


# -- Unit: _extract_skill_mcp_tool_refs --------------------------------------


class TestExtractSkillMcpToolRefs:
    def test_mcp_full(self):
        text = "---\nname: ecphory\n---\n- mcp__vivesca__histone_search\n"
        refs = _extract_skill_mcp_tool_refs(text)
        assert "histone_search" in refs

    def test_bare_backtick(self):
        text = "---\nname: auscultation\n---\nCall `homeostasis_system` to check.\n"
        refs = _extract_skill_mcp_tool_refs(text)
        assert "homeostasis_system" in refs


# -- Unit: _extract_tool_cross_imports ---------------------------------------


class TestExtractToolCrossImports:
    def test_detects_cross_tool_import(self, tmp_path):
        tools = tmp_path / "tools"
        tools.mkdir()
        # alpha.py imports from beta.py
        (tools / "alpha.py").write_text(
            "from metabolon.tools.beta import beta_func\n"
        )
        (tools / "beta.py").write_text("def beta_func(): pass\n")
        edges = _extract_tool_cross_imports(tools)
        assert len(edges) == 1
        assert edges[0]["source_tool"] == "alpha"
        assert edges[0]["target_tool"] == "beta"
        assert edges[0]["symbol"] == "beta_func"

    def test_ignores_self_import(self, tmp_path):
        tools = tmp_path / "tools"
        tools.mkdir()
        (tools / "alpha.py").write_text(
            "from metabolon.tools.alpha import something\n"
        )
        edges = _extract_tool_cross_imports(tools)
        assert edges == []

    def test_empty_tools_dir(self, tmp_path):
        tools = tmp_path / "empty_tools"
        tools.mkdir()
        assert _extract_tool_cross_imports(tools) == []


# -- Integration: integrin_colony_probe --------------------------------------


class TestIntegrinColonyProbe:
    def test_returns_colony_probe_result(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert type(result).__name__ == "ColonyProbeResult"

    def test_empty_dirs_all_zeros(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.colony_count == 0
        assert result.bud_count == 0
        assert result.skill_count == 0
        assert result.total_detached == 0
        assert result.orphan_buds == []

    def test_colony_references_present_bud(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_colony(c, "review", "- **audit**: invoke audit bud — run check\n")
        _make_bud(b, "audit", "---\nname: audit\n---\nContent.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.detached_colony_bud_refs == []

    def test_colony_references_missing_bud(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_colony(c, "review", "- **ghost**: invoke ghost bud — run check\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert len(result.detached_colony_bud_refs) == 1
        assert result.detached_colony_bud_refs[0]["missing_bud"] == "ghost"
        assert result.detached_colony_bud_refs[0]["colony"] == "review"
        assert result.total_detached == 1

    def test_bud_references_present_skill(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_skill(s, "histology")
        _make_bud(b, "biopsy", '---\nname: biopsy\nskills: ["histology"]\n---\nBody.\n')
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.detached_bud_skill_refs == []

    def test_bud_references_missing_skill(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_bud(b, "biopsy", '---\nname: biopsy\nskills: ["phantom-skill"]\n---\nBody.\n')
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert len(result.detached_bud_skill_refs) == 1
        assert result.detached_bud_skill_refs[0]["bud"] == "biopsy"
        assert result.detached_bud_skill_refs[0]["missing_skill"] == "phantom-skill"

    def test_bud_references_present_mcp_tool(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_tool_module(t, "oghma", ["histone_search", "histone_mark"])
        _make_bud(b, "memory", "---\nname: memory\n---\nCall `histone_search` to find.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.detached_bud_tool_refs == []

    def test_bud_references_missing_mcp_tool(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_bud(b, "memory", "---\nname: memory\n---\nCall mcp__vivesca__ghost_tool here.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert any(
            r["missing_tool"] == "ghost_tool"
            for r in result.detached_bud_tool_refs
        )

    def test_skill_cross_references_present_skill(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_skill(s, "histology", "---\nname: histology\n---\nBody.\n")
        _make_skill(s, "biopsy", "---\nname: biopsy\n---\nFollow /histology precisely.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.detached_skill_skill_refs == []

    def test_skill_cross_references_missing_skill(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_skill(s, "biopsy", "---\nname: biopsy\n---\nFollow /phantom precisely.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert any(
            r["missing_skill"] == "phantom"
            for r in result.detached_skill_skill_refs
        )

    def test_skill_references_registered_tool(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_tool_module(t, "integrin", ["integrin_probe"])
        _make_skill(
            s, "receptor-health",
            "---\nname: receptor-health\n---\nRun integrin_probe to check.\n"
            "More detail: `integrin_probe` daily.\n"
        )
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.detached_skill_tool_refs == []

    def test_skill_references_missing_tool(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_skill(
            s, "receptor-health",
            "---\nname: receptor-health\n---\nRun `ghost_probe` to check.\n"
        )
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert any(
            r["missing_tool"] == "ghost_probe"
            for r in result.detached_skill_tool_refs
        )

    def test_tool_cross_import_detected(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_tool_module(t, "probe", ["integrin_probe"])
        # apoptosis.py imports from integrin.py -- and integrin.py exists
        (t / "apoptosis.py").write_text(
            "from metabolon.tools.probe import integrin_probe\n"
        )
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        # Import is valid -- target module exists
        assert result.detached_tool_tool_refs == []

    def test_tool_cross_import_broken(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        # alpha.py imports from nonexistent.py
        (t / "alpha.py").write_text(
            "from metabolon.tools.nonexistent import something\n"
        )
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert any(
            e["target_tool"] == "nonexistent"
            for e in result.detached_tool_tool_refs
        )

    def test_orphan_buds_when_no_colony_refs(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_bud(b, "lone-wolf", "---\nname: lone-wolf\n---\nBody.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert "lone-wolf" in result.orphan_buds

    def test_referenced_bud_not_orphan(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_colony(c, "review", "- **audit**: invoke audit bud — run check\n")
        _make_bud(b, "audit", "---\nname: audit\n---\nBody.\n")
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert "audit" not in result.orphan_buds

    def test_total_detached_is_sum(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        # 1 broken colony→bud ref
        _make_colony(c, "review", "- **missing-bud**: invoke missing-bud bud\n")
        # 1 broken bud→skill ref
        _make_bud(b, "scout", '---\nskills: ["no-such-skill"]\n---\nBody.\n')
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.total_detached == 2

    def test_counts_are_accurate(self, tmp_path):
        c, b, s, t = _scaffold(tmp_path)
        _make_colony(c, "col-a", "No workers.\n")
        _make_colony(c, "col-b", "No workers.\n")
        _make_bud(b, "bud-a", "---\nname: bud-a\n---\nBody.\n")
        _make_skill(s, "skill-a")
        _make_tool_module(t, "tool-a", ["tool_alpha", "tool_beta"])
        result = integrin_colony_probe(
            colonies_dir=c, buds_dir=b, skills_dir=s, tools_dir=t
        )
        assert result.colony_count == 2
        assert result.bud_count == 1
        assert result.skill_count == 1
        assert result.registered_tool_count == 2

    def test_missing_dirs_dont_crash(self, tmp_path):
        result = integrin_colony_probe(
            colonies_dir=tmp_path / "no_colonies",
            buds_dir=tmp_path / "no_buds",
            skills_dir=tmp_path / "no_skills",
            tools_dir=tmp_path / "no_tools",
        )
        assert result.total_detached == 0
        assert result.colony_count == 0
        assert result.orphan_buds == []
