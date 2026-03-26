"""Locus — canonical paths for the organism.

Single source of truth. Effectors, tools, and scripts import from here
instead of hardcoding paths. When the organism moves, update this file only.

Usage:
    from metabolon.locus import germline, chromatin, praxis, engrams
"""

from pathlib import Path

home = Path.home()

# The two repos
germline = home / "germline"
epigenome = home / "epigenome"

# Chromatin (vault)
chromatin = epigenome / "chromatin"
praxis = chromatin / "Praxis.md"
praxis_archive = chromatin / "Praxis Archive.md"
tonus = chromatin / "Tonus.md"
daily = chromatin / "Daily"

# Engrams (memory)
engrams = epigenome / "engrams"
memory_index = engrams / "MEMORY.md"

# Epigenome structure
phenotype = epigenome / "phenotype"
cofactors = epigenome / "cofactors"
pacemakers = epigenome / "pacemakers"
bud_engrams = epigenome / "bud-engrams"

# Chromatin subdirs
immunity = chromatin / "immunity"
chemosensory = chromatin / "chemosensory"
interoception = chromatin / "interoception"
transcripts = chromatin / "transcripts"
heterochromatin = chromatin / "heterochromatin"

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

# CC integration
claude_dir = home / ".claude"
claude_hooks = claude_dir / "hooks"
claude_skills = claude_dir / "skills"
