from pruthvi_ai.market_scanner import scan_stock, scan_universe


def test_valid_stock_scan():
    candles = {
        "5m": [1],
        "15m": [1],
        "1h": [1],
    }
    result = scan_stock("RELIANCE", candles)
    assert result.status == "READY"


def test_missing_timeframe():
    candles = {
        "5m": [1],
        "15m": [1],
    }
    result = scan_stock("TCS", candles)
    assert result.status == "NO TRADE"


def test_empty_candles():
    candles = {
        "5m": [],
        "15m": [1],
        "1h": [1],
    }
    result = scan_stock("INFY", candles)
    assert result.status == "NO TRADE"


def test_universe_scan():
    stocks = [
        {"Symbol": "RELIANCE"},
        {"Symbol": "TCS"},
    ]
    market_data = {
        "RELIANCE": {"5m": [1], "15m": [1], "1h": [1]},
        "TCS": {"5m": [1], "15m": [1], "1h": [1]},
    }
    results = scan_universe(stocks, market_data)
    assert len(results) == 2
    assert all(item.status == "READY" for item in results)