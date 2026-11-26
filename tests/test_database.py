
from pruthvi_ai.database import PRUTHVIDatabase
from pruthvi_ai.paper_trading import PaperTradingEngine


def test_database_health(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "test.db")
    assert db.health_check()["database"] == "OK"
    assert db.health_check()["paper_only"] is True


def test_audit_logging(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "test.db")
    db.log_event("TEST", "Test event")

    logs = db.get_recent_logs()
    assert any(log["event_type"] == "TEST" for log in logs)


def test_scan_storage(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "test.db")
    db.save_scan("RELIANCE", "READY", "Test scan")

    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE symbol = ?",
            ("RELIANCE",)
        ).fetchone()

    assert row is not None
    assert row["status"] == "READY"


def test_decision_storage(tmp_path):
    db = PRUTHVIDatabase(tmp_path / "test.db")
    db.save_decision("TCS", "NO TRADE", 0.5, "Test")

    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE symbol = ?",
            ("TCS",)
        ).fetchone()

    assert row["action"] == "NO TRADE"


def test_trade_survives_restart(tmp_path):
    path = tmp_path / "persistent.db"

    db1 = PRUTHVIDatabase(path)
    engine1 = PaperTradingEngine(10000, database=db1)

    assert engine1.open_position(
        "RELIANCE", "BUY", 10, 100, 95, 110
    )

    # Simulate restarting the engine.
    db2 = PRUTHVIDatabase(path)
    engine2 = PaperTradingEngine(10000, database=db2)

    positions = engine2.get_open_positions()

    assert len(positions) == 1
    assert positions[0].symbol == "RELIANCE"
    assert engine2.cash == 9000

    assert engine2.close_position("RELIANCE", 110)
    assert engine2.get_realized_pnl() == 100


def test_trade_history_survives_restart(tmp_path):
    path = tmp_path / "history.db"

    db = PRUTHVIDatabase(path)
    engine = PaperTradingEngine(10000, database=db)

    engine.open_position("TCS", "BUY", 10, 100, 95, 110)
    engine.close_position("TCS", 110)

    restarted = PaperTradingEngine(
        10000,
        database=PRUTHVIDatabase(path)
    )

    assert restarted.get_realized_pnl() == 100
    assert len(restarted.trade_history) == 1
