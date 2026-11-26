
from dataclasses import dataclass

from .telegram_reporter import send_telegram_report
from .report_agent import (
    generate_daily_report,
    format_daily_report,
)


@dataclass
class SystemStatus:
    status: str
    scanned_stocks: int
    ready_stocks: int
    rejected_stocks: int


class MasterOrchestrator:

    def run_scan(self, stocks, market_data):
        from .market_scanner import scan_universe

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

    def send_status_report(self, status):
        message = (
            "PRUTHVI AI SYSTEM REPORT\n"
            f"Status: {status.status}\n"
            f"Scanned stocks: {status.scanned_stocks}\n"
            f"Ready stocks: {status.ready_stocks}\n"
            f"Rejected stocks: {status.rejected_stocks}\n"
            "Mode: PAPER ONLY"
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

        trades = paper_trading_engine.trade_history

        report = generate_daily_report(
            scanned_stocks=scanned_stocks,
            decisions=decisions,
            trades=trades,
            errors=errors,
        )

        message = format_daily_report(report)

        return send_telegram_report(message)
