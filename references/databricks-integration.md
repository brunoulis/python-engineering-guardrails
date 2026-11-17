# Contract with official databricks-agent-skills

**Purpose:** single owner for Databricks platform knowledge. Our skill owns
Python maintainability and performance investigations; `databricks-agent-skills`
owns current Azure Databricks APIs, authentication, compute, jobs and operations.

Official upstream: <https://github.com/databricks/databricks-agent-skills>.

## Hard dependency for Databricks-specific work

The presence of `databricks-core` **must be verified**, either through the
coding agent's exposed skill registry or by a real `SKILL.md` installed on disk.
It is not enough to know the skill exists online. Load `databricks-core` before
platform-specific changes and load any specialist skill needed.

- **Missing/unconfirmed:** explain the requirement and official install route;
  stop Databricks-specific implementation, cluster instructions and claims.
  You may still perform Python-general code analysis without applying
  Databricks-specific recommendations.
- **Available:** read upstream skill files through the agent, inspect their
  parent/workflow rules and current official documentation. Verify versions.
- **Conflicting guidance:** platform versions, release notes and feature flags
  matter. Report the conflict; do not silently choose older documentation.
- **No implicit installs:** never run `databricks aitools install` without user
  permission. Don't automatically clone Databricks code or bundle upstream.

`compatibility` in Agent Skills metadata is advisory, not executable dependency
resolution. `tools/py_rails.py doctor` checks local paths but cannot identify
all providers' plugin caches. Pass `--upstream-root` to a specific installation
root where necessary. A local file check does not prove a skill is loaded inside
the current coding agent: confirm its actual availability separately.

## Routing table (look up upstream files, do NOT clone their contents)

| Work | Official skill to activate after `databricks-core` |
| --- | --- |
| Verify latest API/support and limits | `databricks-docs` |
| Execute or examine compute profiles | `databricks-execution-compute` |
| Schedule, run and inspect jobs | `databricks-jobs` |
| Declarative Spark pipelines | `databricks-pipelines` |
| SDK, Databricks Connect, API | `databricks-python-sdk` |
| Spark Structured Streaming | `databricks-spark-structured-streaming` |
| SQL warehouses and queries | `databricks-dbsql` |
| Asset/bundle deployment | `databricks-dabs` |
| Usage/cost/lineage/UC system tables | `databricks-unity-catalog` |

If the upstream repository has changed its available skills, use **its
current manifest** rather than an outdated fixed list here.

## Memory investigation contract

We own the *questions*: Where does memory peak? Is a full materialization
necessary? Is task concurrency bounded? Which operation is likely dominant?
What correctness property needs preservation? What comparison would prove it?

Official Databricks skills + documentation own the *platform answers*: How to
inspect the relevant metrics, which query profile exists, supported APIs,
cache semantics, compute configuration and approved execution mechanisms.

Example: Our AST auditor identifies `.cache()`. That is **not proof of a bad
cache**. Check reuse, storage and data freshness, then use `databricks-docs`
for semantics on the deployed environment. As of 2026-10-23, serverless
DataFrame cache is in public preview under requirements; older limitation pages
can be stale. Never rewrite `cache/unpersist` code without checking that
snapshot/lifecycle behavior preserves correctness.

## Separate licensing

This project is independently authored and MIT licensed. It **does not ship**
upstream Databricks skill files; installing/using upstream software is subject
to its own terms. Linking public docs does not relicence their contents.
