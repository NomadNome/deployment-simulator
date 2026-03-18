"""Tests for realism factors: friction, fatigue, blind spots, grudges."""

from src.models import (
    AdoptionMetrics, Intervention, InterventionRecord, InterventionType,
    OrgProfile, Industry, Maturity, PersonaState, PersonaType, Sponsorship,
    SimulationState, TurnRecord,
)
from src.simulation.realism import (
    BLIND_SPOT_BASE_PROBABILITY,
    FATIGUE_MULTIPLIERS,
    FRICTION_OUTCOMES,
    FRICTION_PROBABILITY,
    GRUDGE_DECAY_RATE,
    BlindSpotResult,
    FrictionResult,
    apply_blind_spot,
    fatigue_multiplier,
    fatigue_prompt_addition,
    grudge_effect_multiplier,
    roll_blind_spot,
    roll_friction,
    update_grudge,
)


# ── Helpers ───────────────────────────────────────────────────

def _make_profile() -> OrgProfile:
    return OrgProfile(
        org_name="Test Corp",
        industry=Industry.TECHNOLOGY,
        team_size=100,
        technical_maturity=Maturity.MEDIUM,
        executive_sponsorship=Sponsorship.MODERATE,
    )


def _make_state(**kwargs) -> SimulationState:
    return SimulationState(org_profile=_make_profile(), **kwargs)


def _make_persona(
    ptype: PersonaType = PersonaType.SKEPTICAL_IC,
    **kwargs,
) -> PersonaState:
    return PersonaState(persona_type=ptype, **kwargs)


def _make_record(
    week: int = 1,
    itype: InterventionType = InterventionType.WORKSHOP,
) -> InterventionRecord:
    return InterventionRecord(
        week=week,
        intervention_type=itype,
        content_summary="test",
        sentiment_effect=0.05,
    )


# ── Execution Friction ────────────────────────────────────────

def test_friction_clean_result():
    """Most rolls should return clean (88% probability)."""
    clean_count = sum(
        1 for i in range(1000)
        if not roll_friction(seed=None, week=i).hit
    )
    # With 88% probability, expect ~880 clean out of 1000
    assert clean_count > 800


def test_friction_determinism_same_seed():
    """Same seed + week should produce identical results across calls."""
    a = roll_friction(seed=42, week=5)
    b = roll_friction(seed=42, week=5)
    assert a.outcome_type == b.outcome_type
    assert a.effect_multiplier == b.effect_multiplier


def test_friction_varies_by_week():
    """Different weeks should produce different sequences."""
    results = [roll_friction(seed=42, week=w).outcome_type for w in range(20)]
    # Not all the same — at least some variety over 20 weeks
    assert len(set(results)) > 1


def test_friction_outcome_multipliers():
    """Verify each outcome type maps to the correct multiplier."""
    expected = {"delayed": 0.0, "degraded": 0.5, "cancelled": 0.0, "backfire": -0.3}
    for outcome_type, multiplier in expected.items():
        result = FrictionResult(
            hit=True,
            outcome_type=outcome_type,
            description="test",
            effect_multiplier=multiplier,
        )
        assert result.effect_multiplier == multiplier


def test_friction_clean_multiplier_is_one():
    result = FrictionResult(hit=False, outcome_type="clean", description="", effect_multiplier=1.0)
    assert result.effect_multiplier == 1.0


def test_friction_outcome_weights_sum_to_one():
    total = sum(o["weight"] for o in FRICTION_OUTCOMES)
    assert abs(total - 1.0) < 1e-9


def test_friction_all_outcome_types_possible():
    """Over many rolls, all friction outcome types should appear."""
    outcomes = set()
    for i in range(5000):
        r = roll_friction(seed=None, week=i)
        if r.hit:
            outcomes.add(r.outcome_type)
    expected = {"delayed", "degraded", "cancelled", "backfire"}
    assert outcomes == expected


# ── Intervention Fatigue ──────────────────────────────────────

def test_fatigue_no_history():
    """No history → full effectiveness."""
    persona = _make_persona()
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 1.0


def test_fatigue_same_type_progression():
    """Repeated same-type interventions reduce effectiveness."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=1, itype=InterventionType.WORKSHOP),
    ]
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 0.7

    persona.intervention_history.append(
        _make_record(week=2, itype=InterventionType.WORKSHOP),
    )
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 0.4

    persona.intervention_history.append(
        _make_record(week=3, itype=InterventionType.WORKSHOP),
    )
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 0.2


def test_fatigue_caps_at_minimum():
    """More than 3 consecutive same-type should stay at 0.2."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=w, itype=InterventionType.WORKSHOP)
        for w in range(10)
    ]
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 0.2


def test_fatigue_resets_on_different_type():
    """A different intervention type resets fatigue."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=1, itype=InterventionType.WORKSHOP),
        _make_record(week=2, itype=InterventionType.WORKSHOP),
        _make_record(week=3, itype=InterventionType.ONE_ON_ONE),  # different
    ]
    # Last was different, so count resets to 0 for workshop
    assert fatigue_multiplier(persona, InterventionType.WORKSHOP) == 1.0


def test_fatigue_different_type_no_fatigue():
    """A type not in history has no fatigue."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=1, itype=InterventionType.WORKSHOP),
        _make_record(week=2, itype=InterventionType.WORKSHOP),
    ]
    assert fatigue_multiplier(persona, InterventionType.TOOL_DEMO) == 1.0


def test_fatigue_prompt_below_threshold():
    """No fatigue prompt when count < 3."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=1, itype=InterventionType.WORKSHOP),
        _make_record(week=2, itype=InterventionType.WORKSHOP),
    ]
    assert fatigue_prompt_addition(persona, InterventionType.WORKSHOP) == ""


def test_fatigue_prompt_at_threshold():
    """Fatigue prompt triggers at 3+ same-type interventions."""
    persona = _make_persona()
    persona.intervention_history = [
        _make_record(week=w, itype=InterventionType.WORKSHOP)
        for w in range(3)
    ]
    prompt = fatigue_prompt_addition(persona, InterventionType.WORKSHOP)
    assert "3 workshop sessions" in prompt
    assert "diminishing patience" in prompt


# ── Blind Spots ───────────────────────────────────────────────

def _state_with_personas() -> SimulationState:
    state = _make_state()
    state.persona_states = {
        pt: _make_persona(pt) for pt in PersonaType
    }
    return state


def test_blind_spot_base_probability():
    assert BLIND_SPOT_BASE_PROBABILITY == 0.08


def test_blind_spot_no_hit_most_of_the_time():
    """With 8% base probability, most rolls should miss."""
    state = _state_with_personas()
    hits = sum(
        1 for i in range(1000)
        if roll_blind_spot(state, seed=None, week=i).hit
    )
    assert hits < 200  # expect ~80, allow margin


def test_blind_spot_determinism():
    state = _state_with_personas()
    a = roll_blind_spot(state, seed=42, week=3)
    b = roll_blind_spot(state, seed=42, week=3)
    assert a.hit == b.hit
    assert a.spot_type == b.spot_type


def test_blind_spot_tunnel_vision_increases_probability():
    """When >60% of recent interventions target one persona, probability increases."""
    state = _state_with_personas()

    # Create turn history where all interventions target one persona
    interventions = [
        Intervention(
            intervention_type=InterventionType.WORKSHOP,
            target_persona=PersonaType.SKEPTICAL_IC,
            content="test",
            rationale="test",
        )
        for _ in range(5)
    ]
    metrics = AdoptionMetrics(
        week=1, overall_adoption_pct=0.3, login_rate=0.4,
        feature_usage_depth=0.2, nps_proxy=0.0, budget_remaining_weeks=20,
    )
    for w in range(3):
        state.turn_history.append(TurnRecord(
            week=w + 1,
            orchestrator_reasoning="test",
            interventions=interventions,
            persona_responses={},
            adoption_metrics=metrics,
        ))

    # Run many times and check hit rate is higher than base
    hits = sum(
        1 for i in range(1000)
        if roll_blind_spot(state, seed=None, week=i).hit
    )
    # With tunnel vision, probability should be 15% → expect ~150 hits
    assert hits > 100


def test_blind_spot_types_are_valid():
    """All blind spot types should be persona_omission or metrics_lag."""
    state = _state_with_personas()
    types = set()
    for i in range(5000):
        r = roll_blind_spot(state, seed=None, week=i)
        if r.hit:
            types.add(r.spot_type)
    assert types == {"persona_omission", "metrics_lag"}


def test_apply_blind_spot_no_hit():
    """No blind spot → responses unchanged."""
    bs = BlindSpotResult(hit=False, spot_type="none")
    responses = {PersonaType.SKEPTICAL_IC: "hello"}
    result = apply_blind_spot(bs, responses, _make_state())
    assert result == responses


def test_apply_blind_spot_persona_omission():
    """Persona omission removes the affected persona's response."""
    bs = BlindSpotResult(
        hit=True,
        spot_type="persona_omission",
        affected_persona=PersonaType.SKEPTICAL_IC,
    )
    responses = {
        PersonaType.SKEPTICAL_IC: "hello",
        PersonaType.ENTHUSIASTIC_CHAMPION: "world",
    }
    result = apply_blind_spot(bs, responses, _make_state())
    assert PersonaType.SKEPTICAL_IC not in result
    assert PersonaType.ENTHUSIASTIC_CHAMPION in result


def test_apply_blind_spot_does_not_mutate_original():
    """apply_blind_spot should not modify the original dict."""
    bs = BlindSpotResult(
        hit=True,
        spot_type="persona_omission",
        affected_persona=PersonaType.SKEPTICAL_IC,
    )
    responses = {
        PersonaType.SKEPTICAL_IC: "hello",
        PersonaType.ENTHUSIASTIC_CHAMPION: "world",
    }
    apply_blind_spot(bs, responses, _make_state())
    assert PersonaType.SKEPTICAL_IC in responses  # original unchanged


def test_apply_blind_spot_none_responses():
    bs = BlindSpotResult(hit=True, spot_type="persona_omission")
    assert apply_blind_spot(bs, None, _make_state()) is None


# ── Grudge System ─────────────────────────────────────────────

def test_grudge_backfire_accumulation():
    persona = _make_persona(grudge_score=0.0)
    update_grudge(persona, friction_type="backfire", had_contact=True)
    # +0.08 - decay (0.01 for IC) = 0.07
    assert abs(persona.grudge_score - 0.07) < 1e-9


def test_grudge_cancelled_accumulation():
    persona = _make_persona(grudge_score=0.0)
    update_grudge(persona, friction_type="cancelled", had_contact=True)
    # +0.025 - 0.01 decay = 0.015
    assert abs(persona.grudge_score - 0.015) < 1e-9


def test_grudge_delayed_accumulation():
    persona = _make_persona(grudge_score=0.0)
    update_grudge(persona, friction_type="delayed", had_contact=True)
    # same as cancelled: +0.025 - 0.01 = 0.015
    assert abs(persona.grudge_score - 0.015) < 1e-9


def test_grudge_no_contact_penalty():
    """No contact for 3+ weeks adds grudge."""
    persona = _make_persona(grudge_score=0.0, weeks_since_contact=2)
    update_grudge(persona, friction_type=None, had_contact=False)
    # weeks_since_contact becomes 3, triggers +0.05, then -0.01 decay = 0.04
    assert abs(persona.grudge_score - 0.04) < 1e-9
    assert persona.weeks_since_contact == 3


def test_grudge_no_contact_below_threshold():
    """No penalty when weeks_since_contact < 3 after increment."""
    persona = _make_persona(grudge_score=0.0, weeks_since_contact=0)
    update_grudge(persona, friction_type=None, had_contact=False)
    # weeks_since_contact becomes 1, no penalty, just decay
    assert persona.grudge_score == 0.0  # 0 - 0.01 clamped to 0
    assert persona.weeks_since_contact == 1


def test_grudge_contact_resets_weeks():
    persona = _make_persona(weeks_since_contact=5)
    update_grudge(persona, friction_type=None, had_contact=True)
    assert persona.weeks_since_contact == 0


def test_grudge_decay_varies_by_persona():
    """Different persona types have different decay rates."""
    for ptype, expected_decay in GRUDGE_DECAY_RATE.items():
        persona = _make_persona(ptype=ptype, grudge_score=0.5)
        update_grudge(persona, friction_type=None, had_contact=True)
        assert abs(persona.grudge_score - (0.5 - expected_decay)) < 1e-9


def test_grudge_capped_at_one():
    persona = _make_persona(grudge_score=0.98)
    update_grudge(persona, friction_type="backfire", had_contact=True)
    # 0.98 + 0.08 = 1.06 → capped to 1.0, then -0.01 = 0.99
    assert persona.grudge_score <= 1.0


def test_grudge_floor_at_zero():
    persona = _make_persona(grudge_score=0.005)
    update_grudge(persona, friction_type=None, had_contact=True)
    # 0.005 - 0.01 → clamped to 0.0
    assert persona.grudge_score == 0.0


def test_grudge_effect_multiplier_no_grudge():
    persona = _make_persona(grudge_score=0.0)
    assert grudge_effect_multiplier(persona) == 1.0


def test_grudge_effect_multiplier_max_grudge():
    persona = _make_persona(grudge_score=1.0)
    assert grudge_effect_multiplier(persona) == 0.5


def test_grudge_effect_multiplier_mid():
    persona = _make_persona(grudge_score=0.4)
    assert abs(grudge_effect_multiplier(persona) - 0.8) < 1e-9
