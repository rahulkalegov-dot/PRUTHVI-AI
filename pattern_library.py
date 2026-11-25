
"""PRUTHVI AI - Comprehensive Pattern Library.

This file registers patterns for future detector implementation.
Registration does not mean a pattern is validated or tradable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PatternDefinition:
    name: str
    category: str
    direction: str


PATTERN_LIBRARY = (
    # Reversal chart patterns
    PatternDefinition("Double Top", "reversal", "bearish"),
    PatternDefinition("Double Bottom", "reversal", "bullish"),
    PatternDefinition("Head and Shoulders", "reversal", "bearish"),
    PatternDefinition("Inverse Head and Shoulders", "reversal", "bullish"),
    PatternDefinition("Triple Top", "reversal", "bearish"),
    PatternDefinition("Triple Bottom", "reversal", "bullish"),
    PatternDefinition("Rounding Top", "reversal", "bearish"),
    PatternDefinition("Rounding Bottom", "reversal", "bullish"),
    PatternDefinition("Diamond Top", "reversal", "bearish"),
    PatternDefinition("Diamond Bottom", "reversal", "bullish"),

    # Continuation patterns
    PatternDefinition("Bull Flag", "continuation", "bullish"),
    PatternDefinition("Bear Flag", "continuation", "bearish"),
    PatternDefinition("Bullish Pennant", "continuation", "bullish"),
    PatternDefinition("Bearish Pennant", "continuation", "bearish"),
    PatternDefinition("Ascending Triangle", "continuation", "bullish"),
    PatternDefinition("Descending Triangle", "continuation", "bearish"),
    PatternDefinition("Symmetrical Triangle", "continuation", "neutral"),
    PatternDefinition("Rectangle", "continuation", "neutral"),
    PatternDefinition("Rising Three Methods", "continuation", "bullish"),
    PatternDefinition("Falling Three Methods", "continuation", "bearish"),

    # Wedges and channels
    PatternDefinition("Rising Wedge", "wedge", "bearish"),
    PatternDefinition("Falling Wedge", "wedge", "bullish"),
    PatternDefinition("Ascending Channel", "channel", "bullish"),
    PatternDefinition("Descending Channel", "channel", "bearish"),
    PatternDefinition("Horizontal Channel", "channel", "neutral"),
    PatternDefinition("Broadening Formation", "chart", "neutral"),
    PatternDefinition("Broadening Top", "chart", "bearish"),
    PatternDefinition("Broadening Bottom", "chart", "bullish"),

    # Candlestick patterns
    *(
        PatternDefinition(name, "candlestick", direction)
        for name, direction in (
            ("Doji", "neutral"),
            ("Dragonfly Doji", "bullish"),
            ("Gravestone Doji", "bearish"),
            ("Hammer", "bullish"),
            ("Inverted Hammer", "bullish"),
            ("Hanging Man", "bearish"),
            ("Shooting Star", "bearish"),
            ("Bullish Engulfing", "bullish"),
            ("Bearish Engulfing", "bearish"),
            ("Piercing Line", "bullish"),
            ("Dark Cloud Cover", "bearish"),
            ("Morning Star", "bullish"),
            ("Evening Star", "bearish"),
            ("Three White Soldiers", "bullish"),
            ("Three Black Crows", "bearish"),
            ("Tweezer Top", "bearish"),
            ("Tweezer Bottom", "bullish"),
            ("Harami", "neutral"),
            ("Harami Cross", "neutral"),
            ("Marubozu", "neutral"),
            ("Spinning Top", "neutral"),
            ("Three Inside Up", "bullish"),
            ("Three Inside Down", "bearish"),
            ("Three Outside Up", "bullish"),
            ("Three Outside Down", "bearish"),
            ("Kicking Pattern", "neutral"),
            ("Abandoned Baby", "neutral"),
        )
    ),

    # Price-action structures
    *(
        PatternDefinition(name, "price_action", "neutral")
        for name in (
            "Breakout",
            "Breakdown",
            "Retest",
            "Pullback",
            "Throwback",
            "Fakeout",
            "Liquidity Sweep",
            "Stop Hunt",
            "Support Rejection",
            "Resistance Rejection",
            "Change of Character",
            "Break of Structure",
            "Higher High",
            "Higher Low",
            "Lower High",
            "Lower Low",
            "Order Block",
            "Fair Value Gap",
            "Liquidity Grab",
        )
    ),
)


def get_pattern_library():
    """Return all registered pattern definitions."""
    return PATTERN_LIBRARY
