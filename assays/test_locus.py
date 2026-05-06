"""Tests for locus — canonical path registry."""

from pathlib import Path

from metabolon.locus import (
    PLATFORM_SYMLINKS,
    assays,
    chromatin,
    claude_dir,
    effectors,
    epigenome,
    g1,
    germline,
    home,
    marks,
    memory_index,
    phenotype_md,
    praxis,
)


def test_home_is_home():
    assert home == Path.home()


def test_locus_germline_under_home():
    assert germline == home / "germline"


def test_epigenome_under_home():
    assert epigenome == home / "epigenome"


def test_chromatin_under_epigenome():
    assert chromatin == epigenome / "chromatin"


def test_praxis_path():
    assert praxis == chromatin / "Praxis.md"


def test_g1_path():
    assert g1 == chromatin / "G1.md"


def test_marks_under_epigenome():
    assert marks == epigenome / "marks"


def test_memory_index():
    assert memory_index == marks / "MEMORY.md"


def test_germline_exists():
    assert germline.exists()


def test_epigenome_exists():
    assert epigenome.exists()


def test_effectors_under_germline():
    assert effectors == germline / "effectors"


def test_assays_under_germline():
    assert assays == germline / "assays"


def test_claude_dir():
    assert claude_dir == home / ".claude"


def test_platform_symlinks_is_list():
    assert isinstance(PLATFORM_SYMLINKS, list)
    assert all(isinstance(p, Path) for p in PLATFORM_SYMLINKS)


def test_phenotype_md_path():
    assert phenotype_md.name == "phenotype.md"
