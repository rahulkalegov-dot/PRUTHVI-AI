from pruthvi_ai.safety import (
    trading_mode,
    real_trading_allowed,
    can_execute_paper_order,
    safety_status,
)


def test_paper_only():
    assert trading_mode() == "PAPER_ONLY"


def test_real_trading_disabled():
    assert real_trading_allowed() is False


def test_execution_locked():
    assert can_execute_paper_order(
        risk_approved=True
    ) is False


def test_safety_status():
    status = safety_status()

    assert status["paper_only"] is True
    assert status["live_trading"] is False
    assert status["execution_enabled"] is False