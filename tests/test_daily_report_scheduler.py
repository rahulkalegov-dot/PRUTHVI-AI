
from datetime import datetime
from zoneinfo import ZoneInfo

from pruthvi_ai.database import PRUTHVIDatabase
from pruthvi_ai.daily_report_scheduler import DailyReportScheduler


IST = ZoneInfo("Asia/Kolkata")
DUE_TIME = datetime(2026, 11, 26, 15, 36, tzinfo=IST)


def get_scheduler_errors(db_path):
    db = PRUTHVIDatabase(db_path)

    with db.connect() as conn:
        rows = conn.execute("""
            SELECT event_type, message, details
            FROM audit_logs
            WHERE event_type = 'DAILY_REPORT_SCHEDULER_ERROR'
            ORDER BY id
        """).fetchall()

    return [dict(row) for row in rows]


def test_report_generation_failure_is_audited(tmp_path):
    db_path = tmp_path / "scheduler.db"

    def failing_provider():
        raise RuntimeError("Report database unavailable")

    scheduler = DailyReportScheduler(
        report_provider=failing_provider,
        sender=lambda message: (True, "sent"),
        db_path=db_path,
    )

    assert scheduler.run_once(DUE_TIME) is False

    errors = get_scheduler_errors(db_path)

    assert len(errors) == 1
    assert errors[0]["event_type"] == "DAILY_REPORT_SCHEDULER_ERROR"
    assert "report_generation" in errors[0]["message"]
    assert "Report database unavailable" in errors[0]["message"]
    assert '"failure_stage": "report_generation"' in errors[0]["details"]
    assert '"exception_type": "RuntimeError"' in errors[0]["details"]


def test_telegram_failure_is_audited(tmp_path):
    db_path = tmp_path / "telegram-failure.db"

    scheduler = DailyReportScheduler(
        report_provider=lambda: "Test daily report",
        sender=lambda message: (False, "Telegram API rejected message"),
        db_path=db_path,
    )

    assert scheduler.run_once(DUE_TIME) is False

    errors = get_scheduler_errors(db_path)

    assert len(errors) == 1
    assert "telegram_send" in errors[0]["message"]
    assert "Telegram API rejected message" in errors[0]["message"]
    assert '"exception_type": "TelegramSendError"' in errors[0]["details"]


def test_empty_report_is_audited(tmp_path):
    db_path = tmp_path / "empty-report.db"

    scheduler = DailyReportScheduler(
        report_provider=lambda: " ",
        sender=lambda message: (True, "sent"),
        db_path=db_path,
    )

    assert scheduler.run_once(DUE_TIME) is False

    errors = get_scheduler_errors(db_path)

    assert len(errors) == 1
    assert "report_generation" in errors[0]["message"]
    assert "Daily report is empty" in errors[0]["message"]


def test_success_does_not_create_failure_audit(tmp_path):
    db_path = tmp_path / "success.db"

    scheduler = DailyReportScheduler(
        report_provider=lambda: "Test daily report",
        sender=lambda message: (True, "Message sent"),
        db_path=db_path,
    )

    assert scheduler.run_once(DUE_TIME) is True
    assert get_scheduler_errors(db_path) == []


def test_scheduler_error_appears_in_daily_report_errors(tmp_path):
    from pruthvi_ai.daily_report_service import generate_sqlite_daily_report

    db_path = tmp_path / "daily-errors.db"

    scheduler = DailyReportScheduler(
        report_provider=lambda: (_ for _ in ()).throw(
            RuntimeError("Test scheduler failure")
        ),
        sender=lambda message: (True, "sent"),
        db_path=db_path,
    )

    assert scheduler.run_once(DUE_TIME) is False

    report = generate_sqlite_daily_report(
        db_path=db_path,
        report_date=DUE_TIME.date(),
    )

    assert report["summary"]["errors_count"] >= 1
    assert any(
        item["event_type"] == "DAILY_REPORT_SCHEDULER_ERROR"
        for item in report["errors"]
    )
