
"""PRUTHVI AI persistent database.
Supports local SQLite and Neon PostgreSQL.
PAPER TRADING ONLY. No live broker execution.
"""

import json
import math
import os
import re
import sqlite3
import uuid

from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "pruthvi_ai.db"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = Path(
    os.getenv("PRUTHVI_DB_PATH", str(DEFAULT_DB_PATH))
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_database_url(url):
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def convert_placeholders(sql):
    """Convert SQLite placeholders to PostgreSQL placeholders."""
    return re.sub(r"\?", "%s", sql)


class PostgreSQLConnection:
    """Compatibility wrapper for SQLite-style execute calls."""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, params=None):
        return self.connection.execute(
            convert_placeholders(sql),
            params or (),
        )

    def executescript(self, script):
        # PostgreSQL executes each statement separately.
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                self.connection.execute(statement)

    def close(self):
        self.connection.close()


class PRUTHVIDatabase:

    def __init__(self, db_path=None):
        self.use_postgres = bool(DATABASE_URL) and db_path is None
        self.db_path = Path(db_path) if db_path else DATABASE_PATH

        if not self.use_postgres:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.initialize()

    @contextmanager
    def connect(self):
        """Open a database connection and always close it."""

        if self.use_postgres:
            import psycopg
            from psycopg.rows import dict_row

            raw = psycopg.connect(
                normalize_database_url(DATABASE_URL),
                row_factory=dict_row,
                connect_timeout=10,
            )
            conn = PostgreSQLConnection(raw)

            try:
                yield conn
                raw.commit()
            except Exception:
                raw.rollback()
                raise
            finally:
                raw.close()

        else:
            raw = sqlite3.connect(
                str(self.db_path),
                timeout=30,
            )
            raw.row_factory = sqlite3.Row
            raw.execute("PRAGMA foreign_keys = ON")
            raw.execute("PRAGMA busy_timeout = 30000")

            try:
                yield raw
                raw.commit()
            except Exception:
                raw.rollback()
                raise
            finally:
                raw.close()

    def initialize(self):

        if self.use_postgres:
            statements = [
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    score DOUBLE PRECISION,
                    reasoning TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS risk_checks (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    reason TEXT,
                    details TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS paper_trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL
                        CHECK (side IN ('BUY', 'SELL')),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    entry_price DOUBLE PRECISION NOT NULL,
                    stop_loss DOUBLE PRECISION NOT NULL,
                    target DOUBLE PRECISION NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_price DOUBLE PRECISION,
                    exit_time TEXT,
                    gross_pnl DOUBLE PRECISION,
                    net_pnl DOUBLE PRECISION,
                    status TEXT NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN', 'CLOSED'))
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS daily_report_deliveries (
                    report_date TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    attempted_at TEXT NOT NULL,
                    sent_at TEXT
                )
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_paper_trades_status
                ON paper_trades(status)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_scans_timestamp
                ON scans(timestamp)
                """,
            ]

            with self.connect() as conn:
                for statement in statements:
                    conn.execute(statement)

        else:
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
                        side TEXT NOT NULL
                            CHECK (side IN ('BUY', 'SELL')),
                        quantity INTEGER NOT NULL CHECK (quantity > 0),
                        entry_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        target REAL NOT NULL,
                        entry_time TEXT NOT NULL,
                        exit_price REAL,
                        exit_time TEXT,
                        gross_pnl REAL,
                        net_pnl REAL,
                        status TEXT NOT NULL DEFAULT 'OPEN'
                            CHECK (status IN ('OPEN', 'CLOSED'))
                    );

                    CREATE TABLE IF NOT EXISTS daily_report_deliveries (
                        report_date TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        attempted_at TEXT NOT NULL,
                        sent_at TEXT
                    );

                    CREATE INDEX IF NOT EXISTS idx_paper_trades_status
                    ON paper_trades(status);

                    CREATE INDEX IF NOT EXISTS idx_scans_timestamp
                    ON scans(timestamp);
                """)

        self.log_event(
            "DATABASE_INITIALIZED",
            "Database initialized in paper-only mode.",
            {
                "engine": "PostgreSQL" if self.use_postgres else "SQLite",
                "paper_only": True,
            },
        )

    def log_event(self, event_type, message, details=None):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs
                (timestamp, event_type, message, details)
                VALUES (?, ?, ?, ?)
                """,
                (
                    utc_now(),
                    str(event_type),
                    str(message),
                    json.dumps(details, default=str)
                    if details is not None else None,
                ),
            )

    def log_audit(self, event_type, details=None, message=None):
        self.log_event(
            event_type,
            message or str(event_type),
            details,
        )

    def save_scan(self, symbol, status, reason=""):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO scans
                (timestamp, symbol, status, reason)
                VALUES (?, ?, ?, ?)
                """,
                (utc_now(), str(symbol), str(status), str(reason)),
            )

    def save_decision(self, symbol, action, score=None, reasoning=""):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions
                (timestamp, symbol, action, score, reasoning)
                VALUES (?, ?, ?, ?, ?)
                """,
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
                """
                INSERT INTO risk_checks
                (timestamp, symbol, approved, reason, details)
                VALUES (?, ?, ?, ?, ?)
                """,
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
            raise ValueError("Invalid symbol or trade side")

        if isinstance(quantity, bool) or int(quantity) != quantity:
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        prices = (entry_price, stop_loss, target)

        if not all(
            isinstance(value, (int, float))
            and math.isfinite(value)
            and value > 0
            for value in prices
        ):
            raise ValueError("Trade prices must be positive finite numbers")

        if side == "BUY" and not stop_loss < entry_price < target:
            raise ValueError("Invalid BUY stop-loss or target")

        if side == "SELL" and not target < entry_price < stop_loss:
            raise ValueError("Invalid SELL stop-loss or target")

        trade_id = str(uuid.uuid4())

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO paper_trades (
                    trade_id, symbol, side, quantity,
                    entry_price, stop_loss, target,
                    entry_time, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """,
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
            "Virtual trade opened",
            {"trade_id": trade_id, "symbol": symbol},
        )

        return trade_id

    def record_trade_close(
        self, trade_id, exit_price, gross_pnl, net_pnl=None
    ):
        values = (
            exit_price,
            gross_pnl,
            gross_pnl if net_pnl is None else net_pnl,
        )

        try:
            if not all(math.isfinite(float(v)) for v in values):
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("Exit price and P&L must be finite numbers")

        if float(exit_price) <= 0:
            raise ValueError("Exit price must be positive")

        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE paper_trades
                SET exit_price = ?,
                    exit_time = ?,
                    gross_pnl = ?,
                    net_pnl = ?,
                    status = 'CLOSED'
                WHERE trade_id = ? AND status = 'OPEN'
                """,
                (
                    float(exit_price),
                    utc_now(),
                    float(gross_pnl),
                    float(gross_pnl if net_pnl is None else net_pnl),
                    str(trade_id),
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError("Trade not found or already closed")

        self.log_event(
            "PAPER_TRADE_CLOSED",
            "Virtual trade closed",
            {"trade_id": str(trade_id)},
        )

    def get_open_trades(self):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM paper_trades
                WHERE status = 'OPEN'
                ORDER BY entry_time
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_trade_history(self):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM paper_trades
                ORDER BY entry_time DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_recent_logs(self, limit=100):
        if isinstance(limit, bool) or int(limit) <= 0:
            raise ValueError("Limit must be positive")

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY id DESC LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
            return [dict(row) for row in rows]

    def health_check(self):
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1").fetchone()

            return {
                "database": "OK",
                "engine": (
                    "PostgreSQL" if self.use_postgres else "SQLite"
                ),
                "paper_only": True,
            }

        except Exception as exc:
            return {
                "database": "ERROR",
                "engine": (
                    "PostgreSQL" if self.use_postgres else "SQLite"
                ),
                "error": str(exc),
                "paper_only": True,
            }
