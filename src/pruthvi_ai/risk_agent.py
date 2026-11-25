from dataclasses import dataclass


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
    daily_loss=0
):
    limits = RiskLimits()

    if min(capital, entry, stop_loss) <= 0:
        return False, "Invalid price or capital"

    if stop_loss >= entry:
        return False, "Invalid BUY stop-loss"

    if open_positions >= limits.max_positions:
        return False, "Maximum positions reached"

    if trades_today >= limits.max_trades_per_day:
        return False, "Daily trade limit reached"

    if daily_loss >= capital * limits.max_daily_loss:
        return False, "Daily loss limit reached"

    risk_amount = capital * limits.max_risk_per_trade

    quantity = int(risk_amount / (entry - stop_loss))

    if quantity < 1:
        return False, "Insufficient capital for minimum position"

    return True, {
        "quantity": quantity,
        "risk_amount": risk_amount,
        "maximum_loss_per_share": entry - stop_loss
    }