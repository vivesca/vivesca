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
g1 = chromatin / "G1.md"
daily = chromatin / "Daily"
north_star = chromatin / "North Star.md"
now = chromatin / "NOW.md"
consulting = chromatin / "Consulting"
poiesis_reports = chromatin / "Poiesis Reports"

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
signals_dir = loci / "signals"
rheotaxis_log = signals_dir / "rheotaxis.jsonl"

# Endocytosis (RSS content intake)
endocytosis_cache = home / ".cache" / "endocytosis"
endocytosis_cargo = endocytosis_cache / "cargo.jsonl"
endocytosis_affinity = endocytosis_cache / "relevance.jsonl"
endocytosis_recycling = endocytosis_cache / "engagement.jsonl"
endocytosis_alerts = endocytosis_cache / "alert-signals.jsonl"

# Vivesca data directory (~/.local/share/vivesca)
vivesca_data = home / ".local" / "share" / "vivesca"
infections_log = vivesca_data / "infections.jsonl"
signals_log = vivesca_data / "signals.jsonl"
checkpoints_db = vivesca_data / "checkpoints.db"
genome_md = vivesca_data / "genome.md"
phantoms_db = vivesca_data / "phantoms.json"
requests_log = vivesca_data / "requests.jsonl"
skill_registry = vivesca_data / "skill-forks.yaml"
signal_history = vivesca_data / "signal-history.jsonl"
ribosome_log = vivesca_data / "ribosome.jsonl"
complement_state = vivesca_data / "complement.json"
variants_root = vivesca_data / "variants"
setpoints_dir = vivesca_data / "setpoints"
goals_dir = vivesca_data / "goals"

# CC integration
claude_dir = home / ".claude"
claude_hooks = claude_dir / "hooks"
claude_skills = claude_dir / "skills"
claude_settings = claude_dir / "settings.json"
claude_nightly_health = claude_dir / "nightly-health.md"
claude_skill_usage = claude_dir / "skill-usage.tsv"
claude_skill_flywheel = claude_dir / "skill-flywheel-daily.md"
claude_stats_cache = claude_dir / "stats-cache.json"
claude_credentials = claude_dir / ".credentials.json"
claude_allostasis_state = claude_dir / "allostasis-state.json"
claude_plugins_cache = claude_dir / "plugins" / "cache"
claude_memory = claude_dir / "projects" / "-Users-terry" / "memory"

# CRISPR cache
crispr_cache = home / ".cache" / "crispr"

# Temp and logs
tmp = home / "tmp"
logs_dir = home / "logs"

# Platform-dependent directories (macOS)
launch_agents = home / "Library" / "LaunchAgents"

# Phenotype — single source of truth for all platform entry points
phenotype_md = membrane / "phenotype.md"

# Platform phenotype symlinks: each should point to phenotype_md
# When a new CLI platform appears, add its entry here.
PLATFORM_SYMLINKS: list[Path] = [
    home / "CLAUDE.md",  # Claude Code reads ~/CLAUDE.md
    home / ".gemini" / "GEMINI.md",  # Gemini CLI reads ~/.gemini/GEMINI.md
]

# LLM CLI fingerprint: dirs with settings.json + (state.json or projects/)
# This filters out generic CLI tools (docker, railway, etc.)
PLATFORM_MARKERS_REQUIRED = "settings.json"
PLATFORM_MARKERS_CONFIRM = frozenset({"state.json", "projects", "history.jsonl"})
