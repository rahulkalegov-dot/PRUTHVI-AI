from dataclasses import dataclass


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
    risk_approved
):
    if not symbol or not risk_approved:
        return Decision(
            symbol, "NO TRADE", 0,
            "Risk approval missing"
        )

    if not news_verified:
        return Decision(
            symbol, "NO TRADE", 0,
            "News verification missing"
        )

    if market_trend not in ("BULLISH", "BEARISH"):
        return Decision(
            symbol, "NO TRADE", 0,
            "Market trend uncertain"
        )

    if not -1 <= technical_score <= 1:
        raise ValueError("Invalid technical score")

    if not -1 <= strategy_score <= 1:
        raise ValueError("Invalid strategy score")

    score = (
        technical_score * 0.6
        + strategy_score * 0.4
    )

    if market_trend == "BULLISH" and score >= 0.7:
        action = "BUY"
    elif market_trend == "BEARISH" and score <= -0.7:
        action = "SELL"
    else:
        action = "NO TRADE"

    return Decision(
        symbol,
        action,
        round(score, 3),
        f"Technical={technical_score}, "
        f"Strategy={strategy_score}, "
        f"Market={market_trend}"
    )