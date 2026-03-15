"""Tests for persona initialization and state updates (no LLM calls)."""

from src.agents.persona import initialize_persona_states, _intervention_effect, PersonaAgent
from src.models import (
    Industry, Intervention, InterventionType, Maturity,
    OrgProfile, PersonaState, PersonaType, Sponsorship,
)


def _make_profile(**kwargs):
    defaults = dict(
        org_name="Test", industry=Industry.TECHNOLOGY, team_size=100,
        technical_maturity=Maturity.MEDIUM, executive_sponsorship=Sponsorship.MODERATE,
    )
    defaults.update(kwargs)
    return OrgProfile(**defaults)


def test_initialize_creates_all_personas():
    profile = _make_profile()
    states = initialize_persona_states(profile)
    assert len(states) == 4
    assert PersonaType.SKEPTICAL_IC in states
    assert PersonaType.ENTHUSIASTIC_CHAMPION in states
    assert PersonaType.RISK_AVERSE_VP in states
    assert PersonaType.OVERWHELMED_IT_ADMIN in states


def test_champion_starts_highest_sentiment():
    profile = _make_profile()
    states = initialize_persona_states(profile)
    champion = states[PersonaType.ENTHUSIASTIC_CHAMPION]
    ic = states[PersonaType.SKEPTICAL_IC]
    assert champion.sentiment_score > ic.sentiment_score


def test_strong_sponsorship_boosts_states():
    weak = initialize_persona_states(_make_profile(executive_sponsorship=Sponsorship.WEAK))
    strong = initialize_persona_states(_make_profile(executive_sponsorship=Sponsorship.STRONG))
    # Strong sponsorship should produce higher VP sentiment
    assert strong[PersonaType.RISK_AVERSE_VP].sentiment_score > weak[PersonaType.RISK_AVERSE_VP].sentiment_score


def test_high_maturity_boosts_states():
    low = initialize_persona_states(_make_profile(technical_maturity=Maturity.LOW))
    high = initialize_persona_states(_make_profile(technical_maturity=Maturity.HIGH))
    # High maturity should produce higher IC sentiment
    assert high[PersonaType.SKEPTICAL_IC].sentiment_score >= low[PersonaType.SKEPTICAL_IC].sentiment_score


def test_influence_network():
    """Personas should have influenced_by relationships."""
    profile = _make_profile()
    states = initialize_persona_states(profile)
    # IC is influenced by champion
    assert PersonaType.ENTHUSIASTIC_CHAMPION in states[PersonaType.SKEPTICAL_IC].influenced_by


def test_intervention_effect_lookup():
    """Tool demo should have positive effect on skeptical IC."""
    effect = _intervention_effect(PersonaType.SKEPTICAL_IC, InterventionType.TOOL_DEMO)
    assert effect > 0


def test_intervention_effect_negative():
    """Workshops have negative effect on overwhelmed IT admin."""
    effect = _intervention_effect(PersonaType.OVERWHELMED_IT_ADMIN, InterventionType.WORKSHOP)
    assert effect < 0


def test_intervention_effect_escalation_on_ic():
    """Escalation should be negative for skeptical IC."""
    effect = _intervention_effect(PersonaType.SKEPTICAL_IC, InterventionType.ESCALATION)
    assert effect < 0


def test_update_state_positive_effect():
    state = PersonaState(
        persona_type=PersonaType.SKEPTICAL_IC,
        sentiment_score=0.5, trust_level=0.5, cognitive_load=0.3,
    )
    intervention = Intervention(
        intervention_type=InterventionType.TOOL_DEMO,
        target_persona=PersonaType.SKEPTICAL_IC,
        content="Demo", rationale="Test",
    )
    agent = PersonaAgent(PersonaType.SKEPTICAL_IC)
    effect = agent.update_state(state, intervention, {PersonaType.SKEPTICAL_IC: state})
    assert effect > 0
    assert state.trust_level > 0.5  # trust should grow


def test_update_state_high_cognitive_load_dampens():
    """High cognitive load should dampen intervention effect."""
    normal_state = PersonaState(
        persona_type=PersonaType.SKEPTICAL_IC,
        sentiment_score=0.5, trust_level=0.5, cognitive_load=0.3,
    )
    overloaded_state = PersonaState(
        persona_type=PersonaType.SKEPTICAL_IC,
        sentiment_score=0.5, trust_level=0.5, cognitive_load=0.9,
    )
    iv = Intervention(
        intervention_type=InterventionType.TOOL_DEMO,
        target_persona=PersonaType.SKEPTICAL_IC,
        content="Demo", rationale="Test",
    )
    agent = PersonaAgent(PersonaType.SKEPTICAL_IC)
    effect_normal = agent.update_state(normal_state, iv, {PersonaType.SKEPTICAL_IC: normal_state})
    effect_overloaded = agent.update_state(overloaded_state, iv, {PersonaType.SKEPTICAL_IC: overloaded_state})
    assert abs(effect_overloaded) < abs(effect_normal)


def test_update_state_cognitive_load_decays():
    state = PersonaState(
        persona_type=PersonaType.SKEPTICAL_IC,
        sentiment_score=0.5, cognitive_load=0.5,
    )
    iv = Intervention(
        intervention_type=InterventionType.ASYNC_COMMUNICATION,
        target_persona=PersonaType.SKEPTICAL_IC,
        content="Update", rationale="Test",
    )
    agent = PersonaAgent(PersonaType.SKEPTICAL_IC)
    agent.update_state(state, iv, {PersonaType.SKEPTICAL_IC: state})
    assert state.cognitive_load < 0.5  # should decay
