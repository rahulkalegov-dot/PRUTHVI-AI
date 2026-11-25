
"""PRUTHVI AI - Candlestick Pattern Detection Engine.

Preliminary pattern detection only.
Signals never authorize or execute trades.
"""

from dataclasses import dataclass
from math import isfinite
from typing import List, Sequence


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self):
        values = (self.open, self.high, self.low, self.close, self.volume)

        if not all(isfinite(v) for v in values):
            raise ValueError("Candle values must be finite")

        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

        if self.high < max(self.open, self.close):
            raise ValueError("Invalid candle high")

        if self.low > min(self.open, self.close):
            raise ValueError("Invalid candle low")


@dataclass(frozen=True)
class PatternSignal:
    pattern: str
    direction: str
    confidence: float
    candle_index: int
    reasoning: str


def candle_metrics(candle: Candle):
    body = abs(candle.close - candle.open)
    candle_range = candle.high - candle.low

    return {
        "body": body,
        "range": candle_range,
        "upper_shadow": candle.high - max(candle.open, candle.close),
        "lower_shadow": min(candle.open, candle.close) - candle.low,
    }


def _signal(name, direction, confidence, index, reason):
    return PatternSignal(name, direction, confidence, index, reason)


def detect_candlestick_patterns(
    candles: Sequence[Candle],
) -> List[PatternSignal]:
    """Detect selected single-, two- and three-candle patterns."""

    if not candles:
        return []

    if not all(isinstance(c, Candle) for c in candles):
        raise TypeError("All inputs must be Candle objects")

    signals = []

    for i, candle in enumerate(candles):
        m = candle_metrics(candle)
        body = m["body"]
        rng = m["range"]
        upper = m["upper_shadow"]
        lower = m["lower_shadow"]

        if rng <= 0:
            continue

        bullish = candle.close > candle.open
        bearish = candle.close < candle.open

        # Single-candle patterns
        if body <= rng * 0.10:
            signals.append(_signal(
                "Doji", "neutral", 0.70, i,
                "Open and close are very close"
            ))

        if body > 0 and lower >= body * 2 and upper <= rng * 0.15:
            signals.append(_signal(
                "Hammer", "bullish", 0.65, i,
                "Long lower shadow and small upper shadow"
            ))

        if body > 0 and upper >= body * 2 and lower <= rng * 0.15:
            if bullish:
                signals.append(_signal(
                    "Inverted Hammer", "bullish", 0.60, i,
                    "Bullish candle with a long upper shadow"
                ))
            elif bearish:
                signals.append(_signal(
                    "Shooting Star", "bearish", 0.60, i,
                    "Bearish candle with a long upper shadow"
                ))

        if body >= rng * 0.90:
            if bullish:
                signals.append(_signal(
                    "Marubozu", "bullish", 0.75, i,
                    "Large bullish body with small shadows"
                ))
            elif bearish:
                signals.append(_signal(
                    "Marubozu", "bearish", 0.75, i,
                    "Large bearish body with small shadows"
                ))

        if i == 0:
            continue

        previous = candles[i - 1]
        pm = candle_metrics(previous)

        previous_bullish = previous.close > previous.open
        previous_bearish = previous.close < previous.open

        # Two-candle patterns
        if (
            previous_bearish and bullish
            and candle.open <= previous.close
            and candle.close >= previous.open
        ):
            signals.append(_signal(
                "Bullish Engulfing", "bullish", 0.75, i,
                "Bullish body engulfs previous bearish body"
            ))

        if (
            previous_bullish and bearish
            and candle.open >= previous.close
            and candle.close <= previous.open
        ):
            signals.append(_signal(
                "Bearish Engulfing", "bearish", 0.75, i,
                "Bearish body engulfs previous bullish body"
            ))

        # Piercing Line
        previous_midpoint = (previous.open + previous.close) / 2
        if (
            previous_bearish and bullish
            and candle.open < previous.low
            and candle.close > previous_midpoint
            and candle.close < previous.open
        ):
            signals.append(_signal(
                "Piercing Line", "bullish", 0.70, i,
                "Bullish close penetrates the previous bearish body"
            ))

        # Dark Cloud Cover
        if (
            previous_bullish and bearish
            and candle.open > previous.high
            and candle.close < previous_midpoint
            and candle.close > previous.open
        ):
            signals.append(_signal(
                "Dark Cloud Cover", "bearish", 0.70, i,
                "Bearish close penetrates the previous bullish body"
            ))

        # Tweezer patterns: similar highs or lows
        scale = max(previous.high, previous.low, candle.high, candle.low)
        tolerance = scale * 0.001

        if (
            previous_bullish and bearish
            and abs(previous.high - candle.high) <= tolerance
        ):
            signals.append(_signal(
                "Tweezer Top", "bearish", 0.65, i,
                "Two candles have nearly equal highs"
            ))

        if (
            previous_bearish and bullish
            and abs(previous.low - candle.low) <= tolerance
        ):
            signals.append(_signal(
                "Tweezer Bottom", "bullish", 0.65, i,
                "Two candles have nearly equal lows"
            ))

        # Three-candle patterns
        if i < 2:
            continue

        first, middle = candles[i - 2], candles[i - 1]
        first_body = abs(first.close - first.open)
        middle_body = abs(middle.close - middle.open)
        last_body = body

        first_midpoint = (first.open + first.close) / 2

        # Morning Star
        if (
            first.close < first.open
            and middle_body <= first_body * 0.40
            and bullish
            and candle.close > first_midpoint
        ):
            signals.append(_signal(
                "Morning Star", "bullish", 0.70, i,
                "Bearish candle, small middle candle and bullish recovery"
            ))

        # Evening Star
        if (
            first.close > first.open
            and middle_body <= first_body * 0.40
            and bearish
            and candle.close < first_midpoint
        ):
            signals.append(_signal(
                "Evening Star", "bearish", 0.70, i,
                "Bullish candle, small middle candle and bearish reversal"
            ))

        # Three White Soldiers
        if (
            first.close > first.open
            and middle.close > middle.open
            and bullish
            and first.close < middle.close < candle.close
            and first.open < middle.open < candle.open
        ):
            signals.append(_signal(
                "Three White Soldiers", "bullish", 0.75, i,
                "Three consecutive rising bullish candles"
            ))

        # Three Black Crows
        if (
            first.close < first.open
            and middle.close < middle.open
            and bearish
            and first.close > middle.close > candle.close
            and first.open > middle.open > candle.open
        ):
            signals.append(_signal(
                "Three Black Crows", "bearish", 0.75, i,
                "Three consecutive declining bearish candles"
            ))

    return signals
