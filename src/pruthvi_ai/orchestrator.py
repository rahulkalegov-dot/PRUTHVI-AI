
from dataclasses import dataclass
import logging
from typing import Optional

from .telegram_reporter import send_telegram_report
from .report_agent import (
    generate_daily_report,
    format_daily_report,
)

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    status: str
    scanned_stocks: int
    ready_stocks: int
    rejected_stocks: int
    errors: int = 0


class MasterOrchestrator:

    def __init__(
        self,
        database=None,
        risk_agent=None,
        decision_agent=None,
    ):
        self.database = database
        self.risk_agent = risk_agent
        self.decision_agent = decision_agent
        self.last_errors = []

    def _log_error(self, message):
        self.last_errors.append(message)
        logger.exception(message)

        if self.database is not None:
            try:
                self.database.log_audit(
                    event_type="ORCHESTRATOR_ERROR",
                    details={"message": message},
                )
            except Exception:
                logger.exception("Database error logging failed")

    def run_scan(self, stocks, market_data):
        from .market_scanner import scan_universe

        self.last_errors = []

        try:
            results = scan_universe(stocks, market_data)

            ready = sum(
                1 for item in results
                if item.status == "READY"
            )

            rejected = len(results) - ready

            return results, SystemStatus(
                status="SCAN_COMPLETED",
                scanned_stocks=len(results),
                ready_stocks=ready,
                rejected_stocks=rejected,
            )

        except Exception as exc:
            self._log_error(f"Scan failed: {exc}")

            return [], SystemStatus(
                status="SCAN_FAILED",
                scanned_stocks=0,
                ready_stocks=0,
                rejected_stocks=0,
                errors=1,
            )

    def send_status_report(self, status):
        message = (
            "PRUTHVI AI SYSTEM REPORT\n"
            f"Status: {status.status}\n"
            f"Scanned stocks: {status.scanned_stocks}\n"
            f"Ready stocks: {status.ready_stocks}\n"
            f"Rejected stocks: {status.rejected_stocks}\n"
            f"Errors: {status.errors}\n"
            "Mode: PAPER ONLY\n"
            "Live trading: DISABLED"
        )

        return send_telegram_report(message)

    def send_daily_report(
        self,
        scanned_stocks,
        decisions,
        paper_trading_engine,
        errors=None,
    ):
        if paper_trading_engine is None:
            return False, "Paper trading engine is missing"

        try:
            trades = paper_trading_engine.trade_history

            report = generate_daily_report(
                scanned_stocks=scanned_stocks,
                decisions=decisions,
                trades=trades,
                errors=errors or self.last_errors,
            )

            message = format_daily_report(report)

            return send_telegram_report(message)

        except Exception as exc:
            self._log_error(f"Daily report failed: {exc}")
            return False, "Daily report generation failed"

    def health_check(self):
        database_ok = False

        if self.database is not None:
            try:
                database_ok = bool(self.database.health_check())
            except Exception:
                logger.exception("Database health check failed")

        return {
            "status": "HEALTHY" if not self.last_errors else "DEGRADED",
            "database_connected": database_ok,
            "paper_only": True,
            "live_trading_enabled": False,
            "auto_execution_enabled": False,
            "release_approved": False,
        }
