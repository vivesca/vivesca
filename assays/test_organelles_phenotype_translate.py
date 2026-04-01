"""Tests for metabolon.organelles.phenotype_translate."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.phenotype_translate import (
    CC_TO_GEMINI_EVENT,
    GEMINI_ADAPTER_PATH,
    GEMINI_SETTINGS_PATH,
    SyncResult,
    TranslationResult,
    _ensure_symlink,
    _is_synaptic_script,
    _wrap_command,
    diff_settings,
    merge_hooks_into_gemini,
    read_cc_settings,
    read_gemini_settings,
    sync_phenotype,
    translate_hooks,
    translate_to_gemini,
)


# ── fixtures ────────────────────────────────────────────────────────────────

ADAPTER = Path("/fake/gemini_adapter.py")


def _cc_hooks_one_command(event: str = "PreToolUse", command: str = "python3 /some/hooks/synapse.py") -> dict:
    """Build a minimal CC hooks dict with one command hook."""
    return {
        event: [
            {
                "hooks": [
                    {"type": "command", "command": command},
                ],
            },
        ],
    }


def _cc_hooks_with_matcher() -> dict:
    return {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {"type": "command", "command": "python3 /some/hooks/check.py"},
                ],
            },
        ],
    }


# ── _is_synaptic_script ────────────────────────────────────────────────────

class TestIsSynapticScript:
    def test_hooks_dir(self) -> None:
        assert _is_synaptic_script("python3 ~/.claude/hooks/synapse.py") is True

    def test_synaptic_dir(self) -> None:
        assert _is_synaptic_script("python3 ~/germline/synaptic/axon.py") is True

    def test_absolute_path_hooks(self) -> None:
        assert _is_synaptic_script("/usr/bin/python3 /home/terry/.claude/hooks/dendrite.py") is True

    def test_non_hook_script(self) -> None:
        assert _is_synaptic_script("python3 /tmp/random.py") is False

    def test_no_py_file(self) -> None:
        assert _is_synaptic_script("echo hello") is False

    def test_empty_command(self) -> None:
        assert _is_synaptic_script("") is False

    def test_non_synaptic_py(self) -> None:
        assert _is_synaptic_script("python3 ~/scripts/myscript.py") is False


# ── _wrap_command ───────────────────────────────────────────────────────────

class TestWrapCommand:
    def test_basic_python3(self) -> None:
        wrapped = _wrap_command("python3 ~/hooks/synapse.py", ADAPTER)
        assert str(ADAPTER) in wrapped
        assert "~/hooks/synapse.py" in wrapped
        assert wrapped.startswith("python3")

    def test_with_env(self) -> None:
        wrapped = _wrap_command("/usr/bin/env python3 ~/hooks/synapse.py", ADAPTER)
        assert "/usr/bin/env" in wrapped
        assert str(ADAPTER) in wrapped

    def test_non_python_command(self) -> None:
        wrapped = _wrap_command("bash /some/hooks/script.sh", ADAPTER)
        # Non-python gets wrapped with python3 adapter
        assert "python3" in wrapped
        assert str(ADAPTER) in wrapped

    def test_empty_command(self) -> None:
        assert _wrap_command("", ADAPTER) == ""


# ── translate_hooks ────────────────────────────────────────────────────────

class TestTranslateHooks:
    def test_event_mapping(self) -> None:
        """All mapped events translate correctly."""
        cc = _cc_hooks_one_command("PreToolUse")
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
        assert "BeforeTool" in gemini
        assert result.hooks_translated == 1

    def test_all_event_mappings(self) -> None:
        """Every CC_TO_GEMINI_EVENT key produces a Gemini event."""
        for cc_event, gemini_event in CC_TO_GEMINI_EVENT.items():
            cc = _cc_hooks_one_command(cc_event)
            gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
            assert gemini_event in gemini, f"{cc_event} → {gemini_event} missing"
            assert result.hooks_translated == 1

    def test_unknown_event_dropped(self) -> None:
        cc = _cc_hooks_one_command("SomeWeirdEvent")
        cc["SomeWeirdEvent"][0]["hooks"][0]["command"] = "python3 x.py"
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
        assert "SomeWeirdEvent" in result.events_dropped
        assert len(gemini) == 0

    def test_silently_dropped_event(self) -> None:
        cc = _cc_hooks_one_command("InstructionsLoaded")
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
        assert "InstructionsLoaded" not in result.events_dropped
        assert len(gemini) == 0

    def test_prompt_hook_skipped(self) -> None:
        cc = {
            "Stop": [
                {
                    "hooks": [
                        {"type": "prompt", "command": "Say hello"},
                    ],
                },
            ],
        }
        with pytest.warns(UserWarning, match="prompt-type hook"):
            gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
        assert result.prompt_hooks_skipped == 1
        assert len(gemini) == 0

    def test_command_hook_translated(self) -> None:
        cc = _cc_hooks_one_command()
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER, wrap=False)
        assert result.hooks_translated == 1
        assert result.hooks_wrapped == 0

    def test_synaptic_script_wrapped(self) -> None:
        cc = _cc_hooks_one_command(command="python3 ~/.claude/hooks/synapse.py")
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER, wrap=True)
        assert result.hooks_wrapped == 1
        assert str(ADAPTER) in gemini["BeforeTool"][0]["hooks"][0]["command"]

    def test_wrap_disabled(self) -> None:
        cc = _cc_hooks_one_command(command="python3 ~/.claude/hooks/synapse.py")
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER, wrap=False)
        assert result.hooks_wrapped == 0
        cmd = gemini["BeforeTool"][0]["hooks"][0]["command"]
        assert cmd == "python3 ~/.claude/hooks/synapse.py"

    def test_matcher_preserved(self) -> None:
        cc = _cc_hooks_with_matcher()
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER, wrap=False)
        assert gemini["BeforeTool"][0]["matcher"] == "Bash"

    def test_empty_hooks(self) -> None:
        gemini, result = translate_hooks({}, adapter_path=ADAPTER)
        assert gemini == {}
        assert result.hooks_translated == 0

    def test_unknown_hook_type_skipped(self) -> None:
        cc = {
            "Stop": [
                {
                    "hooks": [
                        {"type": "unknown_type", "command": "echo hi"},
                    ],
                },
            ],
        }
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER)
        assert len(gemini) == 0
        assert result.hooks_translated == 0

    def test_multiple_definitions(self) -> None:
        cc = {
            "PreToolUse": [
                {"hooks": [{"type": "command", "command": "python3 a.py"}]},
                {"hooks": [{"type": "command", "command": "python3 b.py"}]},
            ],
        }
        gemini, result = translate_hooks(cc, adapter_path=ADAPTER, wrap=False)
        assert len(gemini["BeforeTool"]) == 2
        assert result.hooks_translated == 2


# ── TranslationResult ──────────────────────────────────────────────────────

class TestTranslationResult:
    def test_summary_basic(self) -> None:
        r = TranslationResult(hooks_translated=3, hooks_wrapped=1, prompt_hooks_skipped=0, events_dropped=[], dry_run=False)
        s = r.summary
        assert "Translated 3 hook(s)." in s
        assert "Wrapped 1" in s

    def test_summary_dry_run(self) -> None:
        r = TranslationResult(hooks_translated=1, hooks_wrapped=0, prompt_hooks_skipped=0, events_dropped=[], dry_run=True)
        assert "(dry-run)" in r.summary

    def test_summary_with_skipped_and_dropped(self) -> None:
        r = TranslationResult(hooks_translated=2, hooks_wrapped=0, prompt_hooks_skipped=1, events_dropped=["Foo"], dry_run=False)
        s = r.summary
        assert "Skipped 1 prompt-type" in s
        assert "Foo" in s


# ── read_cc_settings / read_gemini_settings ────────────────────────────────

class TestReadSettings:
    def test_read_cc_missing_file(self, tmp_path: Path) -> None:
        assert read_cc_settings(tmp_path / "nope.json") == {}

    def test_read_cc_valid(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_text('{"hooks": {}}', encoding="utf-8")
        assert read_cc_settings(p) == {"hooks": {}}

    def test_read_cc_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_text("NOT JSON", encoding="utf-8")
        assert read_cc_settings(p) == {}

    def test_read_gemini_missing(self, tmp_path: Path) -> None:
        assert read_gemini_settings(tmp_path / "nope.json") == {}

    def test_read_gemini_valid(self, tmp_path: Path) -> None:
        p = tmp_path / "settings.json"
        p.write_text('{"hooks": {"BeforeTool": []}}', encoding="utf-8")
        data = read_gemini_settings(p)
        assert "hooks" in data


# ── merge_hooks_into_gemini ────────────────────────────────────────────────

class TestMergeHooks:
    def test_merge_into_empty(self) -> None:
        merged = merge_hooks_into_gemini({}, {"BeforeTool": []})
        assert "hooks" in merged

    def test_merge_preserves_other_keys(self) -> None:
        current = {"theme": "dark", "hooks": {"old": []}}
        merged = merge_hooks_into_gemini(current, {"BeforeTool": []})
        assert merged["theme"] == "dark"
        assert "BeforeTool" in merged["hooks"]

    def test_empty_gemini_hooks_no_overwrite(self) -> None:
        current = {"theme": "dark"}
        merged = merge_hooks_into_gemini(current, {})
        assert "hooks" not in merged


# ── diff_settings ──────────────────────────────────────────────────────────

class TestDiffSettings:
    def test_no_changes(self) -> None:
        assert diff_settings({"a": 1}, {"a": 1}) == "(no changes)"

    def test_with_changes(self) -> None:
        diff = diff_settings({"a": 1}, {"a": 2})
        assert "-  \"a\": 1" in diff or '"a": 1' in diff
        assert "+  \"a\": 2" in diff or '"a": 2' in diff


# ── _ensure_symlink ────────────────────────────────────────────────────────

class TestEnsureSymlink:
    def test_create_new(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# phenotype")
        link = tmp_path / "link.md"
        assert _ensure_symlink(link, target, dry_run=False) == "fixed"
        assert link.is_symlink()

    def test_correct_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# phenotype")
        link = tmp_path / "link.md"
        link.symlink_to(target)
        assert _ensure_symlink(link, target, dry_run=False) == "ok"

    def test_wrong_target_fixed(self, tmp_path: Path) -> None:
        target1 = tmp_path / "old.md"
        target1.write_text("old")
        target2 = tmp_path / "new.md"
        target2.write_text("new")
        link = tmp_path / "link.md"
        link.symlink_to(target1)
        assert _ensure_symlink(link, target2, dry_run=False) == "fixed"
        assert link.resolve() == target2.resolve()

    def test_regular_file_blocks(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# phenotype")
        link = tmp_path / "link.md"
        link.write_text("I am a regular file")
        assert _ensure_symlink(link, target, dry_run=False) == "failed"

    def test_dry_run_does_not_create(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# phenotype")
        link = tmp_path / "link.md"
        assert _ensure_symlink(link, target, dry_run=True) == "fixed"
        assert not link.exists()

    def test_dry_run_does_not_fix_wrong_target(self, tmp_path: Path) -> None:
        target1 = tmp_path / "old.md"
        target1.write_text("old")
        target2 = tmp_path / "new.md"
        target2.write_text("new")
        link = tmp_path / "link.md"
        link.symlink_to(target1)
        assert _ensure_symlink(link, target2, dry_run=True) == "fixed"
        # Should still point to old target
        assert link.resolve() == target1.resolve()


# ── SyncResult ─────────────────────────────────────────────────────────────

class TestSyncResult:
    def test_ok_true(self) -> None:
        r = SyncResult(
            symlinks_ok=["/a"], symlinks_fixed=[], symlinks_failed=[],
            hooks_result=None, gemini_md_ok=True, integrin_issues=[],
            unknown_platforms=[], dry_run=False,
        )
        assert r.ok is True

    def test_ok_false_failed_symlink(self) -> None:
        r = SyncResult(
            symlinks_ok=[], symlinks_fixed=[], symlinks_failed=["/bad"],
            hooks_result=None, gemini_md_ok=True, integrin_issues=[],
            unknown_platforms=[], dry_run=False,
        )
        assert r.ok is False

    def test_ok_false_integrin_issues(self) -> None:
        r = SyncResult(
            symlinks_ok=["/a"], symlinks_fixed=[], symlinks_failed=[],
            hooks_result=None, gemini_md_ok=True,
            integrin_issues=[{"path": "/x", "problem": "broken"}],
            unknown_platforms=[], dry_run=False,
        )
        assert r.ok is False

    def test_ok_false_gemini_md(self) -> None:
        r = SyncResult(
            symlinks_ok=["/a"], symlinks_fixed=[], symlinks_failed=[],
            hooks_result=None, gemini_md_ok=False, integrin_issues=[],
            unknown_platforms=[], dry_run=False,
        )
        assert r.ok is False

    def test_summary_contains_sections(self) -> None:
        r = SyncResult(
            symlinks_ok=["/a"], symlinks_fixed=["/b"], symlinks_failed=[],
            hooks_result=TranslationResult(1, 0, 0, [], False),
            gemini_md_ok=True, integrin_issues=[], unknown_platforms=[],
            dry_run=False, skills_synced=3,
        )
        s = r.summary
        assert "Symlinks" in s
        assert "Hooks" in s
        assert "Skills" in s
        assert "GEMINI.md" in s
        assert "Integrin" in s

    def test_summary_dry_run(self) -> None:
        r = SyncResult(
            symlinks_ok=["/a"], symlinks_fixed=[], symlinks_failed=[],
            hooks_result=None, gemini_md_ok=True, integrin_issues=[],
            unknown_platforms=[], dry_run=True,
        )
        assert "(dry-run)" in r.summary

    def test_summary_unknown_platforms(self) -> None:
        r = SyncResult(
            symlinks_ok=[], symlinks_fixed=[], symlinks_failed=[],
            hooks_result=None, gemini_md_ok=True, integrin_issues=[],
            unknown_platforms=["wombo"], dry_run=False,
        )
        assert "wombo" in r.summary


# ── sync_phenotype (mocked) ────────────────────────────────────────────────

class TestSyncPhenotype:
    """sync_phenotype uses local imports from metabolon.locus and integrin.

    We patch at the *source* module because the function does
    ``from metabolon.locus import ...`` inside its body.
    """

    @patch("metabolon.enzymes.integrin._check_phenotype_symlinks", return_value=([], []))
    @patch("metabolon.locus.phenotype_md")
    @patch("metabolon.locus.PLATFORM_SYMLINKS")
    @patch("metabolon.locus.receptors")
    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings", return_value={})
    @patch("metabolon.organelles.phenotype_translate.read_cc_settings")
    def test_sync_dry_run(
        self,
        mock_read_cc: MagicMock,
        mock_read_gemini: MagicMock,
        mock_receptors: MagicMock,
        mock_platforms: MagicMock,
        mock_phenotype_md: MagicMock,
        mock_check: MagicMock,
        tmp_path: Path,
    ) -> None:
        cc_path = tmp_path / ".claude" / "settings.json"
        cc_path.parent.mkdir(parents=True)
        cc_path.write_text(json.dumps({
            "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python3 /hooks/synapse.py"}]}]}
        }))
        gemini_path = tmp_path / ".gemini" / "settings.json"

        mock_read_cc.return_value = json.loads(cc_path.read_text())
        mock_platforms.__iter__ = lambda self: iter([])
        mock_receptors.is_dir.return_value = False
        mock_phenotype_md.resolve.return_value = Path("/fake/phenotype.md")

        result = sync_phenotype(
            dry_run=True,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert isinstance(result, SyncResult)
        assert result.dry_run is True

    @patch("metabolon.enzymes.integrin._check_phenotype_symlinks", return_value=([], []))
    @patch("metabolon.locus.phenotype_md")
    @patch("metabolon.locus.PLATFORM_SYMLINKS")
    @patch("metabolon.locus.receptors")
    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings", return_value={})
    def test_sync_no_cc_settings(
        self,
        mock_read_gemini: MagicMock,
        mock_receptors: MagicMock,
        mock_platforms: MagicMock,
        mock_phenotype_md: MagicMock,
        mock_check: MagicMock,
        tmp_path: Path,
    ) -> None:
        cc_path = tmp_path / "nonexistent.json"
        gemini_path = tmp_path / ".gemini" / "settings.json"

        # cc_path doesn't exist → hooks_result should be None
        mock_platforms.__iter__ = lambda self: iter([])
        mock_receptors.is_dir.return_value = False
        mock_phenotype_md.resolve.return_value = Path("/fake/phenotype.md")

        result = sync_phenotype(
            dry_run=False,
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
        )
        assert result.hooks_result is None


# ── translate_to_gemini ────────────────────────────────────────────────────

class TestTranslateToGemini:
    def test_dry_run_no_write(self, tmp_path: Path) -> None:
        cc_path = tmp_path / "cc_settings.json"
        cc_path.write_text(json.dumps({
            "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python3 a.py"}]}]}
        }))
        gemini_path = tmp_path / ".gemini" / "settings.json"

        with patch("metabolon.organelles.phenotype_translate.read_gemini_settings", return_value={}):
            result, diff_text = translate_to_gemini(
                cc_settings_path=cc_path,
                gemini_settings_path=gemini_path,
                adapter_path=ADAPTER,
                wrap=False,
                dry_run=True,
            )
        assert isinstance(result, TranslationResult)
        assert result.dry_run is True
        assert not gemini_path.exists()

    def test_live_write(self, tmp_path: Path) -> None:
        cc_path = tmp_path / "cc_settings.json"
        cc_path.write_text(json.dumps({
            "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python3 stop.py"}]}]}
        }))
        gemini_path = tmp_path / ".gemini" / "settings.json"

        with patch("metabolon.organelles.phenotype_translate.read_gemini_settings", return_value={}):
            result, diff_text = translate_to_gemini(
                cc_settings_path=cc_path,
                gemini_settings_path=gemini_path,
                adapter_path=ADAPTER,
                wrap=False,
                dry_run=False,
            )
        assert gemini_path.exists()
        data = json.loads(gemini_path.read_text())
        assert "hooks" in data
        assert "AfterAgent" in data["hooks"]

    def test_empty_hooks_no_changes(self, tmp_path: Path) -> None:
        cc_path = tmp_path / "cc_settings.json"
        cc_path.write_text(json.dumps({"hooks": {}}))
        gemini_path = tmp_path / ".gemini" / "settings.json"

        with patch("metabolon.organelles.phenotype_translate.read_gemini_settings", return_value={}):
            result, diff_text = translate_to_gemini(
                cc_settings_path=cc_path,
                gemini_settings_path=gemini_path,
                adapter_path=ADAPTER,
                dry_run=True,
            )
        assert diff_text == "(no changes)"
