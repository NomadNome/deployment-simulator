"""Realism Factors — execution friction, intervention fatigue, blind spots, grudges."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.models import Intervention, InterventionType, PersonaState, PersonaType, SimulationState


# ── Execution Friction ────────────────────────────────────────

FRICTION_PROBABILITY = 0.25

FRICTION_OUTCOMES = [
    {"type": "delayed", "weight": 0.40, "description": "Intervention delayed — rescheduled to next week"},
    {"type": "degraded", "weight": 0.35, "description": "Degraded — low attendance, technical issues, key person absent"},
    {"type": "cancelled", "weight": 0.15, "description": "Cancelled — competing meeting, priority shift"},
    {"type": "backfire", "weight": 0.10, "description": "Backfired — poorly timed, created frustration"},
]


@dataclass
class FrictionResult:
    """Result of a friction roll."""
    hit: bool
    outcome_type: str  # "clean", "delayed", "degraded", "cancelled", "backfire"
    description: str
    effect_multiplier: float  # 1.0 = normal, 0.5 = degraded, 0.0 = cancelled, -0.3 = backfire


def roll_friction(seed: int | None = None, week: int = 0) -> FrictionResult:
    """Roll for execution friction on a single intervention."""
    if seed is not None:
        random.seed(seed + week + random.randint(0, 9999))

    if random.random() > FRICTION_PROBABILITY:
        return FrictionResult(hit=False, outcome_type="clean", description="", effect_multiplier=1.0)

    # Weighted selection
    roll = random.random()
    cumulative = 0.0
    for outcome in FRICTION_OUTCOMES:
        cumulative += outcome["weight"]
        if roll <= cumulative:
            multipliers = {"delayed": 0.0, "degraded": 0.5, "cancelled": 0.0, "backfire": -0.3}
            return FrictionResult(
                hit=True,
                outcome_type=outcome["type"],
                description=outcome["description"],
                effect_multiplier=multipliers[outcome["type"]],
            )

    return FrictionResult(hit=False, outcome_type="clean", description="", effect_multiplier=1.0)


# ── Intervention Fatigue ──────────────────────────────────────

FATIGUE_MULTIPLIERS = [1.0, 0.7, 0.4, 0.2]


def fatigue_multiplier(persona_state: PersonaState, intervention_type: InterventionType) -> float:
    """Reduce effectiveness when the same intervention type is used repeatedly."""
    count = sum(
        1 for record in persona_state.intervention_history
        if record.intervention_type == intervention_type
    )
    return FATIGUE_MULTIPLIERS[min(count, len(FATIGUE_MULTIPLIERS) - 1)]


def fatigue_prompt_addition(persona_state: PersonaState, intervention_type: InterventionType) -> str:
    """Generate a fatigue signal for the persona's LLM prompt."""
    count = sum(
        1 for record in persona_state.intervention_history
        if record.intervention_type == intervention_type
    )
    if count >= 3:
        type_name = intervention_type.value.replace("_", " ")
        return (
            f"\n\nYou have received {count} {type_name} sessions and are growing "
            f"tired of this format. Your responses should reflect diminishing patience."
        )
    return ""


# ── Orchestrator Blind Spots ──────────────────────────────────

BLIND_SPOT_BASE_PROBABILITY = 0.15

BLIND_SPOT_TYPES = [
    {"type": "persona_omission", "weight": 0.40},
    {"type": "signal_misread", "weight": 0.35},
    {"type": "metrics_lag", "weight": 0.25},
]

OPTIMISTIC_SUMMARIES = [
    "Cautiously interested, asked clarifying questions about next steps.",
    "Seemed engaged, nodded along during the discussion.",
    "Brief but positive — mentioned they'd think about it.",
    "Acknowledged the value, asked about timeline.",
]


@dataclass
class BlindSpotResult:
    """Result of a blind spot roll."""
    hit: bool
    spot_type: str  # "none", "persona_omission", "signal_misread", "metrics_lag"
    affected_persona: PersonaType | None = None


def roll_blind_spot(
    state: SimulationState,
    seed: int | None = None,
    week: int = 0,
) -> BlindSpotResult:
    """Roll for orchestrator blind spot this turn."""
    if seed is not None:
        random.seed(seed + week * 7 + 31)

    # Increase probability if orchestrator has tunnel vision on one persona
    prob = BLIND_SPOT_BASE_PROBABILITY
    if state.turn_history:
        recent = state.turn_history[-3:]
        all_targets = [iv.target_persona for t in recent for iv in t.interventions]
        if all_targets:
            from collections import Counter
            counts = Counter(all_targets)
            most_common_pct = counts.most_common(1)[0][1] / len(all_targets)
            if most_common_pct > 0.6:
                prob = 0.25  # tunnel vision increases blind spot chance

    if random.random() > prob:
        return BlindSpotResult(hit=False, spot_type="none")

    # Weighted selection
    roll = random.random()
    cumulative = 0.0
    for spot in BLIND_SPOT_TYPES:
        cumulative += spot["weight"]
        if roll <= cumulative:
            # Pick affected persona (bias toward less-targeted personas)
            personas = list(state.persona_states.keys())
            affected = random.choice(personas)
            return BlindSpotResult(hit=True, spot_type=spot["type"], affected_persona=affected)

    return BlindSpotResult(hit=False, spot_type="none")


def apply_blind_spot(
    blind_spot: BlindSpotResult,
    persona_responses: dict[PersonaType, str] | None,
    state: SimulationState,
) -> dict[PersonaType, str] | None:
    """Apply blind spot to the persona responses or metrics before orchestrator sees them."""
    if not blind_spot.hit or not persona_responses:
        return persona_responses

    modified = dict(persona_responses)

    if blind_spot.spot_type == "persona_omission" and blind_spot.affected_persona in modified:
        del modified[blind_spot.affected_persona]

    elif blind_spot.spot_type == "signal_misread" and blind_spot.affected_persona in modified:
        modified[blind_spot.affected_persona] = random.choice(OPTIMISTIC_SUMMARIES)

    elif blind_spot.spot_type == "metrics_lag" and len(state.turn_history) >= 2:
        # Serve stale metrics — handled in controller by swapping state.metrics
        pass

    return modified


# ── Grudge System ─────────────────────────────────────────────

# Grudge accumulation rates by persona (IC holds grudges longest)
GRUDGE_DECAY_RATE = {
    PersonaType.SKEPTICAL_IC: 0.01,           # very slow forgiveness
    PersonaType.ENTHUSIASTIC_CHAMPION: 0.04,  # wants to believe
    PersonaType.RISK_AVERSE_VP: 0.02,         # professional but remembers
    PersonaType.OVERWHELMED_IT_ADMIN: 0.02,   # neutral
}


def update_grudge(persona_state: PersonaState, friction_type: str | None = None, had_contact: bool = True) -> None:
    """Update grudge score based on what happened this turn."""
    # Accumulate grudge
    if friction_type == "backfire":
        persona_state.grudge_score = min(1.0, persona_state.grudge_score + 0.15)
    elif friction_type in ("cancelled", "delayed"):
        persona_state.grudge_score = min(1.0, persona_state.grudge_score + 0.05)

    # No contact penalty
    if had_contact:
        persona_state.weeks_since_contact = 0
    else:
        persona_state.weeks_since_contact += 1
        if persona_state.weeks_since_contact >= 3:
            persona_state.grudge_score = min(1.0, persona_state.grudge_score + 0.10)

    # Natural decay
    decay = GRUDGE_DECAY_RATE.get(persona_state.persona_type, 0.02)
    persona_state.grudge_score = max(0.0, persona_state.grudge_score - decay)


def grudge_effect_multiplier(persona_state: PersonaState) -> float:
    """Grudge dampens positive intervention effects."""
    return 1.0 - persona_state.grudge_score * 0.5
