
"""SQLite-backed daily reporting for PRUTHVI AI. PAPER ONLY."""
from datetime import datetime, time, timedelta, timezone
import json
from zoneinfo import ZoneInfo

from .database import PRUTHVIDatabase

IST = ZoneInfo("Asia/Kolkata")


def _day_bounds(report_date=None):
    day = report_date or datetime.now(IST).date()
    start = datetime.combine(day, time.min, tzinfo=IST)
    end = start + timedelta(days=1)
    return (
        start.astimezone(timezone.utc).isoformat(),
        end.astimezone(timezone.utc).isoformat(),
    )


def _strategy_performance(conn):
    strategy_by_trade = {}
    rows = conn.execute(
        """SELECT details FROM audit_logs
           WHERE event_type = 'PAPER_TRADE_STRATEGY_SET'
           ORDER BY id"""
    ).fetchall()

    for row in rows:
        try:
            details = json.loads(row["details"] or "{}")
            strategy_by_trade[details["trade_id"]] = (
                details.get("strategy") or "UNASSIGNED"
            )
        except (ValueError, TypeError, KeyError):
            continue

    closed = conn.execute(
        """SELECT trade_id, gross_pnl, net_pnl
           FROM paper_trades WHERE status = 'CLOSED'"""
    ).fetchall()

    groups = {}
    for trade in closed:
        strategy = strategy_by_trade.get(
            trade["trade_id"], "UNASSIGNED"
        )
        group = groups.setdefault(strategy, {
            "strategy": strategy,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "breakeven": 0,
            "gross_pnl": 0.0,
            "net_pnl": 0.0,
        })

        gross = float(trade["gross_pnl"] or 0)
        net = float(trade["net_pnl"] or 0)
        group["total_trades"] += 1
        group["gross_pnl"] += gross
        group["net_pnl"] += net

        if net > 0:
            group["wins"] += 1
        elif net < 0:
            group["losses"] += 1
        else:
            group["breakeven"] += 1

    results = []
    for group in groups.values():
        count = group["total_trades"]
        group["win_rate"] = round(
            group["wins"] / count * 100, 2
        ) if count else 0.0
        group["gross_pnl"] = round(group["gross_pnl"], 2)
        group["net_pnl"] = round(group["net_pnl"], 2)
        results.append(group)

    return sorted(
        results, key=lambda item: item["strategy"]
    )


def generate_sqlite_daily_report(db_path=None, report_date=None):
    db = PRUTHVIDatabase(db_path)
    selected_date = report_date or datetime.now(IST).date()
    start_utc, end_utc = _day_bounds(selected_date)

    report = {
        "date": selected_date.isoformat(),
        "mode": "PAPER ONLY",
        "scans": [],
        "decisions": [],
        "risk_checks": [],
        "trades": [],
        "open_trades": [],
        "errors": [],
        "health": db.health_check(),
        "strategy_performance": [],
        "square_off_verification": None,
    }

    with db.connect() as conn:
        report["scans"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, status, reason, timestamp
                   FROM scans WHERE timestamp >= ? AND timestamp < ?
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

        report["decisions"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, action, score, reasoning, timestamp
                   FROM decisions WHERE timestamp >= ? AND timestamp < ?
                   ORDER BY timestamp""",
                (start_utc, end_utc),
            ).fetchall()
        ]

        report["risk_checks"] = [
            dict(row) for row in conn.execute(
                """SELECT symbol, approved, reason, details, timestamp
                   FROM risk_checks WHERE timestamp >= ? AND timestamp < ?
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
                   WHERE status = 'OPEN' ORDER BY entry_time"""
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

        report["strategy_performance"] = _strategy_performance(conn)

        square_off_row = conn.execute(
            """SELECT timestamp, details FROM audit_logs
               WHERE event_type = 'SQUARE_OFF_VERIFICATION'
                 AND timestamp >= ? AND timestamp < ?
               ORDER BY id DESC LIMIT 1""",
            (start_utc, end_utc),
        ).fetchone()

        if square_off_row:
            try:
                report["square_off_verification"] = {
                    "timestamp": square_off_row["timestamp"],
                    **json.loads(square_off_row["details"] or "{}"),
                }
            except (ValueError, TypeError):
                report["square_off_verification"] = {
                    "status": "AUDIT_DETAILS_INVALID",
                    "timestamp": square_off_row["timestamp"],
                }

    closed_today = [
        t for t in report["trades"] if t["status"] == "CLOSED"
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
        "closed_trades": len(closed_today),
        "open_trades": len(report["open_trades"]),
        "gross_pnl": sum(
            float(t["gross_pnl"] or 0) for t in closed_today
        ),
        "net_pnl": sum(
            float(t["net_pnl"] or 0) for t in closed_today
        ),
        "errors_count": len(report["errors"]),
    }
    return report


def _format_trade_details(trade):
    lines = [
        f"{trade['symbol']} | {trade['side']} | "
        f"Quantity: {trade['quantity']}",
        f"Entry: {float(trade['entry_price']):.2f}",
        f"Stop-Loss: {float(trade['stop_loss']):.2f}",
        f"Target: {float(trade['target']):.2f}",
        f"Status: {trade['status']}",
    ]

    if trade["status"] == "CLOSED":
        lines.extend([
            f"Exit: {float(trade['exit_price']):.2f}",
            f"Gross P&L: {float(trade['gross_pnl'] or 0):.2f}",
            f"Net P&L: {float(trade['net_pnl'] or 0):.2f}",
            f"Exit time: {trade['exit_time']}",
        ])
    else:
        lines.append(
            "Unrealized P&L: Not calculated "
            "(verified current market price unavailable)."
        )
    return "\n".join(lines)


def format_sqlite_daily_report(report):
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
        "PAPER TRADE SUMMARY",
        f"Closed trades today: {summary['closed_trades']}",
        f"Open trades: {summary['open_trades']}",
        f"Gross P&L today: {summary['gross_pnl']:.2f}",
        f"Net P&L today: {summary['net_pnl']:.2f}",
        "",
        "TODAY'S TRADE DETAILS",
    ]

    if report["trades"]:
        for trade in report["trades"]:
            lines.extend(["", _format_trade_details(trade), "--------------------"])
    else:
        lines.append("No trades recorded for this date.")

    lines.extend(["", "ALL CURRENT OPEN POSITIONS"])
    if report["open_trades"]:
        for trade in report["open_trades"]:
            lines.extend(["", _format_trade_details(trade), "--------------------"])
    else:
        lines.append("No open paper positions.")

    lines.extend(["", "ALL-TIME STRATEGY PERFORMANCE"])
    if report["strategy_performance"]:
        for item in report["strategy_performance"]:
            lines.append(
                f"{item['strategy']}: Trades={item['total_trades']}, "
                f"Wins={item['wins']}, Losses={item['losses']}, "
                f"Breakeven={item['breakeven']}, "
                f"Win rate={item['win_rate']:.2f}%, "
                f"Gross P&L={item['gross_pnl']:.2f}, "
                f"Net P&L={item['net_pnl']:.2f}"
            )
    else:
        lines.append("No closed trades available for strategy analysis.")

    lines.extend(["", "SQUARE-OFF VERIFICATION"])
    verification = report["square_off_verification"]
    if verification:
        lines.extend([
            f"Status: {verification.get('status', 'UNKNOWN')}",
            f"Expected positions: {verification.get('expected_positions', 0)}",
            f"Closed: {verification.get('closed_count', 0)}",
            f"Remaining open: {verification.get('remaining_open_count', 0)}",
            f"Remaining symbols: {verification.get('remaining_symbols', [])}",
            f"Skipped symbols: {verification.get('skipped_symbols', [])}",
            f"Reason: {verification.get('reason', '-')}",
        ])
    else:
        lines.append("NOT RUN — no square-off verification record for this date.")

    lines.extend([
        "",
        "SYSTEM HEALTH",
        f"Database: {report['health']['database']}",
        f"Errors: {summary['errors_count']}",
        "",
        "RECENT DECISIONS",
    ])

    for item in report["decisions"][:15]:
        lines.append(
            f"{item['symbol']}: {item['action']} (score: {item['score']})"
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
