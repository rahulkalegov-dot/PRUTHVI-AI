import pandas as pd
import pytest

from pruthvi_ai.universe import get_nifty50


def test_nifty50_returns_50_companies(monkeypatch):
    data = pd.DataFrame({
        "Symbol": [f"STOCK{i}" for i in range(50)],
        "Company Name": [f"Company {i}" for i in range(50)],
    })

    monkeypatch.setattr(
        pd,
        "read_csv",
        lambda *args, **kwargs: data.copy()
    )

    stocks = get_nifty50()

    assert len(stocks) == 50
    assert stocks[0]["Symbol"] == "STOCK0"


def test_universe_rejects_wrong_count(monkeypatch):
    data = pd.DataFrame({
        "Symbol": ["RELIANCE"],
        "Company Name": ["Reliance Industries"],
    })

    monkeypatch.setattr(
        pd,
        "read_csv",
        lambda *args, **kwargs: data.copy()
    )

    with pytest.raises(RuntimeError):
        get_nifty50()