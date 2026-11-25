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
    side="BUY"
):
    limits = RiskLimits()

    values = [capital, entry, stop_loss, daily_loss]

    if not all(isfinite(x) for x in values):
        return False, "Invalid numeric data"

    if min(capital, entry, stop_loss) <= 0:
        return False, "Invalid price or capital"

    if open_positions < 0 or trades_today < 0 or daily_loss < 0:
        return False, "Invalid risk inputs"

    if side not in ("BUY", "SELL"):
        return False, "Invalid trade side"

    if side == "BUY" and stop_loss >= entry:
        return False, "Invalid BUY stop-loss"

    if side == "SELL" and stop_loss <= entry:
        return False, "Invalid SELL stop-loss"

    if open_positions >= limits.max_positions:
        return False, "Maximum positions reached"

    if trades_today >= limits.max_trades_per_day:
        return False, "Daily trade limit reached"

    if daily_loss >= capital * limits.max_daily_loss:
        return False, "Daily loss limit reached"

    risk_per_share = abs(entry - stop_loss)
    risk_amount = capital * limits.max_risk_per_trade

    quantity = int(risk_amount / risk_per_share)

    if quantity < 1:
        return False, "Insufficient capital for minimum position"

    if quantity * entry > capital:
        return False, "Insufficient capital for position exposure"

    return True, {
        "side": side,
        "quantity": quantity,
        "risk_amount": risk_amount,
        "maximum_loss_per_share": risk_per_share
    }