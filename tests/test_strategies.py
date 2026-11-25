from pruthvi_ai.strategies import (
    Strategy,
    get_strategy_registry,
    validate_signal,
    get_active_strategies,
)


def test_all_strategies_registered():
    assert len(Strategy) == 11


def test_registry_contains_all_strategies():
    assert len(get_strategy_registry()) == 11


def test_no_unvalidated_strategies_active():
    assert get_active_strategies() == []


def test_unvalidated_signal_rejected():
    signal = get_strategy_registry()[0]
    assert validate_signal(signal) is False