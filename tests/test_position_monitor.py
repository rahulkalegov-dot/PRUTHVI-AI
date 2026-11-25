from datetime import time

from pruthvi_ai.position_monitor import (
    monitor_position,
    should_stop_new_entries,
)


def test_buy_stop_loss():
    assert monitor_position(
        "BUY", 100, 94, 95, 110
    ) == "STOP_LOSS"


def test_buy_target():
    assert monitor_position(
        "BUY", 100, 111, 95, 110
    ) == "TARGET"


def test_buy_hold():
    assert monitor_position(
        "BUY", 100, 105, 95, 110
    ) == "HOLD"


def test_square_off():
    assert monitor_position(
        "BUY", 100, 105, 95, 110,
        time(15, 16)
    ) == "SQUARE_OFF"


def test_stale_data_stops_entries():
    assert should_stop_new_entries(
        0, 300, False
    ) is True


def test_daily_loss_stops_entries():
    assert should_stop_new_entries(
        300, 300, True
    ) is True