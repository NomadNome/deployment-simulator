"""Core data models for the deployment simulator."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────

class Industry(str, Enum):
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    CONSULTING = "consulting"


class Maturity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sponsorship(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class PersonaType(str, Enum):
    SKEPTICAL_IC = "skeptical_ic"
    ENTHUSIASTIC_CHAMPION = "enthusiastic_champion"
    RISK_AVERSE_VP = "risk_averse_vp"
    OVERWHELMED_IT_ADMIN = "overwhelmed_it_admin"


class InterventionType(str, Enum):
    EXECUTIVE_BRIEFING = "executive_briefing"
    WORKSHOP = "workshop"
    ONE_ON_ONE = "one_on_one"
    ASYNC_COMMUNICATION = "async_communication"
    TOOL_DEMO = "tool_demo"
    PEER_LEARNING_COHORT = "peer_learning_cohort"
    QUICK_WIN_SESSION = "quick_win_session"
    ESCALATION = "escalation"
    OFFICE_HOURS = "office_hours"
    GAMIFIED_CHALLENGE = "gamified_challenge"


class EventType(str, Enum):
    REORG = "reorg"
    COMPETING_TOOL = "competing_tool"
    SPONSOR_DEPARTURE = "sponsor_departure"
    BUDGET_FREEZE = "budget_freeze"
    POSITIVE_PRESS = "positive_press"
    TEAM_EXPANSION = "team_expansion"
    SECURITY_INCIDENT = "security_incident"


class SimulationOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE_BUDGET = "failure_budget"
    FAILURE_TIMEOUT = "failure_timeout"
    IN_PROGRESS = "in_progress"


# ── Organization Profile ──────────────────────────────────────

class OrgProfile(BaseModel):
    """Input configuration for a simulation run."""
    org_name: str
    industry: Industry
    team_size: int = Field(ge=10, le=10000)
    technical_maturity: Maturity
    executive_sponsorship: Sponsorship
    ai_tool_type: str = "AI-powered code assistant"
    budget_weeks: int = Field(default=24, ge=4, le=52)
    success_threshold: float = Field(default=0.70, ge=0.1, le=1.0)
    competing_priorities: list[str] = Field(default_factory=list)


# ── Persona Hidden State ──────────────────────────────────────

class PersonaState(BaseModel):
    """Internal state for a persona agent. Not visible to the orchestrator."""
    persona_type: PersonaType
    sentiment_score: float = Field(default=0.5, ge=0.0, le=1.0)
    adoption_likelihood: float = Field(default=0.3, ge=0.0, le=1.0)
    trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    cognitive_load: float = Field(default=0.3, ge=0.0, le=1.0)
    grudge_score: float = Field(default=0.0, ge=0.0, le=1.0)
    weeks_since_contact: int = Field(default=0)
    influenced_by: list[PersonaType] = Field(default_factory=list)
    intervention_history: list[InterventionRecord] = Field(default_factory=list)

    def apply_sentiment_modifier(self, delta: float) -> None:
        self.sentiment_score = max(0.0, min(1.0, self.sentiment_score + delta))
        # Adoption likelihood loosely tracks sentiment with lag
        self.adoption_likelihood = max(0.0, min(1.0,
            self.adoption_likelihood + (delta * 0.6)
        ))


class InterventionRecord(BaseModel):
    """Record of an intervention received by a persona."""
    week: int
    intervention_type: InterventionType
    content_summary: str
    sentiment_effect: float  # observed change in sentiment


# ── Intervention ──────────────────────────────────────────────

class Intervention(BaseModel):
    """An action the orchestrator takes toward a persona."""
    intervention_type: InterventionType
    target_persona: PersonaType
    content: str  # the orchestrator's framing and message
    rationale: str  # why the orchestrator chose this intervention


# ── Simulation Event ──────────────────────────────────────────

class SimulationEvent(BaseModel):
    """A random organizational event that disrupts the simulation."""
    event_type: EventType
    trigger_week: int
    affected_personas: list[PersonaType]
    sentiment_modifiers: dict[PersonaType, float] = Field(default_factory=dict)
    description: str


# ── Turn Record ───────────────────────────────────────────────

class TurnRecord(BaseModel):
    """Complete record of a single simulation turn."""
    turn_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    week: int
    timestamp: datetime = Field(default_factory=datetime.now)
    orchestrator_reasoning: str
    interventions: list[Intervention]
    persona_responses: dict[PersonaType, str]
    adoption_metrics: AdoptionMetrics
    events_fired: list[SimulationEvent] = Field(default_factory=list)
    replan_triggered: bool = False


# ── Adoption Metrics ──────────────────────────────────────────

class AdoptionMetrics(BaseModel):
    """Global metrics visible to the orchestrator."""
    week: int
    overall_adoption_pct: float = Field(ge=0.0, le=1.0)
    login_rate: float = Field(ge=0.0, le=1.0)
    feature_usage_depth: float = Field(ge=0.0, le=1.0)
    nps_proxy: float = Field(ge=-1.0, le=1.0)
    risk_flags: list[str] = Field(default_factory=list)
    budget_remaining_weeks: int


# ── Simulation State ──────────────────────────────────────────

class SimulationState(BaseModel):
    """Complete simulation state at any point in time."""
    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    org_profile: OrgProfile
    current_week: int = 0
    persona_states: dict[PersonaType, PersonaState] = Field(default_factory=dict)
    metrics: AdoptionMetrics | None = None
    turn_history: list[TurnRecord] = Field(default_factory=list)
    outcome: SimulationOutcome = SimulationOutcome.IN_PROGRESS
    orchestrator_plan: str = ""  # current high-level plan text


# Fix forward reference
PersonaState.model_rebuild()
