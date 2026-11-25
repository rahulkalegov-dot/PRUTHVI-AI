
"""
PRUTHVI AI - Market Data Agent

Responsibilities:
- Register NSE instrument details.
- Normalize incoming market quotes.
- Validate OHLCV candle data.
- Support 5m, 15m and 1h timeframes.
- Reject invalid or incomplete market data.

Safety:
- PAPER ONLY.
- No order placement.
- No live-trading functionality.
- No invented API endpoints.
"""

import csv
import io
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


SUPPORTED_TIMEFRAMES = {"5m", "15m", "1h"}


class DataValidationError(ValueError):
    """Raised when incoming market data is invalid."""


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
    """Validates and organizes market data for PRUTHVI AI."""

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
            raise DataValidationError(
                f"{field} must be a valid number."
            )

        if not math.isfinite(number):
            raise DataValidationError(
                f"{field} must be finite."
            )

        return number

    @staticmethod
    def _timestamp(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise DataValidationError(
                "A valid ISO timestamp is required."
            )

        try:
            parsed = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )
        except ValueError:
            raise DataValidationError(
                "Invalid timestamp format."
            )

        return parsed.isoformat()

    def register_instruments_csv(self, csv_text: str) -> int:
        """
        Register instruments from the MegaBull instrument CSV.

        Expected columns:
        tradingSymbol, instrumentName, instrumentToken
        """

        if not isinstance(csv_text, str) or not csv_text.strip():
            raise DataValidationError("Instrument CSV is empty.")

        reader = csv.DictReader(io.StringIO(csv_text))

        required = {
            "tradingSymbol",
            "instrumentName",
            "instrumentToken",
        }

        if not reader.fieldnames or not required.issubset(
            set(reader.fieldnames)
        ):
            raise DataValidationError(
                "Instrument CSV is missing required columns."
            )

        registered = 0

        for row in reader:
            symbol = self._validate_symbol(
                row.get("tradingSymbol")
            )

            name = str(
                row.get("instrumentName") or ""
            ).strip()

            token = str(
                row.get("instrumentToken") or ""
            ).strip()

            if not name or not token:
                self._reject(
                    symbol,
                    "Missing instrument name or token."
                )
                continue

            self.instruments[symbol] = Instrument(
                trading_symbol=symbol,
                instrument_name=name,
                instrument_token=token,
            )

            registered += 1

        return registered

    def ingest_quote(
        self,
        symbol: str,
        instrument_token: str,
        last_price: Any,
        timestamp: Optional[str] = None,
        source: str = "external",
    ) -> MarketQuote:

        normalized_symbol = self._validate_symbol(symbol)
        price = self._number(last_price, "last_price")

        if price <= 0:
            raise DataValidationError(
                "Last price must be greater than zero."
            )

        if not instrument_token:
            raise DataValidationError(
                "Instrument token is required."
            )

        if not source or not isinstance(source, str):
            raise DataValidationError(
                "Data source must be identified."
            )

        normalized_time = (
            self._timestamp(timestamp)
            if timestamp is not None
            else None
        )

        quote = MarketQuote(
            symbol=normalized_symbol,
            instrument_token=str(instrument_token),
            last_price=price,
            timestamp=normalized_time,
            source=source,
        )

        self.quotes[normalized_symbol] = quote

        return quote

    def ingest_candle(
        self,
        symbol: str,
        timeframe: str,
        timestamp: str,
        open_price: Any,
        high: Any,
        low: Any,
        close: Any,
        volume: Any,
        source: str = "external",
    ) -> Candle:

        normalized_symbol = self._validate_symbol(symbol)

        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise DataValidationError(
                "Unsupported timeframe. Use 5m, 15m or 1h."
            )

        normalized_time = self._timestamp(timestamp)

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
            raise DataValidationError(
                "Volume cannot be negative."
            )

        if h < l:
            raise DataValidationError(
                "High cannot be lower than low."
            )

        if h < max(o, c):
            raise DataValidationError(
                "High must be at least the open and close."
            )

        if l > min(o, c):
            raise DataValidationError(
                "Low must be at most the open and close."
            )

        if not source or not isinstance(source, str):
            raise DataValidationError(
                "Data source must be identified."
            )

        candle = Candle(
            symbol=normalized_symbol,
            timeframe=timeframe,
            timestamp=normalized_time,
            open=o,
            high=h,
            low=l,
            close=c,
            volume=v,
            source=source,
        )

        key = f"{normalized_symbol}:{timeframe}"

        existing = self.candles.setdefault(key, [])

        # Avoid storing the same candle timestamp twice.
        for index, old_candle in enumerate(existing):
            if old_candle.timestamp == normalized_time:
                existing[index] = candle
                return candle

        existing.append(candle)
        existing.sort(key=lambda item: item.timestamp)

        return candle

    def get_quote(self, symbol: str) -> Optional[MarketQuote]:
        return self.quotes.get(
            self._validate_symbol(symbol)
        )

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
    ) -> List[Candle]:

        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise DataValidationError(
                "Unsupported timeframe."
            )

        key = f"{self._validate_symbol(symbol)}:{timeframe}"

        return list(self.candles.get(key, []))

    def get_data_status(self) -> Dict[str, Any]:
        return {
            "registered_instruments": len(self.instruments),
            "available_quotes": len(self.quotes),
            "candle_groups": len(self.candles),
            "total_candles": sum(
                len(items) for items in self.candles.values()
            ),
            "rejected_records": len(self.rejected_records),
            "supported_timeframes": sorted(
                SUPPORTED_TIMEFRAMES
            ),
            "paper_only": True,
            "live_trading_enabled": False,
            "automatic_execution_enabled": False,
        }

    def _reject(self, symbol: str, reason: str) -> None:
        self.rejected_records.append({
            "symbol": symbol,
            "reason": reason,
        })
