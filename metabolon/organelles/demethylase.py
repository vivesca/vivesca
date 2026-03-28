"""demethylase — active memory erasure and consolidation.

Scans histone marks (memory files) for staleness, flags candidates for removal,
protects CpG islands (critical marks) from decay, and strengthens frequently
accessed marks (spaced repetition).

Biology:
- KDM enzymes actively remove histone methyl marks no longer relevant.
- Circadian chromatin remodeling periodically reorganizes and strengthens marks.
- Access-dependent mark stabilization: each retrieval extends half-life.
- CpG islands: protected regions that resist demethylation.

In vivesca: marks accumulate across sessions. The demethylase sweeps for stale
ones, strengthens accessed ones, and protects critical corrections.
"""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from metabolon.locus import marks as MARKS_DIR

# Ephemeral signal channel — paracrine signaling (cell-to-cell via secreted factors)
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
class ConsolidationReport:
    """Results of a circadian chromatin remodeling pass."""

    today_marks: list[MarkAnalysis] = field(default_factory=list)
    clusters_found: list[dict] = field(default_factory=list)
    strengthened: list[MarkAnalysis] = field(default_factory=list)
    methylome_updated: bool = False


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


def _parse_downstream(path: Path) -> list[str]:
    """Extract the downstream YAML list from a signal's frontmatter.

    Handles the block-list format written by emit_signal():
      downstream:
        - cmd1
        - cmd2
    Returns an empty list if no downstream key is present.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []
    end = text.find("---", 3)
    if end == -1:
        return []
    fm_text = text[3:end]
    lines = fm_text.splitlines()
    commands: list[str] = []
    in_downstream = False
    for line in lines:
        if line.strip().startswith("downstream:"):
            in_downstream = True
            continue
        if in_downstream:
            stripped = line.strip()
            if stripped.startswith("- "):
                commands.append(stripped[2:])
            elif stripped == "-":
                commands.append("")
            elif stripped and not stripped.startswith("#"):
                # Non-list line ends the block
                break
    return commands


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

    Biology: access-dependent mark stabilization. Each retrieval strengthens the
    mark, extending its half-life exponentially (analogous to repeated histone
    acetylation reinforcing active gene expression). A mark accessed 5 times
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


def consolidate(marks_dir: Path | None = None) -> ConsolidationReport:
    """Circadian chromatin remodeling — periodic reorganization and strengthening.

    Phase 1 (local remodeling): Identify marks created/modified in the last 24h.
                                These are new modifications to consolidate.
    Phase 2 (domain organization): Cluster new marks with existing related marks.
                                   Update the methylome index with new clusters.
                                   Strengthen marks that were accessed (reinforce active regions).
    """
    from datetime import timedelta

    marks_dir = marks_dir or MARKS_DIR
    report = ConsolidationReport()

    md_files = sorted(marks_dir.glob("*.md"))
    skip = {"MEMORY.md", "methylome.md", "decay-tracker.md"}
    md_files = [f for f in md_files if f.name not in skip]

    all_marks: list[MarkAnalysis] = [analyze_mark(p) for p in md_files]

    # Phase 1 — synaptic: marks modified in the last 24h
    today_marks = [m for m in all_marks if m.last_modified_days == 0]
    report.today_marks = today_marks

    # Phase 2 — systems: cluster today's marks with all existing marks
    if today_marks:
        report.clusters_found = _cluster_marks(all_marks)

        # Strengthen marks that were accessed today (access_count bumped recently)
        # Proxy: marks modified today AND access_count > 0
        for m in today_marks:
            if m.access_count > 0:
                report.strengthened.append(m)

    # Write daily consolidation summary
    daily_dir = Path.home() / "epigenome" / "chromatin" / "Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    summary_path = daily_dir / f"{date_str}-consolidation.md"

    cluster_lines = []
    for c in report.clusters_found[:10]:
        cluster_lines.append(f"- **{c['topic']}** ({c['count']} marks): {', '.join(c['marks'][:3])}")

    today_lines = [f"- {m.path.name} ({m.mark_type}, {m.durability})" for m in report.today_marks]
    strengthened_lines = [f"- {m.path.name} (access_count: {m.access_count})" for m in report.strengthened]

    summary = (
        f"# Chromatin Remodeling — {date_str}\n\n"
        f"## Phase 1: Synaptic (today's experiences)\n\n"
        + (("\n".join(today_lines) + "\n") if today_lines else "_No marks modified today._\n")
        + f"\n## Phase 2: Systems (clusters)\n\n"
        + (("\n".join(cluster_lines) + "\n") if cluster_lines else "_No clusters found._\n")
        + f"\n## Strengthened\n\n"
        + (("\n".join(strengthened_lines) + "\n") if strengthened_lines else "_None strengthened today._\n")
    )
    summary_path.write_text(summary, encoding="utf-8")
    report.methylome_updated = True

    return report


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

    # Also sweep ephemeral signals (acetyl, 14-day TTL)
    if SIGNALS_DIR.exists():
        for path in SIGNALS_DIR.glob("signal_*.md"):
            age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days
            if age > 14:
                if not dry_run:
                    path.unlink()
                report.stale_candidates.append(MarkAnalysis(
                    path=path, name=path.stem, mark_type="signal",
                    durability="acetyl", protected=False, source="unknown",
                    age_days=age, last_modified_days=age, stale=True,
                    reason=f"signal older than 14 days ({age}d)",
                ))

    # Sleep consolidation — replay and strengthen after erasure
    consolidate(marks_dir)

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


# -- Ephemeral signal channel (paracrine signaling) ----------------------------

def _find_existing_signal(name: str) -> Path | None:
    """Return an existing untransduced, non-desensitized signal file by name."""
    if not SIGNALS_DIR.exists():
        return None
    for path in sorted(SIGNALS_DIR.glob("signal_*.md")):
        fm = _parse_frontmatter(path)
        if fm.get("name") == name and fm.get("desensitized", "").lower() not in ("true", "yes"):
            return path
    return None


def _update_frontmatter_field(path: Path, key: str, value: str) -> None:
    """Update or insert a single key in a file's YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    end = text.find("---", 3)
    if end == -1:
        return
    fm_text = text[3:end]
    body = text[end:]
    lines = fm_text.strip().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}:"):
            new_lines.append(f"{key}: {value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}: {value}")
    path.write_text("---\n" + "\n".join(new_lines) + "\n" + body, encoding="utf-8")


def emit_signal(
    name: str,
    content: str,
    source: str = "unknown",
    downstream: list[str] | None = None,
) -> Path:
    """Write an ephemeral acetyl signal for inter-agent communication.

    Biology: paracrine signaling — cells secrete short-range factors that
    neighboring cells detect. These signals are transient, not stored in
    chromatin; they coordinate immediate behavior and decay quickly.

    Signals are acetyl marks in ~/epigenome/signals/. The demethylase sweep
    cleans them up after 14 days.

    Desensitization: if a signal with the same name already exists and hasn't
    been transduced, fire_count is incremented rather than creating a duplicate.
    Biology: sustained receptor stimulation → receptor internalization → attenuation.

    Args:
        name: Signal name (used for deduplication and filtering).
        content: Signal body text.
        source: Identifier of the emitting agent.
        downstream: Optional list of shell commands to run when this signal is
            transduced. Biology: the hormone triggers a cascade of enzyme
            activations downstream.
    """
    import uuid as _uuid

    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    existing = _find_existing_signal(name)
    if existing is not None:
        fm = _parse_frontmatter(existing)
        fire_count = int(fm.get("fire_count", "1")) + 1
        _update_frontmatter_field(existing, "fire_count", str(fire_count))
        return existing

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_id = _uuid.uuid4().hex[:6]
    signal_path = SIGNALS_DIR / f"signal_{name}_{ts}_{short_id}.md"

    downstream_block = ""
    if downstream:
        items = "\n".join(f"  - {cmd}" for cmd in downstream)
        downstream_block = f"downstream:\n{items}\n"

    signal_path.write_text(
        f"---\n"
        f"name: {name}\n"
        f"type: signal\n"
        f"source: {source}\n"
        f"durability: acetyl\n"
        f"fire_count: 1\n"
        f"{downstream_block}"
        f"---\n\n"
        f"{content}\n",
        encoding="utf-8",
    )
    return signal_path


def read_signals(
    name_filter: str | None = None,
    desensitization_threshold: int = 5,
    include_desensitized: bool = False,
    execute_cascade: bool = False,
) -> list[dict]:
    """Read pending signals from the ephemeral channel.

    Args:
        name_filter: Optional prefix to filter signals by name.
        desensitization_threshold: Signals with fire_count >= this are marked
            desensitized and excluded (biology: receptor internalization).
        include_desensitized: If True, return desensitized signals too.
        execute_cascade: If True, execute each signal's downstream commands and
            mark the signal as transduced so it won't fire again. Biology: the
            hormone triggers a cascade of enzyme activations; each enzyme is
            activated exactly once per signal.
    """
    if not SIGNALS_DIR.exists():
        return []
    signals = []
    for path in sorted(SIGNALS_DIR.glob("signal_*.md")):
        fm = _parse_frontmatter(path)
        if name_filter and not fm.get("name", "").startswith(name_filter):
            continue

        # Skip already-transduced signals (cascade already fired)
        if fm.get("transduced", "").lower() in ("true", "yes"):
            continue

        fire_count = int(fm.get("fire_count", "1"))

        # Mark as desensitized if fire_count crosses threshold
        if fire_count >= desensitization_threshold:
            already_marked = fm.get("desensitized", "").lower() in ("true", "yes")
            if not already_marked:
                _update_frontmatter_field(path, "desensitized", "true")
            if not include_desensitized:
                continue

        body = path.read_text(encoding="utf-8")
        # Extract body after second ---
        parts = body.split("---", 2)
        content = parts[2].strip() if len(parts) > 2 else ""

        downstream = _parse_downstream(path)
        cascades_fired: list[str] = []

        if execute_cascade and downstream:
            for cmd in downstream:
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    cascades_fired.append(cmd)
                except subprocess.CalledProcessError:
                    cascades_fired.append(f"FAILED: {cmd}")
            # Mark as transduced — won't fire again
            _update_frontmatter_field(path, "transduced", "true")

        signals.append({
            "name": fm.get("name", path.stem),
            "source": fm.get("source", "unknown"),
            "content": content,
            "path": str(path),
            "age_days": (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).days,
            "fire_count": fire_count,
            "desensitized": fire_count >= desensitization_threshold,
            "downstream": downstream,
            "cascades_fired": cascades_fired,
        })
    return signals


def resensitize(name: str) -> bool:
    """Re-sensitize a desensitized signal (re-surface it).

    Biology: receptor recycling — internalized receptors return to the cell
    surface after the stimulus has cleared. Resets fire_count to 1 and
    removes the desensitized flag so the signal becomes readable again.

    Returns:
        True if a desensitized signal was found and reset, False otherwise.
    """
    if not SIGNALS_DIR.exists():
        return False
    for path in sorted(SIGNALS_DIR.glob("signal_*.md")):
        fm = _parse_frontmatter(path)
        if fm.get("name") != name:
            continue
        if fm.get("desensitized", "").lower() not in ("true", "yes"):
            continue
        # Reset: remove desensitized flag and reset fire_count
        _update_frontmatter_field(path, "desensitized", "false")
        _update_frontmatter_field(path, "fire_count", "1")
        return True
    return False


def transduce(name_filter: str | None = None) -> list[dict]:
    """Execute downstream cascades for all pending signals, then mark them transduced.

    Convenience function combining read_signals + execute_cascade in one call.
    Biology: signal transduction — the hormone (signal) activates a cascade of
    intracellular enzymes (downstream commands), amplifying and routing the
    original message. Each signal is transduced exactly once.

    Args:
        name_filter: Optional prefix to restrict which signals are transduced.

    Returns:
        List of signal dicts (same shape as read_signals) for signals that had
        downstream commands. Each entry includes 'cascades_fired' with the list
        of commands that were executed.
    """
    all_signals = read_signals(
        name_filter=name_filter,
        execute_cascade=True,
    )
    # Return only signals that had downstream commands (cascade was relevant)
    return [s for s in all_signals if s.get("downstream")]


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
