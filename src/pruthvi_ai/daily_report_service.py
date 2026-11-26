
"""SQLite-backed daily reporting for PRUTHVI AI.

Reports are informational only. This module never places broker orders.
"""
import sqlite3
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .database import PRUTHVIDatabase


IST = ZoneInfo("Asia/Kolkata")


def _day_bounds(report_date=None):
    """Return the selected IST day as UTC ISO timestamp boundaries."""
    day = report_date or datetime.now(IST).date()
    start_ist = datetime.combine(day, time.min, tzinfo=IST)
    end_ist = start_ist + timedelta(days=1)

    return start_ist.astimezone(timezone.utc).isoformat(), (
        end_ist.astimezone(timezone.utc).isoformat()
    )


def generate_sqlite_daily_report(db_path=None, report_date=None):
    """Generate a daily report from persisted SQLite records."""
    db = PRUTHVIDatabase(db_path)
    start_utc, end_utc = _day_bounds(report_date)

    report = {
        "date": (report_date or datetime.now(IST).date()).isoformat(),
        "mode": "PAPER ONLY",
        "scans": [],
        "decisions": [],
        "risk_checks": [],
        "trades": [],
        "open_trades": [],
        "errors": [],
        "health": db.health_check(),
        "strategy_performance": (
            "Unavailable: strategy attribution is not stored yet."
        ),
        "square_off_verification": (
            "Unavailable: explicit square-off verification is not stored yet."
        ),
    }

    with db.connect() as conn:
        report["scans"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, status, reason, timestamp
                   FROM scans
                   WHERE timestamp >= ? AND timestamp < ?
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

        report["decisions"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, action, score, reasoning, timestamp
                   FROM decisions
                   WHERE timestamp >= ? AND timestamp < ?
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

        report["risk_checks"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, approved, reason, details, timestamp
                   FROM risk_checks
                   WHERE timestamp >= ? AND timestamp < ?
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

        report["trades"] = [
            dict(row) for row in conn.execute(
                """SELECT * FROM paper_trades
                   WHERE (entry_time >= ? AND entry_time < ?)
                      OR (exit_time >= ? AND exit_time < ?)
                   ORDER BY entry_time""",
                (start_utc, end_utc, start_utc, end_utc),
            ).fetchall()
        ]

        report["open_trades"] = [
            dict(row) for row in conn.execute(
                """SELECT * FROM paper_trades
                   WHERE status = 'OPEN'
                   ORDER BY entry_time"""
            ).fetchall()
        ]

        report["errors"] = [
            dict(row) for row in conn.execute(
                """SELECT timestamp, event_type, message, details
                   FROM audit_logs
                   WHERE timestamp >= ? AND timestamp < ?
                     AND (
                         UPPER(event_type) LIKE '%ERROR%'
                         OR UPPER(event_type) LIKE '%FAIL%'
                         OR UPPER(message) LIKE '%ERROR%'
                         OR UPPER(message) LIKE '%FAIL%'
                     )
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

    closed = [
        trade for trade in report["trades"]
        if trade["status"] == "CLOSED"
    ]

    report["summary"] = {
        "scans_count": len(report["scans"]),
        "unique_symbols_scanned": len({
            item["symbol"] for item in report["scans"]
        }),
        "decisions_count": len(report["decisions"]),
        "risk_checks_count": len(report["risk_checks"]),
        "risk_rejections": sum(
            1 for item in report["risk_checks"]
            if not item["approved"]
        ),
        "closed_trades": len(closed),
        "open_trades": len(report["open_trades"]),
        "gross_pnl": sum(
            float(item["gross_pnl"] or 0) for item in closed
        ),
        "net_pnl": sum(
            float(item["net_pnl"] or 0) for item in closed
        ),
        "errors_count": len(report["errors"]),
    }

    return report


def format_sqlite_daily_report(report):
    """Format the report for Telegram."""
    summary = report["summary"]
    lines = [
        f"PRUTHVI AI DAILY REPORT — {report['date']}",
        f"Mode: {report['mode']}",
        "",
        "SCAN SUMMARY",
        f"Scans: {summary['scans_count']}",
        f"Unique symbols: {summary['unique_symbols_scanned']}",
        "",
        "DECISIONS & RISK",
        f"Decisions: {summary['decisions_count']}",
        f"Risk checks: {summary['risk_checks_count']}",
        f"Risk rejections: {summary['risk_rejections']}",
        "",
        "PAPER TRADES",
        f"Closed trades: {summary['closed_trades']}",
        f"Open trades: {summary['open_trades']}",
        f"Gross P&L: {summary['gross_pnl']:.2f}",
        f"Net P&L: {summary['net_pnl']:.2f}",
        "",
        "SYSTEM HEALTH",
        f"Database: {report['health']['database']}",
        f"Errors: {summary['errors_count']}",
        "",
        "STRATEGY PERFORMANCE",
        report["strategy_performance"],
        "",
        "SQUARE-OFF",
        report["square_off_verification"],
        "",
        "RECENT DECISIONS",
    ]

    for item in report["decisions"][:15]:
        lines.append(
            f"{item['symbol']}: {item['action']} "
            f"(score: {item['score']})"
        )

    if not report["decisions"]:
        lines.append("No decisions recorded for this date.")

    lines.extend(["", "RECENT SCAN RESULTS"])

    for item in report["scans"][:15]:
        lines.append(
            f"{item['symbol']}: {item['status']} — {item['reason'] or '-'}"
        )

    if not report["scans"]:
        lines.append("No scans recorded for this date.")

    return "\n".join(lines)
