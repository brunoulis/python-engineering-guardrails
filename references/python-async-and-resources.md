# Async, resource lifecycle and bounded backpressure

- First separate I/O-bound concurrency from CPU-bound work. Asynchronous Python does not automatically parallelize pure CPU operations.
- Every async task needs an owner, completion rule, cancellation/shutdown path and bounded failure retry policy.
- A semaphore limits simultaneous entries to a critical region but **does not limit the memory of tasks created before entering**. Use a bounded queue and fixed worker count when producer volume may be large.
- Avoid unbounded request retries that multiply work and memory pressure. Include timeouts, jitter/backoff when relevant and idempotent writes.
- Use `async with` for supported clients/sessions and `try/finally` for cleanup; ensure transactions are committed/rolled back explicitly.
- Do not hide exceptions behind `except Exception: pass`, detached `create_task` or cancellation swallowing.
- On modern Python, `Executor.map(buffersize=...)` may bound submissions (added in Python 3.14); verify the project's supported version before using this feature. Older versions need an alternative.
- Avoid launching many concurrent Spark jobs from driver-side Python threads: the Spark driver itself can become the bottleneck.

## Bounded worker pattern (standard library)

See `examples/python/bounded_queue.py` for a working async queue with `maxsize`, fixed workers, error propagation and clean shutdown. Adapt rather than blindly copying it; choice depends on CPU vs I/O, ordering, retry and cancellation contracts.

Official sources: `https://docs.python.org/3/library/asyncio-sync.html`, `https://docs.python.org/3/library/asyncio-queue.html`, `https://docs.python.org/3/library/concurrent.futures.html`, Azure Databricks driver-overload documentation in `source-index.md`.
