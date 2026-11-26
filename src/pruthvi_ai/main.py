
"""Safe startup diagnostics. This command does not start a trading loop."""
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
        "system_status": "INITIALIZED",
    }


def run_diagnostic():
    """Check local persistence without fetching market data or placing orders."""
    from .database import PRUTHVIDatabase
    from .orchestrator import MasterOrchestrator

    db = PRUTHVIDatabase()
    orchestrator = MasterOrchestrator(database=db)

    return {
        **run_system_check(),
        "database": db.health_check(),
        "orchestrator": orchestrator.health_check(),
        "market_data": "PENDING — no verified live OHLCV feed configured",
        "automatic_execution": "DISABLED",
    }


if __name__ == "__main__":
    for key, value in run_diagnostic().items():
        print(f"{key}: {value}")
