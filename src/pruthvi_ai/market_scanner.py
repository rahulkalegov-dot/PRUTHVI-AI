from dataclasses import dataclass


@dataclass
class ScanResult:
    symbol: str
    status: str
    reason: str


def scan_stock(symbol, candles):
    if not symbol or not isinstance(candles, dict):
        return ScanResult(
            str(symbol), "REJECTED", "Invalid input"
        )

    required = {"5m", "15m", "1h"}

    if not required.issubset(candles):
        return ScanResult(
            symbol, "NO TRADE", "Missing timeframe data"
        )

    for timeframe in required:
        if not candles[timeframe]:
            return ScanResult(
                symbol, "NO TRADE",
                f"Missing {timeframe} candles"
            )

    return ScanResult(
        symbol, "READY",
        "All three timeframe datasets received"
    )


def scan_universe(stocks, market_data):
    results = []

    for stock in stocks:
        symbol = stock.get("Symbol", "")

        result = scan_stock(
            symbol,
            market_data.get(symbol, {})
        )

        results.append(result)

    return results