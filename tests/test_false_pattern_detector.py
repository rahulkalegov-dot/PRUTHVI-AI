import pytest
from pruthvi_ai.false_pattern_detector import check_breakout


def test_valid_upward_breakout():
    result = check_breakout("UP", 110, 105, 2000, 1000)
    assert result.status == "POTENTIAL"


def test_valid_downward_breakout():
    result = check_breakout("DOWN", 90, 95, 2000, 1000)
    assert result.status == "POTENTIAL"


def test_false_upward_breakout():
    result = check_breakout("UP", 100, 105, 2000, 1000)
    assert result.status == "FALSE"


def test_weak_volume():
    result = check_breakout("UP", 110, 105, 500, 1000)
    assert result.status == "WEAK"


def test_invalid_direction():
    result = check_breakout("SIDEWAYS", 110, 105, 2000, 1000)
    assert result.status == "REJECTED"


def test_negative_volume():
    result = check_breakout("UP", 110, 105, -1, 1000)
    assert result.status == "REJECTED"