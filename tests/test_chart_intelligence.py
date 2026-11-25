import pytest

from pruthvi_ai.chart_intelligence import (
    analyze_double_pattern,
)


def test_w_pattern_confirmation():
    result = analyze_double_pattern(
        100, 110, 101, 112, "W"
    )
    assert result.status == "CONFIRMED"


def test_m_pattern_confirmation():
    result = analyze_double_pattern(
        110, 100, 109, 98, "M"
    )
    assert result.status == "CONFIRMED"


def test_w_false_pattern():
    result = analyze_double_pattern(
        100, 110, 101, 95, "W"
    )
    assert result.status == "FALSE_PATTERN"


def test_invalid_pattern():
    with pytest.raises(ValueError):
        analyze_double_pattern(
            100, 110, 101, 112, "X"
        )