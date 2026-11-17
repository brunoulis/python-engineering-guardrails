# Changelog

## 0.1.0 — 2026-11-17

- First portable Agent Skill for Python engineering, memory/resource safety and anti-slop philosophy.
- Four modes: audit, implement, refactor and deep-refactor; context-aware profiles.
- **Hard upstream requirement for Databricks-specific work:** official `databricks-core` plus relevant official specialist skills. No bundled Databricks implementation.
- Read-only, stdlib-only Python AST auditor with official skill check, severity/confidence, JSON, SARIF, opt-in baselines and CI gate.
- Unit tests and educational code samples; no live Azure benchmarks.
- Explicit Azure serverless cache public-preview caveat (2026-10-23) to avoid stale blanket restrictions.
