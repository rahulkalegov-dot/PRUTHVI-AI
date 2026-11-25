
import pytest

from pruthvi_ai.pattern_detector import (
    Candle,
    PatternSignal,
    candle_metrics,
    detect_candlestick_patterns,
)


def detect(candles, name):
    signals = detect_candlestick_patterns(candles)
    return [s for s in signals if s.pattern == name]


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
    result = candle_metrics(Candle(100, 105, 98, 103, 1000))
    assert result["body"] == 3
    assert result["range"] == 7
    assert result["upper_shadow"] == 2
    assert result["lower_shadow"] == 2


def test_empty_input():
    assert detect_candlestick_patterns([]) == []


def test_invalid_input_type():
    with pytest.raises(TypeError):
        detect_candlestick_patterns([100, 101])


def test_doji():
    assert detect([Candle(100, 102, 98, 100)], "Doji")


def test_hammer():
    assert detect([Candle(100, 101.2, 97.8, 101)], "Hammer")


def test_inverted_hammer():
    signals = detect([Candle(100, 105, 99.9, 101)], "Inverted Hammer")
    assert signals
    assert signals[0].direction == "bullish"


def test_shooting_star():
    signals = detect([Candle(101, 105, 99.9, 100)], "Shooting Star")
    assert signals
    assert signals[0].direction == "bearish"


def test_bullish_engulfing():
    candles = [
        Candle(105, 106, 99, 100),
        Candle(99, 107, 98, 106),
    ]
    assert detect(candles, "Bullish Engulfing")


def test_bearish_engulfing():
    candles = [
        Candle(100, 106, 99, 105),
        Candle(106, 107, 98, 99),
    ]
    assert detect(candles, "Bearish Engulfing")


def test_piercing_line():
    candles = [
        Candle(100, 101, 94, 95),
        Candle(93, 99, 92, 98),
    ]
    assert detect(candles, "Piercing Line")


def test_dark_cloud_cover():
    candles = [
        Candle(95, 101, 94, 100),
        Candle(102, 103, 96, 97),
    ]
    assert detect(candles, "Dark Cloud Cover")


def test_morning_star():
    candles = [
        Candle(110, 111, 99, 100),
        Candle(100, 102, 99, 101),
        Candle(101, 109, 100, 108),
    ]
    assert detect(candles, "Morning Star")


def test_evening_star():
    candles = [
        Candle(100, 111, 99, 110),
        Candle(110, 111, 108, 109),
        Candle(109, 110, 100, 102),
    ]
    assert detect(candles, "Evening Star")


def test_three_white_soldiers():
    candles = [
        Candle(100, 106, 99, 105),
        Candle(103, 109, 102, 108),
        Candle(106, 112, 105, 111),
    ]
    assert detect(candles, "Three White Soldiers")


def test_three_black_crows():
    candles = [
        Candle(110, 111, 104, 105),
        Candle(108, 109, 101, 102),
        Candle(105, 106, 98, 99),
    ]
    assert detect(candles, "Three Black Crows")


def test_tweezer_top():
    candles = [
        Candle(100, 110, 99, 108),
        Candle(108, 110.05, 102, 104),
    ]
    assert detect(candles, "Tweezer Top")


def test_tweezer_bottom():
    candles = [
        Candle(108, 109, 100, 102),
        Candle(102, 106, 100.05, 105),
    ]
    assert detect(candles, "Tweezer Bottom")


def test_signal_structure():
    signals = detect_candlestick_patterns([
        Candle(100, 102, 98, 100)
    ])

    for signal in signals:
        assert isinstance(signal, PatternSignal)
        assert 0 <= signal.confidence <= 1
        assert signal.direction in {"bullish", "bearish", "neutral"}
        assert signal.reasoning


def test_detector_does_not_authorize_trades():
    signals = detect_candlestick_patterns([
        Candle(100, 102, 98, 100)
    ])

    for signal in signals:
        assert not hasattr(signal, "execute")
        assert not hasattr(signal, "place_order")
