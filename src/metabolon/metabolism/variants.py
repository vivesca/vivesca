"""Genome variant storage — tool descriptions as versioned markdown files."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from metabolon.locus import variants_root

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_ROOT = variants_root


class Genome:
    """Manages tool description variants on disk.

    Each tool gets a locus directory with v0.md (founding, immutable),
    v1.md, v2.md, etc. A metadata.json tracks which allele is active.
    """

    def __init__(self, germ_line: Path = DEFAULT_ROOT, allele_cap: int = 5):
        self.germ_line = germ_line
        self.allele_cap = allele_cap

    def _locus_dir(self, tool: str) -> Path:
        return self.germ_line / tool

    def _allele_metadata_path(self, tool: str) -> Path:
        return self._locus_dir(tool) / "metadata.json"

    def _read_meta(self, tool: str) -> dict:
        mp = self._allele_metadata_path(tool)
        if mp.exists():
            return json.loads(mp.read_text())
        return {"active": 0, "next_id": 1}

    def _write_meta(self, tool: str, meta: dict) -> None:
        mp = self._allele_metadata_path(tool)
        mp.write_text(json.dumps(meta))

    def seed_tool(self, tool: str, description: str) -> None:
        """Create a tool directory with its founding variant (v0).

        Idempotent — if v0 already exists, does nothing.
        """
        d = self._locus_dir(tool)
        d.mkdir(parents=True, exist_ok=True)
        v0 = d / "v0.md"
        if not v0.exists():
            v0.write_text(description)
            self._write_meta(tool, {"active": 0, "next_id": 1})

    def active_allele(self, tool: str) -> str:
        """Return the description text of the currently active variant."""
        meta = self._read_meta(tool)
        vfile = self._locus_dir(tool) / f"v{meta['active']}.md"
        return vfile.read_text()

    def founding_allele(self, tool: str) -> str:
        """Return the founding (v0) description. Always immutable."""
        return (self._locus_dir(tool) / "v0.md").read_text()

    def express_variant(self, tool: str, description: str) -> int:
        """Add a new allele, returning its id. Enforces allele cap."""
        meta = self._read_meta(tool)
        vid = meta["next_id"]
        (self._locus_dir(tool) / f"v{vid}.md").write_text(description)
        meta["next_id"] = vid + 1
        self._write_meta(tool, meta)
        self._enforce_cap(tool)
        return vid

    def promote(self, tool: str, allele_id: int) -> None:
        """Set an allele as the active description for a tool."""
        meta = self._read_meta(tool)
        vfile = self._locus_dir(tool) / f"v{allele_id}.md"
        if not vfile.exists():
            raise ValueError(f"Variant v{allele_id} does not exist for {tool}")
        meta["active"] = allele_id
        self._write_meta(tool, meta)

    def allele_variants(self, tool: str) -> list[int]:
        """Return sorted list of variant ids for a tool."""
        d = self._locus_dir(tool)
        ids = []
        for f in d.glob("v*.md"):
            try:
                ids.append(int(f.stem[1:]))
            except ValueError:
                continue
        return sorted(ids)

    def expressed_tools(self) -> list[str]:
        """Return names of all tools with stored variants."""
        if not self.germ_line.exists():
            return []
        return [d.name for d in self.germ_line.iterdir() if d.is_dir()]

    def _enforce_cap(self, tool: str) -> None:
        """Evict oldest non-founding, non-active alleles if over cap."""
        variants = self.allele_variants(tool)
        if len(variants) <= self.allele_cap:
            return
        meta = self._read_meta(tool)
        active = meta["active"]
        # Recessive alleles: non-founding, non-active (evict oldest first)
        recessive_alleles = [v for v in variants if v != 0 and v != active]
        while len(variants) > self.allele_cap and recessive_alleles:
            evicted_allele = recessive_alleles.pop(0)
            (self._locus_dir(tool) / f"v{evicted_allele}.md").unlink()
            variants.remove(evicted_allele)
