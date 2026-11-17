# Python Engineering Guardrails

**Python-first engineering quality, anti-slop architecture and bounded memory — with an optional Azure Databricks focus and a mandatory official upstream Databricks skill dependency.**

A portable `SKILL.md` for coding agents, inspired by the same philosophy as the
[Flutter](https://github.com/brunoulis/flutter-engineering-guardrails),
[Rust](https://github.com/brunoulis/rust-engineering-guardrails),
[C++](https://github.com/brunoulis/cpp-engineering-guardrails) and
[TypeScript](https://github.com/brunoulis/typescript-engineering-guardrails)
Engineering Guardrails repositories.

> **Principle:** The best optimization may be to move less data or write less code.
> Correctness and maintainability come before speculative improvements.

[Guía en español](README.es.md) · [Philosophy](references/philosophy.md) · [Databricks dependency contract](references/databricks-integration.md)

## What it does

- Review Python architecture, API contracts, tests, resource ownership and asynchronous concurrency without mandating artificial layering.
- Investigate high peak RSS, memory copies, eager materialization and unbounded work in APIs, scripts, ETL and data science.
- On Databricks tasks, differentiate **Python process / Spark driver / executor JVM / Python worker / shuffle / streaming state**.
- Use four modes: `audit` (read-only), `implement`, `refactor`, `deep-refactor`.
- Run an **optional local, read-only AST auditor**, no PySpark installation and no Azure login needed, supporting JSON, SARIF, reviewed baselines and optional CI gates.
- Provide source-backed hypotheses, minimal remediation, proof requirements and reversible changes, never fabricated memory savings.

## Mandatory dependency for Databricks work

Our skill **does not contain or replace Databricks' official platform instructions**. When a Databricks profile is activated it requires the independent official repository:

<https://github.com/databricks/databricks-agent-skills>

Install official stable skills using the supported Databricks CLI:

```bash
databricks aitools install
```

First activate `databricks-core`, then the official specialist (`databricks-docs`, `databricks-execution-compute`, `databricks-jobs`, `databricks-python-sdk`, `databricks-pipelines`, `databricks-spark-structured-streaming`, etc.). Our skill contributes **memory-risk analysis, Python quality and verification**, not duplicate Databricks APIs, configuration snippets or login logic.

The frontmatter dependency is **not installed automatically** by the Agent Skills format. The agent must check its actual skill registry, and the optional CLI checks local installed skill files. Plugin-managed skills may need `--upstream-root` when their cache is not discoverable by the standalone CLI. **If the official dependency cannot be verified, Databricks-specific work is blocked; Python-general work still functions.**

## Install our skill

Copy the **entire** `python-engineering-guardrails` directory, including its `SKILL.md`, to the relevant directory for your agent, for example:

| Coding agent | Project-local | User-level |
| --- | --- | --- |
| Claude Code | `.claude/skills/python-engineering-guardrails/` | `~/.claude/skills/python-engineering-guardrails/` |
| Codex / generic agents using `.agents` | `.agents/skills/python-engineering-guardrails/` | `~/.agents/skills/python-engineering-guardrails/` |

Paths differ for some providers; use your agent's current skill installation instructions. Just copying `SKILL.md` is **not** enough for the bundled references and auditor.

## Run the optional auditor

Requires **Python 3.10+ on the machine running the tool**. It does not impose that minimum version on the Python application being reviewed. Only Python standard-library modules are used.

```bash
# Ordinary Python (does not need Databricks skills)
python tools/py_rails.py audit ../my-python-project --profile python-general

# Check that an official Databricks skill exists locally
python tools/py_rails.py doctor --profile databricks-classic \
  --upstream-root ~/.claude/skills

# Inspect Databricks Python source without running any Spark job
python tools/py_rails.py audit ../my-databricks-project \
  --profile databricks-classic \
  --upstream-root ~/.claude/skills

# JSON, SARIF, optional CI severity gate
python tools/py_rails.py audit ../my-databricks-project \
  --profile databricks-serverless \
  --upstream-root ~/.claude/skills \
  --format sarif --output report.sarif --fail-on P2

# Generate a reviewed baseline at an explicit NEW file path
python tools/py_rails.py audit ../my-python-project \
  --profile python-general --write-baseline baseline.json

python -m unittest discover -s tests -v
```

Use `--upstream-root` with a root that contains `databricks-core/SKILL.md`, `skills/databricks-core/SKILL.md`, or the skill folder itself. The scanner **does not automatically download or authenticate** the upstream dependency.

Exit codes: `0` complete/no gate failures; `1` at least one unbaselined finding meeting `--fail-on`; `2` incomplete scan or invalid input/output; `3` required Databricks upstream skill not found. Output files are **opt-in** and never overwritten.

## Scope of static findings

Current heuristics include:

| Category | Examples | Meaning |
| --- | --- | --- |
| Driver materialization | `collect`, `toPandas`, `list(toLocalIterator())` | Possible driver-memory pressure, data size unknown |
| Spark distribution | `repartition(1)`, `coalesce(1)`, grouped `applyInPandas` | Potential shuffle/skew or oversized partition/group |
| Caching | `cache`, `persist` | **Review**, not a universal ban; compute-specific support matters |
| Serverless compatibility | `.rdd`, `.checkpoint`, SQL/catalog cache methods | Verify documented feature availability for the real environment |
| Local Python | `fetchall`, whole-file readers, `asyncio.create_task` inside loops | Check cardinality, memory growth and work ownership |

**A syntax hit is not proof of a bug or OOM**. For example, collecting 5 rows is sometimes correct. No tool knows the true dataset size or actual cluster peak RAM through AST alone. There is no auto-fix mode and no remote execution.

## Critical 2026 Databricks version caveat

Databricks announced **serverless DataFrame cache public preview on October 23, 2026**, with specific environment/client/preview requirements. `df.cache()` and `df.persist()` can be available on supported serverless environments, with materially different snapshot and `unpersist()` semantics from classic compute. Older serverless limitation pages can contradict this newer release. **Always verify current docs and deployed versions**, never encode “cache unavailable on serverless” as a timeless rule. See [official release notes](https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/) and [feature guide](https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/dataframe-cache).

## Contents

```text
python-engineering-guardrails/
  SKILL.md                        Agent instructions / rules / routing
  references/
    philosophy.md                 Shared family engineering philosophy
    databricks-integration.md    Mandatory upstream contract
    databricks-*.md               Original risk questions and evidence approach
    python-*.md                  Python quality, profiling, async
    source-index.md              Official links with version caveats
  modes/WORKFLOWS.md             Audit/implement/refactor/deep-refactor
  profiles/README.md            Profile selection
  policies/                     Severity and exceptions
  tools/py_rails.py              Offline stdlib AST auditor + dependency doctor
  tests/test_py_rails.py         Offline unit tests
  examples/                      Educational examples, never auto-run
  templates/                     Reproducible audit and compute context
  .github/workflows/ci.yml       Offline CI, no Azure credentials required
```

## Maturity and licensing

**v0.1.0 — initial implementation.** The offline tests verify the scanner's specific patterns and dependency gates; **no live Azure Databricks performance benchmarks have been run**. It does not remotely inspect notebooks that exist only in a Databricks workspace; provide exported `.py` sources. Planned next steps: `.ipynb` support, lower false-positive rates, authenticated development-cluster measurements only with approval.

This independent code/documentation is MIT licensed. Not affiliated with Databricks or Microsoft. The official Databricks skills are **not bundled**; their own license and terms apply.
