from __future__ import annotations

"""Tests for com.vivesca.soma-pull.plist — macOS LaunchAgent plist for soma-pull."""

import xml.etree.ElementTree as ET
from pathlib import Path

PLIST_PATH = Path.home() / "germline/effectors/com.vivesca.soma-pull.plist"


def _parse_plist():
    return ET.parse(str(PLIST_PATH)).getroot()


def _dict_pairs(dict_elem):
    """Yield (key, value) pairs from a plist <dict> element."""
    children = list(dict_elem)
    for i in range(0, len(children), 2):
        yield children[i].text, children[i + 1]


def _dict_value(dict_elem, target_key):
    """Return the value element for a given key in a plist <dict>."""
    for k, v in _dict_pairs(dict_elem):
        if k == target_key:
            return v
    return None


def _array_strings(array_elem):
    """Return list of <string> texts from a plist <array>."""
    return [s.text for s in array_elem.findall("string")]


# ── structural tests ──────────────────────────────────────────────────


def test_plist_file_exists():
    """Plist file exists on disk."""
    assert PLIST_PATH.is_file()


def test_plist_valid_xml():
    """Plist parses as well-formed XML."""
    ET.parse(str(PLIST_PATH))


def test_root_is_plist():
    """Root element is <plist>."""
    root = _parse_plist()
    assert root.tag == "plist"


def test_root_has_version_attribute():
    """Root <plist> has version='1.0'."""
    root = _parse_plist()
    assert root.get("version") == "1.0"


def test_top_level_is_dict():
    """Single top-level child is <dict>."""
    root = _parse_plist()
    children = list(root)
    assert len(children) == 1
    assert children[0].tag == "dict"


# ── Label ──────────────────────────────────────────────────────────────


def test_label_key_present():
    """Label key exists in the dict."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "Label") is not None


def test_label_value():
    """Label matches com.vivesca.soma-pull."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "Label").text == "com.vivesca.soma-pull"


# ── ProgramArguments ──────────────────────────────────────────────────


def test_program_arguments_present():
    """ProgramArguments key exists."""
    root = _parse_plist()
    d = next(iter(root))
    val = _dict_value(d, "ProgramArguments")
    assert val is not None
    assert val.tag == "array"


def test_program_arguments_has_two_entries():
    """ProgramArguments contains exactly python3 path and soma-pull script."""
    root = _parse_plist()
    d = next(iter(root))
    args = _array_strings(_dict_value(d, "ProgramArguments"))
    assert len(args) == 2


def test_program_arguments_first_is_python():
    """First argument ends with python3."""
    root = _parse_plist()
    d = next(iter(root))
    args = _array_strings(_dict_value(d, "ProgramArguments"))
    assert args[0].endswith("python3")


def test_program_arguments_second_is_soma_pull():
    """Second argument points to soma-pull effector."""
    root = _parse_plist()
    d = next(iter(root))
    args = _array_strings(_dict_value(d, "ProgramArguments"))
    assert args[1].endswith("effectors/soma-pull")


# ── StartInterval ─────────────────────────────────────────────────────


def test_start_interval_present():
    """StartInterval key exists."""
    root = _parse_plist()
    d = next(iter(root))
    val = _dict_value(d, "StartInterval")
    assert val is not None


def test_start_interval_900_seconds():
    """StartInterval is 900 seconds (15 minutes)."""
    root = _parse_plist()
    d = next(iter(root))
    val = _dict_value(d, "StartInterval")
    assert val.text == "900"
    assert int(val.text) == 900


# ── StandardOutPath / StandardErrorPath ───────────────────────────────


def test_stdout_path_present():
    """StandardOutPath key exists."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "StandardOutPath") is not None


def test_stderr_path_present():
    """StandardErrorPath key exists."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "StandardErrorPath") is not None


def test_stdout_path_is_log():
    """StandardOutPath ends with soma-pull-stdout.log."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "StandardOutPath").text.endswith("soma-pull-stdout.log")


def test_stderr_path_is_log():
    """StandardErrorPath ends with soma-pull-stderr.log."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "StandardErrorPath").text.endswith("soma-pull-stderr.log")


# ── RunAtLoad ─────────────────────────────────────────────────────────


def test_run_at_load_present():
    """RunAtLoad key exists."""
    root = _parse_plist()
    d = next(iter(root))
    assert _dict_value(d, "RunAtLoad") is not None


def test_run_at_load_is_true():
    """RunAtLoad is set to true."""
    root = _parse_plist()
    d = next(iter(root))
    val = _dict_value(d, "RunAtLoad")
    assert val.tag == "true"


# ── key count ─────────────────────────────────────────────────────────


def test_dict_has_expected_key_count():
    """Top-level dict has exactly 6 keys."""
    root = _parse_plist()
    d = next(iter(root))
    keys = [c.text for c in d.findall("key")]
    assert len(keys) == 6
    expected = {
        "Label",
        "ProgramArguments",
        "StartInterval",
        "StandardOutPath",
        "StandardErrorPath",
        "RunAtLoad",
    }
    assert set(keys) == expected
