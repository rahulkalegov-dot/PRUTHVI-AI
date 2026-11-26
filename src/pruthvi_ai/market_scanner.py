
"""Input-readiness scanner only; READY means data arrived, not a trade signal."""
from dataclasses import dataclass


@dataclass
class ScanResult:
    symbol: str
    status: str
    reason: str


def scan_stock(symbol, candles, database=None):
    normalized = str(symbol).strip().upper() if symbol is not None else ""

    if not normalized or not isinstance(candles, dict):
        result = ScanResult(normalized, "REJECTED", "Invalid input")
    else:
        required = ("5m", "15m", "1h")
        missing = [
            tf for tf in required
            if tf not in candles or not candles[tf]
        ]

        if missing:
            result = ScanResult(
                normalized,
                "NO TRADE",
                "Missing or empty timeframe data: " + ", ".join(missing),
            )
        else:
            result = ScanResult(
                normalized,
                "READY",
                "All timeframe datasets received; analytical validation is still required",
            )

    if database is not None and result.symbol:
        database.save_scan(result.symbol, result.status, result.reason)

    return result


def scan_universe(stocks, market_data, database=None):
    if not isinstance(stocks, (list, tuple)):
        raise TypeError("stocks must be a list or tuple")

    if not isinstance(market_data, dict):
        raise TypeError("market_data must be a dictionary")

    results = []

    for stock in stocks:
        if not isinstance(stock, dict):
            results.append(
                ScanResult("", "REJECTED", "Invalid stock record")
            )
            continue

        symbol = stock.get("Symbol", stock.get("symbol", ""))
        candles = market_data.get(
            str(symbol).upper(),
            market_data.get(symbol, {}),
        )

        results.append(
            scan_stock(symbol, candles, database)
        )

    return results
