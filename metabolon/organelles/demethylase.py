"""demethylase — active memory erasure and consolidation.

Scans histone marks (memory files) for staleness, flags candidates for removal,
protects CpG islands (critical marks) from decay, and strengthens frequently
accessed marks (spaced repetition).

Biology:
- KDM enzymes actively remove histone methyl marks no longer relevant.
- Sleep consolidation replays and strengthens important memories.
- Spaced repetition: each access extends a memory's half-life exponentially.
- CpG islands: protected regions that resist demethylation.

In vivesca: marks accumulate across sessions. The demethylase sweeps for stale
ones, strengthens accessed ones, and protects critical corrections.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from metabolon.locus import marks as MARKS_DIR

# Ephemeral signal channel — octopus interbrachial commissure
SIGNALS_DIR = Path.home() / "epigenome" / "signals"


@dataclass
class MarkAnalysis:
    """Analysis of a single histone mark (memory file)."""

    path: Path
    name: str
    mark_type: str  # feedback, finding, user, project, reference
    durability: str  # methyl (durable) or acetyl (volatile)
    protected: bool  # CpG island — never erased
    source: str  # cc, gemini, codex, user, unknown
    age_days: int
    last_modified_days: int
    access_count: int = 0  # spaced repetition: how many times accessed
    stale: bool = False
    reason: str = ""


@dataclass
class DemethylaseReport:
    """Results of a demethylase sweep."""

    total_marks: int = 0
    methyl_marks: int = 0
    acetyl_marks: int = 0
    protected_marks: int = 0
    stale_candidates: list[MarkAnalysis] = field(default_factory=list)
    source_distribution: dict[str, int] = field(default_factory=dict)
    type_distribution: dict[str, int] = field(default_factory=dict)
    mark_clusters: list[dict] = field(default_factory=list)


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract YAML frontmatter from a mark file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def _infer_durability(fm: dict, path: Path) -> str:
    """Infer durability from frontmatter or filename convention."""
    if "durability" in fm:
        return fm["durability"]
    # Checkpoints and resolved items are acetyl (volatile)
    name = path.stem
    if name.startswith("checkpoint_") or name.startswith("resolved_"):
        return "acetyl"
    # Everything else defaults to methyl (durable)
    return "methyl"


def _infer_source(fm: dict) -> str:
    """Infer mark source from frontmatter."""
    if "source" in fm:
        return fm["source"]
    return "unknown"


def _infer_protected(fm: dict, path: Path) -> bool:
    """Check if mark is a CpG island (protected from erasure)."""
    if fm.get("protected", "").lower() in ("true", "yes"):
        return True
    # Core behavioral corrections are always protected
    name = path.stem
    core_patterns = [
        "feedback_keep_digging",
        "feedback_hold_position",
        "feedback_pull_the_thread",
        "feedback_more_autonomous",
        "feedback_stop_asking_obvious",
    ]
    return name in core_patterns


def analyze_mark(path: Path) -> MarkAnalysis:
    """Analyze a single mark file."""
    fm = _parse_frontmatter(path)
    stat = path.stat()
    now = datetime.now()
    modified = datetime.fromtimestamp(stat.st_mtime)
    age = now - modified
    access_count = int(fm.get("access_count", "0"))

    return MarkAnalysis(
        path=path,
        name=fm.get("name", path.stem),
        mark_type=fm.get("type", "unknown"),
        durability=_infer_durability(fm, path),
        protected=_infer_protected(fm, path),
        source=_infer_source(fm),
        age_days=age.days,
        last_modified_days=age.days,
        access_count=access_count,
    )


def _effective_threshold(base_days: int, access_count: int) -> int:
    """Spaced repetition: each access doubles the decay threshold.

    Biology: Ebbinghaus forgetting curve. Each retrieval strengthens the memory
    trace, extending its half-life exponentially. A mark accessed 5 times
    lives 32x longer than one never accessed.
    """
    multiplier = 2 ** min(access_count, 8)  # cap at 256x to prevent infinity
    return base_days * multiplier


def _detect_staleness(mark: MarkAnalysis, threshold_days: int = 90) -> MarkAnalysis:
    """Flag a mark as stale based on age, durability, and access history."""
    if mark.protected:
        return mark  # CpG island — never stale

    if mark.durability == "acetyl":
        effective = _effective_threshold(14, mark.access_count)
        if mark.age_days > effective:
            mark.stale = True
            mark.reason = f"acetyl mark older than {effective}d (base 14d × 2^{mark.access_count} accesses, actual {mark.age_days}d)"
    elif mark.durability == "methyl":
        effective = _effective_threshold(threshold_days, mark.access_count)
        if mark.age_days > effective:
            mark.stale = True
            mark.reason = f"methyl mark older than {effective}d (base {threshold_days}d × 2^{mark.access_count}, actual {mark.age_days}d)"

    # Project memories decay faster — active work changes
    if mark.mark_type == "project" and not mark.stale:
        effective = _effective_threshold(30, mark.access_count)
        if mark.age_days > effective:
            mark.stale = True
            mark.reason = f"project mark older than {effective}d (base 30d × 2^{mark.access_count}, actual {mark.age_days}d)"

    return mark


def _cluster_marks(marks: list[MarkAnalysis]) -> list[dict]:
    """Identify mark clusters (histone code combinatorics).

    Groups marks that share a topic prefix, revealing patterns
    where multiple marks combine to form a behavioral rule.
    """
    clusters: dict[str, list[str]] = {}
    for m in marks:
        # Extract topic from filename: feedback_keep_digging → keep_digging
        stem = m.path.stem
        parts = stem.split("_", 1)
        if len(parts) == 2:
            prefix, topic = parts
            # Group by first meaningful word of topic
            topic_key = topic.split("_")[0] if "_" in topic else topic
            clusters.setdefault(topic_key, []).append(stem)

    # Only return clusters with 2+ marks (combinatorial patterns)
    return [
        {"topic": k, "marks": v, "count": len(v)}
        for k, v in sorted(clusters.items(), key=lambda x: -len(x[1]))
        if len(v) >= 2
    ]


def sweep(
    marks_dir: Path | None = None,
    threshold_days: int = 90,
    dry_run: bool = True,
) -> DemethylaseReport:
    """Run a demethylase sweep across all marks.

    Args:
        marks_dir: Directory containing mark files. Defaults to locus.marks.
        threshold_days: Days before a methyl mark is considered stale.
        dry_run: If True, only report — don't delete.

    Returns:
        DemethylaseReport with findings.
    """
    marks_dir = marks_dir or MARKS_DIR
    report = DemethylaseReport()

    md_files = sorted(marks_dir.glob("*.md"))
    # Skip index files
    skip = {"MEMORY.md", "methylome.md", "decay-tracker.md"}
    md_files = [f for f in md_files if f.name not in skip]

    analyses: list[MarkAnalysis] = []
    for path in md_files:
        mark = analyze_mark(path)
        mark = _detect_staleness(mark, threshold_days)
        analyses.append(mark)

    report.total_marks = len(analyses)
    report.methyl_marks = sum(1 for m in analyses if m.durability == "methyl")
    report.acetyl_marks = sum(1 for m in analyses if m.durability == "acetyl")
    report.protected_marks = sum(1 for m in analyses if m.protected)
    report.stale_candidates = [m for m in analyses if m.stale]

    # Source distribution (imprinting)
    for m in analyses:
        report.source_distribution[m.source] = report.source_distribution.get(m.source, 0) + 1

    # Type distribution
    for m in analyses:
        report.type_distribution[m.mark_type] = report.type_distribution.get(m.mark_type, 0) + 1

    # Histone code clusters
    report.mark_clusters = _cluster_marks(analyses)

    # Erase stale marks if not dry run
    if not dry_run:
        for m in report.stale_candidates:
            m.path.unlink()

    return report


def record_access(path: Path) -> None:
    """Record that a mark was accessed — strengthens it against decay.

    Biology: Each retrieval of a memory strengthens the synaptic trace.
    Increments access_count in frontmatter.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    end = text.find("---", 3)
    if end == -1:
        return

    fm_text = text[3:end]
    body = text[end:]

    # Parse current access_count
    lines = fm_text.strip().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith("access_count:"):
            count = int(line.split(":", 1)[1].strip())
            new_lines.append(f"access_count: {count + 1}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append("access_count: 1")

    path.write_text("---\n" + "\n".join(new_lines) + "\n" + body, encoding="utf-8")


# -- Ephemeral signal channel (octopus interbrachial commissure) ---------------

def emit_signal(name: str, content: str, source: str = "unknown") -> Path:
    """Write an ephemeral acetyl signal for inter-agent communication.

    Biology: Octopus arms communicate via the interbrachial commissure —
    a narrow nerve bundle for short-lived coordination signals. These signals
    are not long-term memories; they decay quickly.

    Signals are acetyl marks in ~/epigenome/signals/. The demethylase sweep
    cleans them up after 14 days.
    """
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    signal_path = SIGNALS_DIR / f"signal_{name}_{ts}.md"
    signal_path.write_text(
        f"---\n"
        f"name: {name}\n"
        f"type: signal\n"
        f"source: {source}\n"
        f"durability: acetyl\n"
        f"---\n\n"
        f"{content}\n",
        encoding="utf-8",
    )
    return signal_path


def read_signals(name_filter: str | None = None) -> list[dict]:
    """Read pending signals from the ephemeral channel.

    Args:
        name_filter: Optional prefix to filter signals by name.
    """
    if not SIGNALS_DIR.exists():
        return []
    signals = []
    for path in sorted(SIGNALS_DIR.glob("signal_*.md")):
        fm = _parse_frontmatter(path)
        if name_filter and not fm.get("name", "").startswith(name_filter):
            continue
        body = path.read_text(encoding="utf-8")
        # Extract body after second ---
        parts = body.split("---", 2)
        content = parts[2].strip() if len(parts) > 2 else ""
        signals.append({
            "name": fm.get("name", path.stem),
            "source": fm.get("source", "unknown"),
            "content": content,
            "path": str(path),
            "age_days": (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days,
        })
    return signals


def format_report(report: DemethylaseReport) -> str:
    """Format a DemethylaseReport for display."""
    lines = [
        f"Demethylase sweep: {report.total_marks} marks",
        f"  Methyl (durable): {report.methyl_marks}",
        f"  Acetyl (volatile): {report.acetyl_marks}",
        f"  Protected (CpG): {report.protected_marks}",
        f"  Stale candidates: {len(report.stale_candidates)}",
        "",
        "Source distribution (imprinting):",
    ]
    for source, count in sorted(report.source_distribution.items(), key=lambda x: -x[1]):
        lines.append(f"  {source}: {count}")

    lines.append("")
    lines.append("Type distribution:")
    for mtype, count in sorted(report.type_distribution.items(), key=lambda x: -x[1]):
        lines.append(f"  {mtype}: {count}")

    if report.mark_clusters:
        lines.append("")
        lines.append(f"Mark clusters (histone code, top 10):")
        for cluster in report.mark_clusters[:10]:
            lines.append(f"  {cluster['topic']} ({cluster['count']} marks): {', '.join(cluster['marks'][:3])}...")

    if report.stale_candidates:
        lines.append("")
        lines.append("Stale candidates:")
        for m in report.stale_candidates[:20]:
            prot = " [CpG]" if m.protected else ""
            lines.append(f"  {m.path.name} ({m.age_days}d, {m.durability}){prot}: {m.reason}")

    return "\n".join(lines)
