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

For a local change, inspect the supported Python versions, callers and tests. Identify when validation, resource acquisition, iteration and cleanup occur. Preserve the caller's ownership and error behavior. Exercise observable success and failure paths. For memory-sensitive work distinguish retained data, transient allocations and external resources.

Build regression tests from the caller's guarantees. A legal implementation may perform work eagerly or lazily, reuse an object or return an equivalent one. Assert timing, identity and internal call counts only when the contract requires them. Where behavior must survive an optimization, compare public results and errors with the working implementation across several short update sequences. Measure required work at the stated boundary.

- For async cancellation or resource lifetime decisions, consult [async and resources](references/python-async-and-resources.md). For memory claims, use [memory and profiling](references/python-memory-and-profiling.md).
- For audit, refactor, migration, dependency changes, platform work or an OOM investigation, select the applicable workflow and references in the [engineering guide](engineering-guide.md). Audit the source read-only unless edits are requested.

## Mandatory Databricks upstream integration

1. For Databricks-specific advice or changes, verify and load the official `databricks-core` and relevant product skill as described in [Databricks integration](references/databricks-integration.md).
2. If the required upstream skills are unavailable, **stop the
   Databricks-specific portion** and explain the missing prerequisite. Continue any independent Python work. Cloud operations require explicit authorization.

For an implementation, state the behavior delivered, checks run and material limitations. For an audit, lead with the finding and its consequence. Answer direct questions at the requested level of detail.
