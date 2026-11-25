from pruthvi_ai.risk_agent import approve_trade


def test_valid_trade():
    approved, result = approve_trade(
        capital=10000,
        entry=100,
        stop_loss=98
    )

    assert approved is True
    assert result["quantity"] == 50


def test_invalid_stop_loss():
    approved, result = approve_trade(
        capital=10000,
        entry=100,
        stop_loss=101
    )

    assert approved is False


def test_max_positions():
    approved, result = approve_trade(
        capital=10000,
        entry=100,
        stop_loss=98,
        open_positions=2
    )

    assert approved is False


def test_daily_loss_limit():
    approved, result = approve_trade(
        capital=10000,
        entry=100,
        stop_loss=98,
        daily_loss=300
    )

    assert approved is False


def test_trade_limit():
    approved, result = approve_trade(
        capital=10000,
        entry=100,
        stop_loss=98,
        trades_today=5
    )

    assert approved is False