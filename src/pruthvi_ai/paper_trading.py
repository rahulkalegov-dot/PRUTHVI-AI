
from dataclasses import dataclass
from datetime import datetime, timezone

from .database import PRUTHVIDatabase


PAPER_ONLY = True
LIVE_TRADING_ENABLED = False
AUTO_EXECUTION_ENABLED = False
RELEASE_APPROVED = False


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

    def __init__(self, capital=10000, database=None):
        if capital <= 0:
            raise ValueError("Invalid capital")

        self.initial_capital = capital
        self.cash = capital
        self.positions = []
        self.trade_history = []
        self.database = database or PRUTHVIDatabase()
        self.trade_ids = {}

        self._restore_from_database()

    def _restore_from_database(self):
        """Restore persisted positions and trade history."""

        history = self.database.get_trade_history()
        open_trades = []

        realized_pnl = 0.0
        invested_amount = 0.0

        for trade in history:
            if trade["status"] == "OPEN":
                open_trades.append(trade)
            else:
                realized_pnl += float(trade["gross_pnl"] or 0)

                self.trade_history.append({
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "entry": trade["entry_price"],
                    "exit": trade["exit_price"],
                    "quantity": trade["quantity"],
                    "gross_pnl": trade["gross_pnl"],
                    "net_pnl": trade["net_pnl"],
                })

        for trade in open_trades:
            position = PaperPosition(
                symbol=trade["symbol"],
                side=trade["side"],
                quantity=trade["quantity"],
                entry_price=trade["entry_price"],
                stop_loss=trade["stop_loss"],
                target=trade["target"],
                entry_time=datetime.fromisoformat(
                    trade["entry_time"]
                ),
                status="OPEN",
            )

            self.positions.append(position)
            self.trade_ids[position.symbol] = trade["trade_id"]

            invested_amount += (
                position.entry_price * position.quantity
            )

        self.cash = (
            self.initial_capital
            + realized_pnl
            - invested_amount
        )

    def open_position(
        self,
        symbol,
        side,
        quantity,
        entry,
        stop_loss,
        target,
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
        else:
            if not target < entry < stop_loss:
                return False

        cost = entry * quantity

        if cost > self.cash:
            return False

        # Save to persistent storage before changing engine state.
        trade_id = self.database.record_trade_open(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry,
            stop_loss=stop_loss,
            target=target,
        )

        position = PaperPosition(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry,
            stop_loss=stop_loss,
            target=target,
            entry_time=datetime.now(timezone.utc),
        )

        self.cash -= cost
        self.positions.append(position)
        self.trade_ids[symbol] = trade_id

        return True

    def get_open_positions(self):
        return [
            position
            for position in self.positions
            if position.status == "OPEN"
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

            trade_id = self.trade_ids.get(symbol)

            if not trade_id:
                return False

            # Persist the exit before updating engine state.
            self.database.record_trade_close(
                trade_id=trade_id,
                exit_price=exit_price,
                gross_pnl=pnl,
                net_pnl=pnl,
            )

            self.cash += (
                position.entry_price * position.quantity + pnl
            )

            position.status = "CLOSED"

            self.trade_history.append({
                "symbol": symbol,
                "side": position.side,
                "entry": position.entry_price,
                "exit": exit_price,
                "quantity": position.quantity,
                "gross_pnl": pnl,
                "net_pnl": pnl,
            })

            self.trade_ids.pop(symbol, None)

            return True

        return False

    def get_realized_pnl(self):
        return sum(
            trade["gross_pnl"]
            for trade in self.trade_history
        )
