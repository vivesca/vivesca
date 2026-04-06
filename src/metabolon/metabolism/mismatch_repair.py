"""Self-assessment of biological design precision.

Three levels:
1. Vocabulary — old class/term names still in code (grep-based)
2. Structure — components using the wrong protocol for their behaviour
3. Orphan — registered resources with no consumer binding

The executive substrate senses all three. Vocabulary gaps close via rename.
Structural gaps close via refactor. Orphan gaps close by binding the resource
to a consumer — constitution, CLAUDE.md, or a skill trigger. Like an orphan
receptor, the structure exists but nothing in the organism activates it.

"""

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from metabolon.locus import genome_md
from metabolon.locus import home as _home

SRC_DIR = Path(__file__).parent.parent  # metabolon/

# Receptor binding sites — where resources activate (constitution, CLAUDE.md).
_RECEPTOR_BINDING_SITES: list[Path] = [
    genome_md,
    _home / "CLAUDE.md",
]


# ── Vocabulary gaps ──────────────────────────────────────────────


@dataclass
class VocabularyGap:
    """A known naming imprecision."""

    old_term: str
    new_term: str
    layer: str  # "autonomic" or "cortical"
    reason: str
    grep_pattern: str
    exclude_file: str = ""


VOCABULARY_GAPS: list[VocabularyGap] = [
    VocabularyGap(
        old_term="DnaSubstrate",
        new_term="ExecutiveSubstrate",
        layer="cortical",
        reason="DNA is descriptive (builds proteins); constitution audit is executive function",
        grep_pattern=r"\bDnaSubstrate\b",
        exclude_file="precision.py",
    ),
    VocabularyGap(
        old_term="CrystalSubstrate",
        new_term="ConsolidationSubstrate",
        layer="cortical",
        reason="crystals are geological; memory staging is hippocampal consolidation",
        grep_pattern=r"\bCrystalSubstrate\b",
        exclude_file="precision.py",
    ),
]


# ── Orphan gaps ─────────────────────────────────────────────────


@dataclass
class OrphanGap:
    """A registered resource with no consumer reference."""

    uri: str
    source_file: str


def _detect_orphan_gaps(
    src: Path = SRC_DIR,
    consumer_files: list[Path] | None = None,
) -> list[OrphanGap]:
    """Detect orphan resources — registered but unbound to any consumer.

    Receptor binding sites are where the LLM learns what to read (constitution,
    CLAUDE.md). A resource URI absent from all binding sites is orphaned —
    like a receptor with no ligand, it exists but nothing activates it.
    """
    consumers = consumer_files or _RECEPTOR_BINDING_SITES

    # 1. Collect all registered resource URIs via AST.
    resources_dir = src / "resources"
    registered: list[tuple[str, str]] = []  # (uri, source_file)
    if resources_dir.exists():
        for py_file in sorted(resources_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except (SyntaxError, OSError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dec in node.decorator_list:
                    call_node = dec if isinstance(dec, ast.Call) else None
                    if not call_node or not call_node.args:
                        continue
                    name_node = dec.func if isinstance(dec, ast.Call) else dec
                    dec_name = None
                    if isinstance(name_node, ast.Name):
                        dec_name = name_node.id
                    elif isinstance(name_node, ast.Attribute):
                        dec_name = name_node.attr
                    if dec_name != "resource":
                        continue
                    first_arg = call_node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        registered.append((first_arg.value, py_file.name))

    if not registered:
        return []

    # 2. Read all consumer files into one search corpus.
    corpus = ""
    for cf in consumers:
        try:
            corpus += cf.read_text()
        except OSError:
            continue

    # 3. Flag any URI not found in the corpus.
    lesions = []
    for uri, source_file in registered:
        if uri not in corpus:
            lesions.append(OrphanGap(uri=uri, source_file=source_file))
    return lesions


# ── Structural gaps ──────────────────────────────────────────────


@dataclass
class StructuralGap:
    """A component using the wrong protocol for its behaviour."""

    file: str
    component: str
    current_layer: str  # what it looks like (has sense/candidates/act = cortical)
    actual_layer: str  # what it does (no LLM imports = autonomic)
    reason: str


def _detect_structural_gaps(src: Path = SRC_DIR) -> list[StructuralGap]:
    """Detect components that look cortical but behave autonomically, or vice versa.

    Heuristic: a Substrate implementation that never references LLM/haiku/enzyme
    is probably autonomic and shouldn't use the 4-phase cortical protocol.
    """
    lesions = []
    substrates_dir = src / "metabolism" / "substrates"
    if not substrates_dir.exists():
        return lesions

    # Scan all Python files, not just substrates — detect any component
    # that claims one layer but behaves like the other
    for py_file in src.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            source = py_file.read_text()
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # Check: autonomic component that imports LLM (should be cortical?)
            docstring = ast.get_docstring(node) or ""

            is_labelled_autonomic = "autonomic" in docstring.lower()
            is_labelled_cortical = "cortical" in docstring.lower()

            # Check actual imports, not string mentions
            imports_symbiont = any(
                (isinstance(n, ast.ImportFrom) and n.module and "llm" in n.module)
                or (isinstance(n, ast.Import) and any("llm" in a.name for a in n.names))
                for n in ast.iter_child_nodes(tree)
            )

            if is_labelled_autonomic and imports_symbiont:
                lesions.append(
                    StructuralGap(
                        file=py_file.name,
                        component=node.name,
                        current_layer="labelled autonomic",
                        actual_layer="uses LLM (cortical?)",
                        reason=f"{node.name} claims autonomic but imports LLM",
                    )
                )
            elif is_labelled_cortical and not imports_symbiont and "substrate" not in py_file.name:
                # Substrates are cortical by intent (produce proposals for LLM evaluation)
                # even though they don't call LLM directly — sweep.py does
                lesions.append(
                    StructuralGap(
                        file=py_file.name,
                        component=node.name,
                        current_layer="labelled cortical",
                        actual_layer="no LLM usage found",
                        reason=f"{node.name} claims cortical but no LLM reference — verify",
                    )
                )

    return lesions


# ── Unified scan ──────────────────────────────────────────────


@dataclass
class GapReport:
    """Result of scanning for any gap."""

    kind: str  # "vocabulary" or "structural"
    description: str
    closed: bool
    references: list[str] = field(default_factory=list)


def scan(src: Path = SRC_DIR) -> list[GapReport]:
    """Scan source for all known gaps — vocabulary and structural."""
    reports = []

    # Vocabulary
    for gap in VOCABULARY_GAPS:
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", gap.grep_pattern, str(src)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            hits = [
                line
                for line in result.stdout.splitlines()
                if gap.exclude_file not in line and "precision.py" not in line
            ]
            reports.append(
                GapReport(
                    kind="vocabulary",
                    description=f"{gap.old_term} → {gap.new_term}: {gap.reason}",
                    closed=len(hits) == 0,
                    references=hits,
                )
            )
        except Exception:
            reports.append(
                GapReport(
                    kind="vocabulary",
                    description=f"{gap.old_term} → {gap.new_term}",
                    closed=False,
                )
            )

    # Structural
    for gap in _detect_structural_gaps(src):
        reports.append(
            GapReport(
                kind="structural",
                description=f"{gap.component} in {gap.file}: {gap.reason}",
                closed=False,
                references=[f"{gap.current_layer} → should be {gap.actual_layer}"],
            )
        )

    # Orphan resources
    for gap in _detect_orphan_gaps(src):
        reports.append(
            GapReport(
                kind="orphan",
                description=f"{gap.uri} ({gap.source_file}): no consumer binding",
                closed=False,
            )
        )

    try:
        from metabolon.operons import dormant

        for operon in dormant():
            reports.append(
                GapReport(
                    kind="dormant",
                    description=f"{operon.reaction}: transcribed but not translated",
                    closed=False,
                )
            )
    except ImportError:
        pass

    return reports


def summary() -> str:
    """Human-readable gap summary for vigilis."""
    reports = scan()
    if not reports:
        return "Precision: clean"

    lines = []
    vocab = [r for r in reports if r.kind == "vocabulary"]
    struct = [r for r in reports if r.kind == "structural"]

    orphan = [r for r in reports if r.kind == "orphan"]

    if vocab:
        closed = sum(1 for r in vocab if r.closed)
        lines.append(f"Vocabulary: {closed}/{len(vocab)} closed")
        for r in vocab:
            status = "ok" if r.closed else f"OPEN ({len(r.references)})"
            lines.append(f"  {r.description[:60]}: {status}")

    if struct:
        lines.append(f"Structure: {len(struct)} mismatches")
        for r in struct:
            lines.append(f"  {r.description[:80]}")

    if orphan:
        lines.append(f"Orphan: {len(orphan)} unbound resources")
        for r in orphan:
            lines.append(f"  {r.description[:80]}")

    dormant_operons = [r for r in reports if r.kind == "dormant"]

    if dormant_operons:
        lines.append(f"Dormant: {len(dormant_operons)} inactive operons")
        for r in dormant_operons:
            lines.append(f"  {r.description[:80]}")

    if not vocab and not struct and not orphan and not dormant_operons:
        return "Precision: clean"

    return "\n".join(lines)
