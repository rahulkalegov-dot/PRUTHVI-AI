from datetime import datetime, time


def monitor_position(
    side,
    entry,
    current,
    stop_loss,
    target,
    market_time=None
):
    if min(entry, current, stop_loss, target) <= 0:
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

    if side == "SELL":
        if not target < entry < stop_loss:
            return "INVALID_LEVELS"

        if current >= stop_loss:
            return "STOP_LOSS"

        if current <= target:
            return "TARGET"

    if market_time is not None:
        if market_time >= time(15, 15):
            return "SQUARE_OFF"

    return "HOLD"


def should_stop_new_entries(
    daily_loss,
    maximum_daily_loss,
    data_healthy
):
    if not data_healthy:
        return True

    if daily_loss >= maximum_daily_loss:
        return True

    return False