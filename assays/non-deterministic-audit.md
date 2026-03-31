# Non-deterministic Test Audit

**Date:** 2026-03-31
**Scope:** `assays/test_*.py` (all test files)

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 High | 3 | Will fail under CI load or clock boundary |
| 🟡 Medium | 6 | Fragile timing/date assumptions |
| 🟢 Low | ~15 | Uses live clock for fixture data (mostly safe) |

---

## 🔴 HIGH — Likely to fail under load

### 1. `test_chemoreception.py:152` — 2-second clock tolerance
```python
assert abs(content - time.time()) < 2
```
**Issue:** Asserts debounce timestamp is within 2s of live clock. Under CI load (GC pause, container throttling) this can exceed 2s.
**Fix:** Patch `time.time` to a fixed value, or widen tolerance to 10s, or assert only that `content > 0`.

### 2. `test_linkedin_monitor.py:1843-1863` — Performance assertions
```python
assert elapsed < 1.0  # 1000 hashes should take < 1 second
assert elapsed < 2.0  # 100 parses should take < 2 seconds
```
**Issue:** Wall-clock performance tests. Fail under CI resource contention.
**Fix:** Use `@pytest.mark.slow` and skip in CI, or replace with algorithmic complexity assertions.

### 3. `test_cytokinesis.py:870-871` — Narrow time-delta window
```python
delta = datetime.now() - parsed
assert 7000 < delta.total_seconds() < 7300  # ~2 hours ± 5 min
```
**Issue:** Asserts a "2 hours ago" timestamp is within a 5-minute window of live clock. Fragile.
**Fix:** Patch `datetime.now` in the code under test, or widen the window.

---

## 🟡 MEDIUM — Fragile timing/date assumptions

### 4. `test_capco_prep.py:150` — `time.sleep(0.1)` for mtime ordering
```python
time.sleep(0.1)
new = _file(capco, "new.txt", "new")
```
**Issue:** Relies on filesystem mtime resolution after 100ms sleep. On very fast filesystems (tmpfs) the mtime may not differ.
**Fix:** Set mtime explicitly with `os.utime(path, (old_time, old_time))`.

### 5. `test_histone_integration.py:69` — `time.sleep(0.05)` for mtime ordering
**Same pattern as #4.** 50ms sleep to ensure different mtimes.

### 6. `test_chemoreceptor.py:59` — `assert result == str(date.today())`
**Issue:** Tests a `_today_date()` helper against live clock. Theoretically fails at midnight rollover. Practically safe but not hermetic.
**Fix:** Patch `date.today` to return a fixed date.

### 7. `test_consulting_card.py:106,166` — `date.today()` in assertions
```python
assert f"created: {date.today().isoformat()}" in md
assert path.name == f"{today_str}-ai-governance.md"
```
**Issue:** Same midnight-rollover concern as #6.

### 8. `test_circadian_probe.py:546,778` — `date.today()` in assertions
```python
assert date.today().isoformat() in result
```
**Issue:** Tests that `build_digest()` includes today's date. Midnight-rollover risk.

### 9. `test_cytokinesis.py` (12 occurrences) — `datetime.now()` in assertions
Lines: 648, 666, 692, 700, 721, 870, 1456, 1472, 1494, 1649, 1686, 2084, 2096
**Issue:** Pattern `today = datetime.now().strftime(...)` then asserts generated output contains `today`. Midnight-rollover risk.

---

## 🟢 LOW — Live clock used for fixture data (mostly safe)

These use `time.time()` to construct test fixture timestamps but don't assert against live clock:

| File | Lines | Pattern |
|------|-------|---------|
| `test_electroreception_actions.py` | 33, 57, 84, 112 | `apple_ns = int((time.time() - 978307200) * 1_000_000_000)` |
| `test_circadian_probe.py` | 106, 133, 161, 184, 211 | `old_time = time.time() - (N * 86400)` |
| `test_capco_prep.py` | 45 | `old_time = time.time() - age_days * 86400` |
| `test_cytokinesis.py` | 156, 164, 172, 1783–1808 | `old_mtime = time.time() - N` |
| `test_gemmule_clean.py` | 34, 43, 49 | `old_time = time.time() - age_seconds` |
| `test_legatum.py` | 99–123 | `now = time.time()` then patches both getmtime and time.time |
| `test_autoimmune.py` | 168–237 | `datetime.now() + timedelta(...)` for test fixture dates |
| `test_chromatin_decay_report.py` | 207, 215 | `datetime.now() - timedelta(...)` for fixture dates |
| `test_demethylase.py` | 384 | `datetime.now().strftime(...)` in test helper |
| `test_methylation.py` | 88–89 | `datetime.now(UTC) - timedelta(...)` for fixture dates |
| `test_methylation_review.py` | 162, 198 | `datetime.now()` for test fixture dates |

These are **safe** because the live clock is only used to generate relative offsets. No assertion depends on the exact wall-clock time.

---

## Not flagged (correctly handled)

- **`test_legatum.py`** — Uses `time.time()` then immediately patches both `os.path.getmtime` and `time.time` via `with patch(...)`. Fully deterministic.
- **`test_endocytosis_rss_fetcher.py`** — Network calls via `requests.get` are properly `@patch`ed.
- **`test_lacuna.py`** — `httpx.Client` used only in mock setup, no real network calls.
- **Subprocess integration tests** — Scripts are invoked via `subprocess.run` for integration testing. These depend on tool availability but are not timing-dependent.
- **`os.getpid()`** in `test_golem.py` — PID is stable within a test run. Not a non-determinism source.
