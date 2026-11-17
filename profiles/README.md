# Domain profiles — hypotheses, not imposed architecture

Select the smallest relevant set; different modules can have different profiles.

| Profile | Inspect | Avoid assuming |
| --- | --- | --- |
| `python-general` | typing, resources, errors, testability, package constraints | classes, DI or a new framework required |
| `api-service` | input validation, auth, DB lifecycle, backpressure, pagination, timeouts | concurrency always helps |
| `async-io` | task/queue bounds, cancellation, close-on-error, retry storm | semaphore alone bounds tasks allocated |
| `batch-etl` | streaming inputs, checkpointing, transactional output, cardinality | pandas is always wrong |
| `data-science` | dataset copies, float fidelity, reproducibility, memory profiling | single-node work automatically needs Spark |
| `library-sdk` | public compatibility, versioned API, type and error contracts | breaking API changes are safe cleanup |
| `databricks-classic` | Spark UI, driver/executor/worker, node_timeline, Spark plan, skew/spill | Spark configs must be overridden |
| `databricks-serverless` | query profile, Spark Connect, UDF limits, supported configuration | classic Spark UI/RDD/cache semantics necessarily apply |
| `databricks-streaming` | source rates, batch time, watermark, state store, checkpoint | batch tuning alone fixes state OOM |

For Databricks: establish Azure workspace/runtime, Unity Catalog, compute type, access mode and job semantics before applying profile-specific instructions. Re-check official documentation after runtime upgrades.

**Required:** For any `databricks-*` profile activate official `databricks-core` and relevant specialist skill first. See `references/databricks-integration.md`. Serverless DataFrame caching was added in public preview in October 2026 with version requirements; never treat support as timeless.
