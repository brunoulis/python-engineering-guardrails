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

# Python engineering guardrails

Use the project's Python versions and callers. Trace validation, iteration, resource ownership and cleanup on failure. Test public guarantees; assert timing, identity or internal calls only when required. For optimizations, compare results and errors with the working version across short update sequences. Measure work at the stated boundary.

Read related source together and expand check output on failure. See [async resource ownership](references/python-async-and-resources.md) or [memory measurements](references/python-memory-and-profiling.md) for the relevant section. For audits, migrations, platform work or wider refactors, select the workflow in the [engineering guide](engineering-guide.md). Audit read-only unless edits are requested. Report behavior, checks and material limits.

## Mandatory Databricks upstream integration

Load official `databricks-core` and the relevant product skill per [Databricks integration](references/databricks-integration.md). If either is unavailable, **stop the
   Databricks-specific portion** and explain what is missing. Continue independent Python work. Cloud operations require explicit authorization.
