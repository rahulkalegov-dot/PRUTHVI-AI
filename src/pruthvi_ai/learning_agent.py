from dataclasses import dataclass


@dataclass
class TradeReview:
    symbol: str
    strategy: str
    pnl: float
    result: str


def review_trade(symbol, strategy, pnl):
    if not symbol or not strategy:
        raise ValueError("Symbol and strategy are required")

    if pnl > 0:
        result = "WIN"
    elif pnl < 0:
        result = "LOSS"
    else:
        result = "BREAKEVEN"

    return TradeReview(
        symbol=symbol,
        strategy=strategy,
        pnl=pnl,
        result=result
    )


def calculate_strategy_performance(trades):
    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0
        }

    wins = sum(1 for trade in trades if trade.result == "WIN")
    losses = sum(1 for trade in trades if trade.result == "LOSS")

    return {
        "total_trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(trades) * 100, 2),
        "total_pnl": round(sum(trade.pnl for trade in trades), 2)
    }