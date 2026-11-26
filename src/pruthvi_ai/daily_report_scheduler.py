
"""Scheduled daily Telegram reports for PRUTHVI AI.

Informational reporting only. No broker orders or trade execution.
Runs on weekdays at 15:35 Asia/Kolkata.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
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


def _next_report_time(now=None):
    """Return the next weekday report time in IST."""
    current = now or datetime.now(IST)

    if current.tzinfo is None:
        current = current.replace(tzinfo=IST)
    else:
        current = current.astimezone(IST)

    candidate = current.replace(
        hour=REPORT_HOUR,
        minute=REPORT_MINUTE,
        second=0,
        microsecond=0,
    )

    if current >= candidate:
        candidate += timedelta(days=1)

    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)

    return candidate


class DailyReportScheduler:
    """Thread-safe weekday scheduler for daily Telegram reports."""

    def __init__(
        self,
        report_provider=None,
        sender=None,
        db_path=None,
        poll_interval=20,
    ):
        self.report_provider = (
            report_provider or self._generate_report
        )
        self.sender = sender or send_telegram_report
        self.db_path = db_path
        self.poll_interval = max(1, int(poll_interval))

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._last_attempted_date = None

    def _database(self):
        return PRUTHVIDatabase(self.db_path)

    def _generate_report(self):
        report = generate_sqlite_daily_report(
            db_path=self.db_path
        )
        return format_sqlite_daily_report(report)

    def _already_sent(self, report_date):
        db = self._database()

        with db.connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM audit_logs
                WHERE event_type = 'DAILY_REPORT_SENT'
                  AND json_extract(details, '$.report_date') = ?
                LIMIT 1
                """,
                (report_date.isoformat(),),
            ).fetchone()

        return row is not None

    def _record_event(self, event_type, message, report_date, details=None):
        db = self._database()

        payload = {
            "report_date": report_date.isoformat(),
        }

        if details:
            payload.update(details)

        db.log_event(event_type, message, payload)

    def run_once(self, now=None):
        """Send today's report when due; return True only on success."""
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
            if self._last_attempted_date == report_date:
                return False

            try:
                if self._already_sent(report_date):
                    self._last_attempted_date = report_date
                    return False

                message = self.report_provider()

                if not isinstance(message, str) or not message.strip():
                    raise ValueError("Daily report is empty")

                success, response = self.sender(message)

                if not success:
                    raise RuntimeError(
                        str(response or "Telegram send failed")
                    )

                self._record_event(
                    "DAILY_REPORT_SENT",
                    "Scheduled daily Telegram report sent.",
                    report_date,
                )

                self._last_attempted_date = report_date
                return True

            except Exception as error:
                logger.exception("Daily report scheduler failed")

                try:
                    self._record_event(
                        "DAILY_REPORT_ERROR",
                        str(error),
                        report_date,
                    )
                except Exception:
                    logger.exception(
                        "Could not persist scheduler error"
                    )

                # Permit retry on the next scheduler poll.
                return False

    def start(self):
        """Start the scheduler in a daemon thread."""
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
            "Daily Telegram report scheduler started: "
            "weekdays at %02d:%02d IST",
            REPORT_HOUR,
            REPORT_MINUTE,
        )

        while not self._stop_event.is_set():
            self.run_once()
            self._stop_event.wait(self.poll_interval)

    def stop(self, timeout=5):
        """Stop the scheduler gracefully."""
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)


def run_daily_report_scheduler():
    """Run the scheduler as a standalone process."""
    scheduler = DailyReportScheduler()
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    run_daily_report_scheduler()
