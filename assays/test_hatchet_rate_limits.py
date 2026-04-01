from __future__ import annotations

"""Tests for Hatchet server-side rate limits in hatchet-golem/worker.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

WORKER_PATH = "/home/terry/germline/effectors/hatchet-golem/worker.py"


def _exec_worker(mock_hatchet):
    """Exec the worker module with a mocked Hatchet and return the namespace."""
    ns: dict = {"__name__": "worker", "__file__": WORKER_PATH}
    with patch("hatchet_sdk.Hatchet", return_value=mock_hatchet):
        exec(open(WORKER_PATH).read(), ns)
    return ns


def _make_mock_hatchet():
    """Build a mock Hatchet with capturable .task() and .rate_limits."""
    mock_rate_limits = MagicMock()
    mock_hatchet = MagicMock()
    mock_hatchet.rate_limits = mock_rate_limits
    mock_hatchet.task.side_effect = lambda **kw: lambda fn: fn
    return mock_hatchet


def _capture_task_calls():
    """Load worker and capture the kwargs passed to each @hatchet.task call."""
    decorator_calls: list[dict] = []

    def capture_task(**kw):
        decorator_calls.append(kw)
        return lambda fn: fn

    mock_hatchet = MagicMock()
    mock_hatchet.task = capture_task
    mock_hatchet.rate_limits = MagicMock()

    _exec_worker(mock_hatchet)
    return decorator_calls


# ── Rate limit registration tests ──────────────────────────────────────


def test_rate_limit_keys_registered():
    """h.rate_limits.put() is called for all four provider keys."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    assert mock_hatchet.rate_limits.put.call_count == 5
    keys = [c.args[0] for c in mock_hatchet.rate_limits.put.call_args_list]
    assert keys == ["zhipu-rpm", "infini-rpm", "volcano-rpm", "gemini-rpm", "codex-rpm"]


def test_zhipu_rate_limit_params():
    """zhipu-rpm: 200 req/hour."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    call_args = mock_hatchet.rate_limits.put.call_args_list[0]
    assert call_args.args[0] == "zhipu-rpm"
    assert call_args.kwargs["limit"] == 200
    from hatchet_sdk.rate_limit import RateLimitDuration
    assert call_args.kwargs["duration"] == RateLimitDuration.HOUR


def test_infini_rate_limit_params():
    """infini-rpm: 200 req/hour."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    call_args = mock_hatchet.rate_limits.put.call_args_list[1]
    assert call_args.args[0] == "infini-rpm"
    assert call_args.kwargs["limit"] == 200
    from hatchet_sdk.rate_limit import RateLimitDuration
    assert call_args.kwargs["duration"] == RateLimitDuration.HOUR


def test_volcano_rate_limit_params():
    """volcano-rpm: 200 req/hour."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    call_args = mock_hatchet.rate_limits.put.call_args_list[2]
    assert call_args.args[0] == "volcano-rpm"
    assert call_args.kwargs["limit"] == 200
    from hatchet_sdk.rate_limit import RateLimitDuration
    assert call_args.kwargs["duration"] == RateLimitDuration.HOUR


def test_gemini_rate_limit_params():
    """gemini-rpm: 60 req/minute."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    call_args = mock_hatchet.rate_limits.put.call_args_list[3]
    assert call_args.args[0] == "gemini-rpm"
    assert call_args.kwargs["limit"] == 60
    from hatchet_sdk.rate_limit import RateLimitDuration
    assert call_args.kwargs["duration"] == RateLimitDuration.MINUTE


def test_codex_rate_limit_params():
    """codex-rpm: 60 req/minute."""
    mock_hatchet = _make_mock_hatchet()
    _exec_worker(mock_hatchet)

    call_args = mock_hatchet.rate_limits.put.call_args_list[4]
    assert call_args.args[0] == "codex-rpm"
    assert call_args.kwargs["limit"] == 60
    from hatchet_sdk.rate_limit import RateLimitDuration
    assert call_args.kwargs["duration"] == RateLimitDuration.MINUTE


# ── Task decorator rate_limits parameter tests ─────────────────────────


def test_all_tasks_have_rate_limits():
    """Every @hatchet.task has a non-empty rate_limits list."""
    calls = _capture_task_calls()
    for dc in calls:
        assert dc["rate_limits"], f"Task {dc['name']} missing rate_limits"
        assert len(dc["rate_limits"]) == 1


def test_zhipu_task_rate_limit_key():
    """golem-zhipu task uses 'zhipu-rpm' rate limit key."""
    calls = _capture_task_calls()
    zhipu = next(c for c in calls if c["name"] == "golem-zhipu")
    rl = zhipu["rate_limits"][0]
    assert rl.static_key == "zhipu-rpm"
    assert rl.units == 1


def test_infini_task_rate_limit_key():
    """golem-infini task uses 'infini-rpm' rate limit key."""
    calls = _capture_task_calls()
    infini = next(c for c in calls if c["name"] == "golem-infini")
    rl = infini["rate_limits"][0]
    assert rl.static_key == "infini-rpm"
    assert rl.units == 1


def test_volcano_task_rate_limit_key():
    """golem-volcano task uses 'volcano-rpm' rate limit key."""
    calls = _capture_task_calls()
    volcano = next(c for c in calls if c["name"] == "golem-volcano")
    rl = volcano["rate_limits"][0]
    assert rl.static_key == "volcano-rpm"
    assert rl.units == 1


def test_gemini_task_rate_limit_key():
    """golem-gemini task uses 'gemini-rpm' rate limit key."""
    calls = _capture_task_calls()
    gemini = next(c for c in calls if c["name"] == "golem-gemini")
    rl = gemini["rate_limits"][0]
    assert rl.static_key == "gemini-rpm"
    assert rl.units == 1


def test_codex_task_rate_limit_key():
    """golem-codex task uses 'codex-rpm' rate limit key."""
    calls = _capture_task_calls()
    codex = next(c for c in calls if c["name"] == "golem-codex")
    rl = codex["rate_limits"][0]
    assert rl.static_key == "codex-rpm"
    assert rl.units == 1


def test_five_tasks_registered():
    """Exactly 5 provider tasks are decorated."""
    calls = _capture_task_calls()
    assert len(calls) == 5
    names = {c["name"] for c in calls}
    assert names == {"golem-zhipu", "golem-infini", "golem-volcano", "golem-gemini", "golem-codex"}
