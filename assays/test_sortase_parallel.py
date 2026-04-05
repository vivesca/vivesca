from __future__ import annotations

"""Integration test for parallel sortase dispatch — verifies status.json atomicity under concurrency."""


import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

import pytest

from metabolon.sortase.executor import _status_path, register_running, unregister_running

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_status_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point sortase executor at a temporary status directory for test isolation."""
    status_file = tmp_path / "status.json"
    monkeypatch.setenv("OPIFEX_STATUS_PATH", str(status_file))
    return tmp_path


def _read_status() -> list:
    """Read current status.json contents."""
    path = _status_path()
    if not path.exists():
        return []
    return json.loads(path.read_text())


def test_parallel_register_creates_exact_entries():
    """Three concurrent register_running() calls must produce exactly 3 entries."""
    task_ids = ["alpha", "beta", "gamma"]

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(lambda tid=tid: (register_running(tid), tid)[1]) for tid in task_ids
        ]
        results = [f.result() for f in as_completed(futures)]

    assert sorted(results) == sorted(task_ids)

    status = _read_status()
    assert len(status) == 3, f"expected 3 entries, got {len(status)}: {status}"
    assert sorted(status) == sorted(task_ids)

    # Verify valid JSON round-trip
    path = _status_path()
    parsed = json.loads(path.read_text())
    assert isinstance(parsed, list)
    assert sorted(parsed) == sorted(task_ids)


def test_parallel_unregister_empties_status():
    """Three concurrent unregister_running() calls must leave status.json as an empty list."""
    # Pre-populate with 3 entries
    task_ids = ["delta", "epsilon", "zeta"]
    for tid in task_ids:
        register_running(tid)

    assert len(_read_status()) == 3, "precondition: 3 entries before unregister"

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(lambda tid=tid: (unregister_running(tid), tid)[1]) for tid in task_ids
        ]
        results = [f.result() for f in as_completed(futures)]

    assert sorted(results) == sorted(task_ids)

    status = _read_status()
    assert status == [], f"expected empty list after full unregister, got: {status}"

    # File should still be valid JSON
    path = _status_path()
    parsed = json.loads(path.read_text())
    assert parsed == []


def test_mixed_register_unregister_no_corruption():
    """Interleaved register and unregister must not corrupt status.json."""
    # Register 3, then unregister 1 — all launched simultaneously
    work = [
        ("register", "kappa"),
        ("register", "lambda"),
        ("register", "mu"),
        ("unregister", "kappa"),
    ]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = []
        for action, tid in work:
            if action == "register":
                futures.append(pool.submit(register_running, tid))
            else:
                futures.append(pool.submit(unregister_running, tid))
        results = [f.result() for f in as_completed(futures)]

    assert len(results) == 4

    # Should have exactly 2 remaining entries (lambda, mu)
    status = _read_status()
    assert len(status) == 2, f"expected 2 remaining entries, got {len(status)}: {status}"
    assert sorted(status) == ["lambda", "mu"]

    # Valid JSON
    path = _status_path()
    parsed = json.loads(path.read_text())
    assert isinstance(parsed, list)
