
import pytest

from pruthvi_ai.data_agent import (
    DataAgent,
    DataValidationError,
    SUPPORTED_TIMEFRAMES,
)


@pytest.fixture
def agent():
    return DataAgent()


def test_supported_timeframes():
    assert SUPPORTED_TIMEFRAMES == {"5m", "15m", "1h"}


def test_register_instruments_csv(agent):
    csv_text = (
        "tradingSymbol,instrumentName,instrumentToken\n"
        "RELIANCE,Reliance Industries,738561\n"
        "TCS,Tata Consultancy Services,2953217\n"
    )

    count = agent.register_instruments_csv(csv_text)

    assert count == 2
    assert "RELIANCE" in agent.instruments
    assert "TCS" in agent.instruments


def test_reject_invalid_csv(agent):
    with pytest.raises(DataValidationError):
        agent.register_instruments_csv("wrong,columns\nA,B")


def test_ingest_quote(agent):
    quote = agent.ingest_quote(
        symbol="reliance",
        instrument_token="738561",
        last_price=1500,
        timestamp="2026-11-25T10:00:00+05:30",
    )

    assert quote.symbol == "RELIANCE"
    assert quote.last_price == 1500
    assert agent.get_quote("RELIANCE") == quote


def test_reject_invalid_quote_price(agent):
    with pytest.raises(DataValidationError):
        agent.ingest_quote("RELIANCE", "738561", -10)


def test_ingest_valid_candle(agent):
    candle = agent.ingest_candle(
        symbol="RELIANCE",
        timeframe="5m",
        timestamp="2026-11-25T10:00:00+05:30",
        open_price=100,
        high=110,
        low=95,
        close=105,
        volume=10000,
    )

    assert candle.symbol == "RELIANCE"
    assert candle.timeframe == "5m"
    assert candle.close == 105
    assert len(agent.get_candles("RELIANCE", "5m")) == 1


def test_reject_invalid_timeframe(agent):
    with pytest.raises(DataValidationError):
        agent.ingest_candle(
            "RELIANCE", "1m",
            "2026-11-25T10:00:00+05:30",
            100, 110, 95, 105, 1000,
        )


def test_reject_invalid_ohlc(agent):
    with pytest.raises(DataValidationError):
        agent.ingest_candle(
            "RELIANCE", "5m",
            "2026-11-25T10:00:00+05:30",
            100, 90, 95, 105, 1000,
        )


def test_reject_negative_volume(agent):
    with pytest.raises(DataValidationError):
        agent.ingest_candle(
            "RELIANCE", "15m",
            "2026-11-25T10:00:00+05:30",
            100, 110, 95, 105, -1,
        )


def test_duplicate_candle_timestamp_updates_existing(agent):
    timestamp = "2026-11-25T10:00:00+05:30"

    agent.ingest_candle(
        "RELIANCE", "5m", timestamp,
        100, 110, 95, 105, 1000,
    )

    agent.ingest_candle(
        "RELIANCE", "5m", timestamp,
        100, 112, 95, 111, 1500,
    )

    candles = agent.get_candles("RELIANCE", "5m")

    assert len(candles) == 1
    assert candles[0].close == 111


def test_data_status_keeps_safety_locks(agent):
    status = agent.get_data_status()

    assert status["paper_only"] is True
    assert status["live_trading_enabled"] is False
    assert status["automatic_execution_enabled"] is False
