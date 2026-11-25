from pruthvi_ai.paper_trading import PaperTradingEngine


def test_initial_capital():
    engine = PaperTradingEngine(10000)
    assert engine.cash == 10000


def test_open_buy():
    engine = PaperTradingEngine(10000)

    result = engine.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110
    )

    assert result is True
    assert engine.cash == 9000


def test_close_buy():
    engine = PaperTradingEngine(10000)

    engine.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110
    )

    result = engine.close_position("RELIANCE", 110)

    assert result is True
    assert engine.get_realized_pnl() == 100


def test_invalid_order():
    engine = PaperTradingEngine(10000)

    result = engine.open_position(
        "RELIANCE", "BUY", 10, 100, 105, 110
    )

    assert result is False


def test_insufficient_cash():
    engine = PaperTradingEngine(10000)

    result = engine.open_position(
        "RELIANCE", "BUY", 200, 100, 95, 110
    )

    assert result is False