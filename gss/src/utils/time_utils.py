from __future__ import annotations

import random


def rand_whole_second_ms(min_ms: int, max_ms: int) -> int:
    """
    Return a random duration in milliseconds that is an integer number of seconds
    between min_ms and max_ms (inclusive bounds), i.e., a multiple of 1000.

    Assumes inputs are given in milliseconds. If the [min_ms, max_ms] range does
    not include any whole-second values, this falls back to the nearest value
    within the range that is a multiple of 1000 by clamping.
    """
    # Normalize to integers
    lo = int(min_ms)
    hi = int(max_ms)
    if lo > hi:
        lo, hi = hi, lo

    # Compute whole-second bounds (in seconds)
    min_sec = (lo + 999) // 1000  # ceil(lo/1000)
    max_sec = hi // 1000          # floor(hi/1000)

    if min_sec <= max_sec:
        import random as _r
        sec = _r.randint(min_sec, max_sec)
        return sec * 1000

    # Fallback: clamp to the nearest multiple of 1000 within [lo, hi]
    # Prefer rounding lo up to next 1000 if possible; otherwise round hi down.
    lo_ceil = ((lo + 999) // 1000) * 1000
    if lo_ceil <= hi:
        return lo_ceil
    return (hi // 1000) * 1000
