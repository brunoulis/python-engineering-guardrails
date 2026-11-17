# Azure Databricks context: classic vs serverless

**Only after verifying and activating `databricks-core`** (see
`databricks-integration.md`). Databricks platform instructions themselves
belong upstream in `databricks-docs`, `databricks-execution-compute` and
other official skills. This document only identifies questions essential for
our memory audit.

## Questions required for an honest diagnosis

- Azure workspace / cloud; interactive, jobs, SQL warehouse or pipelines;
  classic vs serverless; DBR or serverless environment version, and feature
  preview flags; Spark Connect and client version; Photon/access mode.
- Data volume (rows, bytes, partition-size distribution) and concurrency.
- Which domain sees pressure? Python driver, driver JVM, executors, Python
  UDF workers, shuffle spill, streaming state or cloud storage?
- Baseline: schema/result correctness, peak memory, elapsed time, spill,
  retries and cost, if permitted and measurable.

## Serverless cache: a *versioned* behavior, not a timeless prohibition

**2026-10-23:** Databricks announced **public preview** DataFrame caching in
serverless. In supported workspaces/environment/client versions, `df.cache()`
and `df.persist()` work; this is not necessarily the same semantics as classic
Spark cache. Official feature doc lists environment >=5, Databricks Connect
Python >=18.1.8, and workspace preview enabled. Classic-style SQL/catalog
cache APIs still have unsupported cases. An older or localized limitations
page may still say all caching APIs are unsupported.

Consequences for our skill:

- Never report `df.cache()` as universally unsupported on serverless.
- Verify environment, actual preview, **snapshot consistency**, eager vs lazy
  evaluation, cache invalidation and `unpersist` behavior before a refactor.
- A cache may reduce recomputation while increasing storage cost and changing
  freshness semantics. Keep it only if repeatedly reused and justified.
- Cite the documentation *consulted at the time of the user task*; do not
  assume static text in this repository is current.

## What not to do

No automatic overrides of `spark.executor.memory`, `spark.sql.shuffle.partitions`,
AQE, spill thresholds, broadcast thresholds, node sizes or cache storage levels.
These are not style rules. Reason about physical plans and actual data.

## Official references

- Serverless release notes:
  https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/
- Serverless DataFrame cache:
  https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/dataframe-cache
- Serverless limitations:
  https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/limitations
- Adaptive query execution:
  https://learn.microsoft.com/en-us/azure/databricks/optimizations/aqe

Checked as of 2026-11-17; re-check on each Databricks-specific task.
