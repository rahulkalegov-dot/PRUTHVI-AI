
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


def test_non_finite_values_rejected():
    with pytest.raises(ValueError):
        Candle(float("nan"), 105, 98, 103, 1000)


def test_candle_metrics():
    candle = Candle(100, 105, 98, 103, 1000)
    result = candle_metrics(candle)

    assert result["body"] == 3
    assert result["range"] == 7
    assert result["upper_shadow"] == 2
    assert result["lower_shadow"] == 2


def test_empty_candle_list():
    assert detect_candlestick_patterns([]) == []


def test_invalid_input_type():
    with pytest.raises(TypeError):
        detect_candlestick_patterns([100, 101])


def test_doji_detection():
    candle = Candle(100, 102, 98, 100, 1000)
    signals = detect_candlestick_patterns([candle])

    assert any(s.pattern == "Doji" for s in signals)


def test_hammer_detection():
    candle = Candle(100, 101.2, 97.8, 101, 1000)
    signals = detect_candlestick_patterns([candle])

    assert any(s.pattern == "Hammer" for s in signals)


def test_inverted_hammer_detection():
    candle = Candle(100, 105, 99.9, 101, 1000)
    signals = detect_candlestick_patterns([candle])

    assert any(
        s.pattern == "Inverted Hammer"
        and s.direction == "bullish"
        for s in signals
    )


def test_shooting_star_detection():
    candle = Candle(101, 105, 99.9, 100, 1000)
    signals = detect_candlestick_patterns([candle])

    assert any(
        s.pattern == "Shooting Star"
        and s.direction == "bearish"
        for s in signals
    )


def test_inverted_hammer_not_shooting_star():
    candle = Candle(100, 105, 99.9, 101, 1000)
    signals = detect_candlestick_patterns([candle])

    assert not any(
        s.pattern == "Shooting Star"
        for s in signals
    )


def test_shooting_star_not_inverted_hammer():
    candle = Candle(101, 105, 99.9, 100, 1000)
    signals = detect_candlestick_patterns([candle])

    assert not any(
        s.pattern == "Inverted Hammer"
        for s in signals
    )


def test_bullish_engulfing_detection():
    candles = [
        Candle(105, 106, 99, 100, 1000),
        Candle(99, 107, 98, 106, 1500),
    ]

    signals = detect_candlestick_patterns(candles)

    assert any(
        s.pattern == "Bullish Engulfing"
        for s in signals
    )


def test_bearish_engulfing_detection():
    candles = [
        Candle(100, 106, 99, 105, 1000),
        Candle(106, 107, 98, 99, 1500),
    ]

    signals = detect_candlestick_patterns(candles)

    assert any(
        s.pattern == "Bearish Engulfing"
        for s in signals
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
        assert signal.reasoning


def test_detector_does_not_authorize_trades():
    candles = [Candle(100, 102, 98, 100, 1000)]
    signals = detect_candlestick_patterns(candles)

    for signal in signals:
        assert not hasattr(signal, "execute")
        assert not hasattr(signal, "place_order")
