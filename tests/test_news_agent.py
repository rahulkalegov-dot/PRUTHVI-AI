from datetime import datetime, timezone, timedelta

from pruthvi_ai.news_agent import (
    NewsItem,
    validate_news,
    classify_news,
    get_news_decision,
)


def test_verified_news():
    item = NewsItem(
        headline="Company announces results",
        source="Official NSE",
        published_at=datetime.now(timezone.utc),
        symbol="RELIANCE",
        verified=True,
    )

    assert validate_news(item) is True
    assert classify_news(item) == "VERIFIED"


def test_unverified_news():
    item = NewsItem(
        headline="Market news",
        source="Unknown source",
        published_at=datetime.now(timezone.utc),
        verified=False,
    )

    assert classify_news(item) == "UNVERIFIED"
    assert get_news_decision(item) == "NO TRADE"


def test_invalid_future_news():
    item = NewsItem(
        headline="Future news",
        source="NSE",
        published_at=datetime.now(timezone.utc)
        + timedelta(days=1),
        verified=True,
    )

    assert validate_news(item) is False