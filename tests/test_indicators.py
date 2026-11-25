import pandas as pd
import pytest

from pruthvi_ai.indicators import calculate_indicators


def sample_data(rows=100):
    return pd.DataFrame({
        "open": [100 + i for i in range(rows)],
        "high": [103 + i for i in range(rows)],
        "low": [99 + i for i in range(rows)],
        "close": [102 + i for i in range(rows)],
        "volume": [1000 + i * 10 for i in range(rows)],
    })


def test_indicators_created():
    result = calculate_indicators(sample_data())

    expected = [
        "EMA_9",
        "EMA_21",
        "EMA_50",
        "RSI_14",
        "MACD",
        "MACD_SIGNAL",
        "ATR_14",
        "VOLUME_SMA_20",
    ]

    for column in expected:
        assert column in result.columns


def test_indicator_output_rows():
    result = calculate_indicators(sample_data())
    assert len(result) == 100


def test_insufficient_candles():
    with pytest.raises(ValueError):
        calculate_indicators(sample_data(20))


def test_missing_columns():
    with pytest.raises(ValueError):
        calculate_indicators(pd.DataFrame({"close": [100] * 60}))


def test_invalid_prices():
    data = sample_data()
    data.loc[0, "close"] = -100

    with pytest.raises(ValueError):
        calculate_indicators(data)