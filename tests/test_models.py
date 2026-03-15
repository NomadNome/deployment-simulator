"""Tests for data models."""

from src.models import (
    AdoptionMetrics, Industry, Intervention, InterventionType, Maturity,
    OrgProfile, PersonaState, PersonaType, SimulationEvent, SimulationOutcome,
    SimulationState, Sponsorship, TurnRecord,
)


def test_org_profile_creation():
    profile = OrgProfile(
        org_name="Test Corp",
        industry=Industry.TECHNOLOGY,
        team_size=100,
        technical_maturity=Maturity.MEDIUM,
        executive_sponsorship=Sponsorship.MODERATE,
    )
    assert profile.org_name == "Test Corp"
    assert profile.budget_weeks == 24  # default
    assert profile.success_threshold == 0.70  # default


def test_org_profile_validation():
    """Team size must be between 10 and 10000."""
    import pytest
    with pytest.raises(Exception):
        OrgProfile(
            org_name="Tiny",
            industry=Industry.TECHNOLOGY,
            team_size=5,
            technical_maturity=Maturity.LOW,
            executive_sponsorship=Sponsorship.WEAK,
        )


def test_persona_state_defaults():
    state = PersonaState(persona_type=PersonaType.SKEPTICAL_IC)
    assert state.sentiment_score == 0.5
    assert state.adoption_likelihood == 0.3
    assert state.trust_level == 0.5
    assert state.cognitive_load == 0.3


def test_persona_state_apply_sentiment_modifier():
    state = PersonaState(persona_type=PersonaType.SKEPTICAL_IC, sentiment_score=0.5)
    state.apply_sentiment_modifier(0.2)
    assert state.sentiment_score == 0.7
    # Adoption tracks sentiment with lag (0.6x)
    assert abs(state.adoption_likelihood - 0.42) < 0.01


def test_persona_state_clamps_to_bounds():
    state = PersonaState(persona_type=PersonaType.ENTHUSIASTIC_CHAMPION, sentiment_score=0.9)
    state.apply_sentiment_modifier(0.5)
    assert state.sentiment_score == 1.0  # clamped


def test_intervention_serialization():
    iv = Intervention(
        intervention_type=InterventionType.WORKSHOP,
        target_persona=PersonaType.SKEPTICAL_IC,
        content="Test workshop",
        rationale="Testing",
    )
    data = iv.model_dump()
    assert data["intervention_type"] == "workshop"
    assert data["target_persona"] == "skeptical_ic"


def test_simulation_state_initialization():
    profile = OrgProfile(
        org_name="Test",
        industry=Industry.TECHNOLOGY,
        team_size=100,
        technical_maturity=Maturity.MEDIUM,
        executive_sponsorship=Sponsorship.MODERATE,
    )
    state = SimulationState(org_profile=profile)
    assert state.current_week == 0
    assert state.outcome == SimulationOutcome.IN_PROGRESS
    assert len(state.turn_history) == 0


def test_all_enums_have_values():
    """Verify all enum types have expected members."""
    assert len(PersonaType) == 4
    assert len(InterventionType) == 10
    assert len(Industry) == 6
    assert len(Maturity) == 3
    assert len(Sponsorship) == 3
    assert len(SimulationOutcome) == 4
