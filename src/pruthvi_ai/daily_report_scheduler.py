
"""Persistent daily Telegram report scheduler with SQLite failure auditing.

PAPER ONLY. No broker orders or trade execution.
Weekdays at 15:35 Asia/Kolkata.
"""

import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .daily_report_service import (
    generate_sqlite_daily_report,
    format_sqlite_daily_report,
)
from .telegram_reporter import send_telegram_report
from .database import PRUTHVIDatabase


IST = ZoneInfo("Asia/Kolkata")
REPORT_HOUR = 15
REPORT_MINUTE = 35

logger = logging.getLogger(__name__)


class DailyReportScheduler:
    def __init__(
        self,
        report_provider=None,
        sender=None,
        db_path=None,
        poll_interval=20,
    ):
        self.report_provider = report_provider or self._generate_report
        self.sender = sender or send_telegram_report
        self.db_path = db_path
        self.poll_interval = max(1, int(poll_interval))

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

        self._initialize_delivery_table()

    def _database(self):
        return PRUTHVIDatabase(self.db_path)

    def _initialize_delivery_table(self):
        db = self._database()

        with db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_report_deliveries (
                    report_date TEXT PRIMARY KEY,
                    status TEXT NOT NULL
                        CHECK(status IN ('SENDING', 'SENT')),
                    attempted_at TEXT NOT NULL,
                    sent_at TEXT
                )
            """)

    def _generate_report(self):
        report = generate_sqlite_daily_report(db_path=self.db_path)
        return format_sqlite_daily_report(report)

    def _claim_report_date(self, report_date):
        """Atomically claim the date to prevent duplicate reports."""
        db = self._database()
        date_key = report_date.isoformat()

        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")

            old_record = conn.execute("""
                SELECT 1
                FROM audit_logs
                WHERE event_type = 'DAILY_REPORT_SENT'
                  AND json_extract(details, '$.report_date') = ?
                LIMIT 1
            """, (date_key,)).fetchone()

            if old_record:
                return False

            inserted = conn.execute("""
                INSERT OR IGNORE INTO daily_report_deliveries
                    (report_date, status, attempted_at)
                VALUES (?, 'SENDING', ?)
            """, (date_key, datetime.now(IST).isoformat()))

            return inserted.rowcount == 1

    def _mark_sent(self, report_date):
        db = self._database()

        with db.connect() as conn:
            conn.execute("""
                UPDATE daily_report_deliveries
                SET status = 'SENT', sent_at = ?
                WHERE report_date = ? AND status = 'SENDING'
            """, (
                datetime.now(IST).isoformat(),
                report_date.isoformat(),
            ))

        db.log_event(
            "DAILY_REPORT_SENT",
            "Scheduled daily Telegram report sent.",
            {"report_date": report_date.isoformat()},
        )

    def _record_failure(
        self,
        report_date,
        stage,
        error,
        exception_type=None,
    ):
        """Persist a structured scheduler failure in SQLite."""
        details = {
            "component": "daily_report_scheduler",
            "report_date": report_date.isoformat(),
            "failure_stage": str(stage),
            "exception_type": (
                exception_type
                or type(error).__name__
            ),
            "error": str(error),
            "paper_only": True,
        }

        self._database().log_event(
            "DAILY_REPORT_SCHEDULER_ERROR",
            f"Daily report scheduler failed during {stage}: {error}",
            details,
        )

    def run_once(self, now=None):
        """Run one scheduled attempt and audit failures."""
        current = now or datetime.now(IST)

        if current.tzinfo is None:
            current = current.replace(tzinfo=IST)
        else:
            current = current.astimezone(IST)

        if current.weekday() >= 5:
            return False

        scheduled = current.replace(
            hour=REPORT_HOUR,
            minute=REPORT_MINUTE,
            second=0,
            microsecond=0,
        )

        if current < scheduled:
            return False

        report_date = current.date()

        with self._lock:
            stage = "claim"

            try:
                if not self._claim_report_date(report_date):
                    return False

                stage = "report_generation"
                message = self.report_provider()

                if not isinstance(message, str) or not message.strip():
                    raise ValueError("Daily report is empty")

                stage = "telegram_send"
                success, response = self.sender(message)

                if not success:
                    self._record_failure(
                        report_date,
                        stage,
                        response or "Telegram send failed",
                        exception_type="TelegramSendError",
                    )
                    return False

                stage = "mark_sent"
                self._mark_sent(report_date)
                return True

            except Exception as error:
                logger.exception(
                    "Daily report scheduler failed at stage %s",
                    stage,
                )

                try:
                    self._record_failure(
                        report_date,
                        stage,
                        error,
                    )
                except Exception:
                    logger.exception(
                        "Could not save scheduler failure to SQLite"
                    )

                return False

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="pruthvi-daily-report-scheduler",
            daemon=True,
        )
        self._thread.start()

    def _run(self):
        logger.info(
            "Daily report scheduler started at %02d:%02d IST",
            REPORT_HOUR,
            REPORT_MINUTE,
        )

        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                # Last-resort protection: keep the worker alive.
                logger.exception("Unexpected scheduler loop failure")

            self._stop_event.wait(self.poll_interval)

    def stop(self, timeout=5):
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)


def run_daily_report_scheduler():
    scheduler = DailyReportScheduler()
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    run_daily_report_scheduler()
