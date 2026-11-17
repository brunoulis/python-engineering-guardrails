---
name: python-engineering-guardrails
description: >-
  Implement, audit and refactor Python APIs, async services and data pipelines. Covers
  resource ownership, memory profiling, Pandas, PySpark and Azure Databricks.
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

# Python engineering guardrails

Use the project's Python versions and callers. Trace validation, iteration, resource ownership and cleanup on failure. Test public guarantees; assert timing, identity or internal calls only when required. For optimizations, compare public results and errors with the previous version across updates. Separate compatibility tests from work-count tests. If initialization can be eager or lazy, both must pass. For a warm-read guarantee, arrange and call the public read once, snapshot counters, repeat the read, then assert the delta. Check each assertion against both allowed strategies before finishing.

For a local refactor, read the affected implementation, caller and nearest tests together. Reuse those observations for the patch and checks. Keep passing output to counts; retain failure diagnostics. See [async resource ownership](references/python-async-and-resources.md) or [memory measurements](references/python-memory-and-profiling.md) for the relevant section. For wider refactors, use the relevant section of [workflows](modes/WORKFLOWS.md); for audits, migrations or platform work, use the [engineering guide](engineering-guide.md). Audit read-only unless edits are requested. Report behavior, checks and material limits.

## Mandatory Databricks upstream integration

Load official `databricks-core` and the relevant product skill per [Databricks integration](references/databricks-integration.md). If either is unavailable, **stop the
   Databricks-specific portion** and explain what is missing. Continue independent Python work. Cloud operations require explicit authorization.
