
"""Conservative decision gate. A BUY/SELL decision is not an order."""
from dataclasses import dataclass
from math import isfinite


@dataclass
class Decision:
    symbol: str
    action: str
    score: float
    reasoning: str


def make_decision(
    symbol,
    technical_score,
    strategy_score,
    news_verified,
    market_trend,
    risk_approved,
    database=None,
):
    normalized = (
        str(symbol).strip().upper()
        if isinstance(symbol, str) else ""
    )

    def result(action, score, reason):
        decision = Decision(
            normalized, action, score, reason
        )

        if database is not None and normalized:
            database.save_decision(
                normalized, action, score, reason
            )

        return decision

    if not normalized:
        return result("NO TRADE", 0.0, "Invalid symbol")

    if not risk_approved:
        return result("NO TRADE", 0.0, "Risk approval missing")

    if not news_verified:
        return result("NO TRADE", 0.0, "News verification missing")

    if market_trend not in ("BULLISH", "BEARISH"):
        return result("NO TRADE", 0.0, "Market trend uncertain")

    try:
        technical_score = float(technical_score)
        strategy_score = float(strategy_score)
    except (TypeError, ValueError):
        return result("NO TRADE", 0.0, "Invalid score data")

    if not isfinite(technical_score) or not isfinite(strategy_score):
        return result("NO TRADE", 0.0, "Non-finite score data")

    if not -1 <= technical_score <= 1 or not -1 <= strategy_score <= 1:
        return result("NO TRADE", 0.0, "Scores must be between -1 and 1")

    score = technical_score * 0.6 + strategy_score * 0.4

    if market_trend == "BULLISH" and score >= 0.7:
        action = "BUY"
    elif market_trend == "BEARISH" and score <= -0.7:
        action = "SELL"
    else:
        action = "NO TRADE"

    return result(
        action,
        round(score, 3),
        f"Technical={technical_score}, Strategy={strategy_score}, Market={market_trend}",
    )
