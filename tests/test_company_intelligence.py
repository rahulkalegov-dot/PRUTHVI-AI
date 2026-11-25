from pruthvi_ai.company_intelligence import (
    create_company_profile,
    validate_profile,
)


def test_create_company():
    profile = create_company_profile(
        "RELIANCE",
        "Reliance Industries"
    )

    assert profile.symbol == "RELIANCE"
    assert profile.decision == "NO TRADE"


def test_profile_validation():
    profile = create_company_profile(
        "TCS",
        "Tata Consultancy Services"
    )

    assert validate_profile(profile) is True


def test_invalid_decision():
    profile = create_company_profile(
        "INFY",
        "Infosys"
    )

    profile.decision = "UNKNOWN"

    assert validate_profile(profile) is False


def test_empty_symbol():
    try:
        create_company_profile("", "Test Company")
        assert False
    except ValueError:
        assert True