"""Anatomy resource — auto-generated organism overview.

Resources:
  vivesca://anatomy — introspected anatomy overview
"""

from __future__ import annotations

import ast
import logging
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_SRC = Path(__file__).resolve().parent.parent  # metabolon/


def _extract_decorated_names(module_path: Path, decorator_name: str) -> list[dict]:
    """Parse a Python file's AST and return functions decorated with *decorator_name*.

    Returns a list of dicts with 'func_name' and 'decorator_arg' (the first
    positional string argument to the decorator, e.g. the tool name or URI).
    """
    results: list[dict] = []
    try:
        tree = ast.parse(module_path.read_text())
    except (SyntaxError, OSError):
        return results

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            # Handles both @tool(...) and @tool
            call_node = dec if isinstance(dec, ast.Call) else None
            name_node = dec

            if isinstance(dec, ast.Call):
                name_node = dec.func

            # Resolve decorator name from ast.Name or ast.Attribute
            dec_name = None
            if isinstance(name_node, ast.Name):
                dec_name = name_node.id
            elif isinstance(name_node, ast.Attribute):
                dec_name = name_node.attr

            if dec_name != decorator_name:
                continue

            # Extract first positional arg or 'name' keyword arg
            dec_arg = None
            if call_node and call_node.args:
                first = call_node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    dec_arg = first.value
            if call_node and not dec_arg:
                for kw in call_node.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        dec_arg = kw.value.value
                        break
            if call_node and not dec_arg:
                for kw in call_node.keywords:
                    if kw.arg == "uri" and isinstance(kw.value, ast.Constant):
                        dec_arg = kw.value.value
                        break

            results.append(
                {
                    "func_name": node.name,
                    "decorator_arg": dec_arg or node.name,
                }
            )
    return results


def _scan_directory(
    directory: Path,
    decorator_name: str,
    label: str,
) -> list[str]:
    """Scan a directory for Python modules and extract decorated functions.

    Returns markdown lines describing what was found.
    """
    lines: list[str] = []
    if not directory.exists():
        lines.append(f"  _(no {label} directory)_")
        return lines

    modules = sorted(p for p in directory.glob("*.py") if p.name != "__init__.py")
    if not modules:
        lines.append(f"  _(no {label} modules)_")
        return lines

    for mod in modules:
        entries = _extract_decorated_names(mod, decorator_name)
        if entries:
            names = ", ".join(f"`{e['decorator_arg']}`" for e in entries)
            lines.append(f"- **{mod.name}**: {names}")
        else:
            lines.append(f"- **{mod.name}**: _(no @{decorator_name} found)_")

    return lines


def _metabolism_summary() -> list[str]:
    """Read metabolism state — graceful fallback if empty."""
    lines: list[str] = []
    try:
        from metabolon.metabolism.signals import SensorySystem
        from metabolon.metabolism.variants import Genome

        store = Genome()
        tools = store.expressed_tools()
        total_variants = sum(len(store.allele_variants(t)) for t in tools)
        lines.append(
            f"- Variant store: **{len(tools)}** tool(s), **{total_variants}** total variant(s)"
        )

        collector = SensorySystem()
        since = datetime.now(UTC) - timedelta(days=7)
        recent = collector.recall_since(since)
        lines.append(f"- Signals (last 7 days): **{len(recent)}**")

        if recent:
            tool_counts: dict[str, int] = {}
            for s in recent:
                tool_counts[s.tool] = tool_counts.get(s.tool, 0) + 1
            top = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_str = ", ".join(f"`{t}` ({c})" for t, c in top)
            lines.append(f"- Most active: {top_str}")
    except Exception:
        lines.append("- _(metabolism data unavailable)_")

    return lines


# ── New section helpers ──────────────────────────────────────────────


def _extract_module_docstring(module_path: Path) -> str:
    """Extract the module-level docstring from a Python file via AST."""
    try:
        tree = ast.parse(module_path.read_text())
        return ast.get_docstring(tree) or ""
    except (SyntaxError, OSError):
        return ""


def _extract_tool_details(module_path: Path) -> list[dict]:
    """Extract @tool-decorated functions with docstring (first line) and params."""
    results: list[dict] = []
    try:
        tree = ast.parse(module_path.read_text())
    except (SyntaxError, OSError):
        return results

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_tool = False
        tool_name = node.name
        for dec in node.decorator_list:
            call_node = dec if isinstance(dec, ast.Call) else None
            name_node = dec
            if isinstance(dec, ast.Call):
                name_node = dec.func
            dec_name = None
            if isinstance(name_node, ast.Name):
                dec_name = name_node.id
            elif isinstance(name_node, ast.Attribute):
                dec_name = name_node.attr
            if dec_name != "tool":
                continue
            is_tool = True
            # Extract tool name from decorator args
            if call_node:
                for kw in call_node.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        tool_name = kw.value.value
                        break
                else:
                    if call_node.args:
                        first = call_node.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            tool_name = first.value

        if not is_tool:
            continue

        docstring = ast.get_docstring(node) or ""
        first_line = docstring.split("\n")[0].strip() if docstring else ""
        params = [arg.arg for arg in node.args.args if arg.arg != "self"]

        results.append(
            {
                "name": tool_name,
                "doc": first_line,
                "params": params,
            }
        )
    return results


def _organ_descriptions(src: Path) -> list[str]:
    """For each tool module, extract module docstring + per-tool details."""
    lines: list[str] = []
    tools_dir = src / "tools"
    if not tools_dir.exists():
        lines.append("_(no tools directory)_")
        return lines

    modules = sorted(p for p in tools_dir.glob("*.py") if p.name != "__init__.py")
    for mod in modules:
        mod_doc = _extract_module_docstring(mod)
        # First line of module docstring as domain summary
        first_line = mod_doc.split("\n")[0].strip() if mod_doc else mod.stem
        lines.append(f"### {mod.stem}")
        lines.append(f"{first_line}")

        tool_details = _extract_tool_details(mod)
        if tool_details:
            for td in tool_details:
                param_str = ", ".join(td["params"]) if td["params"] else ""
                doc_part = f" -- {td['doc']}" if td["doc"] else ""
                lines.append(f"- `{td['name']}({param_str})`{doc_part}")
        lines.append("")
    return lines


def _extract_substrate_info(module_path: Path) -> dict | None:
    """Extract substrate class info via AST: class name, docstring, layer, methods."""
    try:
        source = module_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return None

    mod_doc = ast.get_docstring(tree) or ""

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Look for classes ending in Substrate
        if not node.name.endswith("Substrate"):
            continue

        class_doc = ast.get_docstring(node) or ""

        # Detect layer from module docstring or class docstring
        combined = (mod_doc + " " + class_doc).lower()
        if "cortical" in combined:
            layer = "cortical"
        elif "autonomic" in combined:
            layer = "autonomic"
        else:
            layer = "unspecified"

        # Extract the 4-method protocol docstrings
        methods: dict[str, str] = {}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in (
                "sense",
                "candidates",
                "act",
                "report",
            ):
                method_doc = ast.get_docstring(item) or ""
                methods[item.name] = method_doc.split("\n")[0].strip()

        return {
            "class_name": node.name,
            "class_doc": class_doc.split("\n")[0].strip() if class_doc else "",
            "layer": layer,
            "methods": methods,
            "module_doc_first_line": mod_doc.split("\n")[0].strip() if mod_doc else "",
        }
    return None


def _substrate_map(src: Path) -> list[str]:
    """Scan substrates directory and extract class info."""
    lines: list[str] = []
    substrates_dir = src / "metabolism" / "substrates"
    if not substrates_dir.exists():
        lines.append("_(no substrates directory)_")
        return lines

    modules = sorted(p for p in substrates_dir.glob("*.py") if p.name != "__init__.py")
    if not modules:
        lines.append("_(no substrate modules)_")
        return lines

    for mod in modules:
        info = _extract_substrate_info(mod)
        if not info:
            continue
        lines.append(f"### {info['class_name']} ({info['layer']})")
        lines.append(f"{info['module_doc_first_line']}")

        if info["methods"]:
            for method_name in ("sense", "candidates", "act", "report"):
                doc = info["methods"].get(method_name, "")
                if doc:
                    lines.append(f"- **{method_name}**: {doc}")
        lines.append("")
    return lines


def _extract_module_summary(module_path: Path) -> dict | None:
    """Extract module docstring + key class/function names from a Python file."""
    try:
        source = module_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return None

    mod_doc = ast.get_docstring(tree) or ""
    first_line = mod_doc.split("\n")[0].strip() if mod_doc else ""

    classes: list[str] = []
    functions: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and not node.name.startswith("_"):
            functions.append(node.name)

    return {
        "first_line": first_line,
        "classes": classes,
        "functions": functions,
    }


def _metabolism_modules(src: Path) -> list[str]:
    """Scan metabolism/*.py (not substrates/) for module summaries."""
    lines: list[str] = []
    met_dir = src / "metabolism"
    if not met_dir.exists():
        lines.append("_(no metabolism directory)_")
        return lines

    modules = sorted(p for p in met_dir.glob("*.py") if p.name != "__init__.py" and p.is_file())
    if not modules:
        lines.append("_(no metabolism modules)_")
        return lines

    for mod in modules:
        info = _extract_module_summary(mod)
        if not info:
            continue
        exports: list[str] = []
        if info["classes"]:
            exports.extend(info["classes"])
        if info["functions"]:
            exports.extend(info["functions"])
        export_str = ", ".join(f"`{e}`" for e in exports) if exports else "_(none)_"
        lines.append(f"- **{mod.stem}**: {info['first_line']}")
        lines.append(f"  Exports: {export_str}")
    return lines


def _organism_theory(project_root: Path) -> list[str]:
    """Extract key concepts from DESIGN.md — concise summary."""
    lines: list[str] = []
    design_path = project_root / "design.md"
    if not design_path.exists():
        lines.append("_(DESIGN.md not found)_")
        return lines

    try:
        text = design_path.read_text()
    except OSError:
        lines.append("_(DESIGN.md unreadable)_")
        return lines

    # Extract specific sections by heading
    section_keys = [
        ("The Theory", "theory"),
        ("The Three Bodies", "three_bodies"),
        ("The Flywheel, Not The Balance", "flywheel"),
        ("The Body Plan", "body_plan"),
        ("Metabolism", "metabolism"),
        ("Two Metabolisms", "two_metabolisms"),
        ("Three Knowledge Artifacts", "three_artifacts"),
    ]

    # Parse sections: split by ## headings
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line.lstrip("# ").strip()
            current_lines = []
        elif line.startswith("### ") and current_heading:
            # Include subsections in parent
            current_lines.append(line)
        else:
            current_lines.append(line)
    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    def _first_paragraph(section_text: str) -> str:
        """Extract first non-empty paragraph (before any blank line or code block)."""
        result_lines: list[str] = []
        for sline in section_text.splitlines():
            stripped = sline.strip()
            if not stripped and result_lines:
                break
            if stripped.startswith("```"):
                break
            if stripped.startswith("|"):
                break
            if stripped:
                result_lines.append(stripped)
        return " ".join(result_lines)

    for heading, _key in section_keys:
        content = sections.get(heading, "")
        if not content:
            continue
        summary = _first_paragraph(content)
        if summary:
            lines.append(f"**{heading}:** {summary}")

    return lines


def _known_lesions(project_root: Path) -> list[str]:
    """Scan genome/plans/ for active plans + optionally count failing tests."""
    lines: list[str] = []
    plans_dir = project_root / "plans"

    # Active plans
    if plans_dir.exists():
        plan_files = sorted(plans_dir.glob("*.md"))
        active_plans: list[tuple[str, str]] = []
        for pf in plan_files:
            try:
                text = pf.read_text()
            except OSError:
                continue
            # Parse YAML frontmatter for status: active
            if not text.startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            frontmatter = parts[1]
            status = ""
            title = ""
            for fm_line in frontmatter.splitlines():
                fm_line = fm_line.strip()
                if fm_line.startswith("status:"):
                    status = fm_line.split(":", 1)[1].strip()
                elif fm_line.startswith("title:"):
                    raw_title = fm_line.split(":", 1)[1].strip()
                    title = raw_title.strip("\"'")
            if status == "active" and title:
                # First non-empty line after frontmatter as summary
                body = parts[2].strip()
                summary_line = ""
                for bl in body.splitlines():
                    bl = bl.strip()
                    if bl and not bl.startswith("#"):
                        summary_line = bl[:120]
                        break
                active_plans.append((title, summary_line))

        if active_plans:
            for title, summary in active_plans:
                lines.append(f"- **{title}**")
                if summary:
                    lines.append(f"  {summary}")
        else:
            lines.append("_(no active plans)_")
    else:
        lines.append("_(no plans directory)_")

    # Test health — fast, safe, graceful
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=no", "-q", "--no-header"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30,
            env={
                **__import__("os").environ,
                "VIVESCA_HYGIENE_NO_TESTS": "1",
            },
        )
        output = result.stdout + result.stderr
        passed = failed = errors = 0
        for m in re.finditer(r"(\d+)\s+(passed|failed|error)", output):
            count, kind = int(m.group(1)), m.group(2)
            if kind == "passed":
                passed = count
            elif kind == "failed":
                failed = count
            elif kind == "error":
                errors = count
        if passed or failed or errors:
            status = "healthy" if failed == 0 and errors == 0 else "UNHEALTHY"
            lines.append(f"- Tests: {status} ({passed} passed, {failed} failed, {errors} errors)")
    except Exception:
        lines.append("- Tests: _(could not run)_")

    return lines


def _operon_heartbeat() -> list[str]:
    """Run the operon substrate and return a compact heartbeat summary."""
    lines: list[str] = []
    try:
        from metabolon.metabolism.substrates.operons import OperonSubstrate

        substrate = OperonSubstrate()
        sensed = substrate.sense(days=30)
        healthy = [e for e in sensed if not e["stale"]]
        stale = [e for e in sensed if e["stale"]]

        lines.append(
            f"**{len(healthy)}** healthy, **{len(stale)}** stale (of {len(sensed)} expressed)\n"
        )

        if stale:
            for e in stale:
                if e["days_since"] is not None:
                    lines.append(
                        f"- {e['reaction']}: {e['days_since']:.0f}d ago (cadence: {e['cadence_days']}d)"
                    )
                else:
                    lines.append(f"- {e['reaction']}: never fired (cadence: {e['cadence_days']}d)")
    except Exception:
        lines.append("_(operon heartbeat unavailable)_")
    return lines


def _operon_summary() -> list[str]:
    """Summarise the organism's operon map from metabolon.operons."""
    lines: list[str] = []
    try:
        from metabolon.operons import OPERONS

        live = [e for e in OPERONS if e.expressed]
        dormant = [e for e in OPERONS if not e.expressed]
        crystallised = [e for e in OPERONS if e.precipitation == "crystallised"]

        for e in OPERONS:
            status = "dormant" if not e.expressed else e.precipitation
            enzymes = ", ".join(f"`{t}`" for t in e.enzymes) if e.enzymes else "—"
            lines.append(f"- **{e.reaction}** [{status}]: {e.product[:80]}")
            lines.append(f"  Enzymes: {enzymes}")

        lines.append("")
        lines.append(
            f"Total: **{len(OPERONS)}** operons "
            f"({len(live)} active, {len(dormant)} dormant, "
            f"{len(crystallised)} crystallised)"
        )
    except ImportError:
        lines.append("_(operon map not found)_")
    return lines


# ── Main generator ──────────────────────────────────────────────


def express_anatomy(src_root: Path | None = None) -> str:
    """Build the anatomy overview markdown.

    Accepts an optional *src_root* override for testing.
    """
    src = src_root or _SRC
    project_root = src.parent  # project root (germline/)

    sections: list[str] = []
    sections.append("# vivesca — Anatomy\n")
    sections.append("_Auto-generated by introspecting the organism._\n")

    # Organism Theory
    sections.append("## Organism Theory\n")
    theory = _organism_theory(project_root)
    if theory:
        sections.extend(theory)
    sections.append("")

    # Organ Descriptions
    sections.append("## Organ Descriptions\n")
    sections.extend(_organ_descriptions(src))

    # Substrate Map
    sections.append("## Substrate Map\n")
    sections.extend(_substrate_map(src))

    # Metabolism Modules
    sections.append("## Metabolism Modules\n")
    sections.append("Architecture: signals -> fitness -> variants -> gates -> repair -> sweep\n")
    sections.extend(_metabolism_modules(src))
    sections.append("")

    # Tools (existing)
    sections.append("## Registered Tools\n")
    sections.extend(_scan_directory(src / "tools", "tool", "tools"))
    sections.append("")

    # Resources (existing)
    sections.append("## Registered Resources\n")
    sections.extend(_scan_directory(src / "resources", "resource", "resources"))
    sections.append("")

    # Codons (prompts)
    sections.append("## Registered Codons\n")
    sections.extend(_scan_directory(src / "codons", "codon", "codons"))
    sections.append("")

    # Operon Map
    sections.append("## Operon Map\n")
    sections.extend(_operon_summary())
    sections.append("")

    # Operon Heartbeat
    sections.append("## Operon Heartbeat\n")
    sections.extend(_operon_heartbeat())
    sections.append("")

    # Metabolism State
    sections.append("## Metabolism State\n")
    sections.extend(_metabolism_summary())
    sections.append("")

    # Known Lesions
    sections.append("## Known Lesions\n")
    sections.extend(_known_lesions(project_root))
    sections.append("")

    return "\n".join(sections)
