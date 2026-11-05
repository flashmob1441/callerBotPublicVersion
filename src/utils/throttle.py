import time

_last_hit: dict[tuple, float] = {}


def allow(key: tuple, cooldown: float) -> bool:
    """True if `key` wasn't seen in the last `cooldown` seconds (and records the hit)."""
    now = time.monotonic()
    if len(_last_hit) > 1000:
        for k in [k for k, t in _last_hit.items() if now - t > 3600]:
            del _last_hit[k]
    last = _last_hit.get(key)
    if last is not None and now - last < cooldown:
        return False
    _last_hit[key] = now
    return True
