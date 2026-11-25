from pruthvi_ai.risk_agent import approve_trade


def test_valid_buy_trade():
    approved, result = approve_trade(10000, 100, 98)
    assert approved is True
    assert result["quantity"] == 50
    assert result["side"] == "BUY"


def test_valid_sell_trade():
    approved, result = approve_trade(
        10000, 100, 102, side="SELL"
    )
    assert approved is True
    assert result["quantity"] == 50
    assert result["side"] == "SELL"


def test_invalid_buy_stop_loss():
    approved, _ = approve_trade(10000, 100, 101)
    assert approved is False


def test_invalid_sell_stop_loss():
    approved, _ = approve_trade(
        10000, 100, 98, side="SELL"
    )
    assert approved is False


def test_max_positions():
    approved, _ = approve_trade(
        10000, 100, 98, open_positions=2
    )
    assert approved is False


def test_daily_loss_limit():
    approved, _ = approve_trade(
        10000, 100, 98, daily_loss=300
    )
    assert approved is False


def test_trade_limit():
    approved, _ = approve_trade(
        10000, 100, 98, trades_today=5
    )
    assert approved is False


def test_insufficient_exposure():
    approved, _ = approve_trade(
        100, 100, 98
    )
    assert approved is False