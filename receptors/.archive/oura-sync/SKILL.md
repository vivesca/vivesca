---
name: oura-sync
description: Sync Oura Ring data to DuckDB and backup CSV to GitHub. "sync oura", "oura stats"
github_url: https://github.com/terry-li-hm/oura-data
github_hash: d89d067
user_invocable: true
---

# Oura Data Sync

Sync sleep, readiness, resilience, activity, workout, stress, and more from Oura Ring API to local DuckDB, with CSV backup to private GitHub repo.

## Repository

- **Repo:** `~/oura-data` (https://github.com/terry-li-hm/oura-data)
- **Database:** `~/oura-data/data/oura.duckdb` (local only)
- **Backup:** `~/oura-data/exports/*.csv` (tracked in git)
- **Token:** `~/oura-data/.env`
- **Analysis:** `[[Oura Data Analysis]]` in vault

## Quick Access (MCP)

For real-time data without sync, use MCP server via mcporter:

```bash
# OpenClaw
mcporter call oura.get_sleep_data
mcporter call oura.get_readiness_data
mcporter call oura.get_activity_data
mcporter call oura.get_heart_rate_data

# Claude Code
mcp__oura__get_sleep_data
```

Use MCP for quick checks. Use DuckDB sync for historical analysis.

## Commands

### Sync Data

```bash
cd ~/oura-data

# Sync last 7 days (default)
uv run python scripts/sync.py

# Backfill N days
uv run python scripts/sync.py --backfill 30

# Full historical sync (5 years)
uv run python scripts/sync.py --backfill 1825

# Include intraday heart rate (high volume!)
uv run python scripts/sync.py --backfill 30 --heartrate
```

### Export & Backup to GitHub

```bash
cd ~/oura-data
uv run python scripts/sync.py --export
git add exports/
git commit -m "Backup oura data $(date +%Y-%m-%d)"
git push
```

### Query Data

```bash
cd ~/oura-data
uv run python -c "
import duckdb
con = duckdb.connect('data/oura.duckdb')
for row in con.execute('SELECT day, efficiency, average_hrv FROM sleep ORDER BY day DESC LIMIT 7').fetchall():
    print(row)
"
```

## Full Workflow (Periodic)

Run this monthly to ensure complete backup:

1. **Sync all data:** `uv run python scripts/sync.py --backfill 1825`
2. **Export CSV:** `uv run python scripts/sync.py --export`
3. **Backup to GitHub:** `git add exports/ && git commit -m "Backup" && git push`
4. **Update analysis:** Run queries and update `[[Oura Data Analysis]]` in vault

## Storage Strategy

| Location | Contents | Purpose |
|----------|----------|---------|
| `data/oura.duckdb` | Full database | Fast local queries |
| `exports/*.csv` | All tables | Git backup (human-readable, diffable) |

## Available Tables

| Table | Records | Key Fields |
|-------|---------|------------|
| `sleep` | 2,133 | day, efficiency, average_hrv, average_heart_rate, deep/light/rem_sleep_duration |
| `readiness` | 1,505 | day, score, temperature_deviation, contributors |
| `resilience` | 703 | day, level, contributors |
| `daily_activity` | 1,578 | day, steps, active_calories, high/medium/low_activity_time, score |
| `workout` | 3,143 | day, activity (walking/running/etc), calories, distance, intensity |
| `daily_stress` | 809 | day, day_summary (normal/stressful/restored), stress_high, recovery_high |
| `daily_spo2` | 1,226 | day, spo2_percentage, breathing_disturbance_index |
| `tag` | 69 | day, tags (alcohol, late_meal, supplements, etc) |
| `session` | 3 | day, type (meditation/breathing), mood, heart_rate |
| `heartrate` | optional | timestamp, bpm, source (awake/sleep) - high volume! |

## Analysis Queries

When user asks for analysis, run these and save to `[[Oura Data Analysis]]`:

```sql
-- Yearly trends
SELECT EXTRACT(year FROM day) as year,
    ROUND(AVG(average_hrv), 1) as avg_hrv,
    ROUND(AVG(efficiency), 1) as efficiency
FROM sleep WHERE efficiency > 10 GROUP BY year ORDER BY year;

-- Workout frequency by year
SELECT EXTRACT(year FROM day) as year,
    activity, COUNT(*) as count
FROM workout
GROUP BY year, activity
ORDER BY year, count DESC;

-- HRV vs efficiency correlation
SELECT CASE
    WHEN average_hrv < 50 THEN 'HRV <50'
    WHEN average_hrv < 70 THEN 'HRV 50-70'
    WHEN average_hrv < 90 THEN 'HRV 70-90'
    ELSE 'HRV 90+'
END as hrv_bucket,
ROUND(AVG(efficiency), 1) as avg_efficiency
FROM sleep WHERE efficiency > 10 AND average_hrv > 0
GROUP BY hrv_bucket;

-- Stress patterns
SELECT day_summary, COUNT(*) as days,
    ROUND(AVG(stress_high)/3600, 1) as avg_stress_hours,
    ROUND(AVG(recovery_high)/3600, 1) as avg_recovery_hours
FROM daily_stress
GROUP BY day_summary;

-- Activity score vs sleep quality
SELECT
    CASE WHEN a.score < 60 THEN 'Low activity'
         WHEN a.score < 80 THEN 'Medium activity'
         ELSE 'High activity' END as activity_level,
    ROUND(AVG(s.efficiency), 1) as next_night_efficiency
FROM daily_activity a
JOIN sleep s ON s.day = a.day + INTERVAL 1 DAY
WHERE s.efficiency > 10
GROUP BY activity_level;

-- Optimal bedtime
SELECT EXTRACT(hour FROM bedtime_start) as bed_hour,
    ROUND(AVG(efficiency), 1) as efficiency
FROM sleep WHERE efficiency > 10
GROUP BY bed_hour HAVING COUNT(*) >= 20
ORDER BY bed_hour;

-- Day of week pattern
SELECT CASE EXTRACT(dow FROM day)
    WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'
    WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri'
    WHEN 6 THEN 'Sat' END as weekday,
ROUND(AVG(efficiency), 1) as efficiency
FROM sleep WHERE efficiency > 10
GROUP BY EXTRACT(dow FROM day) ORDER BY EXTRACT(dow FROM day);
```

## Workflow Summary

| User Says | Action |
|-----------|--------|
| "sync oura" | Run sync with default 7 days |
| "sync all oura data" | Run `--backfill 1825` |
| "backup oura" | Export + git commit + push |
| "oura stats" / "how's my sleep" | Query DuckDB, show recent data |
| "analyze oura data" | Run full analysis, save to vault |
| "what workouts did I do" | Query workout table |
| "how stressed was I" | Query daily_stress table |

## Error Handling

- **If .env missing or invalid token**: Check `~/oura-data/.env` for valid `OURA_TOKEN`
- **If API rate limited**: Wait and retry; Oura has generous limits but can throttle
- **If DuckDB file locked**: Close other connections; only one write connection allowed
- **If sync fails mid-backfill**: Re-run same command — it handles partial syncs gracefully
- **If heartrate data huge**: Use `--heartrate` flag sparingly; consider date ranges

## Privacy Notes

- Health data is sensitive — keep `oura.duckdb` local only
- CSV exports go to git but repo should be private
- Never share token or export to shared locations
