
import pytest

from pruthvi_ai.pattern_detector import (
    Candle,
    PatternSignal,
    candle_metrics,
    detect_candlestick_patterns,
)


def test_candle_creation():
    candle = Candle(100, 105, 98, 103, 1000)
    assert candle.close == 103


def test_invalid_candle_prices():
    with pytest.raises(ValueError):
        Candle(100, 95, 98, 103, 1000)


def test_negative_volume_rejected():
    with pytest.raises(ValueError):
        Candle(100, 105, 98, 103, -1)


def test_candle_metrics():
    candle = Candle(100, 105, 98, 103, 1000)
    result = candle_metrics(candle)

    assert result["body"] == 3
    assert result["range"] == 7
    assert result["upper_shadow"] == 2
    assert result["lower_shadow"] == 2


def test_empty_candle_list():
    assert detect_candlestick_patterns([]) == []


def test_doji_detection():
    candle = Candle(100, 102, 98, 100, 1000)

    signals = detect_candlestick_patterns([candle])

    assert any(signal.pattern == "Doji" for signal in signals)


def test_hammer_detection():
    candle = Candle(100, 101.2, 97.8, 101, 1000)

    signals = detect_candlestick_patterns([candle])

    assert any(signal.pattern == "Hammer" for signal in signals)


def test_bullish_engulfing_detection():
    candles = [
        Candle(105, 106, 99, 100, 1000),
        Candle(99, 107, 98, 106, 1500),
    ]

    signals = detect_candlestick_patterns(candles)

    assert any(
        signal.pattern == "Bullish Engulfing"
        for signal in signals
    )


def test_bearish_engulfing_detection():
    candles = [
        Candle(100, 106, 99, 105, 1000),
        Candle(106, 107, 98, 99, 1500),
    ]

    signals = detect_candlestick_patterns(candles)

    assert any(
        signal.pattern == "Bearish Engulfing"
        for signal in signals
    )


def test_signals_have_valid_structure():
    candles = [Candle(100, 102, 98, 100, 1000)]

    signals = detect_candlestick_patterns(candles)

    for signal in signals:
        assert isinstance(signal, PatternSignal)
        assert 0 <= signal.confidence <= 1
        assert signal.direction in {
            "bullish", "bearish", "neutral"
        }
