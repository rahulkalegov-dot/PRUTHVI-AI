from pruthvi_ai.decision_agent import make_decision


def test_bullish_buy():
    result = make_decision(
        "RELIANCE", 0.9, 0.9,
        True, "BULLISH", True
    )
    assert result.action == "BUY"


def test_bearish_sell():
    result = make_decision(
        "TCS", -0.9, -0.9,
        True, "BEARISH", True
    )
    assert result.action == "SELL"


def test_uncertain_market():
    result = make_decision(
        "INFY", 0.9, 0.9,
        True, "SIDEWAYS", True
    )
    assert result.action == "NO TRADE"


def test_risk_rejection():
    result = make_decision(
        "HDFC", 0.9, 0.9,
        True, "BULLISH", False
    )
    assert result.action == "NO TRADE"


def test_unverified_news():
    result = make_decision(
        "ICICI", 0.9, 0.9,
        False, "BULLISH", True
    )
    assert result.action == "NO TRADE"