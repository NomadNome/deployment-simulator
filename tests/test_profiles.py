"""Tests for organization profiles."""

from src.simulation.profiles import PROFILES, ACME_FINANCIAL, MERIDIAN_HEALTHCARE, NOVA_TECH
from src.models import Industry, Maturity, Sponsorship


def test_three_profiles_exist():
    assert len(PROFILES) == 3
    assert "acme_financial" in PROFILES
    assert "meridian_healthcare" in PROFILES
    assert "nova_tech" in PROFILES


def test_acme_financial():
    p = ACME_FINANCIAL
    assert p.industry == Industry.FINANCIAL_SERVICES
    assert p.technical_maturity == Maturity.HIGH
    assert p.executive_sponsorship == Sponsorship.STRONG
    assert p.team_size == 200


def test_meridian_healthcare():
    p = MERIDIAN_HEALTHCARE
    assert p.industry == Industry.HEALTHCARE
    assert p.technical_maturity == Maturity.LOW
    assert p.executive_sponsorship == Sponsorship.WEAK
    assert p.budget_weeks == 20
    assert p.success_threshold == 0.60
    assert len(p.competing_priorities) == 3


def test_nova_tech():
    p = NOVA_TECH
    assert p.industry == Industry.TECHNOLOGY
    assert p.technical_maturity == Maturity.MEDIUM
    assert p.executive_sponsorship == Sponsorship.MODERATE
    assert p.budget_weeks == 24


def test_profiles_are_valid():
    """All profiles should serialize without error."""
    for name, profile in PROFILES.items():
        data = profile.model_dump()
        assert data["org_name"]
        assert data["team_size"] >= 10
