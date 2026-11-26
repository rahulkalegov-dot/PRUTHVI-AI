
"""Risk gate for virtual trades. Approval is mandatory before paper entry."""
from dataclasses import dataclass
from math import isfinite


@dataclass
class RiskLimits:
    max_risk_per_trade: float = 0.01
    max_daily_loss: float = 0.03
    max_positions: int = 2
    max_trades_per_day: int = 5


def approve_trade(
    capital,
    entry,
    stop_loss,
    open_positions=0,
    trades_today=0,
    daily_loss=0,
    side="BUY",
    database=None,
    symbol="UNKNOWN",
    limits=None,
):
    limits = limits or RiskLimits()

    def reject(reason):
        if database is not None:
            database.save_risk_check(symbol, False, reason)
        return False, reason

    try:
        values = [
            float(capital),
            float(entry),
            float(stop_loss),
            float(daily_loss),
        ]

        if not all(isfinite(v) for v in values):
            return reject("Invalid numeric data")

        capital, entry, stop_loss, daily_loss = values

        if isinstance(open_positions, bool) or int(open_positions) != open_positions:
            return reject("Invalid open-position count")

        if isinstance(trades_today, bool) or int(trades_today) != trades_today:
            return reject("Invalid daily trade count")

        open_positions = int(open_positions)
        trades_today = int(trades_today)

    except (TypeError, ValueError, OverflowError):
        return reject("Invalid risk inputs")

    if capital <= 0 or entry <= 0 or stop_loss <= 0:
        return reject("Invalid price or capital")

    if open_positions < 0 or trades_today < 0 or daily_loss < 0:
        return reject("Invalid risk inputs")

    if side not in ("BUY", "SELL"):
        return reject("Invalid trade side")

    if side == "BUY" and stop_loss >= entry:
        return reject("Invalid BUY stop-loss")

    if side == "SELL" and stop_loss <= entry:
        return reject("Invalid SELL stop-loss")

    if open_positions >= limits.max_positions:
        return reject("Maximum positions reached")

    if trades_today >= limits.max_trades_per_day:
        return reject("Daily trade limit reached")

    if daily_loss >= capital * limits.max_daily_loss:
        return reject("Daily loss limit reached")

    risk_per_share = abs(entry - stop_loss)
    risk_amount = capital * limits.max_risk_per_trade
    quantity = int(risk_amount // risk_per_share)

    if quantity < 1:
        return reject("Insufficient capital for minimum position")

    if quantity * entry > capital:
        return reject("Insufficient capital for position exposure")

    result = {
        "side": side,
        "quantity": quantity,
        "risk_amount": risk_amount,
        "maximum_loss_per_share": risk_per_share,
        "maximum_trade_loss": quantity * risk_per_share,
    }

    if database is not None:
        database.save_risk_check(
            symbol, True, "Risk checks passed", result
        )

    return True, result
