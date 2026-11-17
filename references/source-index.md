# Authoritative sources and version checks

**Last editorial review: 2026-11-17.** Sources are links, not bundled copies;
re-check for the **actual deployed** Azure Databricks environment whenever
making a platform-specific recommendation. Use the separately installed
`databricks-docs` and other relevant official Databricks skills as the primary
upstream source of truth. We do not redistribute upstream Databricks skills.

## Agent skill architecture

- Official Agent Skills specification:
  https://agentskills.io/specification
- Databricks official skills, installation, lists and routing:
  https://github.com/databricks/databricks-agent-skills
- Official Databricks skill manifest (upstream may add/remove skills):
  https://github.com/databricks/databricks-agent-skills/blob/main/manifest.json

## Azure Databricks: verify platform feature availability on each task

- Serverless release notes and **2026-10-23 DataFrame cache public preview**:
  https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/
- Serverless DataFrame caching, requirements, snapshot and unpersist semantics:
  https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/dataframe-cache
- Serverless limitations (note: older crawled/localized versions may contradict
  newer feature pages; resolve by dated release notes and actual environment):
  https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/limitations
- Adaptive query execution / skew tuning:
  https://learn.microsoft.com/en-us/azure/databricks/optimizations/aqe
- Performance recommendations:
  https://learn.microsoft.com/en-us/azure/databricks/optimizations/
- Spark UI troubleshooting:
  https://learn.microsoft.com/en-us/azure/databricks/optimizations/spark-ui-guide/
- Spark memory issue diagnosis:
  https://learn.microsoft.com/en-us/azure/databricks/optimizations/spark-ui-guide/spark-memory-issues
- Classic compute system tables and node memory telemetry:
  https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/compute
- Spark query profile (follow official docs and product routes):
  https://learn.microsoft.com/en-us/azure/databricks/sql/user/queries/query-profile

## Apache Spark / PySpark (check version, not just /latest)

- `DataFrame.toLocalIterator()`: largest partition in memory, up to two with
  prefetch, Spark Connect differences:
  https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.toLocalIterator.html
- `GroupedData.applyInPandas()`: group memory/skew and supported iterator forms:
  https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.GroupedData.applyInPandas.html
- Spark Structured Streaming concepts:
  https://spark.apache.org/docs/latest/streaming/index.html

## Python memory, async and tests

- `tracemalloc` tracks Python allocations, not total native/JVM RSS:
  https://docs.python.org/3/library/tracemalloc.html
- `asyncio.Queue`, maxsize and producer backpressure:
  https://docs.python.org/3/library/asyncio-queue.html
- `concurrent.futures.Executor.map` versioned `buffersize`:
  https://docs.python.org/3/library/concurrent.futures.html
- `resource` availability varies by OS:
  https://docs.python.org/3/library/resource.html
- Memray (optional native-aware Python memory profiling):
  https://github.com/bloomberg/memray
- pytest (optional existing test runner):
  https://docs.pytest.org/en/stable/

## Family philosophy / independent repositories

- Flutter: https://github.com/brunoulis/flutter-engineering-guardrails
- Rust: https://github.com/brunoulis/rust-engineering-guardrails
- C++: https://github.com/brunoulis/cpp-engineering-guardrails
- TypeScript: https://github.com/brunoulis/typescript-engineering-guardrails

**Evidence hierarchy:** measured production/development run on matching
workload > executed physical plan and task metrics > version-specific official
API constraints > reviewed code-level hypothesis > bare AST syntax match.
Publishing an authoritative link never makes our unsupported savings claims
valid. Mark live test results `NOT_RUN` until they exist.
