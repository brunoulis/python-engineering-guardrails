# Python quality, APIs and architecture

## Discover before suggesting

- Read `pyproject.toml`, resolved lock (`uv.lock`, `poetry.lock`, `requirements*.txt`, `pdm.lock` or existing environment), supported Python versions and entry points; do not assume latest Python documentation applies.
- Look for established project structure and tests. Favor feature-local modules and small pure functions, not artificial folders and one-file-per-class.
- Respect sync/async API contracts, validation/error types, timezones, timezone-aware datetimes, numeric precision, sort order, stable serialization and file/DB schema.
- Prefer type annotations at public and complex boundaries when they improve comprehension. Types do not replace runtime validation for untrusted input.
- Dataclasses, enums, protocols, TypedDict and Pydantic are optional tools with different purposes; pick by actual contracts and existing dependencies.
- Never add a new ORM, DI container, generic repository or abstract interface merely to decouple a single caller.
- Avoid mutable default arguments, broad bare `except`, silent error swallowing, hidden global state and unsafe deserialization of untrusted pickle.
- Avoid introducing `Any` casts or broad type suppressions to make type checking green; explain unavoidable boundary types.

## Refactor rubric

1. **Keep:** simplest working version with clear tests.
2. **Local extraction:** a pure transformation or resource-lifecycle helper is valuable when it reduces cognitive load or duplication.
3. **Boundary:** add a service/protocol only when it isolates IO/latency/failure or enables meaningful substitution.
4. **Migration:** only after cost, compatibility, tests and rollback are established.

## Dependencies and reproducibility

- Prefer existing lockfile/tooling. Do not blindly replace Poetry/pip with uv; `uv` can be useful for reproducible lock, but migration must be justified.
- Do not unilaterally change the audited app's supported Python version or install packages on its cluster.
- In Databricks, check Runtime's bundled libraries and the job's environment before choosing or pinning third-party packages. Local and remote Python environments may differ.
