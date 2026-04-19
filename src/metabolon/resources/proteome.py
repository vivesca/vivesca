"""Effectors — how the organism acts on the world.

Resources:
  vivesca://effectors — CLI tools, MCP tools, and trigger routing
"""

import ast
import contextlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from metabolon.cytosol import VIVESCA_ROOT
from metabolon.resources.anatomy import _extract_tool_details

_BIN_DIR = VIVESCA_ROOT / "effectors"
_VIVESCA_TOOLS = Path(__file__).resolve().parent.parent / "enzymes"
_ROUTING_TABLE = VIVESCA_ROOT / "proteome.md"
_RECEPTORS_DIR = VIVESCA_ROOT / "membrane" / "receptors"
_CYTOSKELETON_DIR = VIVESCA_ROOT / "membrane" / "cytoskeleton"
_ASSAYS_DIR = VIVESCA_ROOT / "assays"
_CACHE_PATH = Path.home() / ".cache" / "proteome-index.json"


# ---------------------------------------------------------------------------
# v1: core scanners
# ---------------------------------------------------------------------------


def _scan_effector_dir(bin_dir: Path) -> list[dict]:
    """Scan vivesca/effectors/ for executable files with optional --help descriptions."""
    entries: list[dict] = []
    if not bin_dir.exists():
        return entries

    for f in sorted(bin_dir.iterdir()):
        if f.name.startswith(".") or f.name.startswith("_"):
            continue
        if not f.is_file():
            continue
        # Skip __pycache__, compiled files, backup files
        if f.name == "__pycache__" or f.suffix in (".pyc", ".sh.bak"):
            continue
        # Check executable bit
        if not os.access(f, os.X_OK):
            continue
        desc = _extract_effector_description(f)
        entries.append(
            {
                "name": f.name,
                "type": "cli",
                "source": "vivesca/effectors/",
                "description": desc,
                "path": str(f),
            }
        )
    return entries


def _extract_effector_description(f: Path) -> str:
    """Extract description from an effector file."""
    try:
        text = f.read_text(errors="replace")
    except OSError:
        return ""
    if f.suffix == ".py" or text.startswith("#!/"):
        # Python file: look for module docstring
        if f.suffix == ".py" or "python" in text.split("\n")[0]:
            return _extract_python_docstring(text)
        # Shell script: first comment after shebang and set -e
        return _extract_shell_comment(text)
    return ""


def _extract_python_docstring(text: str) -> str:
    """Extract the first module-level docstring from Python source."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        # Fallback: regex for triple-quoted string near top
        m = re.search(r'"""(.+?)"""', text, re.DOTALL)
        if m:
            return m.group(1).strip().split("\n")[0].strip()
        return ""
    doc = ast.get_docstring(tree)
    if doc:
        return doc.split("\n")[0].strip()
    return ""


def _extract_shell_comment(text: str) -> str:
    """Extract first meaningful comment from a shell script."""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#!/"):
            continue
        if stripped in ("set -e", "set -eu", "set -eo pipefail", "set -euo pipefail"):
            continue
        if stripped.startswith("#") and not stripped.startswith("#!"):
            return stripped.lstrip("# ").strip()
        if stripped and not stripped.startswith("#"):
            break
    return ""


def _scan_organelle_tools(tools_dir: Path) -> list[dict]:
    """Scan vivesca tool modules for @tool-decorated functions."""
    entries: list[dict] = []
    if not tools_dir.exists():
        return entries

    for mod in sorted(tools_dir.glob("*.py")):
        if mod.name == "__init__.py":
            continue
        details = _extract_tool_details(mod)
        for td in details:
            doc = td["doc"] if td["doc"] else ""
            entries.append(
                {
                    "name": td["name"],
                    "type": "mcp",
                    "source": f"vivesca/{mod.stem}",
                    "description": doc,
                }
            )
    return entries


def _read_signal_routing(path: Path) -> str:
    """Read the curated trigger→tool routing table."""
    if not path.exists():
        return ""
    try:
        return path.read_text().strip()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# v1: skills scanner
# ---------------------------------------------------------------------------


def _scan_skills(receptors_dir: Path | None = None) -> list[dict]:
    """Scan membrane/receptors/*/SKILL.md for skill definitions."""
    rd = receptors_dir or _RECEPTORS_DIR
    entries: list[dict] = []
    if not rd.exists():
        return entries

    for skill_dir in sorted(rd.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith(".") or skill_dir.name.startswith("_"):
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        entry = _parse_skill_md(skill_md, skill_dir.name)
        entries.append(entry)
    return entries


def _parse_skill_md(path: Path, fallback_name: str) -> dict:
    """Parse a SKILL.md file and extract frontmatter fields."""
    try:
        text = path.read_text()
    except OSError:
        return {
            "name": fallback_name,
            "type": "skill",
            "description": "",
            "triggers": None,
            "path": str(path),
        }

    # Parse YAML frontmatter
    fm = _parse_frontmatter(text)
    return {
        "name": fm.get("name", fallback_name),
        "type": "skill",
        "description": fm.get("description", ""),
        "triggers": fm.get("triggers"),
        "path": str(path),
    }


def _parse_frontmatter(text: str) -> dict:
    """Parse simple YAML frontmatter (between --- delimiters)."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    yaml_text = parts[1].strip()
    try:
        import yaml

        return yaml.safe_load(yaml_text) or {}
    except Exception:
        # Fallback: parse key: value lines manually
        result: dict = {}
        for line in yaml_text.split("\n"):
            if ":" in line and not line.startswith(" "):
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip()
        return result


# ---------------------------------------------------------------------------
# v1: full index, search, stats, cache
# ---------------------------------------------------------------------------


def full_index(
    bin_dir: Path | None = None,
    tools_dir: Path | None = None,
    receptors_dir: Path | None = None,
    use_cache: bool = True,
) -> list[dict]:
    """Return combined index of all capabilities (effectors, skills, MCP tools)."""
    if use_cache:
        cached = _load_cache()
        if cached is not None:
            return cached

    bd = bin_dir or _BIN_DIR
    td = tools_dir or _VIVESCA_TOOLS
    rd = receptors_dir or _RECEPTORS_DIR

    entries = _scan_effector_dir(bd) + _scan_skills(rd) + _scan_organelle_tools(td)

    if use_cache:
        _save_cache(entries)

    return entries


def search_index(
    query: str,
    index: list[dict] | None = None,
) -> list[dict]:
    """Search the index: exact name > name contains > description contains."""
    entries = index if index is not None else full_index()
    q = query.lower()

    exact: list[dict] = []
    name_match: list[dict] = []
    desc_match: list[dict] = []

    for e in entries:
        name = e.get("name", "").lower()
        desc = e.get("description", "").lower()
        if name == q:
            exact.append(e)
        elif q in name:
            name_match.append(e)
        elif q in desc:
            desc_match.append(e)

    return exact + name_match + desc_match


def get_stats(index: list[dict] | None = None) -> dict:
    """Return counts by type."""
    entries = index if index is not None else full_index()
    counts: dict[str, int] = {}
    for e in entries:
        t = e.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _cache_valid() -> bool:
    """Check whether the cache is still fresh."""
    if not _CACHE_PATH.exists():
        return False
    try:
        cache_mtime = _CACHE_PATH.stat().st_mtime
    except OSError:
        return False
    for d in (_BIN_DIR, _RECEPTORS_DIR):
        if d.exists():
            try:
                if d.stat().st_mtime > cache_mtime:
                    return False
            except OSError:
                return False
    return True


def _load_cache() -> list[dict] | None:
    """Load index from cache if valid, else return None."""
    if not _cache_valid():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text())
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _save_cache(entries: list[dict]) -> None:
    """Write index to cache file."""
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(entries, indent=2))
    except OSError:
        pass


def invalidate_cache() -> None:
    """Remove the cache file (used by --refresh)."""
    with contextlib.suppress(OSError):
        _CACHE_PATH.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# v1: markdown index (existing)
# ---------------------------------------------------------------------------


def express_effector_index(
    bin_dir: Path | None = None,
    tools_dir: Path | None = None,
    routing_path: Path | None = None,
) -> str:
    """Build a unified tool index from CLI binaries, MCP tools, and routing table."""
    bd = bin_dir or _BIN_DIR
    td = tools_dir or _VIVESCA_TOOLS
    rp = routing_path or _ROUTING_TABLE

    cli_tools = _scan_effector_dir(bd)
    mcp_tools = _scan_organelle_tools(td)

    lines: list[str] = []

    lines.append("# Tool Index\n")

    # Routing table (curated trigger→tool mapping)
    routing = _read_signal_routing(rp)
    if routing:
        lines.append(routing)
        lines.append("")

    # MCP tools (computed)
    lines.append(f"## MCP Tools ({len(mcp_tools)})\n")
    lines.append("| Tool | Domain | Description |")
    lines.append("|------|--------|-------------|")
    for t in mcp_tools:
        desc = t.get("description", "")[:80]
        lines.append(f"| `{t['name']}` | {t['source']} | {desc} |")

    # CLI tools (computed)
    lines.append(f"\n## CLI Tools ({len(cli_tools)})\n")
    lines.append("| Tool | Source |")
    lines.append("|------|--------|")
    for t in cli_tools:
        lines.append(f"| `{t['name']}` | {t['source']} |")

    total = len(cli_tools) + len(mcp_tools)
    lines.insert(1, f"_Total: {total} tools ({len(mcp_tools)} MCP, {len(cli_tools)} CLI)_\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# v2: analysis subcommands
# ---------------------------------------------------------------------------


def scan_untested(
    bin_dir: Path | None = None,
    assays_dir: Path | None = None,
) -> list[dict]:
    """Find effectors with no corresponding test file.

    Compares effector names against assays/test_<name>.py files.
    """
    bd = bin_dir or _BIN_DIR
    ad = assays_dir or _ASSAYS_DIR

    effectors = _scan_effector_dir(bd)

    # Collect covered names from test files
    covered: set[str] = set()
    if ad.exists():
        for tf in ad.glob("test_*.py"):
            name = tf.stem[len("test_") :]
            covered.add(name)

    uncovered: list[dict] = []
    for e in effectors:
        if e["name"] not in covered:
            uncovered.append(
                {
                    "name": e["name"],
                    "path": e.get("path", ""),
                    "has_test": False,
                }
            )
    return uncovered


def scan_stale(
    days: int = 90,
    bin_dir: Path | None = None,
    receptors_dir: Path | None = None,
) -> list[dict]:
    """Find capabilities not touched in the last N days.

    Checks git log for each file. Returns entries sorted stalest-first.
    """
    bd = bin_dir or _BIN_DIR
    rd = receptors_dir or _RECEPTORS_DIR

    entries: list[dict] = []

    # Check effectors
    if bd.exists():
        for f in sorted(bd.iterdir()):
            if f.name.startswith(".") or f.name.startswith("_"):
                continue
            if not f.is_file() or not os.access(f, os.X_OK):
                continue
            last_date = _git_last_modified(f)
            if last_date is None:
                continue
            days_since = (datetime.now(UTC) - last_date).days
            if days_since > days:
                entries.append(
                    {
                        "name": f.name,
                        "type": "effector",
                        "last_modified": last_date.isoformat(),
                        "days_since": days_since,
                    }
                )

    # Check skills
    if rd.exists():
        for skill_dir in sorted(rd.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            last_date = _git_last_modified(skill_md)
            if last_date is None:
                continue
            days_since = (datetime.now(UTC) - last_date).days
            if days_since > days:
                entries.append(
                    {
                        "name": skill_dir.name,
                        "type": "skill",
                        "last_modified": last_date.isoformat(),
                        "days_since": days_since,
                    }
                )

    # Sort by stalest first
    entries.sort(key=lambda e: e["days_since"], reverse=True)
    return entries


def _git_last_modified(path: Path) -> datetime | None:
    """Get the date of the last commit touching a file."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", str(path)],
            capture_output=True,
            text=True,
            cwd=str(VIVESCA_ROOT),
            timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        # Parse git date format: "2025-01-15 10:30:00 +0800"
        date_str = result.stdout.strip()
        # Handle various git date formats
        for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(date_str[:25], fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except ValueError:
                continue
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def scan_deps(
    name: str,
    bin_dir: Path | None = None,
) -> dict:
    """Show what an effector imports or calls.

    For Python: parse import statements and subprocess calls.
    For shell: grep for other effector names.
    """
    bd = bin_dir or _BIN_DIR
    target = bd / name

    if not target.exists():
        return {"name": name, "imports": [], "calls": [], "error": "not found"}

    try:
        text = target.read_text(errors="replace")
    except OSError:
        return {"name": name, "imports": [], "calls": [], "error": "unreadable"}

    # Determine type
    is_python = target.suffix == ".py" or (
        text.startswith("#!") and "python" in text.split("\n")[0]
    )

    if is_python:
        return _parse_python_deps(name, text, bd)
    else:
        return _parse_shell_deps(name, text, bd)


def _parse_python_deps(name: str, text: str, bin_dir: Path) -> dict:
    """Parse import statements and subprocess calls from Python source."""
    imports: list[str] = []
    calls: list[str] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"name": name, "imports": [], "calls": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, ast.Call):
            # Check for subprocess.run/call/Popen with string args
            func = node.func
            func_name = None
            if isinstance(func, ast.Attribute):
                func_name = func.attr
            elif isinstance(func, ast.Name):
                func_name = func.id
            if func_name in ("run", "call", "Popen", "check_output", "check_call"):
                for arg in node.args:
                    if isinstance(arg, (ast.List, ast.Tuple)):
                        for elt in arg.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                calls.append(elt.value)

    return {"name": name, "imports": imports, "calls": calls}


def _parse_shell_deps(name: str, text: str, bin_dir: Path) -> dict:
    """Grep for other effector names being called in shell scripts."""
    imports: list[str] = []
    calls: list[str] = []

    # Get all effector names for cross-referencing
    effector_names = set()
    if bin_dir.exists():
        for f in bin_dir.iterdir():
            if f.is_file() and os.access(f, os.X_OK) and not f.name.startswith("."):
                effector_names.add(f.name)

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for eff_name in effector_names:
            if eff_name == name:
                continue
            # Look for effector name as a command
            pattern = re.compile(r"\b" + re.escape(eff_name) + r"\b")
            if pattern.search(stripped):
                calls.append(eff_name)

    # Deduplicate calls
    seen: set[str] = set()
    unique_calls: list[str] = []
    for c in calls:
        if c not in seen:
            seen.add(c)
            unique_calls.append(c)

    return {"name": name, "imports": imports, "calls": unique_calls}


def scan_hooks(
    cytoskeleton_dir: Path | None = None,
) -> list[dict]:
    """Inventory all hook functions from cytoskeleton modules.

    Parses synapse.py, axon.py, and dendrite.py.
    """
    cd = cytoskeleton_dir or _CYTOSKELETON_DIR
    results: list[dict] = []

    hook_files = ["synapse.py", "axon.py", "dendrite.py"]
    for hf in hook_files:
        path = cd / hf
        if not path.exists():
            continue
        functions = _extract_hook_functions(path)
        if functions:
            results.append(
                {
                    "hook_file": hf,
                    "functions": functions,
                }
            )

    return results


def _extract_hook_functions(path: Path) -> list[dict]:
    """Extract function names and docstrings from a hook file."""
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        return []

    functions: list[dict] = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue
        doc = ast.get_docstring(node) or ""
        first_line = doc.split("\n")[0].strip() if doc else ""
        # Determine trigger type from the file
        trigger_type = _classify_hook_function(node.name, path.name)
        functions.append(
            {
                "name": node.name,
                "description": first_line,
                "trigger_type": trigger_type,
            }
        )
    return functions


def _classify_hook_function(func_name: str, file_name: str) -> str:
    """Classify a hook function by its trigger type based on naming and file."""
    # File-based classification
    if file_name == "synapse.py":
        return "UserPromptSubmit"
    if file_name == "axon.py":
        return "PreToolUse"
    if file_name == "dendrite.py":
        return "PostToolUse"
    return "unknown"
