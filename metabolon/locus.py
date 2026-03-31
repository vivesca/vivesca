from __future__ import annotations

"""Locus — canonical paths for the organism.

Single source of truth. Effectors, tools, and scripts import from here
instead of hardcoding paths. When the organism moves, update this file only.

Usage:
    from metabolon.locus import germline, chromatin, praxis, marks
"""


from pathlib import Path

home = Path.home()

# The two repos
germline = home / "germline"
epigenome = home / "epigenome"

# Chromatin
chromatin = epigenome / "chromatin"
praxis = chromatin / "Praxis.md"
praxis_archive = chromatin / "Praxis Archive.md"
tonus = chromatin / "Tonus.md"
daily = chromatin / "Daily"

# Engrams (memory)
marks = epigenome / "marks"
memory_index = marks / "MEMORY.md"

# Epigenome structure
phenotype = epigenome / "phenotype"
cofactors = epigenome / "cofactors"
oscillators = epigenome / "oscillators"
bud_marks = epigenome / "bud-marks"

# Chromatin subdirs
immunity = chromatin / "immunity"
chemosensory = chromatin / "chemosensory"
interoception = chromatin / "interoception"
transcripts = chromatin / "transcripts"
heterochromatin = chromatin / "heterochromatin"
reference = chromatin / "Reference"
weekly = chromatin / "Weekly"
spending = chromatin / "Spending"
efferens = chromatin / "Efferens"
pulse_reports = chromatin / "Pulse Reports"
experiments = chromatin / "Experiments"
health = chromatin / "Health"
meal_plan = health / "Weekly Meal Plan - Taikoo Place.md"
symptom_log = health / "Symptom Log.md"
failures = chromatin / "failures.md"
praxis_dismissed = chromatin / "Praxis Dismissed.md"
blog_published = chromatin / "Writing" / "Blog" / "Published"
terryli_hm = chromatin / "terryli.hm.md"
agent_queue = chromatin / "agent-queue.yaml"

# Germline structure
membrane = germline / "membrane"
cytoskeleton = membrane / "cytoskeleton"
receptors = membrane / "receptors"
buds = membrane / "buds"
colonies = membrane / "colonies"
effectors = germline / "effectors"
regulon = germline / "regulon"
operons = germline / "operons"
symbionts = germline / "symbionts"
assays = germline / "assays"

# Loci (deliverables output)
loci = germline / "loci"
poiesis = loci / "poiesis"
pulse = loci / "pulse"

# Endocytosis (RSS content intake)
endocytosis_cache = home / ".cache" / "endocytosis"
endocytosis_cargo = endocytosis_cache / "cargo.jsonl"
endocytosis_affinity = endocytosis_cache / "relevance.jsonl"
endocytosis_recycling = endocytosis_cache / "engagement.jsonl"
endocytosis_alerts = endocytosis_cache / "alert-signals.jsonl"

# CC integration
claude_dir = home / ".claude"
claude_hooks = claude_dir / "hooks"
claude_skills = claude_dir / "skills"

# Phenotype — single source of truth for all platform entry points
phenotype_md = membrane / "phenotype.md"

# Platform phenotype symlinks: each should point to phenotype_md
# When a new CLI platform appears, add its entry here.
PLATFORM_SYMLINKS: list[Path] = [
    home / "CLAUDE.md",              # Claude Code reads ~/CLAUDE.md
    home / ".gemini" / "GEMINI.md",  # Gemini CLI reads ~/.gemini/GEMINI.md
]

# LLM CLI fingerprint: dirs with settings.json + (state.json or projects/)
# This filters out generic CLI tools (docker, railway, etc.)
PLATFORM_MARKERS_REQUIRED = "settings.json"
PLATFORM_MARKERS_CONFIRM = frozenset({"state.json", "projects", "history.jsonl"})
