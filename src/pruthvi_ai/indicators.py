import pandas as pd


def calculate_indicators(df):
    required = {"open", "high", "low", "close", "volume"}

    if not required.issubset(df.columns):
        raise ValueError("Missing required candle columns")

    if len(df) < 50:
        raise ValueError("At least 50 candles required")

    result = df.copy()

    close = result["close"]
    high = result["high"]
    low = result["low"]
    volume = result["volume"]

    if (close <= 0).any() or (volume < 0).any():
        raise ValueError("Invalid price or volume data")

    # Exponential moving averages
    result["EMA_9"] = close.ewm(
        span=9, adjust=False
    ).mean()

    result["EMA_21"] = close.ewm(
        span=21, adjust=False
    ).mean()

    result["EMA_50"] = close.ewm(
        span=50, adjust=False
    ).mean()

    # Relative Strength Index
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/14, adjust=False, min_periods=14
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/14, adjust=False, min_periods=14
    ).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))

    result["RSI_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    result["MACD"] = ema12 - ema26
    result["MACD_SIGNAL"] = result["MACD"].ewm(
        span=9, adjust=False
    ).mean()

    # Average True Range
    previous_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - previous_close).abs(),
        (low - previous_close).abs()
    ], axis=1).max(axis=1)

    result["ATR_14"] = tr.ewm(
        alpha=1/14, adjust=False, min_periods=14
    ).mean()

    # Volume average
    result["VOLUME_SMA_20"] = volume.rolling(20).mean()

    return result