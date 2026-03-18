"""Tests for MetricsTrackerTool — adoption metric computation and risk flags."""

from src.models import (
    AdoptionMetrics, Industry, Maturity, OrgProfile, PersonaState,
    PersonaType, SimulationState, Sponsorship, TurnRecord,
)
from src.tools.metrics_tracker import MetricsTrackerTool


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


def _make_state(
    personas: dict[PersonaType, PersonaState] | None = None,
    week: int = 5,
    **kwargs,
) -> SimulationState:
    state = SimulationState(org_profile=_make_profile(), current_week=week, **kwargs)
    if personas:
        state.persona_states = personas
    return state


def _uniform_personas(adoption: float = 0.5, sentiment: float = 0.5, **kwargs) -> dict[PersonaType, PersonaState]:
    return {
        pt: PersonaState(
            persona_type=pt,
            adoption_likelihood=adoption,
            sentiment_score=sentiment,
            **kwargs,
        )
        for pt in PersonaType
    }


tracker = MetricsTrackerTool()


# ── Empty state ───────────────────────────────────────────────

def test_empty_personas():
    state = _make_state(personas={})
    metrics = tracker.compute_metrics(state)
    assert metrics.overall_adoption_pct == 0.0
    assert metrics.login_rate == 0.0
    assert "No persona data available" in metrics.risk_flags


# ── Adoption aggregation ─────────────────────────────────────

def test_overall_adoption_is_average():
    personas = {
        PersonaType.SKEPTICAL_IC: PersonaState(persona_type=PersonaType.SKEPTICAL_IC, adoption_likelihood=0.2),
        PersonaType.ENTHUSIASTIC_CHAMPION: PersonaState(persona_type=PersonaType.ENTHUSIASTIC_CHAMPION, adoption_likelihood=0.8),
    }
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert abs(metrics.overall_adoption_pct - 0.5) < 0.01


def test_uniform_adoption():
    state = _make_state(personas=_uniform_personas(adoption=0.6))
    metrics = tracker.compute_metrics(state)
    assert abs(metrics.overall_adoption_pct - 0.6) < 0.01


# ── Derived metrics formulas ─────────────────────────────────

def test_login_rate_formula():
    """login_rate = min(1.0, adoption * 1.2 + 0.05)"""
    state = _make_state(personas=_uniform_personas(adoption=0.5))
    metrics = tracker.compute_metrics(state)
    expected = min(1.0, 0.5 * 1.2 + 0.05)  # 0.65
    assert abs(metrics.login_rate - round(expected, 3)) < 0.01


def test_login_rate_capped_at_one():
    """High adoption should cap login_rate at 1.0."""
    state = _make_state(personas=_uniform_personas(adoption=0.9))
    metrics = tracker.compute_metrics(state)
    assert metrics.login_rate == 1.0


def test_feature_depth_formula():
    """feature_depth = adoption * 0.7"""
    state = _make_state(personas=_uniform_personas(adoption=0.6))
    metrics = tracker.compute_metrics(state)
    expected = 0.6 * 0.7  # 0.42
    assert abs(metrics.feature_usage_depth - round(expected, 3)) < 0.01


def test_nps_proxy_formula():
    """nps_proxy = (avg_sentiment - 0.5) * 2"""
    state = _make_state(personas=_uniform_personas(sentiment=0.75))
    metrics = tracker.compute_metrics(state)
    expected = (0.75 - 0.5) * 2  # 0.5
    assert abs(metrics.nps_proxy - round(expected, 3)) < 0.01


def test_nps_proxy_neutral():
    """Sentiment 0.5 → NPS 0."""
    state = _make_state(personas=_uniform_personas(sentiment=0.5))
    metrics = tracker.compute_metrics(state)
    assert abs(metrics.nps_proxy) < 0.01


def test_nps_proxy_negative():
    """Low sentiment → negative NPS."""
    state = _make_state(personas=_uniform_personas(sentiment=0.2))
    metrics = tracker.compute_metrics(state)
    assert metrics.nps_proxy < 0


# ── Budget remaining ─────────────────────────────────────────

def test_budget_remaining():
    state = _make_state(personas=_uniform_personas(), week=10)
    metrics = tracker.compute_metrics(state)
    assert metrics.budget_remaining_weeks == 14  # 24 - 10


# ── Risk flags ────────────────────────────────────────────────

def test_critical_sentiment_flag():
    """Sentiment below 0.25 triggers CRITICAL flag."""
    personas = {
        PersonaType.SKEPTICAL_IC: PersonaState(
            persona_type=PersonaType.SKEPTICAL_IC,
            sentiment_score=0.2,
        ),
    }
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert any("CRITICAL" in f and "skeptical_ic" in f for f in metrics.risk_flags)


def test_warning_sentiment_flag():
    """Sentiment below 0.35 but above 0.25 triggers WARNING."""
    personas = {
        PersonaType.SKEPTICAL_IC: PersonaState(
            persona_type=PersonaType.SKEPTICAL_IC,
            sentiment_score=0.30,
        ),
    }
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert any("WARNING" in f and "declining" in f for f in metrics.risk_flags)


def test_cognitive_load_warning():
    """Cognitive load > 0.8 triggers capacity warning."""
    personas = {
        PersonaType.OVERWHELMED_IT_ADMIN: PersonaState(
            persona_type=PersonaType.OVERWHELMED_IT_ADMIN,
            cognitive_load=0.85,
        ),
    }
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert any("capacity" in f for f in metrics.risk_flags)


def test_low_trust_warning():
    """Trust below 0.3 triggers performative engagement warning."""
    personas = {
        PersonaType.RISK_AVERSE_VP: PersonaState(
            persona_type=PersonaType.RISK_AVERSE_VP,
            trust_level=0.2,
        ),
    }
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert any("trust" in f.lower() for f in metrics.risk_flags)


def test_no_flags_healthy_state():
    """Healthy personas should produce no risk flags."""
    personas = _uniform_personas(adoption=0.6, sentiment=0.7, trust_level=0.7, cognitive_load=0.3)
    state = _make_state(personas=personas)
    metrics = tracker.compute_metrics(state)
    assert len(metrics.risk_flags) == 0


def test_declining_adoption_trend():
    """Adoption drop > 3% triggers declining trend flag."""
    personas = _uniform_personas(adoption=0.4, sentiment=0.5)
    prev_metrics = AdoptionMetrics(
        week=4, overall_adoption_pct=0.5, login_rate=0.6,
        feature_usage_depth=0.35, nps_proxy=0.0, budget_remaining_weeks=20,
    )
    state = _make_state(personas=personas, week=5)
    state.turn_history = [
        TurnRecord(
            week=4,
            orchestrator_reasoning="test",
            interventions=[],
            persona_responses={},
            adoption_metrics=prev_metrics,
        ),
        TurnRecord(
            week=5,
            orchestrator_reasoning="test",
            interventions=[],
            persona_responses={},
            adoption_metrics=prev_metrics,  # need 2 turns for trend detection
        ),
    ]
    metrics = tracker.compute_metrics(state)
    assert any("declining" in f.lower() for f in metrics.risk_flags)


def test_critical_budget_warning():
    """Low budget + low adoption triggers critical budget warning."""
    personas = _uniform_personas(adoption=0.2, sentiment=0.5)
    state = _make_state(personas=personas, week=21)  # 3 weeks remaining, 24 budget
    metrics = tracker.compute_metrics(state)
    # 0.2 < 0.7 * 0.7 = 0.49, and 3 weeks remaining ≤ 4
    assert any("weeks remaining" in f for f in metrics.risk_flags)
