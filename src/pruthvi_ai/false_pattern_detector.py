from dataclasses import dataclass


@dataclass
class PatternCheck:
    pattern: str
    status: str
    reason: str


def check_breakout(
    breakout_direction,
    close_price,
    breakout_level,
    volume,
    average_volume
):
    if min(close_price, breakout_level, volume, average_volume) < 0:
        return PatternCheck(
            "BREAKOUT", "REJECTED", "Invalid data"
        )

    if close_price <= 0 or breakout_level <= 0:
        return PatternCheck(
            "BREAKOUT", "REJECTED", "Invalid price"
        )

    if average_volume <= 0:
        return PatternCheck(
            "BREAKOUT", "REJECTED", "Invalid average volume"
        )

    if breakout_direction == "UP":
        if close_price <= breakout_level:
            return PatternCheck(
                "BREAKOUT", "FALSE", "Price did not close above resistance"
            )

    elif breakout_direction == "DOWN":
        if close_price >= breakout_level:
            return PatternCheck(
                "BREAKOUT", "FALSE", "Price did not close below support"
            )
    else:
        return PatternCheck(
            "BREAKOUT", "REJECTED", "Invalid direction"
        )

    if volume < average_volume:
        return PatternCheck(
            "BREAKOUT", "WEAK", "Volume confirmation missing"
        )

    return PatternCheck(
        "BREAKOUT", "POTENTIAL", "Price and volume conditions passed"
    )