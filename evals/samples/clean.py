#!/usr/bin/env python3
"""Rate limiter for the upload queue."""

import time

# S3 throttles bursts above 3500 req/s per prefix, so we cap below that.
BURST_CEILING = 3000


def acquire(tokens: int, *, now: float | None = None) -> bool:
    now = now if now is not None else time.monotonic()
    return tokens <= BURST_CEILING and now > 0
