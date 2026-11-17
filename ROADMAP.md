# Roadmap — Python Engineering Guardrails

## v0.1.0 completed (2026-11-17)

- Portable Agent Skills specification-compatible `SKILL.md`.
- Shared anti-slop philosophy, four modes and Python architecture/resource profiles.
- Databricks-only official dependency contract and fail-closed offline doctor.
- Original Databricks memory triage layered on official upstream skills; platform instructions remain external.
- Local stdlib AST risk scanner for Python/PySpark: JSON, SARIF, optional baselines, opt-in severity gates, no target edits.
- Offline tests, CI workflow, safety templates, official source index, basic examples.
- Serverless DataFrame cache preview (2026-10-23) version caveat.

## Planned

1. Validate scanner against real anonymized Python/PySpark repositories and quantify false positives/negatives.
2. Add optional exported `.ipynb` analysis (only code cells, no notebook execution).
3. Analyze SQL strings and common Spark plans while reducing context-free guesses and preserving semantics.
4. With explicit permission, validate *a nonproduction Azure workspace* using official upstream skills, current feature flags and read-only logs/query profiles.
5. Capture before/after benchmarks on identical data/compute for schema, peak memory, RSS, skew, shuffle/spill and cost.
6. Optional plugin/agent discovery improvements (avoid treating undiscoverable plugin caches as definitely absent).
7. Add more reproducible test fixtures for PySpark/Delta and release-time source/link checks.

## Known limitations

- Static syntax matches do not prove real RAM issues. Variable types and data cardinality are unknown.
- No live Databricks workspace access, cluster benchmarks, savings percentages or deployment claims.
- `doctor` checks local files, **not** that an agent actually activated a skill or that files were published by Databricks.
- Source `.py` only; remote notebooks / `.ipynb` unsupported in v0.1.
- The baseline identifies rule + path + normalized source line; duplicate identical findings can share a fingerprint. Review accepted issues.
- Python source containing notebook-only `%sql` magic not exported as valid Python may fail to parse; a syntax error means the scan is INCOMPLETE.
