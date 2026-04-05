from __future__ import annotations

"""Tests for the vivesca://anatomy resource."""


from typing import TYPE_CHECKING

from metabolon.resources.anatomy import (
    _extract_decorated_names,
    _extract_substrate_info,
    _known_lesions,
    _metabolism_modules,
    _organ_descriptions,
    _organism_theory,
    _scan_directory,
    _substrate_map,
    express_anatomy,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write_tool_module(directory: Path, filename: str, content: str) -> Path:
    """Write a Python module into a directory."""
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / filename
    p.write_text(content)
    return p


def _build_fake_project(tmp_path: Path) -> Path:
    """Create a minimal project tree mirroring the production layout.

    Production layout: germline/metabolon/ (src_root), germline/design.md, germline/plans/.
    Here: project/vivesca/ (src_root), project/design.md, project/plans/.

    Returns the vivesca path (the src_root).
    """
    project = tmp_path / "project"
    src = project / "vivesca"

    # Tools with module docstrings and tool functions with docstrings + params
    tools = src / "enzymes"
    _write_tool_module(tools, "__init__.py", "")
    _write_tool_module(
        tools,
        "fasti.py",
        '"""fasti -- Google Calendar management.\n\n'
        "Tools:\n"
        "  fasti_list_events  -- list events for a date\n"
        '"""\n'
        "from fastmcp.tools import tool\n\n"
        '@tool(name="fasti_list_events", description="List events")\n'
        "def fasti_list_events(date: str, calendar: str = 'primary') -> str:\n"
        '    """List calendar events for a given date."""\n'
        '    return ""\n\n'
        '@tool(name="fasti_create_event", description="Create event")\n'
        "def fasti_create_event(title: str, start: str, end: str) -> str:\n"
        '    """Create a new calendar event."""\n'
        '    return ""\n',
    )

    # Resources
    resources = src / "resources"
    _write_tool_module(resources, "__init__.py", "")
    _write_tool_module(
        resources,
        "constitution.py",
        "from fastmcp.resources import resource\n\n"
        '@resource("vivesca://constitution")\n'
        "def constitution() -> str:\n"
        '    return ""\n',
    )

    # Codons (prompts)
    codons = src / "codons"
    _write_tool_module(codons, "__init__.py", "")
    _write_tool_module(
        codons,
        "templates.py",
        "from fastmcp.prompts import prompt\n\n"
        '@prompt(name="research", description="Research brief")\n'
        "def research(topic: str) -> str:\n"
        "    return topic\n",
    )

    # Substrates
    substrates = src / "metabolism" / "substrates"
    _write_tool_module(substrates, "__init__.py", "")
    _write_tool_module(
        substrates,
        "constitution.py",
        '"""ExecutiveSubstrate -- cortical metabolism of constitutional rules.\n\n'
        "Deliberative: senses rules and their signal evidence.\n"
        '"""\n\n'
        "class ExecutiveSubstrate:\n"
        '    """Cortical substrate: audits constitution rules."""\n\n'
        "    name: str = 'constitution'\n\n"
        "    def sense(self, days: int = 30) -> list:\n"
        '        """Read constitution rules and cross-reference with signal evidence."""\n'
        "        return []\n\n"
        "    def candidates(self, sensed: list) -> list:\n"
        '        """Rules without evidence are candidates."""\n'
        "        return []\n\n"
        "    def act(self, candidate: dict) -> str:\n"
        '        """Propose action for rules without evidence."""\n'
        "        return ''\n\n"
        "    def report(self, sensed: list, acted: list) -> str:\n"
        '        """Format a constitution audit report."""\n'
        "        return ''\n",
    )
    _write_tool_module(
        substrates,
        "hygiene.py",
        '"""HygieneSubstrate -- metabolism of tooling health.\n\n'
        "Senses dependency freshness, pre-commit hook versions.\n"
        '"""\n\n'
        "class HygieneSubstrate:\n"
        '    """Substrate for dependency and tooling health."""\n\n'
        "    name: str = 'hygiene'\n\n"
        "    def sense(self, days: int = 30) -> list:\n"
        '        """Collect tooling health signals."""\n'
        "        return []\n\n"
        "    def candidates(self, sensed: list) -> list:\n"
        '        """Filter to actionable items."""\n'
        "        return []\n\n"
        "    def act(self, candidate: dict) -> str:\n"
        '        """Execute safe upgrades, propose risky ones."""\n'
        "        return ''\n\n"
        "    def report(self, sensed: list, acted: list) -> str:\n"
        '        """Format a hygiene report."""\n'
        "        return ''\n",
    )

    # Metabolism modules
    met = src / "metabolism"
    _write_tool_module(
        met,
        "signals.py",
        '"""Stimulus collection and JSONL persistence."""\n\n'
        "class SensorySystem:\n"
        "    pass\n\n"
        "class Stimulus:\n"
        "    pass\n",
    )
    _write_tool_module(
        met,
        "fitness.py",
        '"""Per-tool emotion computation from sensory aggregates."""\n\n'
        "class Emotion:\n"
        "    pass\n\n"
        "def sense_affect():\n"
        "    pass\n",
    )
    _write_tool_module(
        met,
        "sweep.py",
        '"""Cold path -- weekly differential evolution sweep."""\n\ndef select():\n    pass\n',
    )
    _write_tool_module(
        met,
        "gates.py",
        '"""Selection pressure -- reflex checks + taste."""\n\ndef reflex_check():\n    pass\n',
    )
    _write_tool_module(
        met,
        "variants.py",
        '"""Genome variant storage -- tool descriptions as versioned markdown files."""\n\n'
        "class Genome:\n"
        "    pass\n",
    )
    _write_tool_module(
        met,
        "repair.py",
        '"""Immune system -- metaprompt-driven healing."""\n\n'
        "class ImmuneRequest:\n"
        "    pass\n\n"
        "async def immune_response():\n"
        "    pass\n",
    )

    # design.md — at project root (mirrors germline/design.md)
    (project / "design.md").write_text(
        "# Vivesca -- Design Philosophy\n\n"
        "## The Theory\n\n"
        "The organism is the unit. Not the human. Not the AI.\n\n"
        "## The Three Bodies\n\n"
        "A vivesca has three components. None is the organism alone.\n\n"
        "## The Flywheel, Not The Balance\n\n"
        "Values are complementary, not competing.\n\n"
        "## The Body Plan\n\n"
        "Vivesca has the structural properties of a living system.\n\n"
        "```\nMembrane -- boundaries\n```\n\n"
        "## Metabolism\n\n"
        "Any artifact with three properties is a metabolism target.\n\n"
        "## Two Metabolisms\n\n"
        "The same experience feeds two consumers.\n\n"
        "## Three Knowledge Artifacts\n\n"
        "Everything dissolves into one of three. No fourth tier.\n\n"
        "| Artifact | Access |\n|---|---|\n| DNA | Always |\n"
    )

    # Plans — at project root (mirrors germline/plans/)
    plans = project / "plans"
    plans.mkdir(parents=True, exist_ok=True)
    (plans / "plan-001.md").write_text(
        "---\n"
        'title: "feat: Wire metabolism loop"\n'
        "status: active\n"
        "---\n\n"
        "# Wire Metabolism Loop\n\n"
        "Wire the existing metabolism modules into a working pipeline.\n"
    )
    (plans / "plan-002.md").write_text(
        "---\n"
        'title: "feat: Old completed plan"\n'
        "status: completed\n"
        "---\n\n"
        "# Old Plan\n\n"
        "This is done.\n"
    )

    return src


class TestExtractDecoratedNames:
    def test_extracts_tool_with_name_kwarg(self, tmp_path):
        mod = tmp_path / "example.py"
        mod.write_text(
            "from fastmcp.tools import tool\n\n"
            '@tool(name="fasti_list_events", description="List events")\n'
            "def fasti_list_events(date: str) -> str:\n"
            '    return "ok"\n'
        )
        results = _extract_decorated_names(mod, "tool")
        assert len(results) == 1
        assert results[0]["func_name"] == "fasti_list_events"
        assert results[0]["decorator_arg"] == "fasti_list_events"

    def test_extracts_resource_with_positional_uri(self, tmp_path):
        mod = tmp_path / "example.py"
        mod.write_text(
            "from fastmcp.resources import resource\n\n"
            '@resource("vivesca://budget")\n'
            "def budget_status() -> str:\n"
            '    return "ok"\n'
        )
        results = _extract_decorated_names(mod, "resource")
        assert len(results) == 1
        assert results[0]["decorator_arg"] == "vivesca://budget"

    def test_extracts_multiple_functions(self, tmp_path):
        mod = tmp_path / "example.py"
        mod.write_text(
            "from fastmcp.tools import tool\n\n"
            '@tool(name="alpha_get", description="Get alpha")\n'
            "def alpha_get() -> str:\n"
            '    return "a"\n\n'
            '@tool(name="alpha_set", description="Set alpha")\n'
            "def alpha_set(v: str) -> str:\n"
            "    return v\n"
        )
        results = _extract_decorated_names(mod, "tool")
        assert len(results) == 2
        names = {r["decorator_arg"] for r in results}
        assert names == {"alpha_get", "alpha_set"}

    def test_ignores_unrelated_decorators(self, tmp_path):
        mod = tmp_path / "example.py"
        mod.write_text(
            "def something():\n"
            "    pass\n\n"
            "@other_decorator\n"
            "def decorated() -> str:\n"
            '    return "x"\n'
        )
        results = _extract_decorated_names(mod, "tool")
        assert len(results) == 0

    def test_handles_syntax_error_gracefully(self, tmp_path):
        mod = tmp_path / "bad.py"
        mod.write_text("def broken(\n")
        results = _extract_decorated_names(mod, "tool")
        assert results == []

    def test_handles_missing_file_gracefully(self, tmp_path):
        mod = tmp_path / "nonexistent.py"
        results = _extract_decorated_names(mod, "tool")
        assert results == []


class TestScanDirectory:
    def test_scans_tool_directory(self, tmp_path):
        tools_dir = tmp_path / "tools"
        _write_tool_module(tools_dir, "__init__.py", "")
        _write_tool_module(
            tools_dir,
            "weather.py",
            "from fastmcp.tools import tool\n\n"
            '@tool(name="weather_fetch", description="Fetch weather")\n'
            "def weather_fetch() -> str:\n"
            '    return "sunny"\n',
        )
        lines = _scan_directory(tools_dir, "tool", "tools")
        combined = "\n".join(lines)
        assert "weather.py" in combined
        assert "weather_fetch" in combined

    def test_missing_directory(self, tmp_path):
        lines = _scan_directory(tmp_path / "nonexistent", "tool", "tools")
        combined = "\n".join(lines)
        assert "no tools directory" in combined

    def test_empty_directory(self, tmp_path):
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        (tools_dir / "__init__.py").write_text("")
        lines = _scan_directory(tools_dir, "tool", "tools")
        combined = "\n".join(lines)
        assert "no tools modules" in combined

    def test_module_without_decorators(self, tmp_path):
        tools_dir = tmp_path / "tools"
        _write_tool_module(tools_dir, "__init__.py", "")
        _write_tool_module(
            tools_dir,
            "utils.py",
            "def helper():\n    pass\n",
        )
        lines = _scan_directory(tools_dir, "tool", "tools")
        combined = "\n".join(lines)
        assert "utils.py" in combined
        assert "no @tool found" in combined


class TestGenerateAnatomy:
    def _build_fake_src(self, tmp_path: Path) -> Path:
        """Create a minimal src/vivesca-like tree."""
        src = tmp_path / "vivesca"

        # Tools
        tools = src / "enzymes"
        _write_tool_module(tools, "__init__.py", "")
        _write_tool_module(
            tools,
            "fasti.py",
            "from fastmcp.tools import tool\n\n"
            '@tool(name="fasti_list_events", description="List events")\n'
            "def fasti_list_events() -> str:\n"
            '    return ""\n\n'
            '@tool(name="fasti_create_event", description="Create event")\n'
            "def fasti_create_event() -> str:\n"
            '    return ""\n',
        )

        # Resources
        resources = src / "resources"
        _write_tool_module(resources, "__init__.py", "")
        _write_tool_module(
            resources,
            "constitution.py",
            "from fastmcp.resources import resource\n\n"
            '@resource("vivesca://constitution")\n'
            "def constitution() -> str:\n"
            '    return ""\n',
        )

        # Codons (prompts)
        codons = src / "codons"
        _write_tool_module(codons, "__init__.py", "")
        _write_tool_module(
            codons,
            "templates.py",
            "from fastmcp.prompts import prompt\n\n"
            '@prompt(name="research", description="Research brief")\n'
            "def research(topic: str) -> str:\n"
            "    return topic\n",
        )

        return src

    def test_returns_valid_markdown(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert isinstance(result, str)
        assert "# vivesca" in result
        assert "## Registered Tools" in result
        assert "## Registered Resources" in result
        assert "## Registered Codons" in result
        assert "## Metabolism State" in result

    def test_includes_tool_names(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert "fasti_list_events" in result
        assert "fasti_create_event" in result

    def test_includes_resource_uris(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert "vivesca://constitution" in result

    def test_includes_prompt_names(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert "research" in result

    def test_includes_metabolism_section(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert "Metabolism State" in result

    def test_lists_module_filenames(self, tmp_path):
        src = self._build_fake_src(tmp_path)
        result = express_anatomy(src_root=src)

        assert "fasti.py" in result
        assert "constitution.py" in result
        assert "templates.py" in result


class TestOrganismTheory:
    def test_extracts_key_sections(self, tmp_path):
        src = _build_fake_project(tmp_path)
        project_root = src.parent
        lines = _organism_theory(project_root)
        combined = "\n".join(lines)

        assert "The Theory" in combined
        assert "Three Bodies" in combined
        assert "Flywheel" in combined
        assert "Body Plan" in combined
        assert "Metabolism" in combined
        assert "Two Metabolisms" in combined
        assert "Three Knowledge Artifacts" in combined

    def test_missing_design_md(self, tmp_path):
        lines = _organism_theory(tmp_path / "nonexistent")
        combined = "\n".join(lines)
        assert "DESIGN.md not found" in combined

    def test_extracts_first_paragraph_content(self, tmp_path):
        src = _build_fake_project(tmp_path)
        project_root = src.parent
        lines = _organism_theory(project_root)
        combined = "\n".join(lines)

        assert "organism is the unit" in combined
        assert "three components" in combined
        assert "complementary" in combined


class TestOrganDescriptions:
    def test_extracts_module_docstrings_and_tools(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _organ_descriptions(src)
        combined = "\n".join(lines)

        assert "### fasti" in combined
        assert "Google Calendar" in combined
        assert "fasti_list_events" in combined
        assert "fasti_create_event" in combined

    def test_shows_tool_params(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _organ_descriptions(src)
        combined = "\n".join(lines)

        assert "date" in combined
        assert "title" in combined
        assert "start" in combined

    def test_shows_tool_docstring_first_line(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _organ_descriptions(src)
        combined = "\n".join(lines)

        assert "List calendar events" in combined
        assert "Create a new calendar event" in combined

    def test_missing_tools_dir(self, tmp_path):
        lines = _organ_descriptions(tmp_path / "nonexistent")
        combined = "\n".join(lines)
        assert "no enzymes directory" in combined


class TestSubstrateMap:
    def test_extracts_substrate_classes(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _substrate_map(src)
        combined = "\n".join(lines)

        assert "ExecutiveSubstrate" in combined
        assert "HygieneSubstrate" in combined

    def test_shows_layer(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _substrate_map(src)
        combined = "\n".join(lines)

        assert "cortical" in combined

    def test_shows_protocol_methods(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _substrate_map(src)
        combined = "\n".join(lines)

        assert "sense" in combined
        assert "candidates" in combined
        assert "act" in combined
        assert "report" in combined

    def test_shows_method_docstrings(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _substrate_map(src)
        combined = "\n".join(lines)

        assert "Read constitution rules" in combined
        assert "Collect tooling health signals" in combined

    def test_missing_substrates_dir(self, tmp_path):
        lines = _substrate_map(tmp_path / "nonexistent")
        combined = "\n".join(lines)
        assert "no substrates directory" in combined


class TestMetabolismModules:
    def test_lists_modules_with_docstrings(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _metabolism_modules(src)
        combined = "\n".join(lines)

        assert "signals" in combined
        assert "fitness" in combined
        assert "sweep" in combined
        assert "gates" in combined
        assert "variants" in combined
        assert "repair" in combined

    def test_shows_module_docstring_first_line(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _metabolism_modules(src)
        combined = "\n".join(lines)

        assert "Stimulus collection" in combined
        assert "emotion computation" in combined
        assert "differential evolution" in combined

    def test_shows_exports(self, tmp_path):
        src = _build_fake_project(tmp_path)
        lines = _metabolism_modules(src)
        combined = "\n".join(lines)

        assert "SensorySystem" in combined
        assert "Emotion" in combined
        assert "Genome" in combined
        assert "reflex_check" in combined

    def test_missing_metabolism_dir(self, tmp_path):
        lines = _metabolism_modules(tmp_path / "nonexistent")
        combined = "\n".join(lines)
        assert "no metabolism directory" in combined


class TestKnownLesions:
    def test_lists_active_plans(self, tmp_path):
        src = _build_fake_project(tmp_path)
        project_root = src.parent
        lines = _known_lesions(project_root)
        combined = "\n".join(lines)

        assert "Wire metabolism loop" in combined

    def test_excludes_completed_plans(self, tmp_path):
        src = _build_fake_project(tmp_path)
        project_root = src.parent
        lines = _known_lesions(project_root)
        combined = "\n".join(lines)

        assert "Old completed plan" not in combined

    def test_missing_plans_dir(self, tmp_path):
        lines = _known_lesions(tmp_path / "nonexistent")
        combined = "\n".join(lines)
        assert "no plans directory" in combined


class TestExtractSubstrateInfo:
    def test_extracts_class_info(self, tmp_path):
        mod = tmp_path / "test_substrate.py"
        mod.write_text(
            '"""TestSubstrate -- cortical test.\n"""\n\n'
            "class TestSubstrate:\n"
            '    """Cortical substrate for testing."""\n\n'
            "    def sense(self, days: int = 30) -> list:\n"
            '        """Sense test artifacts."""\n'
            "        return []\n"
        )
        info = _extract_substrate_info(mod)
        assert info is not None
        assert info["class_name"] == "TestSubstrate"
        assert info["layer"] == "cortical"
        assert "sense" in info["methods"]
        assert "Sense test artifacts" in info["methods"]["sense"]


class TestGenerateAnatomyNewSections:
    """Test that the full express_anatomy output includes all new sections."""

    def test_includes_organism_theory_section(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)

        assert "## Organism Theory" in result
        assert "organism is the unit" in result

    def test_includes_organ_descriptions_section(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)

        assert "## Organ Descriptions" in result
        assert "### fasti" in result
        assert "Google Calendar" in result
        assert "fasti_list_events" in result

    def test_includes_substrate_map_section(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)

        assert "## Substrate Map" in result
        assert "ExecutiveSubstrate" in result
        assert "cortical" in result

    def test_includes_metabolism_modules_section(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)

        assert "## Metabolism Modules" in result
        assert "signals" in result
        assert "fitness" in result
        assert "sweep" in result

    def test_includes_known_lesions_section(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)

        assert "## Known Lesions" in result
        assert "Wire metabolism loop" in result

    def test_output_under_300_lines(self, tmp_path):
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)
        line_count = len(result.splitlines())
        assert line_count < 300, f"Output is {line_count} lines, must be under 300"


class TestGeneratorFunction:
    def test_generator_returns_string(self, tmp_path):
        """express_anatomy returns a string with valid markdown."""
        src = _build_fake_project(tmp_path)
        result = express_anatomy(src_root=src)
        assert isinstance(result, str)
        assert "# vivesca" in result
