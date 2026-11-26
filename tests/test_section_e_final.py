
import json

from pruthvi_ai.database import PRUTHVIDatabase
from pruthvi_ai.paper_trading import PaperTradingEngine
from pruthvi_ai.daily_report_service import (
    generate_sqlite_daily_report,
    format_sqlite_daily_report,
)


def test_strategy_is_saved_and_restored(tmp_path):
    path = tmp_path / "strategy.db"
    db = PRUTHVIDatabase(path)
    engine = PaperTradingEngine(10000, database=db)

    assert engine.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110,
        strategy="BREAKOUT",
    )
    assert engine.close_position("RELIANCE", 110)

    restarted = PaperTradingEngine(
        10000, database=PRUTHVIDatabase(path)
    )
    assert restarted.trade_history[0]["strategy"] == "BREAKOUT"


def test_strategy_performance_appears_in_report(tmp_path):
    path = tmp_path / "strategy-report.db"
    db = PRUTHVIDatabase(path)
    engine = PaperTradingEngine(10000, database=db)

    assert engine.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110,
        strategy="BREAKOUT",
    )
    assert engine.close_position("RELIANCE", 110)

    report = generate_sqlite_daily_report(db_path=path)
    message = format_sqlite_daily_report(report)

    assert "ALL-TIME STRATEGY PERFORMANCE" in message
    assert "BREAKOUT" in message
    assert "Win rate=100.00%" in message


def test_square_off_closes_and_verifies_positions(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "square-off.db")
    engine = PaperTradingEngine(10000, database=db)

    assert engine.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110,
        strategy="BREAKOUT",
    )
    assert engine.open_position(
        "TCS", "BUY", 5, 100, 95, 110,
        strategy="TREND",
    )

    result = engine.square_off_all(
        {"RELIANCE": 105, "TCS": 108}
    )

    assert result["status"] == "VERIFIED"
    assert result["closed_count"] == 2
    assert result["remaining_open_count"] == 0
    assert db.get_open_trades() == []

    logs = db.get_recent_logs()
    audit = [
        item for item in logs
        if item["event_type"] == "SQUARE_OFF_VERIFICATION"
    ]
    assert audit
    details = json.loads(audit[0]["details"])
    assert details["status"] == "VERIFIED"


def test_square_off_missing_price_is_incomplete(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "square-off-incomplete.db")
    engine = PaperTradingEngine(10000, database=db)

    assert engine.open_position(
        "INFY", "BUY", 5, 100, 95, 110,
        strategy="MOMENTUM",
    )

    result = engine.square_off_all({})

    assert result["status"] == "INCOMPLETE"
    assert result["remaining_open_count"] == 1
    assert result["remaining_symbols"] == ["INFY"]
    assert len(db.get_open_trades()) == 1
