from pruthvi_ai.orchestrator import MasterOrchestrator


def test_orchestrator_scan():
    stocks = [
        {"Symbol": "RELIANCE"},
        {"Symbol": "TCS"},
    ]

    market_data = {
        "RELIANCE": {
            "5m": [1], "15m": [1], "1h": [1]
        },
        "TCS": {
            "5m": [1], "15m": [1], "1h": [1]
        },
    }

    orchestrator = MasterOrchestrator()
    results, status = orchestrator.run_scan(stocks, market_data)

    assert len(results) == 2
    assert status.scanned_stocks == 2
    assert status.ready_stocks == 2
    assert status.rejected_stocks == 0


def test_orchestrator_missing_data():
    orchestrator = MasterOrchestrator()

    results, status = orchestrator.run_scan(
        [{"Symbol": "INFY"}], {}
    )

    assert status.scanned_stocks == 1
    assert status.ready_stocks == 0
    assert status.rejected_stocks == 1