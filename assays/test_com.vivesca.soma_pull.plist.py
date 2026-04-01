"""Tests for com.vivesca.soma-pull.plist — launchd plist validation."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PLIST_PATH = Path.home() / "germline" / "effectors" / "com.vivesca.soma-pull.plist"
SOMA_PULL_PATH = Path.home() / "germline" / "effectors" / "soma-pull"


def _parse_plist() -> dict[str, object]:
    """Parse the plist XML and return a flat dict of top-level keys."""
    tree = ET.parse(str(PLIST_PATH))
    root = tree.getroot()
    assert root.tag == "plist"
    dict_el = root.find("dict")
    assert dict_el is not None

    result: dict[str, object] = {}
    children = list(dict_el)
    # plist dict: alternating <key> and value element
    for i in range(0, len(children) - 1, 2):
        key = children[i]
        val = children[i + 1]
        assert key.tag == "key"
        if val.tag == "string":
            result[key.text] = val.text
        elif val.tag == "integer":
            result[key.text] = int(val.text)
        elif val.tag == "true":
            result[key.text] = True
        elif val.tag == "false":
            result[key.text] = False
        elif val.tag == "array":
            result[key.text] = [el.text for el in val]
        else:
            result[key.text] = val
    return result


# ── Structural / XML validity tests ────────────────────────────────────


def test_plist_file_exists():
    """The plist file exists on disk."""
    assert PLIST_PATH.is_file()


def test_plist_is_valid_xml():
    """The plist parses as well-formed XML."""
    ET.parse(str(PLIST_PATH))  # raises ParseError if invalid


def test_plist_root_tag():
    """Root element is <plist version='1.0'>."""
    root = ET.parse(str(PLIST_PATH)).getroot()
    assert root.tag == "plist"
    assert root.attrib.get("version") == "1.0"


def test_plist_has_dict_child():
    """Root plist contains exactly one top-level <dict>."""
    root = ET.parse(str(PLIST_PATH)).getroot()
    dicts = root.findall("dict")
    assert len(dicts) == 1


# ── Key presence tests ────────────────────────────────────────────────


def test_plist_has_required_keys():
    """All required launchd keys are present."""
    data = _parse_plist()
    required = ["Label", "ProgramArguments", "StartInterval",
                 "StandardOutPath", "StandardErrorPath", "RunAtLoad"]
    for key in required:
        assert key in data, f"Missing key: {key}"


# ── Label tests ───────────────────────────────────────────────────────


def test_label_matches_filename():
    """Label matches com.vivesca.soma-pull."""
    data = _parse_plist()
    assert data["Label"] == "com.vivesca.soma-pull"


# ── ProgramArguments tests ────────────────────────────────────────────


def test_program_arguments_is_list():
    """ProgramArguments is a list of strings."""
    data = _parse_plist()
    assert isinstance(data["ProgramArguments"], list)
    assert len(data["ProgramArguments"]) >= 2


def test_program_arguments_second_is_soma_pull():
    """Second ProgramArgument is the soma-pull script path."""
    data = _parse_plist()
    args = data["ProgramArguments"]
    assert args[1].endswith("soma-pull")


def test_soma_pull_script_exists():
    """The soma-pull script referenced by the plist exists."""
    assert SOMA_PULL_PATH.is_file()


def test_soma_pull_is_executable():
    """The soma-pull script is executable."""
    assert SOMA_PULL_PATH.stat().st_mode & 0o111


# ── StartInterval tests ──────────────────────────────────────────────


def test_start_interval_is_900():
    """StartInterval is 900 seconds (15 minutes)."""
    data = _parse_plist()
    assert data["StartInterval"] == 900


# ── RunAtLoad tests ──────────────────────────────────────────────────


def test_run_at_load_is_true():
    """RunAtLoad is true."""
    data = _parse_plist()
    assert data["RunAtLoad"] is True


# ── Log path tests ───────────────────────────────────────────────────


def test_stdout_log_path():
    """StandardOutPath is a .log file under tmp/."""
    data = _parse_plist()
    path = data["StandardOutPath"]
    assert path.endswith(".log")
    assert "soma-pull" in path


def test_stderr_log_path():
    """StandardErrorPath is a .log file under tmp/."""
    data = _parse_plist()
    path = data["StandardErrorPath"]
    assert path.endswith(".log")
    assert "soma-pull" in path


# ── No extra unexpected keys ─────────────────────────────────────────


def test_no_unexpected_keys():
    """Plist contains only known launchd keys (no typos / cruft)."""
    known = {"Label", "ProgramArguments", "StartInterval",
             "StandardOutPath", "StandardErrorPath", "RunAtLoad"}
    data = _parse_plist()
    for key in data:
        assert key in known, f"Unexpected key: {key}"
