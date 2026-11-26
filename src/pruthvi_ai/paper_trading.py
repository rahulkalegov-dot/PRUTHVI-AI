
"""Persistent virtual trade simulator. No broker or live-order interface."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
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
    strategy: str = "UNASSIGNED"


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

    def _strategy_map(self):
        strategies = {}
        for log in self.database.get_recent_logs(limit=10000):
            if log["event_type"] != "PAPER_TRADE_STRATEGY_SET":
                continue
            try:
                details = json.loads(log["details"] or "{}")
                strategies[details["trade_id"]] = details["strategy"]
            except (ValueError, TypeError, KeyError):
                continue
        return strategies

    def _restore_from_database(self):
        history = self.database.get_trade_history()
        strategies = self._strategy_map()
        realized_pnl = 0.0
        invested_amount = 0.0

        for trade in history:
            strategy = strategies.get(
                trade["trade_id"], "UNASSIGNED"
            )

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
                    strategy,
                )
                self.positions.append(pos)
                self.trade_ids[pos.symbol] = trade["trade_id"]
                invested_amount += pos.entry_price * pos.quantity
            else:
                pnl = float(trade["gross_pnl"] or 0)
                realized_pnl += pnl
                self.trade_history.append({
                    "trade_id": trade["trade_id"],
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "strategy": strategy,
                    "entry": trade["entry_price"],
                    "exit": trade["exit_price"],
                    "quantity": trade["quantity"],
                    "gross_pnl": pnl,
                    "net_pnl": float(trade["net_pnl"] or pnl),
                    "entry_time": trade["entry_time"],
                    "exit_time": trade["exit_time"],
                })

        self.cash = (
            self.initial_capital + realized_pnl - invested_amount
        )

    def get_open_positions(self):
        return [
            p for p in self.positions if p.status == "OPEN"
        ]

    def _risk_gate(self, symbol, side, quantity, entry, stop_loss):
        open_positions = len(self.get_open_positions())
        history = self.database.get_trade_history()
        trades_count = len(history)

        realized = sum(
            float(t.get("net_pnl") or 0)
            for t in history if t["status"] == "CLOSED"
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
        return bool(approved and int(quantity) <= int(result["quantity"]))

    def open_position(
        self, symbol, side, quantity, entry, stop_loss, target,
        strategy="UNASSIGNED",
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
                float(entry), float(stop_loss), float(target)
            ]
            if not all(isfinite(v) and v > 0 for v in values):
                return False
            entry, stop_loss, target = values

            if not isinstance(strategy, str) or not strategy.strip():
                return False
            strategy = strategy.strip().upper()

        except (TypeError, ValueError, OverflowError):
            return False

        if any(
            p.symbol == symbol for p in self.get_open_positions()
        ):
            return False
        if len(self.get_open_positions()) >= 2:
            return False
        if side == "BUY" and not stop_loss < entry < target:
            return False
        if side == "SELL" and not target < entry < stop_loss:
            return False
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
            symbol, side, quantity, entry, stop_loss, target
        )

        # Persist strategy attribution against the permanent trade ID.
        self.database.log_event(
            "PAPER_TRADE_STRATEGY_SET",
            f"Strategy assigned to paper trade {trade_id}",
            {"trade_id": trade_id, "strategy": strategy},
        )

        position = PaperPosition(
            symbol,
            side,
            quantity,
            entry,
            stop_loss,
            target,
            datetime.now(timezone.utc),
            "OPEN",
            strategy,
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
                position.entry_price * position.quantity + pnl
            )
            position.status = "CLOSED"

            self.trade_history.append({
                "trade_id": trade_id,
                "symbol": symbol,
                "side": position.side,
                "strategy": position.strategy,
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

    def square_off_all(self, exit_prices, reason="END_OF_DAY"):
        """Close paper positions using supplied prices and audit verification.

        No price is fetched here. Missing/invalid prices leave a position
        open and make the verification INCOMPLETE.
        """
        if not isinstance(exit_prices, dict):
            raise ValueError("exit_prices must be a symbol-to-price dictionary")

        positions = list(self.get_open_positions())
        closed_symbols = []
        skipped_symbols = []

        for position in positions:
            price = exit_prices.get(position.symbol)
            try:
                valid_price = (
                    price is not None
                    and isfinite(float(price))
                    and float(price) > 0
                )
            except (TypeError, ValueError, OverflowError):
                valid_price = False

            if not valid_price:
                skipped_symbols.append(position.symbol)
                self.database.log_event(
                    "SQUARE_OFF_POSITION_SKIPPED",
                    f"No valid exit price for {position.symbol}",
                    {
                        "symbol": position.symbol,
                        "reason": "MISSING_OR_INVALID_EXIT_PRICE",
                        "paper_only": True,
                    },
                )
                continue

            if self.close_position(position.symbol, float(price)):
                closed_symbols.append(position.symbol)
            else:
                skipped_symbols.append(position.symbol)
                self.database.log_event(
                    "SQUARE_OFF_POSITION_ERROR",
                    f"Could not close paper position {position.symbol}",
                    {"symbol": position.symbol, "paper_only": True},
                )

        remaining = [
            p.symbol for p in self.get_open_positions()
        ]
        status = "VERIFIED" if not remaining else "INCOMPLETE"

        details = {
            "status": status,
            "reason": str(reason),
            "expected_positions": len(positions),
            "closed_count": len(closed_symbols),
            "closed_symbols": closed_symbols,
            "skipped_symbols": skipped_symbols,
            "remaining_open_count": len(remaining),
            "remaining_symbols": remaining,
            "paper_only": True,
            "live_trading_enabled": False,
            "automatic_execution_enabled": False,
        }

        self.database.log_event(
            "SQUARE_OFF_VERIFICATION",
            f"Paper square-off verification: {status}",
            details,
        )
        return details

    def get_realized_pnl(self):
        return sum(
            float(t["gross_pnl"]) for t in self.trade_history
        )
