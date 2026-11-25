from pruthvi_ai.report_agent import (
    generate_daily_report,
    format_daily_report,
)


def test_generate_report():
    report = generate_daily_report(
        50, [], [], []
    )

    assert report["scanned_stocks"] == 50
    assert report["executed_trades"] == 0
    assert report["paper_only"] is True


def test_report_with_decisions():
    class Decision:
        def __init__(self, action):
            self.action = action

    decisions = [
        Decision("BUY"),
        Decision("SELL"),
        Decision("HOLD"),
        Decision("NO TRADE"),
    ]

    report = generate_daily_report(
        4, decisions, [], []
    )

    assert report["buy_decisions"] == 1
    assert report["sell_decisions"] == 1
    assert report["hold_decisions"] == 1
    assert report["no_trade_decisions"] == 1


def test_report_pnl():
    trades = [
        {"gross_pnl": 500},
        {"gross_pnl": -200},
    ]

    report = generate_daily_report(2, [], trades)

    assert report["gross_pnl"] == 300


def test_format_report():
    report = generate_daily_report(50, [], [], [])
    text = format_daily_report(report)

    assert "PRUTHVI AI" in text
    assert "PAPER ONLY" in text