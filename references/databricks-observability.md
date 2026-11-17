# Azure Databricks — memory diagnosis and evidence

## Classic compute: recommended triage

1. Record workspace ID (without leaking identifiers in public reports), cluster ID in private notes, DBR version, node types, driver/worker counts, autoscaling, Photon, access mode and active concurrent jobs.
2. Inspect job failure message and executor/driver logs; a generic RPC disassociation is **not** definitive proof of OOM.
3. In **Spark UI**, start at Jobs timeline; find the longest stage and check task duration variance, shuffle read/write, peak execution memory, memory/disk spill and executor failures.
4. If a few tasks dominate, look for data skew, a giant group/broadcast, single partition or an unpartitioned window; if all tasks spill, investigate work/partitions, not only hardware.
5. Inspect cluster metrics and utilization for driver and executors separately. A busy driver plus idle workers suggests scheduling, concurrency, notebooks or driver-side non-Spark processing.
6. Record before/after metrics using identical input/compute/parameter conditions. On shared clusters separate other concurrent workloads as far as possible.

For classic resources, `system.compute.node_timeline` exposes per-minute utilization including `mem_used_percent` and driver indicator. It is a **node utilization aggregate**, not exact per-query peak RSS, and is not a substitute for task-level Spark UI. Access is permission dependent; typically delivered with delay; very short-lived nodes may not be represented.

Use the official `databricks-unity-catalog` skill and its documented, authorized system tables for compute/usage telemetry. The availability, retention and supported compute modes of these tables must be verified; node-level utilization is not per-query memory.

## Serverless

Serverless notebooks/jobs use **query profile** rather than classic Spark UI and restrict Spark configuration. Cache support is **version/preview dependent**: `df.cache()`/`df.persist()` entered public preview in October 2026 with requirements; SQL/catalog cache APIs and checkpoint support differ. See `databricks-runtime-and-compute.md` and always verify current official docs. Some UDFs have separate memory limits; check the current official limits before prescribing changes.

## What counts as evidence?

| Source | What it supports | What it does not prove |
| --- | --- | --- |
| Spark UI stage/task metrics | Shuffle, spill, skew, task memory and failures on classic | Python object-by-object allocations |
| Node timeline (`system.compute.node_timeline`) | Classic node RAM pressure over time | Exact query memory or serverless usage |
| Driver logs and executor logs | Actual OOM/stage errors and runtime context | Root cause without correlating code/plan |
| Serverless query profile | Operators/plan and supported execution diagnostics | Classic Spark UI metrics |
| Local `tracemalloc` | Python allocations in an instrumented process | Whole Spark cluster or native/Arrow/JVM RSS |
| Static AST auditor | Potential risky calls | Dataset size, true OOM, or performance impact |

## Findings format

For each problem, write: hypothesis, memory domain, observed metrics + timestamp, source, process/job context, alternative causes, smallest corrective experiment, expected impact **without inventing numbers**, correctness check, rollback and actual outcome. Unknown data must stay `UNVERIFIED`.

Official docs: Spark UI guide, skew and spill, memory issues, overloaded driver, node compute system tables and serverless limitations in `source-index.md`.
