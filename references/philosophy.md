# Philosophy — Correctness, clarity, bounded resources

This skill is a sibling to the Flutter, Rust, C++ and TypeScript Engineering Guardrails family. It carries their *principles*, not each language's implementation patterns.

1. **Engineering over aesthetics.** Code that passes the linter can still be fragile, costly and poorly understood. Code that is short can still be excellent; neither file length nor abstraction count proves quality.
2. **Simplicity is a functional requirement.** Prefer an obvious function over a hierarchy when both preserve contracts. Don't impose OOP, functional programming, layered architecture, repositories or dependency injection by default.
3. **Design for the current workload.** Keep Python for orchestration where it shines; use native/distributed operations for demonstrated large-scale workloads. Switching to PySpark, Polars, DuckDB or Rust is not automatically a fix.
4. **Correctness before optimization.** Preserve result sets, ordering requirements, timezone and NULL semantics, precision, deduplication, transactional writes, security, and failure behavior.
5. **Memory is a budget, not a prize.** Bound peak RSS, not just the average. Distinguish peak Python memory, JVM heap, worker/native memory, shuffle spill, on-disk caching and total cluster memory. Offloading to disk is not the same as reducing work.
6. **Evidence beats authority and folklore.** A documented API constraint is strong evidence; code smells are leads; benchmark claims require workload and environment details. Keep unknowns visible.
7. **Use runtime defaults until measurement disagrees.** Avoid arbitrary partitions, executor heap overrides, blanket `cache()` and scaling up as the first remedy.
8. **Intentional abstraction.** Extract interfaces only to enforce genuine substitutability, isolation or change boundaries. Prefer pure, testable transformations when feasible.
9. **Small, reversible diffs.** Favor characterization → targeted change → regression check → deployment/rollback plan. Deep refactors must compete with the option to leave code as-is.
10. **Agents must be truthful.** Never convert a grep hit into a confirmed outage; never say a command or Databricks job ran when it did not. Mark source version and execution environment.

## Anti-slop checks before proposing code

- Does this add a new dependency for something the standard library or existing stack already handles?
- Is the abstraction used more than once or does it enforce a clear contract?
- Did we introduce a cache because profiling showed repeated work, or merely because it sounded fast?
- Did we create a new list/DataFrame/copy that can be avoided without hurting clarity?
- For Databricks: are we pushing work to executors or accidentally bringing it back to the driver?
- Are we hiding data correctness problems behind `try/except: pass`, `.fillna` defaults or broad suppressions?
- Can the next engineer understand how to measure and revert this change?

**One-line mantra:** The fastest, safest, most maintainable code is often the code and data movement you never needed.

This file expresses this skill's original synthesis; links to upstream sibling repos and official references are in `references/source-index.md`.
