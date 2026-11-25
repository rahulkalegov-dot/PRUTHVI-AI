from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyProfile:
    symbol: str
    company_name: str

    business: Optional[str] = None
    segments: list = field(default_factory=list)
    subsidiaries: list = field(default_factory=list)

    financial_health: Optional[str] = None
    company_news: list = field(default_factory=list)
    corporate_events: list = field(default_factory=list)

    sector: Optional[str] = None
    competitors: list = field(default_factory=list)

    technical_analysis: Optional[str] = None
    market_context: Optional[str] = None

    risks: list = field(default_factory=list)
    opportunities: list = field(default_factory=list)

    decision: str = "NO TRADE"
    reasoning: str = "Insufficient verified information"


def create_company_profile(symbol, company_name):
    if not symbol or not company_name:
        raise ValueError("Company information is required")

    return CompanyProfile(
        symbol=symbol.strip().upper(),
        company_name=company_name.strip()
    )


def validate_profile(profile):
    if not profile.symbol:
        return False

    if not profile.company_name:
        return False

    if profile.decision not in (
        "BUY", "SELL", "HOLD", "NO TRADE"
    ):
        return False

    return True