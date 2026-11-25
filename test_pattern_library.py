
import pytest

from pruthvi_ai.pattern_library import (
    PATTERN_LIBRARY,
    PatternDefinition,
    get_pattern_library,
)


def test_pattern_library_is_not_empty():
    assert len(PATTERN_LIBRARY) > 0


def test_all_entries_are_pattern_definitions():
    assert all(
        isinstance(pattern, PatternDefinition)
        for pattern in PATTERN_LIBRARY
    )


def test_pattern_names_are_unique():
    names = [pattern.name for pattern in PATTERN_LIBRARY]
    assert len(names) == len(set(names))


def test_all_patterns_have_valid_categories():
    valid_categories = {
        "reversal",
        "continuation",
        "wedge",
        "channel",
        "candlestick",
        "chart",
        "price_action",
    }

    for pattern in PATTERN_LIBRARY:
        assert pattern.category in valid_categories


def test_all_patterns_have_valid_directions():
    valid_directions = {
        "bullish",
        "bearish",
        "neutral",
    }

    for pattern in PATTERN_LIBRARY:
        assert pattern.direction in valid_directions


def test_required_patterns_are_registered():
    names = {
        pattern.name
        for pattern in PATTERN_LIBRARY
    }

    required = {
        "Double Top",
        "Double Bottom",
        "Head and Shoulders",
        "Inverse Head and Shoulders",
        "Bull Flag",
        "Bear Flag",
        "Rising Wedge",
        "Falling Wedge",
        "Bullish Engulfing",
        "Bearish Engulfing",
        "Breakout",
        "Breakdown",
        "Fair Value Gap",
        "Liquidity Sweep",
    }

    assert required.issubset(names)


def test_get_pattern_library_returns_registry():
    assert get_pattern_library() is PATTERN_LIBRARY


def test_pattern_definitions_are_immutable():
    pattern = PATTERN_LIBRARY[0]

    with pytest.raises(AttributeError):
        pattern.name = "Changed"
