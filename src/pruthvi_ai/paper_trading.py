
"""Persistent virtual trade simulator. It has no broker or live-order interface."""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .database import PRUTHVIDatabase
from .risk_agent import approve_trade

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
        if (
            not isinstance(capital, (int, float))
            or not isfinite(float(capital))
            or capital <= 0
        ):
            raise ValueError("Invalid capital")

        self.initial_capital = float(capital)
        self.cash = float(capital)
        self.positions = []
        self.trade_history = []
        self.database = database or PRUTHVIDatabase()
        self.trade_ids = {}

        self._restore_from_database()

    def _restore_from_database(self):
        history = self.database.get_trade_history()
        realized_pnl = 0.0
        invested_amount = 0.0

        for trade in history:
            if trade["status"] == "OPEN":
                entry_time = datetime.fromisoformat(
                    trade["entry_time"]
                )

                pos = PaperPosition(
                    trade["symbol"],
                    trade["side"],
                    int(trade["quantity"]),
                    float(trade["entry_price"]),
                    float(trade["stop_loss"]),
                    float(trade["target"]),
                    entry_time,
                    "OPEN",
                )

                self.positions.append(pos)
                self.trade_ids[pos.symbol] = trade["trade_id"]
                invested_amount += pos.entry_price * pos.quantity

            else:
                pnl = float(trade["gross_pnl"] or 0)
                realized_pnl += pnl

                self.trade_history.append({
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "entry": trade["entry_price"],
                    "exit": trade["exit_price"],
                    "quantity": trade["quantity"],
                    "gross_pnl": pnl,
                    "net_pnl": float(trade["net_pnl"] or pnl),
                    "entry_time": trade["entry_time"],
                    "exit_time": trade["exit_time"],
                })

        self.cash = (
            self.initial_capital
            + realized_pnl
            - invested_amount
        )

    def get_open_positions(self):
        return [
            p for p in self.positions
            if p.status == "OPEN"
        ]

    def _risk_gate(self, symbol, side, quantity, entry, stop_loss):
        open_positions = len(self.get_open_positions())
        history = self.database.get_trade_history()

        # Conservative until reliable session accounting is implemented.
        trades_count = len(history)

        realized = sum(
            float(t.get("net_pnl") or 0)
            for t in history
            if t["status"] == "CLOSED"
        )

        daily_loss = max(0.0, -realized)

        approved, result = approve_trade(
            capital=self.initial_capital,
            entry=float(entry),
            stop_loss=float(stop_loss),
            open_positions=open_positions,
            trades_today=trades_count,
            daily_loss=daily_loss,
            side=side,
            database=self.database,
            symbol=symbol,
        )

        if not approved:
            return False

        return int(quantity) <= int(result["quantity"])

    def open_position(
        self, symbol, side, quantity, entry, stop_loss, target
    ):
        try:
            if not isinstance(symbol, str) or not symbol.strip():
                return False

            symbol = symbol.strip().upper()

            if side not in ("BUY", "SELL"):
                return False

            if (
                isinstance(quantity, bool)
                or int(quantity) != quantity
                or quantity <= 0
            ):
                return False

            quantity = int(quantity)

            values = [
                float(entry),
                float(stop_loss),
                float(target),
            ]

            if not all(isfinite(v) and v > 0 for v in values):
                return False

            entry, stop_loss, target = values

        except (TypeError, ValueError, OverflowError):
            return False

        if any(
            p.symbol == symbol
            for p in self.get_open_positions()
        ):
            return False

        if len(self.get_open_positions()) >= 2:
            return False

        if side == "BUY" and not stop_loss < entry < target:
            return False

        if side == "SELL" and not target < entry < stop_loss:
            return False

        # Mandatory Risk Agent approval occurs inside the engine.
        if not self._risk_gate(
            symbol, side, quantity, entry, stop_loss
        ):
            return False

        reserved = entry * quantity

        if reserved > self.cash:
            self.database.save_risk_check(
                symbol, False, "Insufficient available paper cash"
            )
            return False

        trade_id = self.database.record_trade_open(
            symbol,
            side,
            quantity,
            entry,
            stop_loss,
            target,
        )

        position = PaperPosition(
            symbol,
            side,
            quantity,
            entry,
            stop_loss,
            target,
            datetime.now(timezone.utc),
        )

        self.cash -= reserved
        self.positions.append(position)
        self.trade_ids[symbol] = trade_id

        return True

    def close_position(self, symbol, exit_price):
        try:
            exit_price = float(exit_price)

            if not isfinite(exit_price) or exit_price <= 0:
                return False

        except (TypeError, ValueError):
            return False

        for position in self.positions:
            if (
                position.symbol != symbol
                or position.status != "OPEN"
            ):
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

            self.database.record_trade_close(
                trade_id, exit_price, pnl, pnl
            )

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
                "gross_pnl": pnl,
                "net_pnl": pnl,
                "entry_time": position.entry_time.isoformat(),
                "exit_time": datetime.now(timezone.utc).isoformat(),
            })

            self.trade_ids.pop(symbol, None)

            return True

        return False

    def get_realized_pnl(self):
        return sum(
            float(t["gross_pnl"])
            for t in self.trade_history
        )
