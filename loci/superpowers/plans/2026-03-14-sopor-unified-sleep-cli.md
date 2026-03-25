# Sopor — Unified Sleep Health CLI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single Python CLI (`sopor`) that replaces oura-cli, somnus, and nyx — syncing Oura Ring + EightSleep data into one DuckDB and providing analysis, trends, and LLM-powered insights.

**Architecture:** Python package using Click for CLI, httpx (sync) for API calls, DuckDB for storage, Rich for display. Oura is the primary biometric source; EightSleep is supplementary. All analysis queries target the `nightly_sleep` denormalised table. `sopor why` uses `claude --print` (Max20, free) for LLM analysis.

**Tech Stack:** Python 3.10+, uv, Click, httpx, duckdb, Rich, python-dateutil

**Spec:** `~/docs/superpowers/specs/2026-03-14-sopor-design.md`

**Existing code to port from:**
- Oura API client: `~/code/oura-cli/src/client.rs` (endpoints, auth, models)
- Oura DB schema: `~/code/oura-cli/src/db.rs` (nightly_sleep table, upsert)
- Oura display: `~/code/oura-cli/src/display.rs` (formatting, scores, hypnogram)
- Oura models: `~/code/oura-cli/src/models.rs` (API response types)
- Oura sync script: `~/oura-data/scripts/sync.py` (Python sync reference — has keychain + env var token handling)
- EightSleep API: `~/code/somnus/src/auth.rs` + `~/code/somnus/src/api.rs` (OAuth, intervals endpoint)
- EightSleep models: `~/code/somnus/src/models.rs` (AuthResponse, Interval, Stage, Score, Timeseries)
- EightSleep DB: `~/code/somnus/src/db.rs` (sleep_sessions schema)
- Nyx analysis: `~/code/nyx/src/main.rs` (default view, trend, event, monthly — full file, 424 lines)

**DuckDB paths (existing):**
- Oura: `/Users/terry/oura-data/data/oura.duckdb`
- Somnus: `/Users/terry/.local/share/somnus/somnus.duckdb`
- New unified: `~/.local/share/sopor/sopor.duckdb`

**Credentials:**
- Oura: `OURA_TOKEN` env var (set in `~/.zshenv.local`), fallback `security find-generic-password -s oura-token -w`
- EightSleep: `op item get "Eight Sleep" --vault Agents --fields username/password --reveal`, fallback `EIGHTSLEEP_EMAIL` + `EIGHTSLEEP_PASSWORD` env vars
- EightSleep OAuth app: `CLIENT_ID = "0894c7f33bb94800a03f1f4df13a4f38"`, `CLIENT_SECRET = "f0954a3ed5763ba3d06834c73731a32f15f168f47d4f164751275def86db0c76"`, `AUTH_URL = "https://auth-api.8slp.net/v1/tokens"`

---

## File Structure

```
~/code/sopor/
├── pyproject.toml              # uv project, [project.scripts] sopor = "sopor.cli:cli"
├── AGENTS.md                   # Build/test/conventions for delegates
├── src/
│   └── sopor/
│       ├── __init__.py         # version only
│       ├── cli.py              # Click group + all subcommand imports
│       ├── db.py               # DuckDB: open, schema init, upsert helpers, query helpers
│       ├── oura.py             # Oura API client (sync httpx): token from env/keychain, all endpoints
│       ├── eightsleep.py       # EightSleep API client: op/env auth, OAuth login, intervals
│       ├── display.py          # Rich tables, ASCII charts, color helpers, duration formatting
│       └── commands/
│           ├── __init__.py
│           ├── sync.py         # sopor sync: both APIs → DuckDB
│           ├── today.py        # sopor today: combined last night view
│           ├── scores.py       # sopor scores: one-liner sleep/readiness/activity
│           ├── week.py         # sopor week: 7d table + 4w avg + delta
│           ├── trend.py        # sopor trend: N-day ASCII charts + regression
│           ├── event.py        # sopor event: before/after comparison
│           ├── monthly.py      # sopor monthly: summary + vault report
│           ├── hypnogram.py    # sopor hypnogram: sleep stage chart
│           ├── readiness.py    # sopor readiness: score + contributors
│           ├── activity.py     # sopor activity: steps/calories/movement
│           ├── hrv.py          # sopor hrv: HRV from sleep
│           ├── stress.py       # sopor stress: daily stress
│           ├── why.py          # sopor why: LLM analysis via claude --print
│           ├── json_cmd.py     # sopor json: raw Oura API JSON
│           └── migrate.py      # sopor migrate: one-time data migration
├── tests/
│   ├── __init__.py
│   ├── test_db.py              # Schema, upsert, query tests
│   ├── test_oura.py            # API client tests (mocked HTTP)
│   ├── test_eightsleep.py      # API client tests (mocked HTTP)
│   ├── test_display.py         # Formatting, chart, duration tests
│   └── conftest.py             # Shared fixtures (in-memory DuckDB, sample data)
└── .gitignore
```

---

## Chunk 1: Project Scaffold + Database Layer

### Task 1: Project scaffold

**Files:**
- Create: `~/code/sopor/pyproject.toml`
- Create: `~/code/sopor/src/sopor/__init__.py`
- Create: `~/code/sopor/src/sopor/cli.py`
- Create: `~/code/sopor/AGENTS.md`
- Create: `~/code/sopor/.gitignore`
- Create: `~/code/sopor/tests/__init__.py`
- Create: `~/code/sopor/tests/conftest.py`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p ~/code/sopor/src/sopor/commands ~/code/sopor/tests
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "sopor"
version = "0.1.0"
description = "Unified sleep health CLI — Oura Ring + EightSleep"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "duckdb>=1.0",
    "httpx>=0.27",
    "rich>=13.0",
    "python-dateutil>=2.8",
]

[project.scripts]
sopor = "sopor.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/sopor"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Write __init__.py**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Write minimal cli.py**

```python
import click

@click.group()
@click.version_option()
def cli():
    """Unified sleep health CLI — Oura Ring + EightSleep."""
    pass
```

- [ ] **Step 5: Write AGENTS.md**

```markdown
# Sopor — Build Guide

## Build & Run
```bash
cd ~/code/sopor
uv sync
uv run sopor --help
```

## Test
```bash
uv run pytest -v
```

## Conventions
- Python 3.10+, type hints on all public functions
- Click for CLI, httpx (sync) for HTTP, DuckDB for storage, Rich for display
- All commands work non-interactively (no prompts)
- `nightly_sleep` is the single analysis target for Oura data
- Oura is primary biometric source; EightSleep is supplementary
- Tests use in-memory DuckDB (`:memory:`)

## Key paths
- DB: `~/.local/share/sopor/sopor.duckdb`
- Oura token: `OURA_TOKEN` env var
- EightSleep: `op item get "Eight Sleep" --vault Agents`

## Gotchas
- EightSleep can have multiple sessions per night — PK is session_id, not date
- `bedtime_start` is stored as local HKT (no UTC conversion)
- Use `httpx.Client` (sync), NOT async
- `sopor why` writes context to `~/tmp/`, not `/tmp/`
```

- [ ] **Step 6: Write .gitignore**

```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 7: Write conftest.py with shared fixtures**

```python
import pytest
import duckdb

@pytest.fixture
def db():
    """In-memory DuckDB for testing."""
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()
```

- [ ] **Step 8: Write commands/__init__.py**

```python
# Command modules imported by cli.py
```

- [ ] **Step 9: Verify scaffold**

```bash
cd ~/code/sopor && uv sync && uv run sopor --help
```

Expected: Shows help with version option, no subcommands yet.

- [ ] **Step 10: Init git and commit**

```bash
cd ~/code/sopor && git init && git add -A && git commit -m "feat: project scaffold"
```

---

### Task 2: Database schema and helpers

**Files:**
- Create: `~/code/sopor/src/sopor/db.py`
- Create: `~/code/sopor/tests/test_db.py`

Reference: `~/code/oura-cli/src/db.rs` for Oura schema, `~/code/somnus/src/db.rs` for EightSleep schema. Also check the live Oura DuckDB schema by running:
```bash
uv run --with duckdb python3 -c "
import duckdb
c = duckdb.connect('/Users/terry/oura-data/data/oura.duckdb', read_only=True)
tables = c.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='main'\").fetchall()
for t in tables:
    name = t[0]
    print(f'\n=== {name} ===')
    cols = c.execute(f\"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{name}'\").fetchall()
    for col in cols:
        print(f'  {col[0]:30s} {col[1]}')
"
```

- [ ] **Step 1: Write failing test for DB open and schema**

```python
# tests/test_db.py
from sopor.db import open_db, DB_PATH

def test_open_db_creates_tables(db):
    """open_db on in-memory DB creates all required tables."""
    from sopor.db import init_schema
    init_schema(db)
    tables = [r[0] for r in db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()]
    assert "nightly_sleep" in tables
    assert "eightsleep_sessions" in tables
    assert "daily_activity" in tables
    assert "readiness" in tables
    assert "sync_log" in tables

def test_upsert_nightly_sleep(db):
    """Upsert inserts and updates nightly_sleep rows."""
    from sopor.db import init_schema, upsert_nightly_sleep
    from datetime import date
    init_schema(db)

    row = {
        "day": date(2026, 3, 13),
        "sleep_score": 83,
        "readiness_score": 81,
        "total_sleep_duration": 25200,
        "efficiency": 93,
        "deep_sleep_duration": 5400,
        "rem_sleep_duration": 4800,
        "light_sleep_duration": 13200,
        "awake_time": 1800,
        "average_hrv": 42.0,
        "average_heart_rate": 51.2,
        "bedtime_start": "2026-03-12 23:45:00",
        "bedtime_end": "2026-03-13 06:57:00",
        "restless_periods": 4,
        "sleep_phase_5_min": "112233",
        "temperature_deviation": 0.2,
        "time_in_bed": 27000,
    }
    upsert_nightly_sleep(db, row)
    result = db.execute("SELECT sleep_score FROM nightly_sleep WHERE day = '2026-03-13'").fetchone()
    assert result[0] == 83

    # Update
    row["sleep_score"] = 85
    upsert_nightly_sleep(db, row)
    result = db.execute("SELECT sleep_score FROM nightly_sleep WHERE day = '2026-03-13'").fetchone()
    assert result[0] == 85

def test_upsert_eightsleep_session(db):
    """Upsert inserts EightSleep session by session_id."""
    from sopor.db import init_schema, upsert_eightsleep_session
    from datetime import date
    init_schema(db)

    row = {
        "session_id": "abc123",
        "date": date(2026, 3, 13),
        "duration_secs": 25200,
        "deep_pct": 21.0,
        "light_pct": 47.0,
        "rem_pct": 21.0,
        "awake_pct": 10.0,
        "hrv_avg": 348.0,
        "hr_avg": 54.0,
        "rr_avg": None,
        "bed_temp_avg": 27.2,
        "sleep_score": None,
    }
    upsert_eightsleep_session(db, row)
    result = db.execute("SELECT duration_secs FROM eightsleep_sessions WHERE session_id = 'abc123'").fetchone()
    assert result[0] == 25200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/code/sopor && uv run pytest tests/test_db.py -v
```

Expected: FAIL — `sopor.db` module not found.

- [ ] **Step 3: Write db.py**

Port the schema from the existing DuckDB (match all table definitions exactly). The `init_schema` function creates all tables. Write `upsert_nightly_sleep`, `upsert_eightsleep_session`, and query helpers.

Key tables to create (match existing Oura DuckDB schema exactly):
- `nightly_sleep` — PRIMARY query target (matches `~/code/oura-cli/src/db.rs` schema)
- `eightsleep_sessions` — PK is `session_id TEXT`, with `date DATE` indexed
- `daily_sleep`, `readiness`, `sleep` — raw Oura staging tables
- `daily_activity`, `daily_stress` — activity/stress
- `heartrate` — HR timeseries
- `daily_spo2`, `daily_cardiovascular_age`, `vo2_max` — health
- `sleep_time`, `enhanced_tag`, `tag` — metadata
- `workout`, `session` — exercise
- `resilience`, `rest_mode_period` — recovery
- `sync_log` — sync tracking

Query helpers needed:
- `get_nightly_sleep(conn, start_date, end_date) -> list[dict]` — for week/trend/event
- `get_latest_night(conn, date=None) -> dict | None` — for today
- `get_eightsleep_for_date(conn, date) -> dict | None` — longest session for a date
- `get_readiness_contributors(conn, date) -> dict | None`
- `get_activity(conn, date) -> dict | None`
- `get_stress(conn, date) -> dict | None`

DB path: `~/.local/share/sopor/sopor.duckdb` (create parent dirs if needed).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/code/sopor && uv run pytest tests/test_db.py -v
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: database schema and helpers"
```

---

### Task 3: Display helpers

**Files:**
- Create: `~/code/sopor/src/sopor/display.py`
- Create: `~/code/sopor/tests/test_display.py`

Reference: `~/code/nyx/src/main.rs` lines 87-276 for formatting, ASCII charts, bedtime conversion, linear regression.

- [ ] **Step 1: Write failing tests for display helpers**

```python
# tests/test_display.py
from sopor.display import (
    format_duration,
    format_bedtime,
    bedtime_to_mins_after_noon,
    linear_regression_slope,
    draw_ascii_chart,
)
from datetime import datetime

def test_format_duration_hours_minutes():
    assert format_duration(25200) == "7h 00m"
    assert format_duration(27900) == "7h 45m"
    assert format_duration(3600) == "1h 00m"
    assert format_duration(0) == "0h 00m"
    assert format_duration(None) is None

def test_bedtime_to_mins_after_noon():
    # 23:45 HKT = 23*60+45 = 1425 mins
    dt = datetime(2026, 3, 12, 23, 45, 0)
    assert bedtime_to_mins_after_noon(dt) == 23 * 60 + 45
    # 00:30 next day = (24+0)*60+30 = 1470
    dt2 = datetime(2026, 3, 13, 0, 30, 0)
    assert bedtime_to_mins_after_noon(dt2) == 24 * 60 + 30

def test_format_bedtime():
    assert format_bedtime(23 * 60 + 45) == "23:45"
    assert format_bedtime(24 * 60 + 30) == "00:30"
    assert format_bedtime(None) == "--:--"

def test_linear_regression_slope():
    # Perfect positive: y = x
    data = [(0, 0), (1, 1), (2, 2), (3, 3)]
    assert abs(linear_regression_slope(data) - 1.0) < 0.001
    # Flat
    data2 = [(0, 5), (1, 5), (2, 5)]
    assert abs(linear_regression_slope(data2)) < 0.001
    # Too few points
    assert linear_regression_slope([(0, 0)]) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/code/sopor && uv run pytest tests/test_display.py -v
```

- [ ] **Step 3: Write display.py**

Port from nyx `main.rs`. Include:
- `format_duration(secs: int | None) -> str | None` — "7h 12m"
- `format_bedtime(mins: int | None) -> str` — "23:45" or "--:--"
- `bedtime_to_mins_after_noon(dt: datetime | None) -> int | None` — for consistent bedtime math (hours <12 get +24h)
- `linear_regression_slope(data: list[tuple[float, float]]) -> float | None`
- `draw_ascii_chart(points: list[int | None], min_val: int, max_val: int, rows: int) -> str` — returns string (not prints)
- `color_delta(value: float, higher_is_better: bool) -> str` — Rich markup for green/red deltas
- `make_week_table(data: list[dict], month_data: list[dict]) -> rich.table.Table` — week vs 4w avg table

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/code/sopor && uv run pytest tests/test_display.py -v
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: display helpers — formatting, charts, regression"
```

---

## Chunk 2: API Clients + Sync

### Task 4: Oura API client

**Files:**
- Create: `~/code/sopor/src/sopor/oura.py`
- Create: `~/code/sopor/tests/test_oura.py`

Reference: `~/code/oura-cli/src/client.rs` for endpoints and auth. Also `~/oura-data/scripts/sync.py` for the Python token-handling pattern.

- [ ] **Step 1: Write failing tests for Oura client**

```python
# tests/test_oura.py
import pytest
from unittest.mock import patch, MagicMock
from sopor.oura import OuraClient

def test_oura_client_from_env():
    with patch.dict("os.environ", {"OURA_TOKEN": "test-token"}):
        client = OuraClient()
        assert client.token == "test-token"

def test_oura_client_no_token():
    with patch.dict("os.environ", {}, clear=True):
        with patch("sopor.oura._keychain_token", return_value=None):
            with pytest.raises(RuntimeError, match="OURA_TOKEN"):
                OuraClient()

def test_fetch_daily_sleep(httpx_mock):
    """Test that daily_sleep endpoint is called correctly."""
    # This test verifies URL construction and response parsing.
    # Use httpx's mock or unittest.mock on client.get
    pass  # Flesh out with httpx mock
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Write oura.py**

```python
"""Oura API v2 client (sync httpx)."""
import os
import subprocess
import httpx
from datetime import date, timedelta

API_BASE = "https://api.ouraring.com/v2/usercollection"

def _keychain_token() -> str | None:
    """Try macOS keychain for oura-token."""
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-s", "oura-token", "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None

class OuraClient:
    def __init__(self):
        self.token = os.environ.get("OURA_TOKEN") or _keychain_token()
        if not self.token:
            raise RuntimeError(
                "OURA_TOKEN not set. Get your token at "
                "https://cloud.ouraring.com/personal-access-tokens"
            )
        self.client = httpx.Client(
            base_url=API_BASE,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30,
        )

    def _fetch(self, endpoint: str, start: str, end: str) -> list[dict]:
        """Fetch from Oura API. end_date bumped +1 day (Oura inconsistency)."""
        end_plus = str(date.fromisoformat(end) + timedelta(days=1))
        resp = self.client.get(
            f"/{endpoint}",
            params={"start_date": start, "end_date": end_plus},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def daily_sleep(self, start: str, end: str) -> list[dict]:
        return self._fetch("daily_sleep", start, end)

    def daily_readiness(self, start: str, end: str) -> list[dict]:
        return self._fetch("daily_readiness", start, end)

    def sleep(self, start: str, end: str) -> list[dict]:
        return self._fetch("sleep", start, end)

    def daily_activity(self, start: str, end: str) -> list[dict]:
        return self._fetch("daily_activity", start, end)

    def daily_stress(self, start: str, end: str) -> list[dict]:
        return self._fetch("daily_stress", start, end)

    def heartrate(self, start: str, end: str) -> list[dict]:
        return self._fetch("heartrate", start, end)

    def daily_spo2(self, start: str, end: str) -> list[dict]:
        return self._fetch("daily_spo2", start, end)

    def raw(self, endpoint: str, start: str, end: str) -> dict:
        """Raw JSON response for sopor json command."""
        end_plus = str(date.fromisoformat(end) + timedelta(days=1))
        resp = self.client.get(
            f"/{endpoint}",
            params={"start_date": start, "end_date": end_plus},
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run tests**

```bash
cd ~/code/sopor && uv run pytest tests/test_oura.py -v
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: Oura API client"
```

---

### Task 5: EightSleep API client

**Files:**
- Create: `~/code/sopor/src/sopor/eightsleep.py`
- Create: `~/code/sopor/tests/test_eightsleep.py`

Reference: `~/code/somnus/src/auth.rs` + `~/code/somnus/src/api.rs` for OAuth flow and intervals endpoint.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_eightsleep.py
from unittest.mock import patch
from sopor.eightsleep import _get_credentials

def test_credentials_from_env():
    with patch.dict("os.environ", {
        "EIGHTSLEEP_EMAIL": "test@test.com",
        "EIGHTSLEEP_PASSWORD": "pass123",
    }):
        email, password = _get_credentials()
        assert email == "test@test.com"
        assert password == "pass123"
```

- [ ] **Step 2: Run tests to verify they fail**

- [ ] **Step 3: Write eightsleep.py**

Port from `~/code/somnus/src/auth.rs` and `~/code/somnus/src/api.rs`. Key elements:
- `CLIENT_ID`, `CLIENT_SECRET`, `AUTH_URL` constants (from somnus auth.rs)
- `_get_credentials() -> tuple[str, str]` — env vars first, then `op item get "Eight Sleep" --vault Agents --fields username/password --reveal`
- `_login(email, password) -> dict` — POST to auth-api.8slp.net, returns `{"access_token": ..., "userId": ...}`
- `EightSleepClient` class with `get_intervals(from_date, to_date) -> list[dict]`
- API base: `https://client-api.8slp.net`
- Headers: `User-Agent: Home Assistant 1.0.18`, `Content-Type: application/json`
- If `op` fails, raise a clear error (for sync command to catch and skip gracefully)

- [ ] **Step 4: Run tests**

```bash
cd ~/code/sopor && uv run pytest tests/test_eightsleep.py -v
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: EightSleep API client"
```

---

### Task 6: Sync command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/sync.py`
- Modify: `~/code/sopor/src/sopor/cli.py` — register sync command

Reference: `~/oura-data/scripts/sync.py` for the Oura sync flow (which endpoints to hit, how to build nightly_sleep from daily_sleep + readiness + sleep). `~/code/somnus/src/commands/sync.rs` for EightSleep sync flow.

- [ ] **Step 1: Write sync.py**

The sync command does:
1. Open DuckDB (create if needed)
2. **Oura sync:**
   - Fetch `daily_sleep`, `daily_readiness`, `sleep`, `daily_activity`, `daily_stress` for date range
   - Upsert into raw staging tables
   - For each day: build `nightly_sleep` row from daily_sleep + readiness + sleep (match `~/code/oura-cli/src/db.rs` `build_nightly_sleep_record` logic)
   - Upsert into `nightly_sleep`
   - Print count
3. **EightSleep sync** (wrapped in try/except — skip on failure):
   - Get credentials, login, fetch intervals
   - Filter intervals < 1 hour
   - Convert each interval to `eightsleep_sessions` row (compute stage percentages, metric averages — match `~/code/somnus/src/models.rs` `SleepSession::from_interval`)
   - Upsert into `eightsleep_sessions`
   - Print count
4. Log to `sync_log`

```python
# src/sopor/commands/sync.py
import click
from datetime import date, timedelta

@click.command()
@click.option("--days", default=30, help="Number of days to sync")
def sync(days: int):
    """Sync Oura + EightSleep data to local DB."""
    # Implementation here
```

- [ ] **Step 2: Register in cli.py**

```python
from sopor.commands.sync import sync
cli.add_command(sync)
```

- [ ] **Step 3: Test sync against live APIs**

```bash
cd ~/code/sopor && uv run sopor sync --days 7
```

Expected: "Synced N Oura days + M EightSleep sessions"

- [ ] **Step 4: Verify data in DB**

```bash
uv run --with duckdb python3 -c "
import duckdb
c = duckdb.connect('$HOME/.local/share/sopor/sopor.duckdb', read_only=True)
print('nightly_sleep:', c.execute('SELECT COUNT(*) FROM nightly_sleep').fetchone()[0])
print('eightsleep:', c.execute('SELECT COUNT(*) FROM eightsleep_sessions').fetchone()[0])
print('latest:', c.execute('SELECT day, sleep_score FROM nightly_sleep ORDER BY day DESC LIMIT 3').fetchall())
"
```

- [ ] **Step 5: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: sync command — Oura + EightSleep"
```

---

## Chunk 3: Display Commands

### Task 7: today command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/today.py`
- Modify: `~/code/sopor/src/sopor/cli.py` — register

Reference: spec output format in `~/docs/superpowers/specs/2026-03-14-sopor-design.md` "sopor today" section.

- [ ] **Step 1: Write today.py**

Queries `nightly_sleep` for most recent night (or specified date). Also queries `eightsleep_sessions` for same date. Displays combined view using Rich console.

- [ ] **Step 2: Register in cli.py, test**

```bash
cd ~/code/sopor && uv run sopor today
```

- [ ] **Step 3: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: today command — combined last night view"
```

---

### Task 8: scores command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/scores.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `oura scores` output format.

- [ ] **Step 1: Write scores.py**

One-liner: `Sleep 83  Readiness 81  Activity 72` with readiness contributors beneath. Query `nightly_sleep` + `readiness` (for contributors JSON).

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor scores
git add -A && git commit -m "feat: scores command"
```

---

### Task 9: week command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/week.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `~/code/nyx/src/main.rs` `default_view` (lines 119-159) for the This Week vs 4W Avg table format.

- [ ] **Step 1: Write week.py**

Query `nightly_sleep` for last 7 days and last 28 days. Display Rich table with metrics: Readiness, Sleep Duration, Efficiency, Deep Sleep, REM Sleep, Avg HRV, Avg Heart Rate, Bedtime — each with week avg, 4w avg, and colored delta.

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor week
git add -A && git commit -m "feat: week command — 7d vs 4w comparison"
```

---

### Task 10: trend command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/trend.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `~/code/nyx/src/main.rs` `trend_view` (lines 223-260) for ASCII charts and regression.

- [ ] **Step 1: Write trend.py**

```python
@click.command()
@click.argument("days", default=30, type=int)
def trend(days: int):
    """N-day trend with ASCII charts and regression."""
```

Query `nightly_sleep` for N days. Draw ASCII charts for readiness and bedtime (reuse `display.draw_ascii_chart`). Show linear regression slopes.

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor trend
cd ~/code/sopor && uv run sopor trend 14
git add -A && git commit -m "feat: trend command — ASCII charts + regression"
```

---

### Task 11: event command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/event.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `~/code/nyx/src/main.rs` `event_view` (lines 291-327).

- [ ] **Step 1: Write event.py**

7-day before vs after comparison. Same metric table format as week but comparing pre/post windows.

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor event 2026-03-10 "started-capco-prep"
git add -A && git commit -m "feat: event command — before/after comparison"
```

---

### Task 12: monthly command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/monthly.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `~/code/nyx/src/main.rs` `monthly_view` (lines 329-406).

- [ ] **Step 1: Write monthly.py**

Monthly summary with averages, best/worst night, bedtime consistency (stddev). Saves markdown report to `~/code/vivesca-terry/chromatin/Sleep/YYYY-MM-sopor.md`.

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor monthly 2026-02
git add -A && git commit -m "feat: monthly command — summary + vault report"
```

---

## Chunk 4: Specialized Commands

### Task 13: hypnogram, readiness, activity, hrv, stress commands

**Files:**
- Create: `~/code/sopor/src/sopor/commands/hypnogram.py`
- Create: `~/code/sopor/src/sopor/commands/readiness.py`
- Create: `~/code/sopor/src/sopor/commands/activity.py`
- Create: `~/code/sopor/src/sopor/commands/hrv.py`
- Create: `~/code/sopor/src/sopor/commands/stress.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

Reference: `~/code/oura-cli/src/display.rs` for output formatting of each.

These are simpler display commands that each query one table and format the output:
- `hypnogram`: reads `sleep_phase_5_min` from `nightly_sleep`, renders as ASCII chart (each char = 5 min block: 1=deep, 2=light, 3=REM, 4=awake)
- `readiness`: reads `readiness` table (score + contributors JSON)
- `activity`: reads `daily_activity` table
- `hrv`: reads `average_hrv` from `nightly_sleep` + any HR timeseries if available
- `stress`: reads `daily_stress` table

- [ ] **Step 1: Write all five command files**
- [ ] **Step 2: Register all in cli.py**
- [ ] **Step 3: Test each**

```bash
cd ~/code/sopor && uv run sopor hypnogram
cd ~/code/sopor && uv run sopor readiness
cd ~/code/sopor && uv run sopor activity
cd ~/code/sopor && uv run sopor hrv
cd ~/code/sopor && uv run sopor stress
```

- [ ] **Step 4: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: hypnogram, readiness, activity, hrv, stress commands"
```

---

### Task 14: json command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/json_cmd.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

- [ ] **Step 1: Write json_cmd.py**

```python
@click.command("json")
@click.argument("endpoint")
@click.argument("date", default=None, required=False)
def json_cmd(endpoint: str, date: str | None):
    """Raw JSON from Oura API for piping/debugging."""
    import json as json_lib
    from sopor.oura import OuraClient
    from datetime import date as date_cls

    d = date or str(date_cls.today())
    client = OuraClient()
    data = client.raw(endpoint, d, d)
    click.echo(json_lib.dumps(data, indent=2))
```

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor json daily_sleep 2026-03-13
git add -A && git commit -m "feat: json command — raw Oura API output"
```

---

### Task 15: why command (LLM analysis)

**Files:**
- Create: `~/code/sopor/src/sopor/commands/why.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

- [ ] **Step 1: Write why.py**

1. Query DB: last night's full data, 7-day history, 30-day averages
2. Format as structured text context
3. Write to `~/tmp/sopor-why-context.txt`
4. Run `env -u CLAUDECODE claude --print` with the context file
5. Print the LLM response

```python
@click.command()
@click.argument("date", default=None, required=False)
def why(date: str | None):
    """LLM-powered sleep analysis — why was sleep good/bad?"""
    import subprocess
    import os
    from pathlib import Path

    # ... query DB, build context string ...

    tmp_path = Path.home() / "tmp" / "sopor-why-context.txt"
    tmp_path.parent.mkdir(exist_ok=True)
    tmp_path.write_text(context)

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        ["claude", "--print", tmp_path.read_text()],
        capture_output=True, text=True, env=env,
    )
    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"LLM analysis failed: {result.stderr}", err=True)
```

- [ ] **Step 2: Register, test, commit**

```bash
cd ~/code/sopor && uv run sopor why
git add -A && git commit -m "feat: why command — LLM-powered sleep analysis"
```

---

## Chunk 5: Migration + Finishing

### Task 16: Data migration command

**Files:**
- Create: `~/code/sopor/src/sopor/commands/migrate.py`
- Modify: `~/code/sopor/src/sopor/cli.py`

- [ ] **Step 1: Write migrate.py**

```python
@click.command()
@click.option("--verify", is_flag=True, help="Print row counts without writing")
def migrate(verify: bool):
    """Migrate data from existing oura + somnus DBs."""
```

Steps:
1. If not `--verify`: backup source DBs (copy to `.bak`)
2. ATTACH `~/oura-data/data/oura.duckdb` as `oura_src`
3. ATTACH `~/.local/share/somnus/somnus.duckdb` as `somnus_src`
4. For each table: `INSERT INTO main.{table} SELECT * FROM oura_src.{table} ON CONFLICT DO UPDATE`
5. For somnus: map `sleep_sessions` → `eightsleep_sessions` (rename columns as needed)
6. If `--verify`: print row counts per table (source vs dest), exit without writing
7. Print summary

- [ ] **Step 2: Register, test**

```bash
cd ~/code/sopor && uv run sopor migrate --verify
cd ~/code/sopor && uv run sopor migrate
cd ~/code/sopor && uv run sopor migrate --verify  # confirm counts match
```

- [ ] **Step 3: Commit**

```bash
cd ~/code/sopor && git add -A && git commit -m "feat: migrate command — import from oura + somnus DBs"
```

---

### Task 17: Install binary, create GitHub repo

- [ ] **Step 1: Install as CLI**

```bash
cd ~/code/sopor && uv tool install -e .
```

Verify: `sopor --help` works from any directory.

- [ ] **Step 2: Create GitHub repo**

```bash
cd ~/code/sopor && gh repo create terry-li-hm/sopor --private --source . --push
```

- [ ] **Step 3: Run full migration**

```bash
sopor migrate --verify  # check counts
sopor migrate           # do it
sopor migrate --verify  # confirm
```

- [ ] **Step 4: Verify all commands work with migrated data**

```bash
sopor today
sopor scores
sopor week
sopor trend
sopor event 2026-03-10 "test"
sopor monthly 2026-02
sopor hypnogram
sopor readiness
sopor activity
sopor hrv
sopor stress
sopor json daily_sleep
sopor why
```

- [ ] **Step 5: Commit any fixes**

```bash
cd ~/code/sopor && git add -A && git commit -m "fix: post-migration adjustments" && git push
```

---

### Task 18: LaunchAgent + skill + cleanup

- [ ] **Step 1: Create LaunchAgent**

```bash
cat > ~/officina/launchd/com.terry.sopor-sync.plist << 'XML'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.terry.sopor-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/terry/.local/bin/uv</string>
        <string>run</string>
        <string>--project</string>
        <string>/Users/terry/code/sopor</string>
        <string>sopor</string>
        <string>sync</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/terry/tmp/sopor-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/terry/tmp/sopor-sync.log</string>
</dict>
</plist>
XML
cp ~/officina/launchd/com.terry.sopor-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.terry.sopor-sync.plist
```

- [ ] **Step 2: Create sopor skill**

Create `~/skills/sopor/SKILL.md` with quick reference for all commands, gotchas, and credential setup.

- [ ] **Step 3: Retire old tools** (after Terry confirms sopor works)

```bash
# Unload old LaunchAgents
launchctl unload ~/Library/LaunchAgents/com.terry.oura-sync.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.terry.nyx-monthly.plist 2>/dev/null
# Remove old binaries
rm ~/bin/oura ~/bin/nyx ~/bin/somnus
# Archive old repos (don't delete — keep git history)
# Remove old skills
rm -rf ~/skills/oura ~/skills/somnus ~/skills/nyx
```

- [ ] **Step 4: Update MEMORY.md**

Replace `oura`, `somnus`, `nyx` entries under Active Projects with single `sopor` entry.

- [ ] **Step 5: Final commit and push**

```bash
cd ~/code/sopor && git add -A && git commit -m "chore: LaunchAgent, skill, cleanup" && git push
cd ~/skills && git add -A && git commit -m "feat: add sopor skill, retire oura/somnus/nyx" && git push
```
