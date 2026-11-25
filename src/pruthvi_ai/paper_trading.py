from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PaperPosition:
    symbol: str
    side: str
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    entry_time: datetime
    status: str = "OPEN"


class PaperTradingEngine:

    def __init__(self, capital=10000):
        if capital <= 0:
            raise ValueError("Invalid capital")

        self.initial_capital = capital
        self.cash = capital
        self.positions = []
        self.trade_history = []

    def open_position(
        self, symbol, side, quantity,
        entry, stop_loss, target
    ):
        if not symbol or side not in ("BUY", "SELL"):
            return False

        if quantity <= 0:
            return False

        if min(entry, stop_loss, target) <= 0:
            return False

        if any(
            p.symbol == symbol and p.status == "OPEN"
            for p in self.positions
        ):
            return False

        if len(self.get_open_positions()) >= 2:
            return False

        if side == "BUY":
            if not stop_loss < entry < target:
                return False

            cost = entry * quantity

        else:
            if not target < entry < stop_loss:
                return False

            cost = entry * quantity

        if cost > self.cash:
            return False

        position = PaperPosition(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry,
            stop_loss=stop_loss,
            target=target,
            entry_time=datetime.now(timezone.utc)
        )

        self.cash -= cost
        self.positions.append(position)

        return True

    def get_open_positions(self):
        return [
            p for p in self.positions
            if p.status == "OPEN"
        ]

    def close_position(self, symbol, exit_price):
        if exit_price <= 0:
            return False

        for position in self.positions:
            if position.symbol != symbol:
                continue

            if position.status != "OPEN":
                continue

            if position.side == "BUY":
                pnl = (
                    exit_price - position.entry_price
                ) * position.quantity
            else:
                pnl = (
                    position.entry_price - exit_price
                ) * position.quantity

            self.cash += (
                position.entry_price * position.quantity
                + pnl
            )

            position.status = "CLOSED"

            self.trade_history.append({
                "symbol": symbol,
                "side": position.side,
                "entry": position.entry_price,
                "exit": exit_price,
                "quantity": position.quantity,
                "gross_pnl": pnl
            })

            return True

        return False

    def get_realized_pnl(self):
        return sum(
            trade["gross_pnl"]
            for trade in self.trade_history
        )