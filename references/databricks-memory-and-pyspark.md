# Azure Databricks — memory-risk heuristics (upstream-owned platform instructions)

**Dependency gate:** activate installed official `databricks-core` and appropriate specialist skill before Databricks-specific work (`databricks-integration.md`). These are **risk questions and analysis heuristics**, not a local copy of Databricks platform operations.

## Distinguish four domains

1. **Driver JVM and Python process:** orchestrates queries and may receive data from `collect()` / `toPandas()`; Python loops doing non-Spark work execute here.
2. **Executor JVM:** computes Spark SQL/DataFrame tasks; shuffle, joins, sort, aggregate, broadcast, cache, spill and GC matter.
3. **Python workers / Arrow / pandas:** UDF and `applyInPandas` memory can be outside JVM heap; a JVM-only metric can miss pressure.
4. **Streaming state:** stateful stream operators persist state over micro-batches; a watermark/checkpoint concern, not a one-time driver collection concern.

A machine-level or cluster-level memory chart alone does not identify which domain is responsible. Do not claim `driver OOM` from a generic `ExecutorLostFailure` without checking logs and telemetry.

## Guardrails for costly operations

| Symptom or code | Risk | Safer diagnostic / option |
| --- | --- | --- |
| `df.collect()` | Brings all selected rows to driver | For a full ETL, keep distributed processing/writes; for small metadata, demonstrate bounded size |
| `df.toPandas()` | Materializes local pandas data; driver memory risk | Use Spark SQL/DataFrame transformations or pandas API on Spark if it actually fits the workload |
| `list(df.toLocalIterator())` | Re-materializes an entire iterator on driver | Prefer distributed work; if must iterate, bound input/partitions and consume incrementally |
| `df.toLocalIterator()` | Largest partition must still fit driver memory | Verify partition sizing and do not treat iterator as zero-memory; Spark Connect ignores prefetch flag |
| `.cache()` / `.persist()` | May occupy Spark memory and delay garbage collection | Avoid by default; prove repeated reuse and net benefit; `unpersist` with lifecycle when supported |
| `.repartition(1)` / `.coalesce(1)` | Single oversized task / poor parallelism / OOM | Don't force a single file as default; consider downstream file-management needs |
| `groupBy().applyInPandas()` | All rows for one group held in Python memory | Check max group cardinality and skew; rewrite with native Spark functions when semantically possible |
| Cross join or large broadcast | Task explosion / local memory | Check join keys, physical plan and AQE; let optimizer pick unless benchmark supports a hint |
| Python `udf()` / `pandas_udf()` | Python overhead, Arrow batches, memory pressure, possible Photon fallback | Prefer built-in expressions; inspect UDF semantics and supported runtime |
| Window without `partitionBy` | One task may process all rows | Add partition only if correct for the window's logical scope |

**Nuances that prevent bad advice**

- Databricks advises avoiding Spark caching as a general rule. Do **not** demand caching after a generic repeated-use smell. Disk cache, Spark cache, SQL result cache and Python memoization are different technologies.
- `toLocalIterator()` takes memory comparable to the **largest partition**, potentially two with prefetch. It is not automatically safe for very large partitions.
- The classic `applyInPandas()` pandas.DataFrame API loads complete groups; `spark.sql.execution.arrow.maxRecordsPerBatch` **does not cap group size**. Newer PySpark versions also document an iterator API (added in Spark 4.1); verify the actual Databricks Runtime and function contract before suggesting it as a mitigation.
- AQE can handle shuffle partition coalescing and some skew; verify it is enabled/eligible and inspect the *actual* physical plan before adding a manual repartition, broadcast or salt.
- `spark.sql.shuffle.partitions=auto` can be useful in supported Databricks classic workloads, but is not a universal requirement. Do not override cluster config as a ritual.
- Photon accelerates supported SQL/DataFrame operators; unsupported UDF/RDD paths can fall back to Spark. Benchmark the actual job, not a claimed fixed speedup.
- Many small repeated actions (`count()`, `display`, `show`) can trigger extra jobs; prefer a clearly scoped production action and avoid needless intermediate actions.
- `limit()` changes output semantics and is useful for a **diagnostic sample**, not a production substitute for correct distributed processing.

## Review order

1. Confirm input schema and business semantics; inspect the query and `explain('formatted')` or actual query profile without executing additional large jobs unnecessarily.
2. Minimize inputs: filter/column projection/aggregations on workers; use Delta/PySpark APIs rather than pandas for large distributed data.
3. Check joins and windows for cardinality skew, shuffle amount, distribution and AQE.
4. Check Python worker UDF/group memory, cache lifecycle, and any `collect` or conversion.
5. Profile comparable workload on authorized development data; compare correctness, elapsed time, peak memory, skew/spill and DBU costs when available.

Example: `examples/databricks/driver_oom_before.py` and `driver_oom_after.py` (illustrative, not benchmarked).

Authoritative docs: Azure Databricks PySpark, performance recommendations, pandas function APIs, AQE, Spark UI memory issues, Photon, and Spark `toLocalIterator` API (see `source-index.md`).
