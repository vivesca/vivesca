# CDSW: HiveWarehouseConnector staging directory locked by departed user

## Problem

Kedro pipeline fails with `Py4JJavaError` referencing `/tmp/staging/hwc/apm_test`. The HWC staging directory was created by a previous user (`minniecmin`) who has left the company. Current user can't write to or delete it — `hdfs dfs -rm -r` and `-skipTrash` both return permission denied.

## Fix

Override the staging directory path before running:

```bash
PYSPARK_SUBMIT_ARGS="--conf spark.datasource.hive.warehouse.load.staging.dir=/tmp/staging/hwc/apm_test_terry pyspark-shell" kedro run --pipeline <pipeline> --to-nodes=<node>
```

**Note:** `PYSPARK_SUBMIT_ARGS` does NOT work if the Kedro project creates its own SparkSession programmatically (e.g. in `spark_connector.py`). The env var only applies to `pyspark` shell sessions. Instead, add the config directly to the SparkSession builder:

```python
.config("spark.datasource.hive.warehouse.load.staging.dir", "/tmp/staging/hwc/apm_test_terry")
```

## Why it happens

HWC creates staging dirs in `/tmp/staging/hwc/` with the HDFS user's permissions. If someone leaves and their account is deactivated, the directory persists but no one else can write to or delete it. The default path is project-scoped (`apm_test`), so all users of the same CDSW project collide.

## Discovered

2026-02-24 — STR relabelling Kedro pipeline, CNCBI CDSW.
