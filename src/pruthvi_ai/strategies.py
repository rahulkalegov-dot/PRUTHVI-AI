from dataclasses import dataclass
from enum import Enum


class Strategy(Enum):
    TREND_FOLLOWING = "Trend Following"
    BREAKOUT = "Breakout"
    PULLBACK = "Pullback"
    REVERSAL = "Reversal"
    VWAP = "VWAP"
    MOMENTUM = "Momentum"
    VOLUME_CONFIRMATION = "Volume Confirmation"
    MEAN_REVERSION = "Mean Reversion"
    CHART_PATTERN = "Chart Pattern"
    VOLATILITY = "Volatility Based"
    MULTI_TIMEFRAME = "Multi-Timeframe"


@dataclass
class StrategySignal:
    strategy: str
    decision: str = "NO TRADE"
    confidence: float = 0.0
    reasoning: str = "Not yet validated"
    validated: bool = False


def get_strategy_registry():
    return [
        StrategySignal(strategy=item.value)
        for item in Strategy
    ]


def validate_signal(signal):
    if signal.strategy not in [
        item.value for item in Strategy
    ]:
        return False

    if signal.decision not in (
        "BUY", "SELL", "HOLD", "NO TRADE"
    ):
        return False

    if not 0 <= signal.confidence <= 1:
        return False

    if not signal.validated:
        return False

    return True


def get_active_strategies():
    return []