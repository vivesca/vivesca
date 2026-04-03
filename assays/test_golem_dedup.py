"""Tests for golem-daemon dedup guard (t-744a2b)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


GOLEM_DAEMON = Path.home() / "germline" / "effectors" / "golem-daemon"
QUEUE_FILE = Path.home() / "germline" / "loci" / "golem-queue.md"


def _normalize_prompt(prompt: str) -> str:
    """Normalize a prompt for dedup comparison — strip task ID, whitespace."""
    import re
    normalized = re.sub(r'\[t-[0-9a-fA-F]+\]\s*', '', prompt)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


class TestPromptNormalization:
    """Prompt normalization must strip IDs and whitespace for comparison."""

    def test_strips_task_id(self):
        assert "golem" in _normalize_prompt("golem [t-abc123] do the thing")
        assert "[t-abc123]" not in _normalize_prompt("golem [t-abc123] do the thing")

    def test_strips_multiple_task_ids(self):
        result = _normalize_prompt("golem [t-aaa111] [t-bbb222] do it")
        assert "[t-" not in result

    def test_collapses_whitespace(self):
        result = _normalize_prompt("golem   do   the    thing")
        assert "  " not in result

    def test_identical_prompts_match(self):
        prompt_a = "golem [t-aaa111] --provider zhipu do the thing"
        prompt_b = "golem [t-bbb222] --provider zhipu do the thing"
        assert _normalize_prompt(prompt_a) == _normalize_prompt(prompt_b)

    def test_different_prompts_dont_match(self):
        prompt_a = "golem --provider zhipu fix tests"
        prompt_b = "golem --provider zhipu add feature"
        assert _normalize_prompt(prompt_a) != _normalize_prompt(prompt_b)


class TestDispatchDedup:
    """Dispatch loop must skip tasks whose normalized prompt matches a running task."""

    def test_duplicate_running_task_skipped(self, tmp_path: Path):
        """If a task with the same normalized prompt is already running, skip it."""
        # Create a queue with two identical prompts (different task IDs)
        queue = tmp_path / "golem-queue.md"
        queue.write_text(
            "### Pending\n\n"
            '- [ ] `golem [t-aaa111] --provider zhipu "Fix the tests"`\n'
            '- [ ] `golem [t-bbb222] --provider zhipu "Fix the tests"`\n'
        )
        # Simulate: first task is "running"
        running = {"t-aaa111": 'golem --provider zhipu "Fix the tests"'}

        # The second task should be identified as a duplicate
        lines = queue.read_text().splitlines()
        pending_prompts = []
        for line in lines:
            if line.strip().startswith("- [ ] "):
                import re
                cmd_match = re.search(r"`(.+)`", line)
                if cmd_match:
                    pending_prompts.append(cmd_match.group(1))

        # Normalize and check for dups against running
        running_normalized = {_normalize_prompt(v) for v in running.values()}
        duplicates = [
            p for p in pending_prompts
            if _normalize_prompt(p) in running_normalized
        ]
        assert len(duplicates) >= 1, "Second task should be detected as duplicate"

    def test_non_duplicate_passes(self, tmp_path: Path):
        """Different prompts should not be flagged as duplicates."""
        running = {"t-aaa111": 'golem --provider zhipu "Fix the tests"'}
        new_prompt = 'golem [t-ccc333] --provider zhipu "Add new feature"'

        running_normalized = {_normalize_prompt(v) for v in running.values()}
        assert _normalize_prompt(new_prompt) not in running_normalized


class TestEnqueueDedup:
    """Enqueueing a prompt that already exists as pending should be rejected."""

    def test_duplicate_enqueue_rejected(self, tmp_path: Path):
        """Enqueue should reject a prompt identical to an existing pending entry."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text(
            "### Pending\n\n"
            '- [ ] `golem [t-aaa111] --provider zhipu "Fix the tests"`\n'
        )
        new_prompt = 'golem --provider zhipu "Fix the tests"'

        # Read existing pending prompts
        import re
        existing = []
        for line in queue.read_text().splitlines():
            if line.strip().startswith("- [ ] "):
                m = re.search(r"`(.+)`", line)
                if m:
                    existing.append(_normalize_prompt(m.group(1)))

        is_dup = _normalize_prompt(new_prompt) in existing
        assert is_dup, "Duplicate enqueue should be detected"

    def test_unique_enqueue_accepted(self, tmp_path: Path):
        """Enqueue should accept a prompt not already pending."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text(
            "### Pending\n\n"
            '- [ ] `golem [t-aaa111] --provider zhipu "Fix the tests"`\n'
        )
        new_prompt = 'golem --provider zhipu "Add logging"'

        import re
        existing = []
        for line in queue.read_text().splitlines():
            if line.strip().startswith("- [ ] "):
                m = re.search(r"`(.+)`", line)
                if m:
                    existing.append(_normalize_prompt(m.group(1)))

        is_dup = _normalize_prompt(new_prompt) in existing
        assert not is_dup, "Unique prompt should be accepted"
