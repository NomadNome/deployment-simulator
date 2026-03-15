"""Tests for HITL router and confidence routing."""

from src.models import Intervention, InterventionType, PersonaType
from src.simulation.hitl_router import (
    AUTO_EXECUTE_THRESHOLD, HITLMode, HITLRouter, HumanDecision,
    RoutingLane, classify_confidence, estimate_confidence,
)


def _make_intervention(itype=InterventionType.WORKSHOP, target=PersonaType.SKEPTICAL_IC):
    return Intervention(
        intervention_type=itype,
        target_persona=target,
        content="Test",
        rationale="Testing",
    )


def test_classify_confidence_auto():
    assert classify_confidence(0.85) == RoutingLane.AUTO_EXECUTE
    assert classify_confidence(0.80) == RoutingLane.AUTO_EXECUTE


def test_classify_confidence_review():
    assert classify_confidence(0.65) == RoutingLane.HUMAN_REVIEW
    assert classify_confidence(0.50) == RoutingLane.HUMAN_REVIEW


def test_classify_confidence_escalate():
    assert classify_confidence(0.49) == RoutingLane.ESCALATE
    assert classify_confidence(0.10) == RoutingLane.ESCALATE


def test_estimate_confidence_baseline():
    iv = _make_intervention()
    conf = estimate_confidence(iv, week=1)
    assert 0.05 <= conf <= 0.99


def test_estimate_confidence_escalation_penalty():
    """Escalation interventions should have lower confidence."""
    normal = estimate_confidence(_make_intervention(InterventionType.WORKSHOP), week=1)
    escalation = estimate_confidence(_make_intervention(InterventionType.ESCALATION), week=1)
    assert escalation < normal


def test_estimate_confidence_event_penalty():
    """Active events should reduce confidence."""
    no_events = estimate_confidence(_make_intervention(), week=5, active_events=0)
    with_events = estimate_confidence(_make_intervention(), week=5, active_events=2)
    assert with_events < no_events


def test_estimate_confidence_vp_penalty():
    """VP-targeted interventions should have slightly lower confidence."""
    ic = estimate_confidence(_make_intervention(target=PersonaType.SKEPTICAL_IC), week=1)
    vp = estimate_confidence(_make_intervention(target=PersonaType.RISK_AVERSE_VP), week=1)
    assert vp < ic


def test_router_autopilot_auto_executes():
    router = HITLRouter(mode=HITLMode.AUTOPILOT)
    iv = _make_intervention()
    approved, routed = router.route(iv, confidence=0.90, week=1)
    assert approved is True
    assert len(router.audit_trail) == 1
    assert router.audit_trail[0].human_decision == "auto"


def test_router_autopilot_even_low_confidence():
    """In autopilot, even low confidence auto-executes."""
    router = HITLRouter(mode=HITLMode.AUTOPILOT)
    iv = _make_intervention()
    approved, _ = router.route(iv, confidence=0.30, week=1)
    assert approved is True


def test_router_override_rate():
    router = HITLRouter(mode=HITLMode.AUTOPILOT)
    for _ in range(5):
        router.route(_make_intervention(), confidence=0.85, week=1)
    assert router.override_rate == 0.0


def test_router_audit_trail_records_correctly():
    router = HITLRouter(mode=HITLMode.AUTOPILOT)
    iv = _make_intervention(InterventionType.EXECUTIVE_BRIEFING, PersonaType.RISK_AVERSE_VP)
    router.route(iv, confidence=0.72, week=3, orchestrator_reasoning="Test reasoning")

    entry = router.audit_trail[0]
    assert entry.week == 3
    assert entry.intervention_type == "executive_briefing"
    assert entry.target_persona == "risk_averse_vp"
    assert entry.confidence_score == 0.72
    assert entry.routing_lane == "human_review"


def test_router_summary():
    router = HITLRouter(mode=HITLMode.AUTOPILOT)
    for _ in range(3):
        router.route(_make_intervention(), confidence=0.85, week=1)
    for _ in range(2):
        router.route(_make_intervention(), confidence=0.65, week=2)

    summary = router.get_summary()
    assert summary["total_routed"] == 5
    assert summary["override_rate"] == 0.0
    assert "auto_execute" in summary["lane_distribution"]
