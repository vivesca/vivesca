from __future__ import annotations

"""Tests for metabolon.organelles.phenotype_translate."""

import json
import warnings
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.phenotype_translate import (
    CC_TO_GEMINI_EVENT,
    GEMINI_ADAPTER_PATH,
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


# ── _is_synaptic_script ────────────────────────────────────────────────────


class TestIsSynapticScript:
    def test_hooks_dir_script(self):
        assert _is_synaptic_script("python3 ~/.claude/hooks/synapse.py") is True

    def test_synaptic_dir_script(self):
        assert _is_synaptic_script("python3 ~/germline/synaptic/axon.py") is True

    def test_absolute_path_hooks(self):
        assert _is_synaptic_script("/usr/bin/python3 /home/terry/.claude/hooks/foo.py") is True

    def test_absolute_path_synaptic(self):
        assert _is_synaptic_script("python3 /home/terry/germline/synaptic/bar.py") is True

    def test_non_synaptic_script(self):
        assert _is_synaptic_script("python3 /tmp/random.py") is False

    def test_non_python_command(self):
        assert _is_synaptic_script("bash -c 'echo hi'") is False

    def test_empty_command(self):
        assert _is_synaptic_script("") is False

    def test_whitespace_command(self):
        assert _is_synaptic_script("   ") is False

    def test_env_python_hooks(self):
        assert _is_synaptic_script("/usr/bin/env python3 ~/.claude/hooks/test.py") is True


# ── _wrap_command ──────────────────────────────────────────────────────────


class TestWrapCommand:
    def test_wraps_python_script(self):
        adapter = Path("/some/gemini_adapter.py")
        result = _wrap_command("python3 ~/.claude/hooks/synapse.py", adapter)
        assert "/some/gemini_adapter.py" in result
        assert "~/.claude/hooks/synapse.py" in result

    def test_wraps_with_env(self):
        adapter = Path("/adapter.py")
        result = _wrap_command("/usr/bin/env python3 ~/germline/synaptic/axon.py", adapter)
        assert "/usr/bin/env" in result
        assert "/adapter.py" in result

    def test_wraps_non_python_command(self):
        adapter = Path("/adapter.py")
        result = _wrap_command("bash run.sh", adapter)
        # Should prepend python3 and adapter
        assert "python3" in result
        assert "/adapter.py" in result
        assert "bash run.sh" in result

    def test_empty_command(self):
        adapter = Path("/adapter.py")
        result = _wrap_command("", adapter)
        assert result == ""

    def test_python_no_args(self):
        adapter = Path("/adapter.py")
        result = _wrap_command("python3", adapter)
        assert "python3" in result


# ── translate_hooks ────────────────────────────────────────────────────────


class TestTranslateHooks:
    def _make_hook(self, command: str, hook_type: str = "command") -> dict:
        return {"type": hook_type, "command": command}

    def _make_definition(self, *hooks: dict, matcher: str | None = None) -> dict:
        d: dict[str, Any] = {"hooks": list(hooks)}
        if matcher is not None:
            d["matcher"] = matcher
        return d

    def test_basic_event_mapping(self):
        cc_hooks = {
            "UserPromptSubmit": [self._make_definition(self._make_hook("echo hi"))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert "BeforeAgent" in gemini_hooks
        assert result.hooks_translated == 1

    def test_all_event_mappings(self):
        cc_hooks = {}
        for cc_event in CC_TO_GEMINI_EVENT:
            cc_hooks[cc_event] = [self._make_definition(self._make_hook("echo test"))]
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert result.hooks_translated == len(CC_TO_GEMINI_EVENT)
        assert set(gemini_hooks.keys()) == set(CC_TO_GEMINI_EVENT.values())

    def test_notification_passes_through(self):
        cc_hooks = {
            "Notification": [self._make_definition(self._make_hook("notify.sh"))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert "Notification" in gemini_hooks
        assert result.hooks_translated == 1

    def test_unknown_event_dropped(self):
        cc_hooks = {
            "FakeEvent": [self._make_definition(self._make_hook("echo hi"))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert "FakeEvent" not in gemini_hooks
        assert result.events_dropped == ["FakeEvent"]

    def test_instructions_loaded_silently_dropped(self):
        cc_hooks = {
            "InstructionsLoaded": [self._make_definition(self._make_hook("echo hi"))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert len(gemini_hooks) == 0
        assert result.events_dropped == []

    def test_prompt_hook_skipped_with_warning(self):
        cc_hooks = {
            "UserPromptSubmit": [self._make_definition(self._make_hook("echo hi", "prompt"))],
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert result.prompt_hooks_skipped == 1
        assert len(w) == 1
        assert "prompt-type hook" in str(w[0].message)

    def test_unknown_hook_type_skipped(self):
        cc_hooks = {
            "UserPromptSubmit": [self._make_definition(self._make_hook("", "weird_type"))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert result.hooks_translated == 0
        assert result.prompt_hooks_skipped == 0

    def test_synaptic_script_wrapped(self):
        cmd = "python3 ~/.claude/hooks/synapse.py"
        cc_hooks = {
            "PreToolUse": [self._make_definition(self._make_hook(cmd))],
        }
        adapter = Path("/path/to/gemini_adapter.py")
        gemini_hooks, result = translate_hooks(cc_hooks, adapter_path=adapter, wrap=True)
        assert result.hooks_wrapped == 1
        translated_cmd = gemini_hooks["BeforeTool"][0]["hooks"][0]["command"]
        assert "/path/to/gemini_adapter.py" in translated_cmd
        assert "synapse.py" in translated_cmd

    def test_wrap_disabled(self):
        cmd = "python3 ~/.claude/hooks/synapse.py"
        cc_hooks = {
            "PreToolUse": [self._make_definition(self._make_hook(cmd))],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert result.hooks_wrapped == 0
        assert gemini_hooks["BeforeTool"][0]["hooks"][0]["command"] == cmd

    def test_matcher_preserved(self):
        cc_hooks = {
            "PreToolUse": [
                self._make_definition(self._make_hook("echo hi"), matcher="Bash")
            ],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert gemini_hooks["BeforeTool"][0]["matcher"] == "Bash"

    def test_empty_definition_skipped(self):
        """A definition with no matching hooks (e.g. all prompts) yields no entry."""
        cc_hooks = {
            "UserPromptSubmit": [self._make_definition(self._make_hook("hi", "prompt"))],
        }
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert "BeforeAgent" not in gemini_hooks

    def test_multiple_hooks_in_one_definition(self):
        cc_hooks = {
            "Stop": [
                self._make_definition(
                    self._make_hook("echo one"),
                    self._make_hook("echo two"),
                )
            ],
        }
        gemini_hooks, result = translate_hooks(cc_hooks, wrap=False)
        assert len(gemini_hooks["AfterAgent"][0]["hooks"]) == 2
        assert result.hooks_translated == 2


# ── TranslationResult ──────────────────────────────────────────────────────


class TestTranslationResult:
    def test_summary_basic(self):
        r = TranslationResult(
            hooks_translated=3,
            hooks_wrapped=1,
            prompt_hooks_skipped=0,
            events_dropped=[],
            dry_run=False,
        )
        s = r.summary
        assert "Translated 3 hook(s)." in s
        assert "Wrapped 1 synaptic script(s)" in s

    def test_summary_dry_run(self):
        r = TranslationResult(
            hooks_translated=1,
            hooks_wrapped=0,
            prompt_hooks_skipped=0,
            events_dropped=[],
            dry_run=True,
        )
        assert "(dry-run)" in r.summary

    def test_summary_with_skipped_prompts(self):
        r = TranslationResult(
            hooks_translated=1,
            hooks_wrapped=0,
            prompt_hooks_skipped=2,
            events_dropped=[],
            dry_run=False,
        )
        assert "Skipped 2 prompt-type hook(s)" in r.summary

    def test_summary_with_dropped_events(self):
        r = TranslationResult(
            hooks_translated=1,
            hooks_wrapped=0,
            prompt_hooks_skipped=0,
            events_dropped=["FooEvent", "BarEvent"],
            dry_run=False,
        )
        assert "FooEvent, BarEvent" in r.summary


# ── read_cc_settings / read_gemini_settings ────────────────────────────────


class TestReadSettings:
    def test_read_cc_settings_valid(self, tmp_path):
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps({"hooks": {}}), encoding="utf-8")
        result = read_cc_settings(settings_file)
        assert result == {"hooks": {}}

    def test_read_cc_settings_missing(self, tmp_path):
        result = read_cc_settings(tmp_path / "nonexistent.json")
        assert result == {}

    def test_read_cc_settings_invalid_json(self, tmp_path):
        bad_file = tmp_path / "settings.json"
        bad_file.write_text("{invalid json", encoding="utf-8")
        result = read_cc_settings(bad_file)
        assert result == {}

    def test_read_gemini_settings_valid(self, tmp_path):
        settings_file = tmp_path / "gemini_settings.json"
        settings_file.write_text(json.dumps({"hooks": {"BeforeAgent": []}}), encoding="utf-8")
        result = read_gemini_settings(settings_file)
        assert "hooks" in result

    def test_read_gemini_settings_missing(self, tmp_path):
        result = read_gemini_settings(tmp_path / "nonexistent.json")
        assert result == {}

    def test_read_settings_os_error(self, tmp_path):
        """OSError (e.g. permission denied) returns empty dict."""
        bad_file = tmp_path / "settings.json"
        bad_file.write_text("{}", encoding="utf-8")
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = read_cc_settings(bad_file)
        assert result == {}


# ── merge_hooks_into_gemini ────────────────────────────────────────────────


class TestMergeHooksIntoGemini:
    def test_merge_adds_hooks(self):
        current = {"someKey": "value"}
        gemini_hooks = {"BeforeAgent": [{"hooks": []}]}
        merged = merge_hooks_into_gemini(current, gemini_hooks)
        assert merged["hooks"] == gemini_hooks
        assert merged["someKey"] == "value"

    def test_merge_empty_hooks_preserves_current(self):
        current = {"someKey": "value"}
        merged = merge_hooks_into_gemini(current, {})
        assert "hooks" not in merged
        assert merged == current

    def test_merge_replaces_existing_hooks(self):
        current = {"hooks": {"old": []}}
        new_hooks = {"BeforeAgent": [{"hooks": []}]}
        merged = merge_hooks_into_gemini(current, new_hooks)
        assert merged["hooks"] == new_hooks


# ── diff_settings ──────────────────────────────────────────────────────────


class TestDiffSettings:
    def test_no_changes(self):
        current = {"a": 1}
        assert diff_settings(current, current) == "(no changes)"

    def test_detects_changes(self):
        current = {"a": 1}
        proposed = {"a": 2}
        diff = diff_settings(current, proposed)
        assert "current" in diff
        assert "proposed" in diff
        assert "-  \"a\": 1" in diff
        assert "+  \"a\": 2" in diff


# ── _ensure_symlink ────────────────────────────────────────────────────────


class TestEnsureSymlink:
    def test_correct_symlink_returns_ok(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        assert _ensure_symlink(link, target, dry_run=False) == "ok"

    def test_wrong_target_fixed(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        wrong_target = tmp_path / "wrong.txt"
        wrong_target.write_text("wrong")
        link = tmp_path / "link.txt"
        link.symlink_to(wrong_target)
        assert _ensure_symlink(link, target, dry_run=False) == "fixed"
        assert link.resolve() == target.resolve()

    def test_wrong_target_dry_run_not_fixed(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        wrong_target = tmp_path / "wrong.txt"
        wrong_target.write_text("wrong")
        link = tmp_path / "link.txt"
        link.symlink_to(wrong_target)
        assert _ensure_symlink(link, target, dry_run=True) == "fixed"
        # Link should still point to wrong target in dry run
        assert link.resolve() == wrong_target.resolve()

    def test_missing_symlink_created(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        assert _ensure_symlink(link, target, dry_run=False) == "fixed"
        assert link.resolve() == target.resolve()

    def test_missing_symlink_dry_run_not_created(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        assert _ensure_symlink(link, target, dry_run=True) == "fixed"
        assert not link.exists()

    def test_regular_file_blocks_symlink(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        blocking = tmp_path / "link.txt"
        blocking.write_text("blocking")
        assert _ensure_symlink(blocking, target, dry_run=False) == "failed"

    def test_os_error_returns_failed(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        with patch.object(Path, "symlink_to", side_effect=OSError("nope")):
            assert _ensure_symlink(link, target, dry_run=False) == "failed"


# ── SyncResult ─────────────────────────────────────────────────────────────


class TestSyncResult:
    def test_ok_when_everything_passes(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is True

    def test_not_ok_when_symlinks_failed(self):
        r = SyncResult(
            symlinks_ok=[],
            symlinks_fixed=[],
            symlinks_failed=["/bad/link"],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_not_ok_when_integrin_issues(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=True,
            integrin_issues=[{"path": "x", "problem": "missing"}],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_not_ok_when_gemini_md_missing(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=[],
            symlinks_failed=[],
            hooks_result=None,
            gemini_md_ok=False,
            integrin_issues=[],
            unknown_platforms=[],
            dry_run=False,
        )
        assert r.ok is False

    def test_summary_contains_sections(self):
        r = SyncResult(
            symlinks_ok=["a"],
            symlinks_fixed=["b"],
            symlinks_failed=[],
            hooks_result=TranslationResult(1, 0, 0, [], False),
            gemini_md_ok=True,
            integrin_issues=[],
            unknown_platforms=["weirdOS"],
            dry_run=True,
            skills_synced=5,
        )
        s = r.summary
        assert "Symlinks" in s
        assert "Hooks" in s
        assert "Skills" in s
        assert "GEMINI.md" in s
        assert "Integrin" in s
        assert "weirdOS" in s
        assert "(dry-run)" in s


# ── sync_phenotype (mocked) ────────────────────────────────────────────────


class TestSyncPhenotype:
    def _mock_locus(self, tmp_path):
        """Build mock objects for metabolon.locus imports."""
        mock_locus = MagicMock()
        mock_locus.PLATFORM_SYMLINKS = [tmp_path / "link1.md"]
        mock_locus.phenotype_md = tmp_path / "phenotype.md"
        mock_locus.phenotype_md.write_text("identity")
        # receptors dir with a skill
        receptors = tmp_path / "receptors"
        skill_dir = receptors / "my_skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")
        mock_locus.receptors = receptors
        return mock_locus

    @patch("metabolon.organelles.phenotype_translate.read_cc_settings")
    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings")
    @patch("metabolon.organelles.phenotype_translate._ensure_symlink")
    def test_sync_dry_run(
        self, mock_ensure, mock_read_gemini, mock_read_cc, tmp_path
    ):
        mock_ensure.return_value = "ok"
        mock_read_cc.return_value = {"hooks": {}}
        mock_read_gemini.return_value = {}

        cc_path = tmp_path / "cc_settings.json"
        cc_path.write_text("{}", encoding="utf-8")
        gemini_path = tmp_path / "gemini_settings.json"

        mock_locus = self._mock_locus(tmp_path)
        mock_integrin = MagicMock(return_value=([], []))

        with patch.dict(
            "sys.modules",
            {
                "metabolon.locus": mock_locus,
                "metabolon.enzymes.integrin": mock_integrin,
            },
        ):
            # Also need to patch the imports inside sync_phenotype
            with patch(
                "metabolon.organelles.phenotype_translate.Path.is_symlink",
                return_value=False,
            ), patch(
                "metabolon.organelles.phenotype_translate.Path.resolve",
                return_value=tmp_path / "different.md",
            ):
                result = sync_phenotype(
                    dry_run=True,
                    cc_settings_path=cc_path,
                    gemini_settings_path=gemini_path,
                )
        assert isinstance(result, SyncResult)
        assert result.dry_run is True

    @patch("metabolon.organelles.phenotype_translate._ensure_symlink")
    def test_sync_no_cc_settings_skips_hooks(self, mock_ensure, tmp_path):
        mock_ensure.return_value = "ok"
        cc_path = tmp_path / "cc_settings.json"
        # File doesn't exist → cc_settings_path.exists() returns False

        mock_locus = self._mock_locus(tmp_path)
        mock_integrin = MagicMock(return_value=([], []))

        with patch.dict(
            "sys.modules",
            {
                "metabolon.locus": mock_locus,
                "metabolon.enzymes.integrin": mock_integrin,
            },
        ):
            with patch(
                "metabolon.organelles.phenotype_translate.Path.is_symlink",
                return_value=False,
            ), patch(
                "metabolon.organelles.phenotype_translate.Path.resolve",
                return_value=tmp_path / "different.md",
            ):
                result = sync_phenotype(
                    cc_settings_path=tmp_path / "nonexistent.json",
                    gemini_settings_path=tmp_path / "gemini.json",
                )
        assert result.hooks_result is None


# ── translate_to_gemini (mocked I/O) ───────────────────────────────────────


class TestTranslateToGemini:
    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings")
    @patch("metabolon.organelles.phenotype_translate.read_cc_settings")
    def test_dry_run_no_write(self, mock_read_cc, mock_read_gemini, tmp_path):
        mock_read_cc.return_value = {
            "hooks": {
                "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo hi"}]}],
            }
        }
        mock_read_gemini.return_value = {}

        cc_path = tmp_path / "cc.json"
        cc_path.write_text("{}", encoding="utf-8")
        gemini_path = tmp_path / "gemini.json"

        result, diff_text = translate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
            dry_run=True,
        )
        assert isinstance(result, TranslationResult)
        assert result.dry_run is True
        assert result.hooks_translated == 1
        # gemini.json should NOT be created in dry run
        assert not gemini_path.exists()

    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings")
    @patch("metabolon.organelles.phenotype_translate.read_cc_settings")
    def test_writes_gemini_settings(self, mock_read_cc, mock_read_gemini, tmp_path):
        mock_read_cc.return_value = {
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "echo done"}]}],
            }
        }
        mock_read_gemini.return_value = {"existingKey": True}

        cc_path = tmp_path / "cc.json"
        cc_path.write_text("{}", encoding="utf-8")
        gemini_path = tmp_path / "gemini.json"

        result, diff_text = translate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
            dry_run=False,
        )
        assert result.hooks_translated == 1
        assert gemini_path.exists()
        written = json.loads(gemini_path.read_text(encoding="utf-8"))
        assert "hooks" in written
        assert "AfterAgent" in written["hooks"]
        assert written["existingKey"] is True

    @patch("metabolon.organelles.phenotype_translate.read_gemini_settings")
    @patch("metabolon.organelles.phenotype_translate.read_cc_settings")
    def test_no_changes_diff(self, mock_read_cc, mock_read_gemini, tmp_path):
        """When hooks are empty, diff should show no changes."""
        mock_read_cc.return_value = {"hooks": {}}
        mock_read_gemini.return_value = {}

        cc_path = tmp_path / "cc.json"
        cc_path.write_text("{}", encoding="utf-8")
        gemini_path = tmp_path / "gemini.json"

        result, diff_text = translate_to_gemini(
            cc_settings_path=cc_path,
            gemini_settings_path=gemini_path,
            dry_run=True,
        )
        assert diff_text == "(no changes)"
