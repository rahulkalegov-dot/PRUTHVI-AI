
"""Position-level alerts. This module never places or closes broker orders."""
from datetime import time
from math import isfinite


def monitor_position(
    side,
    entry,
    current,
    stop_loss,
    target,
    market_time=None,
):
    try:
        values = [
            float(entry),
            float(current),
            float(stop_loss),
            float(target),
        ]

        if not all(isfinite(v) and v > 0 for v in values):
            return "INVALID_DATA"

        entry, current, stop_loss, target = values

    except (TypeError, ValueError):
        return "INVALID_DATA"

    if side not in ("BUY", "SELL"):
        return "INVALID_SIDE"

    if side == "BUY":
        if not stop_loss < entry < target:
            return "INVALID_LEVELS"

        if current <= stop_loss:
            return "STOP_LOSS"

        if current >= target:
            return "TARGET"

    else:
        if not target < entry < stop_loss:
            return "INVALID_LEVELS"

        if current >= stop_loss:
            return "STOP_LOSS"

        if current <= target:
            return "TARGET"

    if market_time is not None:
        if not isinstance(market_time, time):
            return "INVALID_MARKET_TIME"

        if market_time >= time(15, 15):
            return "SQUARE_OFF"

    return "HOLD"


def should_stop_new_entries(
    daily_loss,
    maximum_daily_loss,
    data_healthy,
):
    try:
        loss = float(daily_loss)
        limit = float(maximum_daily_loss)

        if (
            not isfinite(loss)
            or not isfinite(limit)
            or loss < 0
            or limit < 0
        ):
            return True

    except (TypeError, ValueError):
        return True

    if not data_healthy:
        return True

    return loss >= limit
