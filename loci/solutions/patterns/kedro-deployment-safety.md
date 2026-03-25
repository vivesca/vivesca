---
module: Data Pipeline
date: 2026-02-23
problem_type: best_practice
component: cli_tool
symptoms:
  - "Preflight check false positive on legitimate upstream code"
  - "kedro run --node=preprocess_strs fails: node not found"
  - "kedro run --pipeline=data_preprocessing fails: pipeline not found"
  - "Catalog overrides to /tmp/ don't catch direct Hive writes"
root_cause: mental_model_error
resolution_type: process_change
severity: medium
tags: [kedro, pipeline, safety, hive, cdsw, naming]
related_files:
  - "~/code/str-relabelling/preflight_check.py"
  - "~/skills/str-relabelling/SKILL.md"
---

# Kedro Deployment Safety Patterns

Discovered during STR Relabelling (FR-MLP-002) deployment to CDSW playground, Feb 2026.

## 1. Safety Checks Must Be Scoped to the Relevant Code Block

**Problem:** A preflight check searched the entire `nodes.py` for `alert_typ_id`, triggering a false positive because legitimate upstream pipeline code uses the same string.

**Rule:** When validating that a patch doesn't contain a specific pattern, scope the search to the patch block only — not the entire file.

```python
# BAD — searches entire file, false positives from unrelated code
if "alert_typ_id" in source:
    print("WARN")

# GOOD — scopes to the patch block
marker_pos = source.find("FR-MLP-002")
if marker_pos != -1:
    patch_block = source[marker_pos:marker_pos + 3000]
    if "alert_typ_id" in patch_block:
        print("WARN")
```

**General pattern:** Any automated check that greps a large file for a string your patch shouldn't have — scope it to the patch region. Large codebases reuse the same identifiers across unrelated functions.

## 2. Kedro Registered Names Differ from Python Function Names

**Problem:** `kedro run --node=preprocess_strs` fails because the node is registered as `predict_preprocess_strs_node`. Similarly, `--pipeline=data_preprocessing` fails because it's `predict_data_preprocessing_pipeline`.

**Rule:** Never assume the Kedro node/pipeline name matches the Python function name. Always check:

```bash
# Find the registered node name
grep -n "preprocess_strs" src/apm/pipelines/data_preprocessing/pipeline.py

# Find registered pipeline names
kedro registry list
# or
grep -n "register_pipelines" src/apm/pipeline_registry.py
```

## 3. Direct Writes Bypass Kedro Catalog Overrides

**Problem:** `save_to_hive_table` inside `preprocess_strs` writes directly to Hive, bypassing the Kedro catalog. Setting `conf/local/catalog.yml` outputs to `/tmp/` doesn't catch it.

**Rule:** Before running any Kedro node, check for direct write calls — not just catalog outputs:

```bash
grep -n "save_to_hive_table\|spark.sql.*INSERT\|write.saveAsTable" nodes.py
```

Then verify which functions contain those writes and whether they're in your execution path.

See also: [Standalone Test Data Masking](standalone-test-data-masking.md) — covers the catalog bypass pattern and the related risk of tests that load data differently from production.

## 4. Safety Verification Chain

Before running a Kedro node that writes to Hive:

1. **`python preflight_check.py`** — write target is test table, patch applied, no known bugs in patch block
2. **Direct write grep** — find all `save_to_hive_table` / `INSERT` / `saveAsTable` calls, map them to functions, confirm only safe functions execute
3. **`grep -n "tmp" conf/local/catalog.yml`** — confirm catalog overrides exist for upstream node I/O
4. **Run with `--to-nodes`** — `kedro run --pipeline=X --to-nodes=Y` runs only the necessary upstream chain, not the full pipeline

Only then: `kedro run --pipeline=predict_data_preprocessing_pipeline --to-nodes=predict_preprocess_strs_node`
