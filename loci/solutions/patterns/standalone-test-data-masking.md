# Standalone Tests That Load Their Own Data Can Mask Production Bugs

**Discovered:** 2026-02-23 (STR Relabelling project)

## The Pattern

A test script that loads data independently (its own SQL query) can pass while the production code would crash, because the test compensates for schema differences that the production code path doesn't.

## What Happened

- `pipeline_node_test.py` loaded `alert_df` with a JOIN to get `alert_typ_id` from a raw table
- The production patch referenced `alert_df["alert_typ_id"]` assuming the column existed
- `alert_typ_id` is **not** in the model table (`imh_apm_core.str`) — production would `KeyError`
- The test always passed because it brought in the column via JOIN
- Every standalone script (dry_run, script_b, script_c) had the same JOIN, reinforcing the blind spot

## The Fix

Removed the `alert_typ_id` filter entirely — the pipeline already filters for system alerts upstream, making it unnecessary.

## General Rule

**If your test loads data differently from the production code path, it's not testing the production code path.** Specifically:

- Test queries that JOIN extra columns → mask missing columns in production
- Test queries that filter data → mask type errors on unfiltered rows
- Test queries from different tables → mask schema differences

## How to Catch This

1. Check whether the test's data loading matches the production function's inputs
2. If the test adds a JOIN/filter the production code doesn't have, ask why
3. The gold standard: import and call the actual function, not a reimplementation
4. Even just `from module import function` catches import/syntax errors the standalone test misses

## Related: Kedro Catalog Overrides Don't Catch Direct Writes

Kedro's `conf/local/catalog.yml` overrides only affect catalog-mediated dataset reads/writes. If a function calls a write helper directly (e.g. `save_to_hive_table`), the catalog override is bypassed entirely. The write goes to whatever the function's config says.

**STR example:** `preprocess_strs` calls `save_to_hive_table` at line ~1788, writing to the table name from `GLOBAL_DATALAKE_APPCORE_NAMES["str_table_name"]` in `parameters.yml`. The `/tmp/` catalog override set up on Feb 11 didn't catch this — it wrote directly to Hive. Safe only because the playground's `parameters.yml` had `str_table_name: "TEST_STR56"` (confirmed not in production GitLab repo).

**Rule:** When checking if a Kedro node is safe to run, grep for direct write calls inside the function, not just catalog outputs. `save_to_hive_table`, `spark.sql("INSERT")`, `df.write.saveAsTable()` all bypass the catalog.
