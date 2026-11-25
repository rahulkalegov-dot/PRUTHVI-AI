from datetime import datetime
from zoneinfo import ZoneInfo


def generate_daily_report(
    scanned_stocks,
    decisions,
    trades,
    errors=None
):
    errors = errors or []

    buy = sum(1 for item in decisions if item.action == "BUY")
    sell = sum(1 for item in decisions if item.action == "SELL")
    hold = sum(1 for item in decisions if item.action == "HOLD")
    no_trade = sum(
        1 for item in decisions if item.action == "NO TRADE"
    )

    gross_pnl = sum(
        trade.get("gross_pnl", 0) for trade in trades
    )

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "scanned_stocks": scanned_stocks,
        "buy_decisions": buy,
        "sell_decisions": sell,
        "hold_decisions": hold,
        "no_trade_decisions": no_trade,
        "executed_trades": len(trades),
        "gross_pnl": round(gross_pnl, 2),
        "errors": errors,
        "paper_only": True
    }


def format_daily_report(report):
    return (
        "PRUTHVI AI — DAILY REPORT\n"
        f"Date: {report['date']}\n"
        f"Scanned stocks: {report['scanned_stocks']}\n"
        f"BUY: {report['buy_decisions']}\n"
        f"SELL: {report['sell_decisions']}\n"
        f"HOLD: {report['hold_decisions']}\n"
        f"NO TRADE: {report['no_trade_decisions']}\n"
        f"Executed virtual trades: {report['executed_trades']}\n"
        f"Gross P&L: ₹{report['gross_pnl']}\n"
        f"Errors: {len(report['errors'])}\n"
        "Trading mode: PAPER ONLY"
    )