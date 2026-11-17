# Python memory and profiling

## First identify the memory domain

A Python process has Python allocations, extension/native allocations, stack, shared libraries, memory-mapped pages and buffers. Peak RSS is not identical to the memory reported by `tracemalloc`, and neither is identical to Databricks executor JVM heap or total node RAM.

Before optimizations, record input size, expected output, Python version, process topology, peak RSS, runtime and correctness. Ask whether the same object is copied multiple times or held by more than one concurrent task.

## Common ways to waste memory

- `list(generator)` / `.readlines()` / eager `json.load()` may materialize an entire input; **only a risk for unbounded input**, not always a defect.
- Large dictionaries/lists of full records when incremental aggregation, bounded chunks, SQL or streaming would be equivalent.
- Repeated conversions between JSON ↔ Python ↔ pandas ↔ Arrow ↔ Spark; watch peak coexistence of old and new buffers.
- `pandas.concat` in a loop and repeated DataFrame copies; accumulate a modest number of chunks only when bounded, or write incrementally.
- `asyncio.gather` with a huge eagerly created task list, unbounded producers, or `ThreadPoolExecutor.map` fed a huge iterable on a Python version without bounded buffering.
- Leaked references held in global caches, exception tracebacks, queued objects or references in long-lived notebook sessions.
- Allocating oversized NumPy dtypes or object columns where validated lower-width/efficient types preserve precision and null semantics.

## Evidence-backed techniques

- A generator or streaming parser avoids a full input list **if the downstream consumer also stays bounded**.
- Use chunked reads with a well-defined maximum chunk size. Account for temporary copies, per-row overhead and output buffering; file size alone is not RAM size.
- Bound **queued work AND active work**, not merely a semaphore around a million already-created tasks.
- Hold explicit context managers for file handles, DB sessions and temporary resources; free references by exiting scope. `gc.collect()` is not a generic optimization and does not guarantee RSS reduction.
- Use `tracemalloc` for Python allocations / before-after snapshots. It does not measure every native/JVM allocation; consider a native-aware profiler such as Memray when supported and authorized.
- Use the project-compatible profiler and never run expensive tracing on production/cluster nodes without authorization.

## Minimal local measurements (opt-in)

```python
import tracemalloc

tracemalloc.start()
# Perform a SMALL, representative, controlled operation here.
current, peak = tracemalloc.get_traced_memory()
print({"tracked_current_bytes": current, "tracked_peak_bytes": peak})
tracemalloc.stop()
```

Do not label these numbers "cluster RAM" or "process peak RSS". For native and process-wide memory, use an appropriate system/process metric alongside tracemalloc. Where no measurements exist, say `NOT_MEASURED`.

Official sources: `https://docs.python.org/3/library/tracemalloc.html`, `https://docs.python.org/3/library/concurrent.futures.html`, `https://github.com/bloomberg/memray`.
