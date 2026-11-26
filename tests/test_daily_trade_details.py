
from datetime import datetime, timezone

from pruthvi_ai.database import PRUTHVIDatabase
from pruthvi_ai.daily_report_service import (
    generate_sqlite_daily_report,
    format_sqlite_daily_report,
)


def test_closed_trade_details_appear_in_daily_report(tmp_path):
    db_path = tmp_path / "trade-details.db"
    db = PRUTHVIDatabase(db_path)

    entry_time = datetime(
        2026, 11, 26, 10, 0, tzinfo=timezone.utc
    ).isoformat()

    trade_id = db.record_trade_open(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        entry_price=100,
        stop_loss=95,
        target=110,
        entry_time=entry_time,
    )

    db.record_trade_close(
        trade_id=trade_id,
        exit_price=110,
        gross_pnl=100,
        net_pnl=100,
    )

    report = generate_sqlite_daily_report(
        db_path=db_path,
        report_date=datetime(2026, 11, 26).date(),
    )

    message = format_sqlite_daily_report(report)

    assert "RELIANCE" in message
    assert "Quantity: 10" in message
    assert "Entry: 100.00" in message
    assert "Stop-Loss: 95.00" in message
    assert "Target: 110.00" in message
    assert "Exit: 110.00" in message
    assert "Gross P&L: 100.00" in message
    assert "Net P&L: 100.00" in message


def test_open_trade_details_appear_without_fake_unrealized_pnl(
    tmp_path,
):
    db_path = tmp_path / "open-trade-details.db"
    db = PRUTHVIDatabase(db_path)

    entry_time = datetime(
        2026, 11, 26, 10, 0, tzinfo=timezone.utc
    ).isoformat()

    db.record_trade_open(
        symbol="TCS",
        side="BUY",
        quantity=5,
        entry_price=200,
        stop_loss=190,
        target=220,
        entry_time=entry_time,
    )

    report = generate_sqlite_daily_report(
        db_path=db_path,
        report_date=datetime(2026, 11, 26).date(),
    )

    message = format_sqlite_daily_report(report)

    assert "TCS" in message
    assert "Quantity: 5" in message
    assert "Entry: 200.00" in message
    assert "Stop-Loss: 190.00" in message
    assert "Target: 220.00" in message
    assert "Status: OPEN" in message
    assert "Unrealized P&L: Not calculated" in message


def test_sell_trade_details_show_correct_values(tmp_path):
    db_path = tmp_path / "sell-trade-details.db"
    db = PRUTHVIDatabase(db_path)

    entry_time = datetime(
        2026, 11, 26, 10, 0, tzinfo=timezone.utc
    ).isoformat()

    trade_id = db.record_trade_open(
        symbol="INFY",
        side="SELL",
        quantity=4,
        entry_price=500,
        stop_loss=520,
        target=470,
        entry_time=entry_time,
    )

    db.record_trade_close(
        trade_id=trade_id,
        exit_price=470,
        gross_pnl=120,
        net_pnl=120,
    )

    report = generate_sqlite_daily_report(
        db_path=db_path,
        report_date=datetime(2026, 11, 26).date(),
    )

    message = format_sqlite_daily_report(report)

    assert "INFY" in message
    assert "SELL" in message
    assert "Entry: 500.00" in message
    assert "Stop-Loss: 520.00" in message
    assert "Target: 470.00" in message
    assert "Exit: 470.00" in message
    assert "Net P&L: 120.00" in message
