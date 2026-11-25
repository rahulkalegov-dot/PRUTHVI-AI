from pruthvi_ai.main import run_system_check


def test_system_check():
    result = run_system_check()

    assert result["project"] == "PRUTHVI AI"
    assert result["version"] == "1.0.0"
    assert result["exchange"] == "NSE"
    assert result["market"] == "NIFTY 50"
    assert result["expected_stocks"] == 50


def test_paper_trading_safety():
    result = run_system_check()

    assert result["paper_only"] is True
    assert result["live_trading"] is False
    assert result["execution_enabled"] is False


def test_initial_status():
    result = run_system_check()

    assert result["system_status"] == "INITIALIZED"