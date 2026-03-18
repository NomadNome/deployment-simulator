"""Tests for experiment runner data transforms — scenario matrix and profile application."""

from src.models import Industry, Maturity, OrgProfile, Sponsorship
from src.simulation.experiment_runner import (
    ExperimentConfig,
    generate_scenario_matrix,
    apply_scenario_to_profile,
)


# ── Helpers ───────────────────────────────────────────────────

def _make_profile(**kwargs) -> OrgProfile:
    defaults = dict(
        org_name="Test Corp",
        industry=Industry.TECHNOLOGY,
        team_size=100,
        technical_maturity=Maturity.MEDIUM,
        executive_sponsorship=Sponsorship.MODERATE,
    )
    defaults.update(kwargs)
    return OrgProfile(**defaults)


def _make_config(sweeps: dict | None = None, **kwargs) -> ExperimentConfig:
    return ExperimentConfig(
        name="test_experiment",
        description="Test",
        base_profile=_make_profile(),
        sweeps=sweeps or {},
        **kwargs,
    )


# ── generate_scenario_matrix ─────────────────────────────────

def test_empty_sweeps():
    config = _make_config(sweeps={})
    scenarios = generate_scenario_matrix(config)
    assert scenarios == [{}]


def test_single_variable():
    config = _make_config(sweeps={"team_size": [50, 100, 500]})
    scenarios = generate_scenario_matrix(config)
    assert len(scenarios) == 3
    assert scenarios[0] == {"team_size": 50}
    assert scenarios[1] == {"team_size": 100}
    assert scenarios[2] == {"team_size": 500}


def test_two_variables_cartesian():
    config = _make_config(sweeps={
        "executive_sponsorship": ["weak", "strong"],
        "team_size": [50, 200],
    })
    scenarios = generate_scenario_matrix(config)
    assert len(scenarios) == 4  # 2 × 2


def test_three_variables_cartesian():
    config = _make_config(sweeps={
        "executive_sponsorship": ["weak", "moderate", "strong"],
        "technical_maturity": ["low", "high"],
        "team_size": [50, 500],
    })
    scenarios = generate_scenario_matrix(config)
    assert len(scenarios) == 12  # 3 × 2 × 2


def test_single_value_sweep():
    config = _make_config(sweeps={"team_size": [100]})
    scenarios = generate_scenario_matrix(config)
    assert len(scenarios) == 1
    assert scenarios[0] == {"team_size": 100}


def test_scenario_keys_match_sweep_keys():
    config = _make_config(sweeps={
        "executive_sponsorship": ["weak", "strong"],
        "team_size": [50, 200],
    })
    scenarios = generate_scenario_matrix(config)
    for s in scenarios:
        assert set(s.keys()) == {"executive_sponsorship", "team_size"}


# ── apply_scenario_to_profile ────────────────────────────────

def test_apply_team_size():
    profile = _make_profile(team_size=100)
    result = apply_scenario_to_profile(profile, {"team_size": 500})
    assert result.team_size == 500
    assert result.org_name == "Test Corp"  # unchanged


def test_apply_does_not_mutate_original():
    profile = _make_profile(team_size=100)
    apply_scenario_to_profile(profile, {"team_size": 500})
    assert profile.team_size == 100  # original unchanged


def test_apply_sponsorship_enum_conversion():
    profile = _make_profile()
    result = apply_scenario_to_profile(profile, {"executive_sponsorship": "strong"})
    assert result.executive_sponsorship == Sponsorship.STRONG


def test_apply_maturity_enum_conversion():
    profile = _make_profile()
    result = apply_scenario_to_profile(profile, {"technical_maturity": "high"})
    assert result.technical_maturity == Maturity.HIGH


def test_apply_industry_enum_conversion():
    profile = _make_profile()
    result = apply_scenario_to_profile(profile, {"industry": "healthcare"})
    assert result.industry == Industry.HEALTHCARE


def test_apply_ignores_unknown_fields():
    """Fields not in OrgProfile should be silently ignored."""
    profile = _make_profile()
    result = apply_scenario_to_profile(profile, {"disruption_level": "multi", "team_size": 200})
    assert result.team_size == 200
    # disruption_level is not an OrgProfile field, so it's ignored


def test_apply_empty_scenario():
    profile = _make_profile(team_size=100)
    result = apply_scenario_to_profile(profile, {})
    assert result.team_size == 100


def test_apply_multiple_fields():
    profile = _make_profile()
    result = apply_scenario_to_profile(profile, {
        "team_size": 2000,
        "executive_sponsorship": "weak",
        "technical_maturity": "low",
    })
    assert result.team_size == 2000
    assert result.executive_sponsorship == Sponsorship.WEAK
    assert result.technical_maturity == Maturity.LOW
