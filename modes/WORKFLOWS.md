# Modes and execution contracts

## AUDIT (read-only)

- Inventory targets, version, environment, data shape, trust boundaries, code ownership, CI and existing test state.
- Inspect code and existing metrics without running costly remote operations.
- Rank findings by impact × probability × evidence × operational risk, not line count.
- Distinguish issue observed in telemetry from a static code heuristic.
- For each finding provide safe minimal patch **proposal**, not an unsolicited edit.
- Output at most three priority experiments and remaining gaps.

## IMPLEMENT

- Identify input/output/error contracts and the smallest scope consistent with existing code.
- Implement with tests, explicit resource cleanup, bounded work and no unasked dependency upgrade.
- Explain version assumptions and actual validation performed.

## REFACTOR

- Establish characterization tests or a clearly recorded baseline of behavior.
- Compare doing nothing, a small local change and a new abstraction.
- Change one conceptual theme, verify, and preserve a simple rollback.
- For a Databricks refactor compare schema and row-level aggregates, null/timezone behavior, and performance on equivalent input; do not claim semantics preserved from a code-only review.

## DEEP-REFACTOR

- Require a concrete architectural failure, not discomfort about file size.
- Write an ADR with no-change option, expected cost, API/data compatibility, staged rollout, verification checkpoints and rollback.
- Do not independently authorize a pipeline migration, job deployment, table rewrite, compute upgrade or production data access.

## Minimum evidence labels

`CONFIRMED`: test/trace/plan shows issue. `PROBABLE`: inspected relevant code and strong causal model. `HEURISTIC`: syntax hit or weak smell. `UNVERIFIED`: necessary runtime/data evidence missing. `NOT_RUN`: a command or cluster experiment was not executed.
