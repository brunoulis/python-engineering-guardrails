# Findings, gates and exceptions

| Severity | Meaning | Example |
| --- | --- | --- |
| P0 | Confirmed immediate data-loss/security/corruption risk | destructive production overwrite without safeguards |
| P1 | Confirmed or strongly evidenced production failure/high impact | driver OOM reproduced on the target job |
| P2 | Actionable, context-dependent engineering risk | `toPandas()` on an unbounded dataframe, evidence missing |
| P3 | Review/maintainability suggestion | non-critical data-copy or possible unnecessary materialization |

A static rule does **not** earn P0/P1 by itself. The bundled scanner emits P2/P3 `HEURISTIC` only. Escalation needs separate human/agent evidence and should be recorded as such.

Baseline is not an exemption: it separates known from new findings. Exceptions require an exact rule and path, documented reason, owner, review date, actual scope and expiry. Never use global suppressions to hide unexamined failures.

CI fail-on gates should be deliberate; a nonzero scanner result from syntax errors means **incomplete**, not "issues absent". Baseline should be reviewed before acceptance.
