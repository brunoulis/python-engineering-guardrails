---
name: python-engineering-guardrails
description: >-
  Engineer, audit and refactor Python code with anti-slop guardrails, bounded-memory
  design, explicit resource ownership, rigorous tests and evidence-driven performance.
  Use for Python APIs, async services, ETL, Pandas, PySpark and Azure Databricks
  memory/OOM investigations. Databricks-specific work requires official
  databricks-agent-skills (databricks-core plus the relevant product skill).
license: MIT
compatibility: >-
  Portable Agent Skills instructions. Optional local auditor: Python 3.10+,
  standard library only. Databricks tasks require separately installed official
  databricks-agent-skills and verified, version-specific platform documentation.
metadata:
  version: "0.1.0"
  family: engineering-guardrails
  upstream_databricks: "https://github.com/databricks/databricks-agent-skills"
---

# Python Engineering Guardrails

**Mission:** Ship the smallest correct, maintainable Python solution. Respect existing
contracts, bound resources, measure where it matters, and never manufacture
confidence. This is a sibling of Flutter, Rust, C++ and TypeScript Engineering
Guardrails, applying the same philosophy in Python rather than copying their
language-specific rules. Read `references/philosophy.md` before major decisions.

## Non-negotiable rules

1. **Inspect before changing:** runtime, entry points, dependency locks, tests, data
   shape, existing architecture and constraints. Unknowns remain `UNVERIFIED`.
2. **Preserve behavior:** types, schemas, null/NaN semantics, timezone, ordering,
   precision, idempotency, side effects, public APIs and failure modes.
3. **Simplicity over ceremony:** no compulsory DDD, classes, repositories, DI,
   microservices, extra packages or folders when a straightforward function works.
4. **Own resources:** context-manage file handles, connections, sessions and
   temporary files; clean up persistent data/streams where supported.
5. **Bound memory and concurrency:** control peak working set, queued jobs, batch
   size and result materialization; avoid eagerly allocating millions of objects.
6. **Move less data:** filter/project/aggregate where work executes; don't move a
   distributed dataset to the Python driver without a size budget.
7. **Measure rather than guess:** distinguish Python allocations, process RSS,
   native memory, Spark driver/executor/worker memory, spill and streaming state.
8. **Prefer targeted refactors:** do nothing if already fit for purpose; keep edits
   small, reversible and covered by meaningful tests.
9. **Trust boundaries matter:** do not log secrets, unpickle untrusted data, bypass
   authorization, run arbitrary production queries or hide failures behind `pass`.
10. **Report evidence faithfully:** static matches are `HEURISTIC`; no live RAM
    savings are claimed without comparable measurements.

## Modes (select one explicitly or infer the narrowest matching intent)

| Mode | Contract |
| --- | --- |
| `audit` | Read-only review, numbered findings, experiments, no source rewrites |
| `implement` | Minimal implementation, contract tests and verification |
| `refactor` | Characterize behavior, edit a small reversible slice, retest |
| `deep-refactor` | Compare no-change vs alternatives, write ADR/stages and rollback; never migrate without authorization |

Read `modes/WORKFLOWS.md` and `policies/severity-and-exceptions.md`.

## Mandatory Databricks upstream integration

**For any Databricks-specific guidance, code change, configuration, migration or
cluster-memory investigation, first verify that the official `databricks-core`
skill is available and load it, plus the relevant official product skill.**

1. Check the agent's available skills; when using the local CLI, run `doctor` to
   verify installed files. Do not mistake a GitHub URL for an installed skill.
2. If `databricks-core` is unavailable or cannot be confirmed, **stop the
   Databricks-specific portion**. Explain installation from the official repo
   (`databricks aitools install`) and continue only ordinary Python analysis.
3. Once available, load `databricks-core`, then route to the official skill:
   `databricks-docs`, `databricks-execution-compute`, `databricks-jobs`,
   `databricks-pipelines`, `databricks-python-sdk`,
   `databricks-spark-structured-streaming` or `databricks-dbsql` as relevant.
   Read `references/databricks-integration.md` for exact responsibility boundaries.
4. **Databricks platform/API/CLI/compute/feature instructions live upstream**.
   Never copy upstream skill files or hardcode timeless availability rules.
   Verify deployed Azure workspace, compute type, environment/DBR version,
   preview flags and the official documentation *at execution time*.
5. Our unique contribution is **Python quality, memory-risk detection, reasoning
   and experimental verification**; the upstream skill owns Databricks specifics.
   The upstream skills do not automatically prove our performance hypotheses.

The frontmatter `compatibility` field is **descriptive**, not a dependency
manager. Enforce this workflow yourself; local scanner blocks Databricks profiles
when it cannot see an official installation. Plugin installs may require an
explicit path for the standalone scanner.

## Workflow

1. **Discover** repo, runtime, workload, tests and data scale. For Databricks:
   identify classic vs serverless, workspace cloud, runtime/environment version,
   Spark Connect, Photon, permissions and relevant job/config ownership.
2. **Establish correctness proof**: input/output schema, invariants, real test
   cases and allowed resource budget. Record what is unknown.
3. **Identify memory domain**: local Python RSS, driver, executor JVM, Python
   worker/Arrow, shuffle/spill, streaming state or storage. Don't conflate them.
4. **Rank alternatives** by correctness risk, expected improvement, operational
   cost and simplicity: no change; smaller data; bounded processing; native Spark
   expressions; targeted partitioning; hardware changes last.
5. **Change the smallest thing** only in `implement`/`refactor` (or explicitly
   authorized `deep-refactor`). Never create production data side effects.
6. **Verify** actual tests and comparable metrics. Report unknowns with `NOT_RUN`
   or `NOT_MEASURED`; include rollback.

## Read references only when applicable

| Trigger | Reference |
| --- | --- |
| All / philosophy | `references/philosophy.md` |
| Python architecture, typing, contracts | `references/python-quality-and-architecture.md` |
| Python allocations, RSS, pandas, profiling | `references/python-memory-and-profiling.md` |
| Async I/O, queues and resource lifecycle | `references/python-async-and-resources.md` |
| Any Databricks task, mandatory dependency | `references/databricks-integration.md` |
| Databricks driver/executor/worker risk patterns | `references/databricks-memory-and-pyspark.md` |
| Databricks telemetry and root-cause evidence | `references/databricks-observability.md` |
| Versioned serverless/classic distinctions | `references/databricks-runtime-and-compute.md` |
| Streaming/state memory risk | `references/databricks-streaming-and-ingestion.md` |
| Test/measurement protocol | `references/testing-and-verification.md` |
| Official source links and date caveats | `references/source-index.md` |

## Optional offline tool (never edits code or contacts Databricks)

```bash
python tools/py_rails.py doctor --profile databricks-classic
python tools/py_rails.py audit ./my-python-project --profile python-general
python tools/py_rails.py audit ./my-databricks-project \
  --profile databricks-classic --upstream-root ~/.claude/skills
```

`audit` supports `--format text|json|sarif`, `--output`, `--exclude-tests`,
`--baseline`, `--write-baseline` and `--fail-on P1|P2|P3`. It is **AST heuristics
only**: a clean scan does not establish efficiency, no finding proves OOM, and
known `collect()` calls may be legitimately bounded. See `README.md` and tests.

**Authorization boundary:** Never launch, resize or configure a cluster, execute
large Spark actions, access sensitive data, publish assets, change tables or
perform cloud writes without explicit permission. Local diagnostics do not
require connecting to Azure.

## Final report contract

Give scope/profile, skill dependencies verified, runtime evidence, memory domain,
findings by P0–P3 and confidence (`CONFIRMED`, `PROBABLE`, `HEURISTIC`,
`UNVERIFIED`), exact file/line, proposed minimal change, risks, verification
actually performed, comparable before/after measurements or `NOT_MEASURED`,
expected cost impact if grounded, rollback and **up to 3 priorities**.
