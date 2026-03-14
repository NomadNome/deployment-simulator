"""Event Catalog — organizational disruptions that perturb the simulation."""

from __future__ import annotations

import random

from src.models import EventType, PersonaType, SimulationEvent


# ── Event Templates ────────────────────────────────────────────

EVENT_CATALOG: list[dict] = [
    {
        "event_type": EventType.REORG,
        "probability_per_week": 0.04,
        "earliest_week": 3,
        "affected_personas": [PersonaType.RISK_AVERSE_VP, PersonaType.ENTHUSIASTIC_CHAMPION],
        "sentiment_modifiers": {
            PersonaType.RISK_AVERSE_VP: -0.15,
            PersonaType.ENTHUSIASTIC_CHAMPION: -0.08,
            PersonaType.OVERWHELMED_IT_ADMIN: -0.05,
        },
        "description": (
            "A reorganization has been announced. The VP's reporting structure is "
            "changing, and the champion's team is being merged with another group. "
            "Priorities are being reassessed across the organization."
        ),
    },
    {
        "event_type": EventType.COMPETING_TOOL,
        "probability_per_week": 0.05,
        "earliest_week": 4,
        "affected_personas": [PersonaType.SKEPTICAL_IC, PersonaType.RISK_AVERSE_VP],
        "sentiment_modifiers": {
            PersonaType.SKEPTICAL_IC: -0.10,
            PersonaType.RISK_AVERSE_VP: -0.08,
            PersonaType.ENTHUSIASTIC_CHAMPION: -0.05,
        },
        "description": (
            "A competitor's AI tool was demoed at an internal tech talk. Several "
            "engineers are now asking why the organization chose this tool instead. "
            "The VP wants to understand the competitive landscape."
        ),
    },
    {
        "event_type": EventType.SPONSOR_DEPARTURE,
        "probability_per_week": 0.02,
        "earliest_week": 6,
        "affected_personas": [PersonaType.RISK_AVERSE_VP, PersonaType.ENTHUSIASTIC_CHAMPION],
        "sentiment_modifiers": {
            PersonaType.RISK_AVERSE_VP: -0.20,
            PersonaType.ENTHUSIASTIC_CHAMPION: -0.12,
            PersonaType.OVERWHELMED_IT_ADMIN: -0.05,
            PersonaType.SKEPTICAL_IC: -0.03,
        },
        "description": (
            "The executive sponsor who originally championed the AI initiative "
            "has left the company. The replacement has not yet been briefed and "
            "has their own priorities. Budget continuity is uncertain."
        ),
    },
    {
        "event_type": EventType.BUDGET_FREEZE,
        "probability_per_week": 0.03,
        "earliest_week": 5,
        "affected_personas": [PersonaType.RISK_AVERSE_VP],
        "sentiment_modifiers": {
            PersonaType.RISK_AVERSE_VP: -0.18,
            PersonaType.ENTHUSIASTIC_CHAMPION: -0.06,
        },
        "description": (
            "A company-wide budget freeze has been announced for the current "
            "quarter. All discretionary spending is under review. The VP is "
            "being asked to justify every line item, including this initiative."
        ),
    },
    {
        "event_type": EventType.POSITIVE_PRESS,
        "probability_per_week": 0.06,
        "earliest_week": 2,
        "affected_personas": [PersonaType.RISK_AVERSE_VP, PersonaType.SKEPTICAL_IC],
        "sentiment_modifiers": {
            PersonaType.RISK_AVERSE_VP: 0.08,
            PersonaType.SKEPTICAL_IC: 0.04,
            PersonaType.ENTHUSIASTIC_CHAMPION: 0.05,
        },
        "description": (
            "A major industry publication featured a case study of a competitor "
            "successfully deploying a similar AI tool, reporting 30% productivity "
            "gains. The article is circulating internally."
        ),
    },
    {
        "event_type": EventType.TEAM_EXPANSION,
        "probability_per_week": 0.03,
        "earliest_week": 4,
        "affected_personas": [PersonaType.OVERWHELMED_IT_ADMIN, PersonaType.SKEPTICAL_IC],
        "sentiment_modifiers": {
            PersonaType.OVERWHELMED_IT_ADMIN: 0.10,
            PersonaType.SKEPTICAL_IC: 0.03,
        },
        "description": (
            "The IT team has hired two new members, reducing the backlog pressure. "
            "The admin has more bandwidth for integration work. A new engineer has "
            "also joined the IC's team and is enthusiastic about the AI tool."
        ),
    },
    {
        "event_type": EventType.SECURITY_INCIDENT,
        "probability_per_week": 0.02,
        "earliest_week": 3,
        "affected_personas": [
            PersonaType.OVERWHELMED_IT_ADMIN,
            PersonaType.RISK_AVERSE_VP,
            PersonaType.SKEPTICAL_IC,
        ],
        "sentiment_modifiers": {
            PersonaType.OVERWHELMED_IT_ADMIN: -0.15,
            PersonaType.RISK_AVERSE_VP: -0.12,
            PersonaType.SKEPTICAL_IC: -0.08,
            PersonaType.ENTHUSIASTIC_CHAMPION: -0.04,
        },
        "description": (
            "A security vulnerability was disclosed in a third-party AI tool "
            "(not yours, but similar category). IT is now conducting an emergency "
            "review of all AI tools in the environment. The VP is asking for a "
            "security posture briefing."
        ),
    },
]


def roll_events(
    week: int,
    seed: int | None = None,
    forced_events: list[dict] | None = None,
) -> list[SimulationEvent]:
    """Roll for random events this week. Returns list of events that fire.

    Args:
        week: Current simulation week.
        seed: Random seed for deterministic event rolls.
        forced_events: List of dicts with 'event_type' and 'week' keys to force-fire.
    """
    if seed is not None:
        random.seed(seed + week)

    fired = []

    # Check forced events first
    if forced_events:
        for forced in forced_events:
            if forced.get("week") == week:
                event_type = EventType(forced["event_type"])
                template = _get_template_by_type(event_type)
                if template:
                    fired.append(SimulationEvent(
                        event_type=template["event_type"],
                        trigger_week=week,
                        affected_personas=template["affected_personas"],
                        sentiment_modifiers=template["sentiment_modifiers"],
                        description=template["description"],
                    ))

    # Random event rolls
    for template in EVENT_CATALOG:
        if week < template["earliest_week"]:
            continue
        if random.random() < template["probability_per_week"]:
            # Don't duplicate a forced event
            if not any(e.event_type == template["event_type"] for e in fired):
                fired.append(SimulationEvent(
                    event_type=template["event_type"],
                    trigger_week=week,
                    affected_personas=template["affected_personas"],
                    sentiment_modifiers=template["sentiment_modifiers"],
                    description=template["description"],
                ))

    return fired


def _get_template_by_type(event_type: EventType) -> dict | None:
    """Look up an event template by its EventType."""
    for template in EVENT_CATALOG:
        if template["event_type"] == event_type:
            return template
    return None
