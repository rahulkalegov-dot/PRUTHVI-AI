from pruthvi_ai.learning_agent import (
    review_trade,
    calculate_strategy_performance,
)


def test_winning_trade():
    trade = review_trade("RELIANCE", "BREAKOUT", 500)
    assert trade.result == "WIN"


def test_losing_trade():
    trade = review_trade("TCS", "TREND", -200)
    assert trade.result == "LOSS"


def test_breakeven_trade():
    trade = review_trade("INFY", "VWAP", 0)
    assert trade.result == "BREAKEVEN"


def test_strategy_performance():
    trades = [
        review_trade("RELIANCE", "BREAKOUT", 500),
        review_trade("TCS", "TREND", -200),
        review_trade("INFY", "VWAP", 0),
    ]

    result = calculate_strategy_performance(trades)

    assert result["total_trades"] == 3
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["win_rate"] == 33.33
    assert result["total_pnl"] == 300


def test_empty_performance():
    result = calculate_strategy_performance([])
    assert result["total_trades"] == 0
    assert result["total_pnl"] == 0