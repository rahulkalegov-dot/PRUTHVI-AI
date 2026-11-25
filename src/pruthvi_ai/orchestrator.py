

from dataclasses import dataclass

import pytest

from pruthvi_ai.orchestrator import (
    MasterOrchestrator,
    SystemStatus,
)


def test_system_status_values():
    status = SystemStatus(
        status="SCAN_COMPLETED",
        scanned_stocks=50,
        ready_stocks=8,
        rejected_stocks=42,
    )

    assert status.status == "SCAN_COMPLETED"
    assert status.scanned_stocks == 50
    assert status.ready_stocks == 8
    assert status.rejected_stocks == 42


def test_run_scan_counts_ready_and_rejected(monkeypatch):
    @dataclass
    class ScanResult:
        status: str

    def fake_scan_universe(stocks, market_data):
        return [
            ScanResult("READY"),
            ScanResult("REJECTED"),
            ScanResult("READY"),
            ScanResult("REJECTED"),
        ]

    monkeypatch.setattr(
        "pruthvi_ai.market_scanner.scan_universe",
        fake_scan_universe,
    )

    orchestrator = MasterOrchestrator()

    results, status = orchestrator.run_scan(
        ["A", "B", "C", "D"],
        {},
    )

    assert len(results) == 4
    assert status.status == "SCAN_COMPLETED"
    assert status.scanned_stocks == 4
    assert status.ready_stocks == 2
    assert status.rejected_stocks == 2


def test_run_scan_with_no_results(monkeypatch):
    def fake_scan_universe(stocks, market_data):
        return []

    monkeypatch.setattr(
        "pruthvi_ai.market_scanner.scan_universe",
        fake_scan_universe,
    )

    orchestrator = MasterOrchestrator()

    results, status = orchestrator.run_scan([], {})

    assert results == []
    assert status.scanned_stocks == 0
    assert status.ready_stocks == 0
    assert status.rejected_stocks == 0


def test_orchestrator_sends_telegram_status_report(monkeypatch):
    captured = {}

    def fake_send(message):
        captured["message"] = message
        return True, "Report sent"

    monkeypatch.setattr(
        "pruthvi_ai.orchestrator.send_telegram_report",
        fake_send,
    )

    status = SystemStatus(
        status="SCAN_COMPLETED",
        scanned_stocks=50,
        ready_stocks=8,
        rejected_stocks=42,
    )

    orchestrator = MasterOrchestrator()
    success, message = orchestrator.send_status_report(status)

    assert success is True
    assert message == "Report sent"
    assert "PRUTHVI AI SYSTEM REPORT" in captured["message"]
    assert "Scanned stocks: 50" in captured["message"]
    assert "Ready stocks: 8" in captured["message"]
    assert "Rejected stocks: 42" in captured["message"]
    assert "PAPER ONLY" in captured["message"]


def test_orchestrator_handles_telegram_failure(monkeypatch):
    def fake_send(message):
        return False, "Telegram connection failed"

    monkeypatch.setattr(
        "pruthvi_ai.orchestrator.send_telegram_report",
        fake_send,
    )

    status = SystemStatus(
        status="SCAN_COMPLETED",
        scanned_stocks=50,
        ready_stocks=0,
        rejected_stocks=50,
    )

    orchestrator = MasterOrchestrator()
    success, message = orchestrator.send_status_report(status)

    assert success is False
    assert message == "Telegram connection failed"
