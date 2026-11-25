from . import config
from .safety import safety_status


def run_system_check():
    status = safety_status()

    return {
        "project": config.PROJECT_NAME,
        "version": config.VERSION,
        "exchange": config.EXCHANGE,
        "market": config.MARKET_INDEX,
        "expected_stocks": config.EXPECTED_STOCK_COUNT,
        "paper_only": status["paper_only"],
        "live_trading": status["live_trading"],
        "execution_enabled": status["execution_enabled"],
        "system_status": "INITIALIZED"
    }


if __name__ == "__main__":
    for key, value in run_system_check().items():
        print(f"{key}: {value}")