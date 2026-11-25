from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


def validate_candle(candle: Candle) -> bool:

    if not candle.symbol:
        return False

    if candle.timeframe not in ("5m", "15m", "1h"):
        return False

    if candle.timestamp.tzinfo is None:
        return False

    if candle.timestamp > datetime.now(timezone.utc):
        return False

    if min(
        candle.open,
        candle.high,
        candle.low,
        candle.close
    ) <= 0:
        return False

    if candle.high < max(candle.open, candle.close):
        return False

    if candle.low > min(candle.open, candle.close):
        return False

    if candle.high < candle.low:
        return False

    if candle.volume < 0:
        return False

    return True


def reject_stale_data(
    timestamp: datetime,
    max_age_seconds: int = 120
) -> bool:

    if timestamp.tzinfo is None:
        return True

    age = (
        datetime.now(timezone.utc) - timestamp
    ).total_seconds()

    return age > max_age_seconds