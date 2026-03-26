"""Locus — canonical paths for the organism.

Single source of truth. Effectors, tools, and scripts import from here
instead of hardcoding paths. When the organism moves, update this file only.

Usage:
    from metabolon.locus import GERMLINE, CHROMATIN, PRAXIS, ENGRAMS
"""

from pathlib import Path

HOME = Path.home()

# The two repos
GERMLINE = HOME / "germline"
EPIGENOME = HOME / "epigenome"

# Chromatin (vault)
CHROMATIN = EPIGENOME / "chromatin"
PRAXIS = CHROMATIN / "Praxis.md"
PRAXIS_ARCHIVE = CHROMATIN / "Praxis Archive.md"
TONUS = CHROMATIN / "Tonus.md"
DAILY = CHROMATIN / "Daily"

# Engrams (memory)
ENGRAMS = EPIGENOME / "engrams"
MEMORY_INDEX = ENGRAMS / "MEMORY.md"

# Epigenome structure
PHENOTYPE = EPIGENOME / "phenotype"
COFACTORS = EPIGENOME / "cofactors"
PACEMAKERS = EPIGENOME / "pacemakers"
BUD_ENGRAMS = EPIGENOME / "bud-engrams"

# Chromatin subdirs
IMMUNITY = CHROMATIN / "immunity"
CHEMOSENSORY = CHROMATIN / "chemosensory"
INTEROCEPTION = CHROMATIN / "interoception"
TRANSCRIPTS = CHROMATIN / "transcripts"
HETEROCHROMATIN = CHROMATIN / "heterochromatin"

# Germline structure
MEMBRANE = GERMLINE / "membrane"
CYTOSKELETON = MEMBRANE / "cytoskeleton"
RECEPTORS = MEMBRANE / "receptors"
BUDS = MEMBRANE / "buds"
COLONIES = MEMBRANE / "colonies"
EFFECTORS = GERMLINE / "effectors"
REGULON = GERMLINE / "regulon"
OPERONS = GERMLINE / "operons"
SYMBIONTS = GERMLINE / "symbionts"
ASSAYS = GERMLINE / "assays"

# CC integration
CLAUDE_DIR = HOME / ".claude"
CLAUDE_HOOKS = CLAUDE_DIR / "hooks"
CLAUDE_SKILLS = CLAUDE_DIR / "skills"
