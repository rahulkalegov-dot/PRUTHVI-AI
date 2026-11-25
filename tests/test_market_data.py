from datetime import datetime, timezone, timedelta
from pruthvi_ai.market_data import (
    Candle,
    validate_candle,
    reject_stale_data,
)


def test_valid_candle():
    candle = Candle(
        symbol="RELIANCE",
        timeframe="5m",
        timestamp=datetime.now(timezone.utc),
        open=100,
        high=110,
        low=95,
        close=105,
        volume=1000,
    )
    assert validate_candle(candle) is True


def test_invalid_candle():
    candle = Candle(
        symbol="RELIANCE",
        timeframe="5m",
        timestamp=datetime.now(timezone.utc),
        open=100,
        high=90,
        low=95,
        close=105,
        volume=1000,
    )
    assert validate_candle(candle) is False


def test_stale_data():
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    assert reject_stale_data(old_time) is True


def test_fresh_data():
    now = datetime.now(timezone.utc)
    assert reject_stale_data(now) is False