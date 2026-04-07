"""Tests for human-readable task IDs.

Task IDs encode harness, model, prompt slug, and hash for at-a-glance identification.
Format: {harness}-{model}-{slug}-{hash}
Example: ribosome-glm51-sha-gate-a1b2c3d4
"""

from __future__ import annotations

import re


class TestTaskIdFormat:
    """Task IDs include harness, model, slug, and hash."""

    def test_slug_from_prompt(self):
        from mtor.dispatch import _make_workflow_id

        wf_id = _make_workflow_id("Implement SHA gate for mtor dispatch", provider="zhipu")
        parts = wf_id.split("-")
        assert len(parts) > 3, f"ID too short, missing slug: {wf_id}"

    def test_includes_harness(self):
        """ID starts with the harness name (ribosome, opencode, droid)."""
        from mtor.dispatch import _make_workflow_id

        wf_id = _make_workflow_id("Add feature", provider="zhipu", harness="ribosome")
        assert wf_id.startswith("ribosome-")

        wf_id2 = _make_workflow_id("Add feature", provider="zhipu", harness="opencode")
        assert wf_id2.startswith("opencode-")

    def test_includes_model_short_name(self):
        """ID includes a short model identifier, not the full provider name."""
        from mtor.dispatch import _make_workflow_id

        wf_id = _make_workflow_id("Add feature", provider="zhipu")
        # "zhipu" maps to model "glm51" (or similar short form)
        # The second segment should be a model identifier, not the raw provider
        parts = wf_id.split("-")
        model_part = parts[1]
        assert len(model_part) <= 10, f"Model segment too long: {model_part}"

    def test_slug_is_lowercase_alphanumeric(self):
        from mtor.dispatch import _make_workflow_id

        wf_id = _make_workflow_id("Fix The BROKEN Cytokinesis CLI!!!", provider="zhipu")
        # Extract slug: between model and hash
        parts = wf_id.split("-")
        slug_part = "-".join(parts[2:-1])
        assert slug_part == slug_part.lower(), f"Slug not lowercase: {slug_part}"
        assert re.match(r"^[a-z0-9-]+$", slug_part), f"Slug has invalid chars: {slug_part}"

    def test_slug_max_length(self):
        from mtor.dispatch import _make_workflow_id

        long_prompt = "Implement a very long and detailed feature that spans multiple files and requires extensive refactoring of the entire codebase"
        wf_id = _make_workflow_id(long_prompt, provider="zhipu")
        assert len(wf_id) <= 80, f"ID too long: {len(wf_id)} chars"

    def test_hash_suffix_for_uniqueness(self):
        from mtor.dispatch import _make_workflow_id

        wf_id = _make_workflow_id("Add tests for feature X", provider="zhipu")
        parts = wf_id.split("-")
        hash_part = parts[-1]
        assert len(hash_part) == 8, f"Hash should be 8 chars: {hash_part}"
        assert re.match(r"^[0-9a-f]+$", hash_part), f"Hash not hex: {hash_part}"

    def test_different_prompts_different_ids(self):
        from mtor.dispatch import _make_workflow_id

        id1 = _make_workflow_id("Add feature A", provider="zhipu")
        id2 = _make_workflow_id("Add feature B", provider="zhipu")
        assert id1 != id2

    def test_same_prompt_same_id(self):
        """Deterministic — same prompt always produces same ID (for Temporal dedup)."""
        from mtor.dispatch import _make_workflow_id

        id1 = _make_workflow_id("Add feature A", provider="zhipu")
        id2 = _make_workflow_id("Add feature A", provider="zhipu")
        assert id1 == id2

    def test_different_harness_different_ids(self):
        """Same prompt on different harness = different ID."""
        from mtor.dispatch import _make_workflow_id

        id1 = _make_workflow_id("Add feature A", provider="zhipu", harness="ribosome")
        id2 = _make_workflow_id("Add feature A", provider="zhipu", harness="opencode")
        assert id1 != id2
