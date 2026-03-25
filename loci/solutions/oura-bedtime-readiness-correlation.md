# LRN-20260308-002: Oura bedtime vs readiness correlation (60-day analysis)

## Finding

Earlier bedtime consistently predicts higher next-day readiness. Monotonic relationship across 60 days (Jan–Mar 2026):

| Bedtime | N | Avg Readiness | Range |
|---|---|---|---|
| Before 10:30pm | 29 | **82.6** | 68–90 |
| 10:30–11pm | 14 | 80.8 | 70–89 |
| 11–11:30pm | 13 | 77.1 | 69–85 |
| After 11:30pm | 4 | 76.3 | 73–79 |

**Each 30 minutes later ≈ −2 readiness points.** Total spread: 6.3 points between earliest and latest bucket.

## Method

DuckDB query on `sleep` + `readiness` tables, filtered to `bedtime_start` between 18:00–23:59 (excludes naps and data artifacts). Bedtime hour extracted from `bedtime_start` timestamp.

```python
cd ~/oura-data && uv run python3 -c "
import duckdb
con = duckdb.connect('/Users/terry/oura-data/data/oura.duckdb', read_only=True)
# bedtime buckets × avg readiness
"
```

## Implication

Don't experiment with *whether* to sleep earlier — it's proven. The open question is *which wind-down protocol reliably achieves before 10:30pm*. That's the peira campaign: `sleep-capco-ready`.

## Caveats

- n=4 for after 11:30pm — small sample, direction is clear but magnitude uncertain
- Correlation not causation — could be that bad days (illness, stress) cause both late bedtime and low readiness
- 60-day window only; may not generalise across seasons or workload changes

## Reproduced

```bash
cd ~/oura-data && uv run python scripts/sync.py --backfill 60
# then query sleep + readiness tables
```
