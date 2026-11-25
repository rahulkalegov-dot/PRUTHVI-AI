from pruthvi_ai.paper_trading import PaperTradingEngine


def test_initial_capital():
    engine = PaperTradingEngine(10000)
    assert engine.cash == 10000


def test_open_buy():
    engine = PaperTradingEngine(10000)
    assert engine.open_position("RELIANCE", "BUY", 10, 100, 95, 110)
    assert engine.cash == 9000


def test_close_buy():
    engine = PaperTradingEngine(10000)
    engine.open_position("RELIANCE", "BUY", 10, 100, 95, 110)
    assert engine.close_position("RELIANCE", 110)
    assert engine.get_realized_pnl() == 100
    assert engine.cash == 10100


def test_open_sell():
    engine = PaperTradingEngine(10000)
    assert engine.open_position("TCS", "SELL", 10, 100, 105, 90)
    assert engine.cash == 9000


def test_close_sell_profit():
    engine = PaperTradingEngine(10000)
    engine.open_position("TCS", "SELL", 10, 100, 105, 90)
    assert engine.close_position("TCS", 90)
    assert engine.get_realized_pnl() == 100
    assert engine.cash == 10100


def test_close_sell_loss():
    engine = PaperTradingEngine(10000)
    engine.open_position("TCS", "SELL", 10, 100, 105, 90)
    assert engine.close_position("TCS", 105)
    assert engine.get_realized_pnl() == -50
    assert engine.cash == 9950


def test_duplicate_position_rejected():
    engine = PaperTradingEngine(10000)
    assert engine.open_position("RELIANCE", "BUY", 10, 100, 95, 110)
    assert not engine.open_position("RELIANCE", "BUY", 5, 100, 95, 110)


def test_closed_position_not_counted():
    engine = PaperTradingEngine(10000)
    engine.open_position("RELIANCE", "BUY", 10, 100, 95, 110)
    engine.close_position("RELIANCE", 100)
    assert engine.open_position("TCS", "BUY", 10, 100, 95, 110)


def test_invalid_order():
    engine = PaperTradingEngine(10000)
    assert not engine.open_position("RELIANCE", "BUY", 10, 100, 105, 110)


def test_insufficient_cash():
    engine = PaperTradingEngine(10000)
    assert not engine.open_position("RELIANCE", "BUY", 200, 100, 95, 110)