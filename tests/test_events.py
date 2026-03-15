"""Tests for event catalog and rolling."""

from src.models import EventType, PersonaType
from src.simulation.events import EVENT_CATALOG, roll_events, _get_template_by_type


def test_event_catalog_count():
    assert len(EVENT_CATALOG) == 7


def test_all_events_have_required_fields():
    for event in EVENT_CATALOG:
        assert "event_type" in event
        assert "probability_per_week" in event
        assert "earliest_week" in event
        assert "affected_personas" in event
        assert "sentiment_modifiers" in event
        assert "description" in event


def test_roll_events_deterministic():
    """Same seed should produce same events."""
    events1 = roll_events(week=5, seed=42)
    events2 = roll_events(week=5, seed=42)
    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1.event_type == e2.event_type


def test_roll_events_respects_earliest_week():
    """Events shouldn't fire before their earliest_week."""
    for week in range(1, 3):
        events = roll_events(week=week, seed=42)
        for event in events:
            template = _get_template_by_type(event.event_type)
            assert week >= template["earliest_week"]


def test_forced_events():
    """Forced events should fire on the specified week."""
    events = roll_events(
        week=3,
        seed=42,
        forced_events=[{"event_type": "reorg", "week": 3}],
    )
    types = [e.event_type for e in events]
    assert EventType.REORG in types


def test_forced_events_wrong_week():
    """Forced events should NOT fire on wrong week."""
    events = roll_events(
        week=5,
        seed=42,
        forced_events=[{"event_type": "reorg", "week": 3}],
    )
    forced_reorgs = [e for e in events if e.event_type == EventType.REORG and e.trigger_week == 3]
    assert len(forced_reorgs) == 0


def test_forced_events_no_duplicates():
    """If a forced event fires, the random roll shouldn't duplicate it."""
    events = roll_events(
        week=10,
        seed=42,
        forced_events=[{"event_type": "positive_press", "week": 10}],
    )
    press_events = [e for e in events if e.event_type == EventType.POSITIVE_PRESS]
    assert len(press_events) <= 1


def test_get_template_by_type():
    template = _get_template_by_type(EventType.SPONSOR_DEPARTURE)
    assert template is not None
    assert template["event_type"] == EventType.SPONSOR_DEPARTURE
    assert PersonaType.RISK_AVERSE_VP in template["sentiment_modifiers"]


def test_get_template_nonexistent():
    # EventType has 7 members, all should have templates
    for et in EventType:
        assert _get_template_by_type(et) is not None
