from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:
    headline: str
    source: str
    published_at: datetime
    symbol: str = ""
    verified: bool = False


def validate_news(item):
    if not item.headline or not item.source:
        return False

    if not isinstance(item.published_at, datetime):
        return False

    if item.published_at.tzinfo is None:
        return False

    if item.published_at > datetime.now(
        item.published_at.tzinfo
    ):
        return False

    return True


def classify_news(item):
    if not validate_news(item):
        return "REJECTED"

    if not item.verified:
        return "UNVERIFIED"

    return "VERIFIED"


def get_news_decision(item):
    status = classify_news(item)

    if status != "VERIFIED":
        return "NO TRADE"

    return "REVIEW REQUIRED"