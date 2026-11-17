"""Stream a newline-delimited input with bounded buffering (stdlib only)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


def nonempty_lines(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            value = line.strip()
            if value:
                yield value


# This remains memory-bounded only if the consumer does NOT call list() on all
# returned values or buffer an unbounded result itself.
