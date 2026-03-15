"""Tests for flywheel metrics and Pilot Scorecard."""

from src.models import OrgProfile, PersonaState, PersonaType, SimulationState, Industry, Maturity, Sponsorship
from src.simulation.flywheel_metrics import (
    FlywheelMetricsTracker, HealthStatus, TrendDirection,
)


def _make_state(adoption=0.5, sentiment=0.5, trust=0.5, week=4):
    profile = OrgProfile(
        org_name="Test", industry=Industry.TECHNOLOGY, team_size=100,
        technical_maturity=Maturity.MEDIUM, executive_sponsorship=Sponsorship.MODERATE,
        budget_weeks=24,
    )
    personas = {
        PersonaType.SKEPTICAL_IC: PersonaState(
            persona_type=PersonaType.SKEPTICAL_IC,
            sentiment_score=sentiment, adoption_likelihood=adoption, trust_level=trust,
        ),
        PersonaType.ENTHUSIASTIC_CHAMPION: PersonaState(
            persona_type=PersonaType.ENTHUSIASTIC_CHAMPION,
            sentiment_score=min(1.0, sentiment + 0.2), adoption_likelihood=min(1.0, adoption + 0.3), trust_level=trust,
        ),
        PersonaType.RISK_AVERSE_VP: PersonaState(
            persona_type=PersonaType.RISK_AVERSE_VP,
            sentiment_score=sentiment, adoption_likelihood=adoption * 0.8, trust_level=trust,
        ),
        PersonaType.OVERWHELMED_IT_ADMIN: PersonaState(
            persona_type=PersonaType.OVERWHELMED_IT_ADMIN,
            sentiment_score=sentiment * 0.8, adoption_likelihood=adoption * 0.5, trust_level=trust * 0.8,
        ),
    }
    state = SimulationState(org_profile=profile, persona_states=personas, current_week=week)
    return state


def test_compute_returns_flywheel_metrics():
    tracker = FlywheelMetricsTracker()
    state = _make_state()
    metrics = tracker.compute(state)
    assert metrics.week == 4
    assert 0 <= metrics.activation_rate <= 1
    assert 0 <= metrics.weekly_engaged_users <= 1
    assert 0 <= metrics.completion_rate <= 1
    assert metrics.cycle_time_delta <= 0  # negative = improvement


def test_compute_stores_history():
    tracker = FlywheelMetricsTracker()
    state = _make_state(week=1)
    tracker.compute(state)
    state.current_week = 2
    tracker.compute(state)
    assert len(tracker.history) == 2


def test_override_rate_passthrough():
    tracker = FlywheelMetricsTracker()
    state = _make_state()
    metrics = tracker.compute(state, override_rate=0.25)
    assert metrics.override_rate == 0.25


def test_risk_flags_critical_sentiment():
    tracker = FlywheelMetricsTracker()
    state = _make_state(sentiment=0.2, week=5)
    metrics = tracker.compute(state)
    critical_flags = [f for f in metrics.risk_flags if "CRITICAL" in f]
    assert len(critical_flags) > 0


def test_risk_flags_late_low_adoption():
    tracker = FlywheelMetricsTracker()
    state = _make_state(adoption=0.2, week=20)
    metrics = tracker.compute(state)
    critical_flags = [f for f in metrics.risk_flags if "remaining" in f]
    assert len(critical_flags) > 0


def test_trend_detection():
    tracker = FlywheelMetricsTracker()
    # Week 1: low adoption
    state1 = _make_state(adoption=0.3, week=1)
    tracker.compute(state1)
    # Week 2: higher adoption
    state2 = _make_state(adoption=0.5, week=2)
    tracker.compute(state2)

    trend = tracker.get_trend("overall_adoption_pct")
    assert trend == TrendDirection.UP


def test_trend_flat():
    tracker = FlywheelMetricsTracker()
    state1 = _make_state(adoption=0.5, week=1)
    tracker.compute(state1)
    state2 = _make_state(adoption=0.5, week=2)
    tracker.compute(state2)

    trend = tracker.get_trend("overall_adoption_pct")
    assert trend == TrendDirection.FLAT


def test_scorecard_generation():
    tracker = FlywheelMetricsTracker()
    state = _make_state()
    tracker.compute(state)
    scorecard = tracker.generate_scorecard()
    assert len(scorecard) == 6  # 6 metrics
    names = [e.name for e in scorecard]
    assert "Activation Rate" in names
    assert "Overall Adoption" in names


def test_empty_personas():
    profile = OrgProfile(
        org_name="Empty", industry=Industry.TECHNOLOGY, team_size=100,
        technical_maturity=Maturity.MEDIUM, executive_sponsorship=Sponsorship.MODERATE,
    )
    state = SimulationState(org_profile=profile, persona_states={})
    tracker = FlywheelMetricsTracker()
    metrics = tracker.compute(state)
    assert metrics.overall_adoption_pct == 0.0
