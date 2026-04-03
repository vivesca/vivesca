from __future__ import annotations

"""Property-based tests for temporal-golem queue parsing.

Uses Hypothesis to generate random queue lines and verify the parser never
crashes and that counts are consistent.
"""

import tempfile
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# Load dispatch module via exec (standard pattern for effectors)
def _load_dispatch():
    source = (Path.home() / "germline/effectors/temporal-golem/dispatch.py").read_text()
    ns: dict = {"__name__": "dispatch_under_test_props"}
    exec(source, ns)
    return ns


_mod = _load_dispatch()
parse_queue = _mod["parse_queue"]


def _with_tmp_queue(content: str) -> Path:
    """Write content to a temp queue file, point the module at it, return path."""
    tmpdir = Path(tempfile.mkdtemp())
    qfile = tmpdir / "golem-queue.md"
    qfile.write_text(content)
    _mod["QUEUE_FILE"] = qfile
    return qfile


# ── Strategies ────────────────────────────────────────────────────────────

_task_hex = st.from_regex(r"[0-9a-f]{6}", fullmatch=True)
_provider = st.sampled_from(["zhipu", "volcano", "gemini", "infini", "codex"])
_max_turns = st.integers(min_value=1, max_value=200)
_prompt = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Z"), max_codepoint=127),
    min_size=1,
    max_size=80,
)
_status = st.sampled_from(["- [ ] ", "- [!!] "])


@st.composite
def queue_line(draw):
    status = draw(_status)
    has_task_id = draw(st.booleans())
    task_hex = draw(_task_hex) if has_task_id else ""
    provider = draw(_provider)
    max_turns = draw(_max_turns)
    prompt = draw(_prompt)
    task_id_part = f"[t-{task_hex}] " if has_task_id else ""
    return f'{status}`golem {task_id_part}--provider {provider} --max-turns {max_turns} "{prompt}"`'


_noise_line = st.one_of(
    st.just("### Section header"),
    st.just("Some explanatory text"),
    st.just(""),
    st.just('- [x] `golem [t-d0ne11] --provider zhipu "done task"`'),
    st.just('- [!] `golem [t-fa1l22] --provider zhipu "failed task"`'),
)


# ── Property tests ────────────────────────────────────────────────────────


@given(line=queue_line())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
def test_parse_queue_never_crashes(line):
    """Parser should handle any well-formed queue line without exceptions."""
    _with_tmp_queue(line + "\n")
    result = parse_queue()
    assert isinstance(result, list)


@given(lines=st.lists(queue_line(), min_size=0, max_size=10))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_queue_count_matches(lines):
    """Number of parsed tasks should equal number of lines."""
    _with_tmp_queue("\n".join(lines) + ("\n" if lines else ""))
    result = parse_queue()
    assert len(result) == len(lines)


@given(lines=st.lists(queue_line(), min_size=1, max_size=5))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_queue_every_task_has_provider(lines):
    """Every parsed task should have a provider string."""
    _with_tmp_queue("\n".join(lines) + "\n")
    result = parse_queue()
    for _, _prompt, provider, _tid, _turns in result:
        assert isinstance(provider, str)
        assert len(provider) > 0


@given(lines=st.lists(queue_line(), min_size=1, max_size=5))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_queue_every_task_has_task_id(lines):
    """Every parsed task should have a task_id starting with t-."""
    _with_tmp_queue("\n".join(lines) + "\n")
    result = parse_queue()
    for _, _prompt, _provider, task_id, _turns in result:
        assert task_id.startswith("t-")
        assert len(task_id) == 8  # t-XXXXXX


@given(lines=st.lists(queue_line(), min_size=1, max_size=5))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_queue_every_task_has_positive_max_turns(lines):
    """Every parsed task should have max_turns > 0."""
    _with_tmp_queue("\n".join(lines) + "\n")
    result = parse_queue()
    for _, _prompt, _provider, _tid, max_turns in result:
        assert isinstance(max_turns, int)
        assert max_turns > 0


@given(task_lines=st.lists(queue_line(), min_size=1, max_size=5), noise=st.lists(_noise_line, min_size=0, max_size=5))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_parse_queue_ignores_noise(task_lines, noise):
    """Parser should only return pending tasks, ignoring noise and completed/failed lines."""
    import random
    all_lines = task_lines + noise
    random.shuffle(all_lines)
    _with_tmp_queue("\n".join(all_lines) + "\n")
    result = parse_queue()
    assert len(result) == len(task_lines)
