
"""Persistent SQLite database for PRUTHVI AI.
PAPER ONLY. No live order execution.
"""

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
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
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
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL,
                    target REAL,
                    entry_time TEXT NOT NULL,
                    exit_price REAL,
                    exit_time TEXT,
                    gross_pnl REAL,
                    net_pnl REAL,
                    status TEXT NOT NULL DEFAULT 'OPEN'
                );
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

    def save_scan(self, symbol, status, reason=""):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO scans
                (timestamp, symbol, status, reason)
                VALUES (?, ?, ?, ?)""",
                (utc_now(), symbol, status, reason),
            )

    def save_decision(self, symbol, action, score=None, reasoning=""):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO decisions
                (timestamp, symbol, action, score, reasoning)
                VALUES (?, ?, ?, ?, ?)""",
                (utc_now(), symbol, action, score, reasoning),
            )

    def save_risk_check(self, symbol, approved, reason="", details=None):
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO risk_checks
                (timestamp, symbol, approved, reason, details)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    utc_now(),
                    symbol,
                    int(bool(approved)),
                    reason,
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
        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")

        if quantity <= 0 or entry_price <= 0:
            raise ValueError("Invalid quantity or entry price")

        if stop_loss is None or target is None:
            raise ValueError("Stop-loss and target are required")

        trade_id = str(uuid.uuid4())

        with self.connect() as conn:
            conn.execute(
                """INSERT INTO paper_trades
                (trade_id, symbol, side, quantity, entry_price,
                 stop_loss, target, entry_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')""",
                (
                    trade_id,
                    symbol,
                    side,
                    quantity,
                    entry_price,
                    stop_loss,
                    target,
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
        self,
        trade_id,
        exit_price,
        gross_pnl,
        net_pnl=None,
    ):
        if exit_price <= 0:
            raise ValueError("Invalid exit price")

        with self.connect() as conn:
            cursor = conn.execute(
                """UPDATE paper_trades
                SET exit_price = ?,
                    exit_time = ?,
                    gross_pnl = ?,
                    net_pnl = ?,
                    status = 'CLOSED'
                WHERE trade_id = ? AND status = 'OPEN'""",
                (
                    exit_price,
                    utc_now(),
                    gross_pnl,
                    gross_pnl if net_pnl is None else net_pnl,
                    trade_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError("Trade not found or already closed")

        self.log_event(
            "PAPER_TRADE_CLOSED",
            "Virtual trade closed",
            {"trade_id": trade_id, "exit_price": exit_price},
        )

    def get_open_trades(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM paper_trades WHERE status = 'OPEN'"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_trade_history(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM paper_trades ORDER BY entry_time"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent_logs(self, limit=100):
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT * FROM audit_logs
                ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def health_check(self):
        with self.connect() as conn:
            conn.execute("SELECT 1").fetchone()

        return {
            "database": "OK",
            "paper_only": True,
            "path": str(self.db_path),
        }
