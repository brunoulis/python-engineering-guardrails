# Testing, profiling and review protocol

## Local Python project

- Use existing format, lint, type and unit/integration suite; don't require tools not installed by the project.
- Common options: `ruff check`, `ruff format --check`, `mypy`/`pyright`, `pytest`; choose the repository's current tools.
- Correctness tests: empty inputs, duplicates, nulls, ordering, timezones, precision, cancellation, retry and transaction behavior.
- Memory tests: representative input sizes; process peak RSS where available and tracked Python allocations when informative. Distinguish cold vs warm runs; record versions, machine, dataset and peak, not just time.

## PySpark/Databricks

- Unit tests can verify pure transformations locally with a **compatible** PySpark, but local Spark isn't proof of Databricks Runtime/Photon/serverless compatibility.
- Compare output **schemas and values**, aggregate counts, duplicate and NULL handling, ordering where contract requires, partition/date semantics, idempotent write behavior and error paths.
- For performance tests on authorized nonproduction data: same input size and cluster/profile, record execution plan, wall time, task count, shuffle read/write, spill, skew, peak driver and executor/node metrics where available, and billed workload cost if authorized.
- Performance on tiny data does not predict full-cluster peak RAM; group size skew and output cardinality are often invisible in a tiny sample.
- Explicitly distinguish `NOT_RUN` (cluster tests not executed), `UNVERIFIED` (missing runtime facts) and `PASSED` (real command and exit result).

## Audit evidence template

- `context`: path, runtime, profile, query/job identity (redact secrets), row and byte scale.
- `finding`: severity, confidence, proof (source line + metrics), risk and minimal correction.
- `verification`: actual command, date, result, before/after measurements, caveats and rollback.
- Never assign a single misleading numeric "code quality" or "RAM efficiency" score without a defensible measurement model.

## CI safety

Auditor itself only reads files. `--write-baseline` or `--output` writes to an explicit report path, which should not be inside the audited project unless the caller authorizes it. SARIF/JSON are for triage and annotations; runtime tests still matter.
