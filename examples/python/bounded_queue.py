"""Bounded async producer/consumer demo (Python 3.10+), no external services.

The task count is bounded (one producer + N workers), as is the queue. The
caller must still ensure the input iterable itself is not eagerly materialized.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable


async def process_bounded(
    items: Iterable[int],
    process: Callable[[int], Awaitable[None]],
    *,
    workers: int = 4,
    queue_size: int = 16,
) -> None:
    if workers <= 0 or queue_size <= 0:
        raise ValueError("workers and queue_size must be positive")

    sentinel = object()
    queue: asyncio.Queue[object] = asyncio.Queue(maxsize=queue_size)

    async def producer() -> None:
        for item in items:
            await queue.put(item)
        for _ in range(workers):
            await queue.put(sentinel)

    async def worker() -> None:
        while True:
            item = await queue.get()
            try:
                if item is sentinel:
                    return
                await process(int(item))
            finally:
                queue.task_done()

    tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    producer_task = asyncio.create_task(producer())
    try:
        # gather propagates producer/worker errors; the finally block cancels
        # outstanding tasks so a failed worker cannot strand the producer.
        await asyncio.gather(producer_task, *tasks)
    finally:
        for task in (producer_task, *tasks):
            if not task.done():
                task.cancel()
        await asyncio.gather(producer_task, *tasks, return_exceptions=True)
