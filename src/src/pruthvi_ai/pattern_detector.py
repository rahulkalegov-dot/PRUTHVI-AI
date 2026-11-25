
"""PRUTHVI AI - Pattern Detection Engine.

Initial candlestick detection module.
Detection is informational only and never authorizes a trade.
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
        values = (
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        )

        if not all(isfinite(value) for value in values):
            raise ValueError("Candle values must be finite")

        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

        if self.high < max(self.open, self.close):
            raise ValueError("High cannot be below open or close")

        if self.low > min(self.open, self.close):
            raise ValueError("Low cannot be above open or close")

        if self.high < self.low:
            raise ValueError("High cannot be below low")


@dataclass(frozen=True)
class PatternSignal:
    pattern: str
    direction: str
    confidence: float
    candle_index: int
    reasoning: str


def candle_metrics(candle: Candle):
    """Calculate candle body, shadows and total range."""

    body = abs(candle.close - candle.open)
    candle_range = candle.high - candle.low

    upper_shadow = (
        candle.high - max(candle.open, candle.close)
    )

    lower_shadow = (
        min(candle.open, candle.close) - candle.low
    )

    return {
        "body": body,
        "range": candle_range,
        "upper_shadow": upper_shadow,
        "lower_shadow": lower_shadow,
    }


def detect_candlestick_patterns(
    candles: Sequence[Candle],
) -> List[PatternSignal]:
    """Detect initial single- and two-candle patterns.

    These are preliminary detections, not validated trading signals.
    """

    if not candles:
        return []

    if not all(isinstance(c, Candle) for c in candles):
        raise TypeError("All inputs must be Candle objects")

    signals = []

    for index, candle in enumerate(candles):
        metrics = candle_metrics(candle)

        body = metrics["body"]
        candle_range = metrics["range"]
        upper = metrics["upper_shadow"]
        lower = metrics["lower_shadow"]

        if candle_range <= 0:
            continue

        bullish = candle.close > candle.open
        bearish = candle.close < candle.open

        # Doji
        if body <= candle_range * 0.10:
            signals.append(PatternSignal(
                "Doji", "neutral", 0.70, index,
                "Open and close are very close"
            ))

        # Hammer
        if (
            lower >= body * 2
            and upper <= candle_range * 0.15
            and body > 0
        ):
            signals.append(PatternSignal(
                "Hammer", "bullish", 0.65, index,
                "Long lower shadow and small upper shadow"
            ))

        # Inverted Hammer
        if (
            upper >= body * 2
            and lower <= candle_range * 0.15
            and body > 0
        ):
            signals.append(PatternSignal(
                "Inverted Hammer", "bullish", 0.60, index,
                "Long upper shadow and small lower shadow"
            ))

        # Shooting Star
        if (
            upper >= body * 2
            and lower <= candle_range * 0.15
            and body > 0
        ):
            signals.append(PatternSignal(
                "Shooting Star", "bearish", 0.60, index,
                "Long upper shadow; trend context still required"
            ))

        # Marubozu
        if body >= candle_range * 0.90:
            if bullish:
                signals.append(PatternSignal(
                    "Marubozu", "bullish", 0.75, index,
                    "Large bullish body with small shadows"
                ))
            elif bearish:
                signals.append(PatternSignal(
                    "Marubozu", "bearish", 0.75, index,
                    "Large bearish body with small shadows"
                ))

        # Two-candle patterns
        if index == 0:
            continue

        previous = candles[index - 1]

        previous_bullish = previous.close > previous.open
        previous_bearish = previous.close < previous.open

        # Bullish Engulfing
        if (
            previous_bearish
            and bullish
            and candle.open <= previous.close
            and candle.close >= previous.open
        ):
            signals.append(PatternSignal(
                "Bullish Engulfing", "bullish", 0.75, index,
                "Current bullish body engulfs previous bearish body"
            ))

        # Bearish Engulfing
        if (
            previous_bullish
            and bearish
            and candle.open >= previous.close
            and candle.close <= previous.open
        ):
            signals.append(PatternSignal(
                "Bearish Engulfing", "bearish", 0.75, index,
                "Current bearish body engulfs previous bullish body"
            ))

    return signals
