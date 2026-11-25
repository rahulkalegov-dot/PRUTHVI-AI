"""
PRUTHVI AI - Safety Guard
Real-money trading is permanently prohibited.
"""

from . import config


def trading_mode():
    return "PAPER_ONLY"


def real_trading_allowed():
    return False


def can_execute_paper_order(risk_approved=False):
    if not config.PAPER_ONLY:
        return False

    if config.LIVE_TRADING_ENABLED:
        return False

    if not config.RELEASE_APPROVED:
        return False

    if not config.AUTO_EXECUTION_ENABLED:
        return False

    if not risk_approved:
        return False

    return True


def safety_status():
    return {
        "paper_only": True,
        "live_trading": False,
        "release_approved": False,
        "risk_approval_required": True,
        "execution_enabled": False,
    }