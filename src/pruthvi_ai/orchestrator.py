
"""Master coordination shell. It does not start autonomous trading."""
from dataclasses import dataclass
import logging

from .telegram_reporter import send_telegram_report
from .report_agent import generate_daily_report, format_daily_report

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    status: str
    scanned_stocks: int
    ready_stocks: int
    rejected_stocks: int
    errors: int = 0


class MasterOrchestrator:
    def __init__(self, database=None, risk_agent=None, decision_agent=None):
        self.database = database
        self.risk_agent = risk_agent
        self.decision_agent = decision_agent
        self.last_errors = []

    def _log_error(self, message):
        self.last_errors.append(str(message))
        logger.error("%s", message)
        if self.database is not None:
            try:
                self.database.log_event(
                    "ORCHESTRATOR_ERROR", str(message), {"message": str(message)}
                )
            except Exception:
                logger.exception("Database error logging failed")

    def run_scan(self, stocks, market_data):
        from .market_scanner import scan_universe
        self.last_errors = []
        try:
            results = scan_universe(stocks, market_data, database=self.database)
            ready = sum(1 for item in results if item.status == "READY")
            rejected = len(results) - ready
            return results, SystemStatus(
                "SCAN_COMPLETED", len(results), ready, rejected, 0
            )
        except Exception as exc:
            self._log_error(f"Scan failed: {exc}")
            return [], SystemStatus("SCAN_FAILED", 0, 0, 0, 1)

    def send_status_report(self, status):
        message = (
            "PRUTHVI AI SYSTEM REPORT\n"
            f"Status: {status.status}\n"
            f"Scanned stocks: {status.scanned_stocks}\n"
            f"Ready datasets: {status.ready_stocks}\n"
            f"Rejected datasets: {status.rejected_stocks}\n"
            f"Errors: {status.errors}\n"
            "Mode: PAPER ONLY\n"
            "Live trading: PERMANENTLY DISABLED\n"
            "Automatic execution: DISABLED\n"
            "READY means data received, not a trade signal."
        )
        return send_telegram_report(message)

    def send_daily_report(self, scanned_stocks, decisions, paper_trading_engine, errors=None):
        if paper_trading_engine is None:
            return False, "Paper trading engine is missing"
        try:
            report = generate_daily_report(
                scanned_stocks=scanned_stocks,
                decisions=decisions,
                trades=paper_trading_engine.trade_history,
                errors=errors if errors is not None else self.last_errors,
            )
            return send_telegram_report(format_daily_report(report))
        except Exception as exc:
            self._log_error(f"Daily report failed: {exc}")
            return False, "Daily report generation failed"

    def health_check(self):
        database_ok = False
        if self.database is not None:
            try:
                result = self.database.health_check()
                database_ok = isinstance(result, dict) and result.get("database") == "OK"
            except Exception as exc:
                self._log_error(f"Database health check failed: {exc}")
        healthy = database_ok and not self.last_errors
        return {
            "status": "HEALTHY" if healthy else "DEGRADED",
            "database_connected": database_ok,
            "paper_only": True,
            "live_trading_enabled": False,
            "auto_execution_enabled": False,
            "release_approved": False,
            "market_data_connected": False,
            "trading_runtime_started": False,
        }
