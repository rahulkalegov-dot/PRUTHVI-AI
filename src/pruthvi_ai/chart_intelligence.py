"""
PRUTHVI AI - Chart Intelligence Agent
Detects W/M patterns and false breakouts.
"""

from dataclasses import dataclass


@dataclass
class PatternResult:
    pattern: str
    status: str
    confidence: float
    reasoning: str


def analyze_double_pattern(
    first_extreme,
    neckline,
    second_extreme,
    current_price,
    pattern="W",
    tolerance=0.02
):
    values = [
        first_extreme,
        neckline,
        second_extreme,
        current_price,
        tolerance
    ]

    if any(value <= 0 for value in values):
        raise ValueError("Prices and tolerance must be positive")

    if tolerance >= 1:
        raise ValueError("Tolerance must be below 1")

    if pattern not in ("W", "M"):
        raise ValueError("Pattern must be W or M")

    similarity = abs(
        first_extreme - second_extreme
    ) / max(first_extreme, second_extreme)

    if similarity > tolerance:
        return PatternResult(
            pattern, "INVALID", 0.0,
            "The two extremes are not sufficiently similar"
        )

    if pattern == "W":

        if neckline <= max(first_extreme, second_extreme):
            return PatternResult(
                pattern, "INVALID", 0.0,
                "Invalid W neckline"
            )

        if current_price < min(first_extreme, second_extreme):
            return PatternResult(
                pattern, "FALSE_PATTERN", 0.0,
                "Price broke below both W lows"
            )

        if current_price > neckline:
            return PatternResult(
                pattern, "CONFIRMED", 1.0,
                "Price crossed above W neckline"
            )

    if pattern == "M":

        if neckline >= min(first_extreme, second_extreme):
            return PatternResult(
                pattern, "INVALID", 0.0,
                "Invalid M neckline"
            )

        if current_price > max(first_extreme, second_extreme):
            return PatternResult(
                pattern, "FALSE_PATTERN", 0.0,
                "Price broke above both M highs"
            )

        if current_price < neckline:
            return PatternResult(
                pattern, "CONFIRMED", 1.0,
                "Price crossed below M neckline"
            )

    return PatternResult(
        pattern, "FORMING", 0.0,
        "Pattern has not confirmed its neckline breakout"
    )