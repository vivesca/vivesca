# SQL-to-Pandas Translation Pitfalls

## Problem

Translating complex SQL joins into pandas merge/filter chains introduces subtle bugs that produce plausible-but-wrong numbers. Three attempts at replicating a multi-table SQL join in pandas all produced different wrong answers (942, 589, 1945 vs correct 1134).

## Root Causes Found

1. **Period filter scope mismatch**: SQL subquery had no date filter (checked all history), but pandas loaded only period-filtered alerts. Result: purely_low_risk count inflated (106 vs 89) because historical high-risk alerts were invisible.

2. **Join path differences**: SQL joined through an intermediary table (`str s2 → str s3 ON entity_nbr → monitored_alerts m`) creating a specific traversal path. Pandas inner join on alert_id produced a different (narrower or wider) set depending on which DataFrame was used as the base.

3. **Filter omissions**: SQL had `m.inference_dt <= s2.str_dt` on context rows. Pandas version initially had no such filter, then used MAX(str_dt) per entity (close but not identical to per-row str_dt).

## Solution

**Don't translate complex SQL to pandas. Run the SQL directly via Spark.**

```python
# Bad: reconstruct SQL logic in pandas
alerts_with_entity = all_alerts.merge(str_df[['alert_id', 'entity_nbr']], ...)
above_low = alerts_with_entity[alerts_with_entity['score'] >= threshold]
# ... 20 more lines of subtle bugs

# Good: run the proven SQL
result = spark_read_sql(f"""
    SELECT DISTINCT ...
    FROM {TABLE} a
    JOIN {STR_TABLE} s2 ON a.alert_id = s2.alert_id
    ...
""")
```

## Rounding Boundary Trap

Pre-rounded columns (e.g. `ROUND(score * 100, 2) AS score_pct`) introduce threshold mismatches. A raw score of `0.004999...` passes `< 0.005` in SQL but becomes `0.50` after rounding, failing `score_pct < 0.5` in pandas. Always filter on raw values, not display columns. Found Feb 2026: 259 vs 260 discrepancy traced to one alert at the `predicted_risk_score_pct` boundary.

## When Pandas Translation IS Safe

- Simple single-table filters and aggregations
- Joins on a single key with no intermediary tables
- Post-query transformations (formatting, pivoting, exporting)

## When to Use SQL Directly

- Multi-table joins (3+ tables)
- Self-joins or same-table-different-alias patterns
- Subqueries with different filter scopes than the main query
- Any query where the SQL is already proven correct

## Reconciliation Pattern

When porting SQL to Python:
1. Run with the SAME parameters as a known-good SQL run
2. Compare ALL output numbers, not just the headline metric
3. If mismatch: don't debug pandas — just run the SQL via Spark
