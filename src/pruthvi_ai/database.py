
"""Persistent SQLite storage for PRUTHVI AI. PAPER ONLY; no broker execution."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "pruthvi_ai.db"
DATABASE_PATH = Path(
    os.environ.get("PRUTHVI_DB_PATH", str(DEFAULT_DB_PATH))
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class PRUTHVIDatabase:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    score REAL,
                    reasoning TEXT
                );

                CREATE TABLE IF NOT EXISTS risk_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    reason TEXT,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS paper_trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    entry_price REAL NOT NULL CHECK(entry_price > 0),
                    stop_loss REAL NOT NULL,
                    target REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_price REAL,
                    exit_time TEXT,
                    gross_pnl REAL,
                    net_pnl REAL,
                    status TEXT NOT NULL DEFAULT 'OPEN'
                        CHECK(status IN ('OPEN', 'CLOSED'))
                );

                CREATE INDEX IF NOT EXISTS idx_paper_trades_status
                    ON paper_trades(status);

                CREATE INDEX IF NOT EXISTS idx_scans_timestamp
                    ON scans(timestamp);
            """)

        self.log_event(
            "DATABASE_INITIALIZED",
            "SQLite database initialized in PAPER ONLY mode."
        )

    def log_event(self, event_type, message, details=None):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO audit_logs
                   (timestamp, event_type, message, details)
                   VALUES (?, ?, ?, ?)""",
                (
                    utc_now(),
                    str(event_type),
                    str(message),
                    json.dumps(details, default=str)
                    if details is not None else None,
                ),
            )

    # Backward-compatible spelling for earlier callers.
    def log_audit(self, event_type, details=None, message=None):
        self.log_event(
            event_type,
            message or str(event_type),
            details,
        )

    def save_scan(self, symbol, status, reason=""):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO scans
                   (timestamp, symbol, status, reason)
                   VALUES (?, ?, ?, ?)""",
                (utc_now(), str(symbol), str(status), str(reason)),
            )

    def save_decision(self, symbol, action, score=None, reasoning=""):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (timestamp, symbol, action, score, reasoning)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    utc_now(),
                    str(symbol),
                    str(action),
                    score,
                    str(reasoning),
                ),
            )

    def save_risk_check(
        self, symbol, approved, reason="", details=None
    ):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO risk_checks
                   (timestamp, symbol, approved, reason, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    utc_now(),
                    str(symbol),
                    int(bool(approved)),
                    str(reason),
                    json.dumps(details, default=str)
                    if details is not None else None,
                ),
            )

    def record_trade_open(
        self,
        symbol,
        side,
        quantity,
        entry_price,
        stop_loss,
        target,
        entry_time=None,
    ):
        if not symbol or side not in ("BUY", "SELL"):
            raise ValueError("Invalid symbol or side")

        if (
            isinstance(quantity, bool)
            or int(quantity) != quantity
            or quantity <= 0
        ):
            raise ValueError("Quantity must be a positive integer")

        values = (entry_price, stop_loss, target)

        if any(
            not isinstance(v, (int, float))
            or not __import__("math").isfinite(v)
            for v in values
        ):
            raise ValueError("Trade prices must be finite numbers")

        if entry_price <= 0 or stop_loss <= 0 or target <= 0:
            raise ValueError("Trade prices must be positive")

        if side == "BUY" and not stop_loss < entry_price < target:
            raise ValueError("Invalid BUY stop-loss/target")

        if side == "SELL" and not target < entry_price < stop_loss:
            raise ValueError("Invalid SELL stop-loss/target")

        trade_id = str(uuid.uuid4())

        with self.connect() as conn:
            conn.execute(
                """INSERT INTO paper_trades
                   (trade_id, symbol, side, quantity, entry_price,
                    stop_loss, target, entry_time, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')""",
                (
                    trade_id,
                    str(symbol),
                    side,
                    int(quantity),
                    float(entry_price),
                    float(stop_loss),
                    float(target),
                    entry_time or utc_now(),
                ),
            )

        self.log_event(
            "PAPER_TRADE_OPENED",
            f"Virtual trade opened for {symbol}",
            {"trade_id": trade_id},
        )

        return trade_id

    def record_trade_close(
        self, trade_id, exit_price, gross_pnl, net_pnl=None
    ):
        import math

        if not all(
            math.isfinite(float(v))
            for v in (
                exit_price,
                gross_pnl,
                gross_pnl if net_pnl is None else net_pnl,
            )
        ):
            raise ValueError("Exit and P&L values must be finite")

        if float(exit_price) <= 0:
            raise ValueError("Invalid exit price")

        with self.connect() as conn:
            cur = conn.execute(
                """UPDATE paper_trades
                   SET exit_price = ?,
                       exit_time = ?,
                       gross_pnl = ?,
                       net_pnl = ?,
                       status = 'CLOSED'
                   WHERE trade_id = ? AND status = 'OPEN'""",
                (
                    float(exit_price),
                    utc_now(),
                    float(gross_pnl),
                    float(gross_pnl if net_pnl is None else net_pnl),
                    str(trade_id),
                ),
            )

            if cur.rowcount != 1:
                raise ValueError(
                    "Trade not found or already closed"
                )

        self.log_event(
            "PAPER_TRADE_CLOSED",
            "Virtual trade closed",
            {
                "trade_id": trade_id,
                "exit_price": exit_price,
            },
        )

    def get_open_trades(self):
        with self.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    """SELECT * FROM paper_trades
                       WHERE status = 'OPEN'
                       ORDER BY entry_time"""
                ).fetchall()
            ]

    def get_trade_history(self):
        with self.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    """SELECT * FROM paper_trades
                       ORDER BY entry_time"""
                ).fetchall()
            ]

    def get_recent_logs(self, limit=100):
        if isinstance(limit, bool) or int(limit) <= 0:
            raise ValueError("Limit must be a positive integer")

        with self.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    """SELECT * FROM audit_logs
                       ORDER BY id DESC LIMIT ?""",
                    (int(limit),),
                ).fetchall()
            ]

    def health_check(self):
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1").fetchone()

            return {
                "database": "OK",
                "engine": "SQLite",
                "paper_only": True,
            }

        except sqlite3.Error:
            return {
                "database": "ERROR",
                "engine": "SQLite",
                "paper_only": True,
            }

