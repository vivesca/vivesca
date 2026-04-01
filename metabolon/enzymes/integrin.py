from __future__ import annotations

from metabolon.locus import (
    chromatin,
    receptors,
    phenotype_md,
    PLATFORM_SYMLINKS,
    PLATFORM_MARKERS_CONFIRM,
    PLATFORM_MARKERS_REQUIRED,
)

"""integrin -- attachment integrity probe.

Biology: integrins are transmembrane receptors that connect a cell's
internal cytoskeleton to the extracellular matrix. They:
  - Probe bidirectionally (inside-out: is the cell ready to bind?
    outside-in: does the attachment point exist and respond?)
  - Cluster into focal adhesions -- shared attachment points where
    failure is catastrophic (many cells lose grip at once)
  - Exist in activation states -- bent (dormant), extended (recently
    tested), open (actively engaged)
  - Trigger anoikis (programmed death) when all attachments are lost
  - Sense stiffness by pulling (mechanotransduction) -- passive
    existence checks miss broken internals

Each concept maps to a design feature in this tool.

Tools:
  integrin_probe           -- full attachment integrity scan
  integrin_apoptosis_check -- nightly stay-alive signal for dormant receptors
  integrin_colony_probe    -- reference integrity across colonies, buds, skills
"""

import filecmp
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import VIVESCA_ROOT
from metabolon.morphology import Secretion

SKILLS_DIR = receptors
SKILL_USAGE_LOG = Path.home() / ".claude" / "skill-usage.tsv"
RECEPTOR_RETIREMENT_LOG = chromatin / "receptor-retirement.md"

# Shell builtins and ubiquitous utilities -- always resolvable
BUILTINS = frozenset(
    {
        "echo",
        "cd",
        "export",
        "if",
        "then",
        "else",
        "fi",
        "for",
        "do",
        "done",
        "while",
        "case",
        "esac",
        "set",
        "unset",
        "source",
        "true",
        "false",
        "exit",
        "return",
        "read",
        "shift",
        "local",
        "declare",
        "eval",
        "exec",
        "cat",
        "head",
        "tail",
        "grep",
        "rg",
        "ls",
        "mkdir",
        "cp",
        "mv",
        "rm",
        "chmod",
        "chown",
        "sleep",
        "wait",
        "kill",
        "test",
        "sed",
        "awk",
        "curl",
        "wget",
        "pip",
        "npm",
        "brew",
        "git",
        "python",
        "python3",
        "node",
        "ruby",
        "uv",
        "cargo",
    }
)

CMD_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

# Known platform config dirs to ignore in new-platform detection
_KNOWN_PLATFORM_DIRS = {p.parent.name for p in PLATFORM_SYMLINKS if p.parent != Path.home()}
_KNOWN_PLATFORM_DIRS.add(".claude")  # ~/.claude is known but symlink lives at ~/CLAUDE.md


def _check_phenotype_symlinks() -> tuple[list[dict], list[str]]:
    """Check platform phenotype symlinks and detect unknown CLI platforms.

    Returns (issues, unknown_platforms).
    issues: list of {path, problem} for known symlinks.
    unknown_platforms: list of dir names that look like CLI platforms but aren't registered.
    """
    issues: list[dict] = []
    for symlink_path in PLATFORM_SYMLINKS:
        if not symlink_path.exists():
            issues.append({"path": str(symlink_path), "problem": "missing"})
        elif not symlink_path.is_symlink():
            issues.append({"path": str(symlink_path), "problem": "not_symlink"})
        elif symlink_path.resolve() != phenotype_md.resolve():
            issues.append({
                "path": str(symlink_path),
                "problem": f"wrong_target:{symlink_path.resolve()}",
            })

    # Detect unknown CLI platform dirs
    unknown: list[str] = []
    for entry in sorted(Path.home().iterdir()):
        if not entry.name.startswith(".") or not entry.is_dir():
            continue
        if entry.name in _KNOWN_PLATFORM_DIRS:
            continue
        try:
            has_marker = (entry / PLATFORM_MARKERS_REQUIRED).exists()
        except PermissionError:
            continue
        if not has_marker:
            continue
        try:
            has_confirm = any((entry / m).exists() for m in PLATFORM_MARKERS_CONFIRM)
        except PermissionError:
            continue
        if has_confirm:
            unknown.append(entry.name)

    return issues, unknown


_LAUNCHAGENTS_DIR = Path.home() / "Library" / "LaunchAgents"


def _check_launchagent_paths() -> list[dict]:
    """Verify ProgramArguments paths in LaunchAgent plists resolve.

    Returns list of {plist, path, problem} for broken references.
    """
    import plistlib

    broken: list[dict] = []
    if not _LAUNCHAGENTS_DIR.is_dir():
        return broken

    for plist_file in sorted(_LAUNCHAGENTS_DIR.iterdir()):
        if plist_file.suffix != ".plist":
            continue
        # Resolve symlinks to read actual content
        real_path = plist_file.resolve() if plist_file.is_symlink() else plist_file
        try:
            with open(real_path, "rb") as fh:
                plist = plistlib.load(fh)
        except Exception:
            broken.append({
                "plist": plist_file.name,
                "path": str(real_path),
                "problem": "unreadable",
            })
            continue

        prog_args = plist.get("ProgramArguments", [])
        for arg in prog_args:
            if not isinstance(arg, str):
                continue
            # Only check clean absolute paths and ~/paths
            expanded = arg.replace("~", str(Path.home())) if arg.startswith("~") else arg
            if not expanded.startswith("/"):
                continue
            # Skip system paths, flags, and compound commands
            if expanded.startswith(("/usr/", "/bin/", "/opt/homebrew/", "/Applications/")):
                continue
            if " && " in expanded or " || " in expanded or " " in arg.split("/")[-1]:
                continue
            if not Path(expanded).exists():
                broken.append({
                    "plist": plist_file.name,
                    "path": arg,
                    "problem": "missing",
                })

    return broken


_ORGANELLES_DIR = VIVESCA_ROOT / "metabolon" / "organelles"
_ENZYMES_DIR = VIVESCA_ROOT / "metabolon" / "enzymes"
_ASSAYS_DIR = VIVESCA_ROOT / "assays"


def _check_untested_code() -> list[dict]:
    """Find organelles and enzymes without corresponding test files.

    Returns list of {module, expected_test, problem} for untested code.
    """
    untested: list[dict] = []
    for code_dir in (_ORGANELLES_DIR, _ENZYMES_DIR):
        if not code_dir.is_dir():
            continue
        for py_file in sorted(code_dir.glob("*.py")):
            if py_file.name.startswith(("_", "test_", ".")):
                continue
            module_name = py_file.stem
            expected_test = _ASSAYS_DIR / f"test_{module_name}.py"
            if not expected_test.exists():
                untested.append({
                    "module": f"{code_dir.name}/{py_file.name}",
                    "expected_test": f"assays/test_{module_name}.py",
                    "problem": "missing",
                })
    return untested


# Match paths inside backticks (preserves spaces) or bare paths
_SKILL_PATH_BACKTICK_RE = re.compile(r"`((?:/Users/\w+|~/)[^`]+)`")
_SKILL_PATH_BARE_RE = re.compile(r"(?:^|\s)((?:/Users/\w+|~/)[a-zA-Z][^\s`\"'>]*)")
_SKIP_FRAGMENTS = frozenset(("YYYY", "*", "/tmp/", "{", "$(", "example", "<"))


def _check_skill_paths() -> list[dict]:
    """Verify hardcoded ~/paths in SKILL.md files resolve.

    Returns list of {skill, path, problem} for broken references.
    Skips template paths, globs, placeholders, and ephemeral dirs.
    """
    broken: list[dict] = []
    if not SKILLS_DIR.is_dir():
        return broken

    home_str = str(Path.home())

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue

        content = skill_file.read_text()
        # Prefer backtick-wrapped paths (preserve spaces), fall back to bare
        paths_found = _SKILL_PATH_BACKTICK_RE.findall(content)
        paths_found += _SKILL_PATH_BARE_RE.findall(content)
        seen: set[str] = set()
        for raw_path in paths_found:
            cleaned = raw_path.rstrip(".,;:)>|`\"'")
            if cleaned in seen or len(cleaned) < 8:
                continue
            seen.add(cleaned)
            if any(skip in cleaned for skip in _SKIP_FRAGMENTS):
                continue
            expanded = cleaned.replace("~", home_str, 1) if cleaned.startswith("~") else cleaned
            if not Path(expanded).exists():
                # Check if it's a space-truncated path (parent exists, sibling starts with basename)
                exp_path = Path(expanded)
                parent = exp_path.parent
                basename = exp_path.name
                if parent.is_dir() and any(
                    child.name.startswith(basename) for child in parent.iterdir()
                ):
                    continue  # Truncation artifact, not a real break
                broken.append({
                    "skill": skill_dir.name,
                    "path": cleaned,
                    "problem": "missing",
                })

    return broken


# -- Result schema --------------------------------------------------------


class IntegrinResult(Secretion):
    """Full probe results -- mirrors integrin biology at each level."""

    total_receptors: int
    total_references: int
    attached: int

    # Outside-in: does the binary exist on PATH?
    detached: list[dict]

    # Mechanotransduction: does the binary respond to --help?
    # (passive existence != functional -- pull to test stiffness)
    mechanically_silent: list[dict]

    # Focal adhesions: binaries referenced by multiple receptors.
    # A focal adhesion failure detaches many cells at once.
    focal_adhesions: list[dict]

    # Anoikis candidates: receptors where ALL references are broken.
    # Total detachment triggers programmed death -- flag for retirement.
    anoikis: list[str]

    # Activation state: bent (dormant >30d), extended (7-30d), open (<7d).
    # Dormant receptors accumulate silent drift.
    activation_state: list[dict]

    # Inside-out: does the receptor's expectation match the binary's
    # actual interface? (Not yet implemented -- needs --help parsing.)

    # Adhesion dependence: receptors sorted by ligand count
    adhesion_dependence: list[dict]

    # Phenotype: platform entry point symlinks
    phenotype_issues: list[dict]
    unknown_platforms: list[str]

    # LaunchAgent: broken paths in plist ProgramArguments
    launchagent_broken: list[dict]

    # Skill paths: hardcoded paths in SKILL.md that don't resolve
    skill_path_broken: list[dict]

    # Untested code: organelles/enzymes without assay files
    untested_code: list[dict]


class ApoptosisResult(Secretion):
    """Stay-alive signal output for dormant receptors.

    Biology: apoptosis is programmed cell death. Receptors that are
    both conformationally bent (long unused) AND have lost all ligand
    attachments have no survival signal -- they are anoikis candidates
    flagged for retirement. Receptors that are bent but still have
    healthy ligands are merely quiescent -- alive but idle.

    This check runs nightly, logs anoikis candidates to the retirement
    ledger, and emits a population summary so the organism knows the
    health of its receptor field.
    """

    open_count: int
    extended_count: int
    bent_count: int
    anoikis_candidate_count: int

    # Bent receptors whose ligands are ALL detached -- retirement candidates
    anoikis_candidates: list[str]

    # Bent receptors that still have at least one healthy ligand -- quiescent
    quiescent: list[str]

    # Extended receptors (7-30 days) -- noted only, no action
    extended: list[str]

    # Whether anoikis candidates were written to the retirement log
    retirement_log_updated: bool

    summary: str


# -- Extraction -----------------------------------------------------------


def _extract_bash_commands(text: str) -> list[str]:
    """Extract first-word commands from explicitly-tagged bash code blocks."""
    results = []
    in_block = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                in_block = False
            else:
                lang = stripped.lstrip("`").strip().lower()
                in_block = lang in ("bash", "shell", "sh")
            continue

        if in_block and stripped and not stripped.startswith("#"):
            cmd = stripped.split()[0]
            if "=" in cmd and not cmd.startswith("-"):
                parts = stripped.split()
                for part in parts[1:]:
                    if "=" not in part:
                        cmd = part
                        break
                else:
                    continue
            results.append(cmd)

    return results


def _is_real_command(cmd: str) -> bool:
    """Filter: does this look like a CLI binary name?"""
    if cmd in BUILTINS:
        return False
    if not CMD_RE.match(cmd):
        return False
    return len(cmd) > 2


# -- Mechanotransduction: active probing ----------------------------------
# Integrins don't just check if the matrix exists -- they pull on it
# and read the response. A binary on PATH might segfault, hang, or
# be the wrong version. --help is the gentlest pull.


def _probe_responsiveness(binary: str) -> bool:
    """Pull on the binary (--help) and check if it responds.

    Mechanotransduction: the cell actively tests stiffness by pulling,
    not just by touching. A binary that exists but doesn't respond to
    --help is like soft matrix -- present but not load-bearing.
    """
    path = shutil.which(binary)
    if not path:
        return False
    try:
        result = subprocess.run(
            [path, "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Any output (stdout or stderr) counts as responsive.
        # Many CLIs print help to stderr. Exit code 0 or 1 both OK.
        return bool(result.stdout.strip() or result.stderr.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


# -- Activation state (affinity log) --------------------------------------


def _read_skill_usage() -> dict[str, datetime]:
    """Read last invocation time per receptor from affinity log."""
    last_used: dict[str, datetime] = {}
    if not SKILL_USAGE_LOG.exists():
        return last_used
    try:
        for line in SKILL_USAGE_LOG.read_text().strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    ts = datetime.fromisoformat(parts[0])
                    receptor = parts[1].strip()
                    if receptor and (receptor not in last_used or ts > last_used[receptor]):
                        last_used[receptor] = ts
                except ValueError:
                    pass
    except OSError:
        pass
    return last_used


# -- Main probe -----------------------------------------------------------


def _run_probe() -> IntegrinResult:
    """Probe all receptor attachment points for integrity.

    Six layers of checking, each inspired by integrin biology:
    1. Outside-in signaling: does the binary resolve on PATH?
    2. Mechanotransduction: does it respond to --help? (active pull)
    3. Focal adhesions: which binaries are shared load-bearing points?
    4. Anoikis: which receptors have lost ALL attachments?
    5. Fragility: which receptors have the most dependencies?
    6. Activation state: bent (dormant), extended (recent), open (active)
    """
    # Layer 0 -- Phenotype, LaunchAgents, skill paths
    phenotype_issues, unknown_platforms = _check_phenotype_symlinks()
    launchagent_broken = _check_launchagent_paths()
    skill_path_broken = _check_skill_paths()
    untested_code = _check_untested_code()

    if not SKILLS_DIR.is_dir():
        return IntegrinResult(
            total_receptors=0,
            total_references=0,
            attached=0,
            detached=[],
            mechanically_silent=[],
            focal_adhesions=[],
            anoikis=[],
            activation_state=[],
            adhesion_dependence=[],
            phenotype_issues=phenotype_issues,
            unknown_platforms=unknown_platforms,
            launchagent_broken=launchagent_broken,
            skill_path_broken=skill_path_broken,
            untested_code=untested_code,
        )

    all_refs: list[dict] = []
    receptor_deps: dict[str, set[str]] = {}
    binary_consumers: Counter[str] = Counter()

    for receptor_dir in sorted(SKILLS_DIR.iterdir()):
        receptor_file = receptor_dir / "SKILL.md"
        if not receptor_file.is_file():
            continue

        receptor_name = receptor_dir.name
        commands = _extract_bash_commands(receptor_file.read_text())

        seen: set[str] = set()
        for cmd in commands:
            if not _is_real_command(cmd) or cmd in seen:
                continue
            seen.add(cmd)

            found = shutil.which(cmd) is not None
            all_refs.append({"receptor": receptor_name, "binary": cmd, "found": found})
            binary_consumers[cmd] += 1

        if seen:
            receptor_deps[receptor_name] = seen

    # Layer 1 -- Outside-in: PATH resolution
    detached = [r for r in all_refs if not r["found"]]

    # Layer 2 -- Mechanotransduction: active pull on found binaries
    # Only probe binaries that resolved -- detached ones already failed layer 1
    found_binaries = {r["binary"] for r in all_refs if r["found"]}
    mechanically_silent = []
    for binary in sorted(found_binaries):
        if not _probe_responsiveness(binary):
            bound_receptors = [r["receptor"] for r in all_refs if r["binary"] == binary]
            mechanically_silent.append({"binary": binary, "receptors": bound_receptors})

    # Layer 3 -- Focal adhesions: shared ligands
    # In biology, integrins cluster into focal adhesion complexes.
    # A single binary referenced by many receptors is a focal adhesion --
    # if it detaches, multiple receptors lose grip simultaneously.
    focal_adhesions = [
        {
            "binary": b,
            "valency": valency,
            "receptors": [r["receptor"] for r in all_refs if r["binary"] == b],
        }
        for b, valency in binary_consumers.most_common()
        if valency >= 2
    ]

    # Layer 4 -- Anoikis: receptors with zero surviving attachments
    # When ALL integrins lose their matrix attachment, the cell triggers
    # programmed death. Receptors where every ligand is detached should
    # be flagged for retirement, not just repair.
    detached_set = {(r["receptor"], r["binary"]) for r in detached}
    anoikis = []
    for receptor_name, ligands in receptor_deps.items():
        if all((receptor_name, lig) in detached_set for lig in ligands):
            anoikis.append(receptor_name)

    # Layer 5 -- Adhesion dependence: receptors sorted by ligand count
    adhesion_dependence = sorted(
        [{"receptor": s, "ligands": len(d)} for s, d in receptor_deps.items()],
        key=lambda x: x["ligands"],
        reverse=True,
    )

    # Layer 6 -- Activation state: bent/extended/open
    # Integrins exist in conformational states. Bent = dormant (never or
    # rarely used). Extended = recently tested. Open = actively engaged.
    # Receptors that stay bent accumulate silent drift -- their references
    # rot without anyone noticing because nobody invokes them.
    now = datetime.now()
    usage = _read_skill_usage()
    activation_state = []
    for receptor_dir in sorted(SKILLS_DIR.iterdir()):
        receptor_file = receptor_dir / "SKILL.md"
        if not receptor_file.is_file():
            continue
        receptor_name = receptor_dir.name
        last = usage.get(receptor_name)
        if last is None:
            state = "bent"
            days = None
        else:
            days_ago = (now - last).days
            if days_ago <= 7:
                state = "open"
            elif days_ago <= 30:
                state = "extended"
            else:
                state = "bent"
            days = days_ago
        activation_state.append(
            {"receptor": receptor_name, "state": state, "days_since_use": days}
        )

    attached = sum(1 for r in all_refs if r["found"])

    return IntegrinResult(
        total_receptors=len(receptor_deps),
        total_references=len(all_refs),
        attached=attached,
        detached=[{"receptor": r["receptor"], "binary": r["binary"]} for r in detached],
        mechanically_silent=mechanically_silent,
        focal_adhesions=focal_adhesions,
        anoikis=anoikis,
        activation_state=activation_state,
        adhesion_dependence=adhesion_dependence[:10],
        phenotype_issues=phenotype_issues,
        unknown_platforms=unknown_platforms,
        launchagent_broken=launchagent_broken,
        skill_path_broken=skill_path_broken,
        untested_code=untested_code,
    )


# -- Apoptosis check: stay-alive signal for dormant receptors -------------


def _log_anoikis_candidates(
    candidates: list[str],
    retirement_log: Path = RECEPTOR_RETIREMENT_LOG,
) -> bool:
    """Append anoikis candidates to the retirement ledger.

    Biology: when a cell receives no survival signal (no integrin-matrix
    contact, no growth factors), it initiates apoptosis. We log the
    candidate list as a structured entry so the organism can decide
    whether to retire or rehabilitate each receptor.

    Returns True if the log was written, False on error.
    """
    if not candidates:
        return False

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d")
    lines = [
        f"\n## {timestamp} -- anoikis candidates\n",
        "_Receptors: bent conformation (>30d unused) + all ligands detached._\n",
    ]
    for receptor in sorted(candidates):
        lines.append(f"- {receptor}\n")

    try:
        retirement_log.parent.mkdir(parents=True, exist_ok=True)
        with retirement_log.open("a") as fh:
            fh.writelines(lines)
        return True
    except OSError:
        return False


def _run_apoptosis_check() -> ApoptosisResult:
    """Emit stay-alive signal for all receptors; log retirement candidates.

    Reads activation_state from integrin_probe, then cross-references
    with anoikis data (all ligands detached) to separate:

    - Bent + all-ligands-detached  → anoikis candidate → log for retirement
    - Bent + ligands healthy       → quiescent → report only
    - Extended (7-30d)             → note only
    - Open (<7d)                   → healthy, no action

    Anoikis candidates are appended to ~/epigenome/chromatin/receptor-retirement.md
    with a datestamp so the organism maintains a longitudinal record.
    """
    probe = _run_probe()

    # Index activation states by receptor name
    state_by_receptor: dict[str, str] = {
        entry["receptor"]: entry["state"] for entry in probe.activation_state
    }

    # Anoikis set from the full probe (all ligands detached)
    anoikis_set: set[str] = set(probe.anoikis)

    open_receptors: list[str] = []
    extended_receptors: list[str] = []
    bent_anoikis: list[str] = []
    bent_quiescent: list[str] = []

    for receptor, state in sorted(state_by_receptor.items()):
        if state == "open":
            open_receptors.append(receptor)
        elif state == "extended":
            extended_receptors.append(receptor)
        elif state == "bent":
            if receptor in anoikis_set:
                # No survival signal on any axis -- retirement candidate
                bent_anoikis.append(receptor)
            else:
                # Ligands still present -- merely quiescent
                bent_quiescent.append(receptor)

    retirement_written = _log_anoikis_candidates(
        bent_anoikis, retirement_log=RECEPTOR_RETIREMENT_LOG
    )

    # Build human-readable summary
    parts = [
        f"{len(open_receptors)} open",
        f"{len(extended_receptors)} extended",
        f"{len(bent_quiescent) + len(bent_anoikis)} bent ({len(bent_anoikis)} anoikis candidates)",
    ]
    summary = " | ".join(parts)
    if bent_anoikis:
        summary += f"\nAnoikis candidates logged to {RECEPTOR_RETIREMENT_LOG}"

    return ApoptosisResult(
        open_count=len(open_receptors),
        extended_count=len(extended_receptors),
        bent_count=len(bent_quiescent) + len(bent_anoikis),
        anoikis_candidate_count=len(bent_anoikis),
        anoikis_candidates=sorted(bent_anoikis),
        quiescent=sorted(bent_quiescent),
        extended=sorted(extended_receptors),
        retirement_log_updated=retirement_written,
        summary=summary,
    )


# -- Colony probe: reference integrity across the full dependency web --------
#
# Biology: gap junctions are direct cytoplasmic channels between cells that
# allow small molecules and signals to pass without crossing a membrane.
# A colony is a tissue -- cells (buds) that communicate through gap junctions
# to coordinate a shared response. If the junction is broken (missing bud,
# missing skill, broken tool), signaling fails silently. This probe
# systematically tests every junction in the tissue.
#
# The dependency web:
#   Colony → Bud → Skill → Skill (cross-ref)
#                         → MCP Tool → MCP Tool (chain) → CLI binary
#                → MCP Tool → CLI binary
#                → CLI binary


COLONIES_DIR = VIVESCA_ROOT / "membrane" / "colonies"
BUDS_DIR = VIVESCA_ROOT / "membrane" / "buds"
TOOLS_DIR = VIVESCA_ROOT / "metabolon" / "enzymes"

# YAML frontmatter parser (minimal -- no external deps)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_YAML_LIST_RE = re.compile(r"\[([^\]]*)\]")
_YAML_SCALAR_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'|([^\s,\'"]+)')

# Pattern: worker name followed by "bud" in colony body
# e.g. "- **financial-audit**: invoke financial-audit bud"
_BUD_REF_RE = re.compile(r"invoke\s+([\w-]+)\s+bud", re.IGNORECASE)

# Pattern: /skillname at start of token (skill invocation syntax).
# Negative lookbehind for /, \w, and ~ to avoid matching path components
# like ~/epigenome/chromatin, /tmp, /usr, /var, etc.
_SKILL_REF_RE = re.compile(r"(?<![/\w~])/([a-z][a-z0-9_-]+)")

# Common path components that are NOT skill names -- used as a deny-list
# to avoid false positives from filesystem paths in skill/colony body text.
_PATH_COMPONENTS = frozenset(
    {
        "tmp",
        "var",
        "usr",
        "opt",
        "etc",
        "home",
        "bin",
        "lib",
        "sbin",
        "dev",
        "sys",
        "proc",
        "run",
        "srv",
        "mnt",
        "media",
        "boot",
        "notes",
        "docs",
        "code",
        "scripts",
        "format",
        "Users",
        "Library",
        # common project sub-dirs and output paths used in vivesca skills
        "brief",
        "findings",
        "eow",
        "clear",
        "thesis",
        "askesis",
        "epigenome",
    }
)

# Pattern: mcp__vivesca__toolname
_MCP_FULL_RE = re.compile(r"mcp__vivesca__([a-z][a-z0-9_]+)")

# Pattern: bare tool name in backtick or inline code context
# Matches `toolname` where toolname ends in _something (snake_case MCP convention)
_MCP_BARE_RE = re.compile(r"`([a-z][a-z0-9]+(?:_[a-z0-9]+)+)`")

# Pattern: tool function imports across metabolon.enzymes modules
_TOOL_IMPORT_RE = re.compile(r"from\s+metabolon\.enzymes\.(\w+)\s+import\s+([^\n]+)")


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract key-value pairs from YAML frontmatter block."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    result: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        # List value?
        lm = _YAML_LIST_RE.match(val)
        if lm:
            items = [
                m2.group(1) or m2.group(2) or m2.group(3)
                for m2 in _YAML_SCALAR_RE.finditer(lm.group(1))
                if any(m2.groups())
            ]
            result[key] = [i for i in items if i]
        else:
            # Scalar -- strip quotes
            sv = _YAML_SCALAR_RE.match(val)
            if sv:
                result[key] = sv.group(1) or sv.group(2) or sv.group(3) or ""
            else:
                result[key] = val
    return result


def _strip_frontmatter(text: str) -> str:
    """Return body text with frontmatter removed."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def _collect_receptor_names(skills_dir: Path) -> frozenset[str]:
    """Return the set of all receptor (skill) directory names."""
    if not skills_dir.is_dir():
        return frozenset()
    return frozenset(
        d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )


def _collect_bud_names(buds_dir: Path) -> frozenset[str]:
    """Return the set of all bud names (stem of .md files)."""
    if not buds_dir.is_dir():
        return frozenset()
    return frozenset(f.stem for f in buds_dir.iterdir() if f.suffix == ".md")


def _collect_registered_tool_names(tools_dir: Path) -> frozenset[str]:
    """Scan metabolon/enzymes/*.py for @tool(name=...) registrations.

    Returns the set of registered MCP tool names.
    """
    tool_name_re = re.compile(r'@tool\s*\([^)]*name\s*=\s*["\']([^"\']+)["\']')
    names: set[str] = set()
    if not tools_dir.is_dir():
        return frozenset()
    for py_file in tools_dir.glob("*.py"):
        try:
            source = py_file.read_text()
        except OSError:
            continue
        for m in tool_name_re.finditer(source):
            names.add(m.group(1))
    return frozenset(names)


def _extract_colony_bud_refs(colony_text: str) -> list[str]:
    """Extract explicit bud references from a colony body.

    Only grabs names that appear in the 'invoke X bud' pattern --
    generic role names (researcher, drafter) are not bud references.
    """
    return _BUD_REF_RE.findall(_strip_frontmatter(colony_text))


def _extract_colony_skill_refs(colony_text: str) -> list[str]:
    """Extract /skillname references from a colony body.

    Filters out common filesystem path components (notes, tmp, docs, etc.)
    to avoid false positives from path strings in body text.
    """
    return [
        name
        for name in _SKILL_REF_RE.findall(_strip_frontmatter(colony_text))
        if name not in _PATH_COMPONENTS
    ]


def _extract_bud_skill_refs(bud_text: str) -> list[str]:
    """Extract skills listed in bud frontmatter."""
    fm = _parse_frontmatter(bud_text)
    raw = fm.get("skills", [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        return [raw] if raw else []
    return []


def _extract_bud_mcp_tool_refs(bud_text: str) -> list[str]:
    """Extract MCP tool references from a bud body (mcp__ and bare snake_case)."""
    body = _strip_frontmatter(bud_text)
    found: set[str] = set()
    # mcp__vivesca__toolname -> toolname
    for m in _MCP_FULL_RE.finditer(body):
        found.add(m.group(1))
    # `bare_tool_name` in backticks -- only snake_case with underscore
    for m in _MCP_BARE_RE.finditer(body):
        found.add(m.group(1))
    return sorted(found)


def _extract_bud_cli_refs(bud_text: str) -> list[str]:
    """Extract CLI binary references from bud bash code blocks."""
    cmds = _extract_bash_commands(_strip_frontmatter(bud_text))
    return [c for c in cmds if _is_real_command(c)]


def _extract_skill_skill_refs(skill_text: str) -> list[str]:
    """Extract /skillname cross-references from a SKILL.md body.

    Filters out common filesystem path components to avoid false positives
    from path strings like ~/epigenome/chromatin/..., /tmp/..., /docs/ in body text.
    """
    return [
        name
        for name in _SKILL_REF_RE.findall(_strip_frontmatter(skill_text))
        if name not in _PATH_COMPONENTS
    ]


def _extract_skill_mcp_tool_refs(skill_text: str) -> list[str]:
    """Extract MCP tool references from a SKILL.md body."""
    body = _strip_frontmatter(skill_text)
    found: set[str] = set()
    for m in _MCP_FULL_RE.finditer(body):
        found.add(m.group(1))
    for m in _MCP_BARE_RE.finditer(body):
        found.add(m.group(1))
    return sorted(found)


def _extract_tool_cross_imports(tools_dir: Path) -> list[dict]:
    """Scan metabolon/enzymes/*.py for cross-tool function imports.

    Returns list of {source_tool, target_tool, symbol} for ALL imports where
    one tool module references another tool module by name. Broken imports
    (target module missing) and valid imports are both included -- the caller
    filters for broken ones.
    """
    edges: list[dict] = []
    if not tools_dir.is_dir():
        return edges
    for py_file in sorted(tools_dir.glob("*.py")):
        if py_file.stem == "__init__":
            continue
        try:
            source = py_file.read_text()
        except OSError:
            continue
        for m in _TOOL_IMPORT_RE.finditer(source):
            target_module = m.group(1)
            if target_module == py_file.stem:
                # self-import -- skip
                continue
            symbols = [s.strip() for s in m.group(2).split(",") if s.strip()]
            for sym in symbols:
                edges.append(
                    {
                        "source_tool": py_file.stem,
                        "target_tool": target_module,
                        "symbol": sym,
                    }
                )
    return edges


class ColonyProbeResult(Secretion):
    """Reference integrity scan across the full colony-bud-skill-tool web.

    Biology: gap junctions are direct cytoplasmic channels between cells
    in a tissue. This probe tests every junction in the colony tissue --
    if a bud is missing, the colony's gap junction is broken; if a skill
    is missing, the bud's metabolic pathway is severed.
    """

    # Population counts
    colony_count: int
    bud_count: int
    skill_count: int
    registered_tool_count: int

    # Layer 1: Colony → Bud (explicit 'invoke X bud' references)
    detached_colony_bud_refs: list[dict]  # [{colony, missing_bud}]

    # Layer 2: Colony → Skill (/skillname references in colony body)
    detached_colony_skill_refs: list[dict]  # [{colony, missing_skill}]

    # Layer 3: Bud → Skill (frontmatter skills: [...])
    detached_bud_skill_refs: list[dict]  # [{bud, missing_skill}]

    # Layer 4: Bud → MCP Tool (mcp__ or bare snake_case in body)
    detached_bud_tool_refs: list[dict]  # [{bud, missing_tool}]

    # Layer 5: Bud → CLI binary (bash code blocks)
    detached_bud_cli_refs: list[dict]  # [{bud, missing_binary}]

    # Layer 6: Skill → Skill (/skillname cross-references in SKILL.md)
    detached_skill_skill_refs: list[dict]  # [{skill, missing_skill}]

    # Layer 7: Skill → MCP Tool (mcp__ or bare in SKILL.md)
    detached_skill_tool_refs: list[dict]  # [{skill, missing_tool}]

    # Layer 8: MCP Tool → MCP Tool (cross-tool imports in src/metabolon/enzymes/)
    detached_tool_tool_refs: list[dict]  # [{source_tool, target_tool, symbol}]

    # Orphan buds: exist on disk but no colony references them
    orphan_buds: list[str]

    # Total broken junction count across all layers
    total_detached: int


def _run_colony_probe(
    colonies_dir: Path = COLONIES_DIR,
    buds_dir: Path = BUDS_DIR,
    skills_dir: Path = SKILLS_DIR,
    tools_dir: Path = TOOLS_DIR,
) -> ColonyProbeResult:
    """Validate reference integrity across the full colony-bud-skill-tool dependency web.

    Eight layers, each traversing one edge type:
    1. Colony → Bud       : 'invoke X bud' patterns -- does the bud exist?
    2. Colony → Skill     : /skillname references -- does the receptor exist?
    3. Bud → Skill        : frontmatter skills: [...] -- does the receptor exist?
    4. Bud → MCP Tool     : mcp__ or bare snake_case in body -- is the tool registered?
    5. Bud → CLI binary   : bash code blocks -- is the binary on PATH?
    6. Skill → Skill      : /skillname in SKILL.md -- does the receptor exist?
    7. Skill → MCP Tool   : mcp__ or bare in SKILL.md -- is the tool registered?
    8. MCP Tool → MCP Tool: cross-tool imports in tools/ -- does the module exist?

    Pure glycolysis -- no LLM. File scanning + cross-referencing only.
    All paths via VIVESCA_ROOT.
    """
    receptor_names = _collect_receptor_names(skills_dir)
    bud_names = _collect_bud_names(buds_dir)
    registered_tools = _collect_registered_tool_names(tools_dir)

    # -- Layer 1 & 2: Colony → Bud and Colony → Skill ----------------------
    detached_colony_bud: list[dict] = []
    detached_colony_skill: list[dict] = []
    colony_referenced_buds: set[str] = set()

    if colonies_dir.is_dir():
        for colony_file in sorted(colonies_dir.iterdir()):
            if colony_file.suffix != ".md":
                continue
            colony_name = colony_file.stem
            try:
                text = colony_file.read_text()
            except OSError:
                continue

            for bud_ref in _extract_colony_bud_refs(text):
                colony_referenced_buds.add(bud_ref)
                if bud_ref not in bud_names:
                    detached_colony_bud.append({"colony": colony_name, "missing_bud": bud_ref})

            for skill_ref in _extract_colony_skill_refs(text):
                if skill_ref not in receptor_names:
                    detached_colony_skill.append(
                        {"colony": colony_name, "missing_skill": skill_ref}
                    )

    # -- Layer 3, 4, 5: Bud → Skill, Bud → MCP Tool, Bud → CLI ----------
    detached_bud_skill: list[dict] = []
    detached_bud_tool: list[dict] = []
    detached_bud_cli: list[dict] = []

    if buds_dir.is_dir():
        for bud_file in sorted(buds_dir.iterdir()):
            if bud_file.suffix != ".md":
                continue
            bud_name = bud_file.stem
            try:
                text = bud_file.read_text()
            except OSError:
                continue

            # Layer 3: Bud → Skill
            for skill_ref in _extract_bud_skill_refs(text):
                if skill_ref not in receptor_names:
                    detached_bud_skill.append({"bud": bud_name, "missing_skill": skill_ref})

            # Layer 4: Bud → MCP Tool
            for tool_ref in _extract_bud_mcp_tool_refs(text):
                if tool_ref not in registered_tools:
                    detached_bud_tool.append({"bud": bud_name, "missing_tool": tool_ref})

            # Layer 5: Bud → CLI binary
            for cmd in _extract_bud_cli_refs(text):
                if shutil.which(cmd) is None:
                    detached_bud_cli.append({"bud": bud_name, "missing_binary": cmd})

    # -- Layer 6 & 7: Skill → Skill, Skill → MCP Tool --------------------
    detached_skill_skill: list[dict] = []
    detached_skill_tool: list[dict] = []

    if skills_dir.is_dir():
        for receptor_dir in sorted(skills_dir.iterdir()):
            skill_file = receptor_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            skill_name = receptor_dir.name
            try:
                text = skill_file.read_text()
            except OSError:
                continue

            # Layer 6: Skill → Skill
            for skill_ref in _extract_skill_skill_refs(text):
                if skill_ref not in receptor_names:
                    detached_skill_skill.append({"skill": skill_name, "missing_skill": skill_ref})

            # Layer 7: Skill → MCP Tool
            for tool_ref in _extract_skill_mcp_tool_refs(text):
                if tool_ref not in registered_tools:
                    detached_skill_tool.append({"skill": skill_name, "missing_tool": tool_ref})

    # -- Layer 8: MCP Tool → MCP Tool (cross-module imports) --------------
    cross_import_edges = _extract_tool_cross_imports(tools_dir)
    tool_module_names = (
        frozenset(f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__")
        if tools_dir.is_dir()
        else frozenset()
    )
    detached_tool_tool = [
        edge for edge in cross_import_edges if edge["target_tool"] not in tool_module_names
    ]

    # -- Orphan buds: exist on disk but never referenced by any colony ----
    orphan_buds = sorted(bud_names - colony_referenced_buds)

    # -- Tally ---------------------------------------------------------------
    total_detached = (
        len(detached_colony_bud)
        + len(detached_colony_skill)
        + len(detached_bud_skill)
        + len(detached_bud_tool)
        + len(detached_bud_cli)
        + len(detached_skill_skill)
        + len(detached_skill_tool)
        + len(detached_tool_tool)
    )

    return ColonyProbeResult(
        colony_count=sum(1 for f in colonies_dir.iterdir() if f.suffix == ".md")
        if colonies_dir.is_dir()
        else 0,
        bud_count=len(bud_names),
        skill_count=len(receptor_names),
        registered_tool_count=len(registered_tools),
        detached_colony_bud_refs=detached_colony_bud,
        detached_colony_skill_refs=detached_colony_skill,
        detached_bud_skill_refs=detached_bud_skill,
        detached_bud_tool_refs=detached_bud_tool,
        detached_bud_cli_refs=detached_bud_cli,
        detached_skill_skill_refs=detached_skill_skill,
        detached_skill_tool_refs=detached_skill_tool,
        detached_tool_tool_refs=detached_tool_tool,
        orphan_buds=orphan_buds,
        total_detached=total_detached,
    )


# -- Proprioception: upstream receptor fork change detection ---------------
#
# Biology: proprioception is the organism's ability to sense changes in
# its own position relative to its environment. Here it detects when
# locally-forked receptor suites have diverged from their upstream
# source -- new skills added upstream, or local copies modified.


REGISTRY_PATH = Path.home() / ".local" / "share" / "vivesca" / "skill-forks.yaml"

DEFAULT_REGISTRY = {
    "superpowers": {
        "local": str(Path.home() / "germline" / "receptors" / "superpowers"),
        "cache_pattern": str(
            Path.home() / ".claude" / "plugins" / "cache" / "claude-plugins-official" / "superpowers"
        ),
    },
    "compound-engineering": {
        "local": str(Path.home() / "germline" / "receptors" / "compound-engineering"),
        "cache_pattern": str(
            Path.home() / ".claude" / "plugins" / "cache" / "every-marketplace" / "compound-engineering"
        ),
    },
}


def restore_fork_registry(path: Path = REGISTRY_PATH) -> dict:
    """Load fork registry from YAML, or return defaults."""
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return DEFAULT_REGISTRY


def find_latest_cache_version(cache_dir: Path) -> Path | None:
    """Find the latest versioned directory in a cache path.

    Looks for directories matching semver (X.Y.Z) pattern.
    Returns the path to the skills/ subdirectory of the latest version.
    """
    if not cache_dir.exists():
        return None

    versions: list[tuple[tuple[int, ...], Path]] = []
    for entry in cache_dir.iterdir():
        if entry.is_dir() and re.match(r"^\d+\.\d+\.\d+$", entry.name):
            parts = tuple(int(x) for x in entry.name.split("."))
            skills_dir = entry / "skills"
            if skills_dir.exists():
                versions.append((parts, skills_dir))

    if not versions:
        return None
    versions.sort(key=lambda x: x[0])
    return versions[-1][1]


def diff_fork(local_dir: Path, cache_dir: Path) -> dict:
    """Compare local fork against upstream cache.

    Returns dict with: modified, added_upstream, removed_locally, total_changes.
    """
    modified: list[str] = []
    added_upstream: list[str] = []
    removed_locally: list[str] = []

    # Collect all relative paths from both sides
    local_files: set[str] = set()
    cache_files: set[str] = set()

    for f in local_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            local_files.add(str(f.relative_to(local_dir)))

    for f in cache_dir.rglob("*"):
        if f.is_file() and not any(p.name == ".git" for p in f.parents):
            cache_files.add(str(f.relative_to(cache_dir)))

    # Modified: in both, but different
    for rel in sorted(local_files & cache_files):
        if not filecmp.cmp(local_dir / rel, cache_dir / rel, shallow=False):
            modified.append(rel)

    # Added upstream: in cache but not local
    added_upstream = sorted(cache_files - local_files)

    # Removed locally: in local but not cache (intentional omissions)
    removed_locally = sorted(local_files - cache_files)

    return {
        "modified": modified,
        "added_upstream": added_upstream,
        "removed_locally": removed_locally,
        "total_changes": len(modified) + len(added_upstream),
    }


# -- Consolidated integrin tool -----------------------------------------------


@tool(
    name="integrin",
    description="Attachment integrity. Actions: probe|apoptosis|colony_probe",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def integrin(
    action: str,
    colonies_dir: Path = COLONIES_DIR,
    buds_dir: Path = BUDS_DIR,
    skills_dir: Path = SKILLS_DIR,
    tools_dir: Path = TOOLS_DIR,
) -> IntegrinResult | ApoptosisResult | ColonyProbeResult:
    """Attachment integrity probe. Dispatch by action.

    Actions:
        probe        -- full receptor attachment integrity scan
        apoptosis    -- nightly stay-alive signal for dormant receptors
        colony_probe -- reference integrity across colonies, buds, skills, tools

    Parameters:
        action: One of probe|apoptosis|colony_probe
        colonies_dir: Path to colonies directory (colony_probe only)
        buds_dir: Path to buds directory (colony_probe only)
        skills_dir: Path to skills/receptors directory
        tools_dir: Path to metabolon/enzymes directory (colony_probe only)
    """
    action = action.lower().strip()
    if action == "probe":
        return _run_probe()
    elif action == "apoptosis":
        return _run_apoptosis_check()
    elif action == "colony_probe":
        return _run_colony_probe(
            colonies_dir=colonies_dir,
            buds_dir=buds_dir,
            skills_dir=skills_dir,
            tools_dir=tools_dir,
        )
    else:
        return IntegrinResult(
            total_receptors=0,
            total_references=0,
            attached=0,
            detached=[],
            mechanically_silent=[],
            focal_adhesions=[],
            anoikis=[],
            activation_state=[],
            adhesion_dependence=[],
            phenotype_issues=[{"path": "", "problem": f"unknown_action:{action}"}],
            unknown_platforms=[],
            launchagent_broken=[],
            skill_path_broken=[],
            untested_code=[],
        )


# Public aliases for pore.py imports
integrin_probe = _run_probe
integrin_apoptosis_check = _run_apoptosis_check
