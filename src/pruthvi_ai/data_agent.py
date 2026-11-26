
"""Market data validation and normalization. No data provider or order API is assumed."""
import csv
import io
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SUPPORTED_TIMEFRAMES = {"5m", "15m", "1h"}


class DataValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Instrument:
    trading_symbol: str
    instrument_name: str
    instrument_token: str


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    instrument_token: str
    last_price: float
    timestamp: Optional[str] = None
    source: str = "external"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "external"


class DataAgent:
    def __init__(self):
        self.instruments: Dict[str, Instrument] = {}
        self.quotes: Dict[str, MarketQuote] = {}
        self.candles: Dict[str, List[Candle]] = {}
        self.rejected_records: List[Dict[str, str]] = []

    @staticmethod
    def _validate_symbol(symbol: Any) -> str:
        if not isinstance(symbol, str) or not symbol.strip():
            raise DataValidationError("Invalid trading symbol.")
        return symbol.strip().upper()

    @staticmethod
    def _number(value: Any, field: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise DataValidationError(f"{field} must be a valid number.")

        if not math.isfinite(number):
            raise DataValidationError(f"{field} must be finite.")

        return number

    @staticmethod
    def _timestamp(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise DataValidationError("A valid ISO timestamp is required.")

        try:
            parsed = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )
        except ValueError:
            raise DataValidationError("Invalid timestamp format.")

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise DataValidationError(
                "Timestamp must include a timezone offset."
            )

        return parsed.isoformat()

    @staticmethod
    def timestamp_is_fresh(timestamp: str, max_age_seconds: int = 120, now=None) -> bool:
        """Freshness check for live runtime; historical backtest candles remain ingestible."""
        if max_age_seconds < 0:
            return False

        try:
            parsed = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                return False

            current = now or datetime.now(timezone.utc)

            if current.tzinfo is None:
                return False

            age = (
                current.astimezone(timezone.utc)
                - parsed.astimezone(timezone.utc)
            ).total_seconds()

            return 0 <= age <= max_age_seconds

        except (TypeError, ValueError):
            return False

    def register_instruments_csv(self, csv_text: str) -> int:
        if not isinstance(csv_text, str) or not csv_text.strip():
            raise DataValidationError("Instrument CSV is empty.")

        reader = csv.DictReader(io.StringIO(csv_text))
        required = {
            "tradingSymbol",
            "instrumentName",
            "instrumentToken",
        }

        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise DataValidationError(
                "Instrument CSV is missing required columns."
            )

        registered = 0

        for row in reader:
            symbol = self._validate_symbol(row.get("tradingSymbol"))
            name = str(row.get("instrumentName") or "").strip()
            token = str(row.get("instrumentToken") or "").strip()

            if not name or not token:
                self._reject(symbol, "Missing instrument name or token.")
                continue

            self.instruments[symbol] = Instrument(
                symbol, name, token
            )
            registered += 1

        return registered

    def ingest_quote(
        self, symbol, instrument_token, last_price,
        timestamp=None, source="external",
    ):
        normalized = self._validate_symbol(symbol)
        price = self._number(last_price, "last_price")

        if price <= 0:
            raise DataValidationError(
                "Last price must be greater than zero."
            )

        if not instrument_token:
            raise DataValidationError("Instrument token is required.")

        if not isinstance(source, str) or not source.strip():
            raise DataValidationError("Data source must be identified.")

        normalized_time = (
            self._timestamp(timestamp)
            if timestamp is not None else None
        )

        quote = MarketQuote(
            normalized,
            str(instrument_token),
            price,
            normalized_time,
            source.strip(),
        )

        self.quotes[normalized] = quote
        return quote

    def ingest_candle(
        self, symbol, timeframe, timestamp, open_price,
        high, low, close, volume, source="external",
    ):
        normalized = self._validate_symbol(symbol)

        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise DataValidationError(
                "Unsupported timeframe. Use 5m, 15m or 1h."
            )

        ts = self._timestamp(timestamp)
        o = self._number(open_price, "open")
        h = self._number(high, "high")
        l = self._number(low, "low")
        c = self._number(close, "close")
        v = self._number(volume, "volume")

        if min(o, h, l, c) <= 0:
            raise DataValidationError(
                "OHLC prices must be greater than zero."
            )

        if v < 0:
            raise DataValidationError("Volume cannot be negative.")

        if h < l or h < max(o, c) or l > min(o, c):
            raise DataValidationError("Invalid OHLC relationship.")

        if not isinstance(source, str) or not source.strip():
            raise DataValidationError("Data source must be identified.")

        candle = Candle(
            normalized, timeframe, ts, o, h, l, c, v, source.strip()
        )

        key = f"{normalized}:{timeframe}"
        items = self.candles.setdefault(key, [])

        for index, old in enumerate(items):
            if old.timestamp == ts:
                items[index] = candle
                return candle

        items.append(candle)
        items.sort(key=lambda item: item.timestamp)

        return candle

    def get_quote(self, symbol):
        return self.quotes.get(self._validate_symbol(symbol))

    def get_candles(self, symbol, timeframe):
        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise DataValidationError("Unsupported timeframe.")

        return list(
            self.candles.get(
                f"{self._validate_symbol(symbol)}:{timeframe}",
                [],
            )
        )

    def get_data_status(self):
        return {
            "registered_instruments": len(self.instruments),
            "available_quotes": len(self.quotes),
            "candle_groups": len(self.candles),
            "total_candles": sum(
                len(v) for v in self.candles.values()
            ),
            "rejected_records": len(self.rejected_records),
            "supported_timeframes": sorted(SUPPORTED_TIMEFRAMES),
            "paper_only": True,
            "live_trading_enabled": False,
            "automatic_execution_enabled": False,
        }

    def _reject(self, symbol, reason):
        self.rejected_records.append({
            "symbol": symbol,
            "reason": reason,
        })
