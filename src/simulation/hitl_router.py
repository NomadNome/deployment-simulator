"""Human-in-the-Loop Escalation Router — confidence-based intervention routing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.models import Intervention, PersonaType

console = Console()


class RoutingLane(str, Enum):
    AUTO_EXECUTE = "auto_execute"
    HUMAN_REVIEW = "human_review"
    ESCALATE = "escalate"


class HumanDecision(str, Enum):
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"
    AUTO = "auto"  # no human involved


class HITLMode(str, Enum):
    AUTOPILOT = "autopilot"   # all interventions auto-execute (batch/experiment mode)
    GUIDED = "guided"         # review + escalate items pause for human input
    DEMO = "demo"             # every intervention pauses (interview walkthrough mode)


@dataclass
class RoutingDecision:
    """A single routing decision in the audit trail."""
    timestamp: str
    week: int
    intervention_type: str
    target_persona: str
    confidence_score: float
    routing_lane: str
    human_decision: str
    human_modification: str | None = None
    orchestrator_reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "week": self.week,
            "intervention_type": self.intervention_type,
            "target_persona": self.target_persona,
            "confidence_score": self.confidence_score,
            "routing_lane": self.routing_lane,
            "human_decision": self.human_decision,
            "human_modification": self.human_modification,
            "orchestrator_reasoning": self.orchestrator_reasoning,
        }


# ── Confidence Thresholds ──────────────────────────────────────

AUTO_EXECUTE_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.50  # between 0.50 and 0.80 → human review


def classify_confidence(score: float) -> RoutingLane:
    """Classify an intervention's confidence score into a routing lane."""
    if score >= AUTO_EXECUTE_THRESHOLD:
        return RoutingLane.AUTO_EXECUTE
    elif score >= REVIEW_THRESHOLD:
        return RoutingLane.HUMAN_REVIEW
    else:
        return RoutingLane.ESCALATE


# ── Confidence Estimation ──────────────────────────────────────

def estimate_confidence(
    intervention: Intervention,
    week: int,
    recent_override_rate: float = 0.0,
    active_events: int = 0,
) -> float:
    """
    Estimate the orchestrator's confidence in an intervention.

    In the full implementation, this would be extracted from the orchestrator's
    reasoning output. For the scaffolding, we use heuristic signals:
    - Escalation-type interventions are inherently lower confidence
    - More active disruption events reduce confidence
    - High recent override rates reduce confidence (calibration signal)
    - Later weeks with low adoption reduce confidence
    """
    base_confidence = 0.75

    # Intervention type modifiers
    type_modifiers = {
        "executive_briefing": 0.0,
        "workshop": 0.05,
        "one_on_one": 0.05,
        "async_communication": 0.10,
        "tool_demo": 0.05,
        "peer_learning_cohort": 0.05,
        "quick_win_session": 0.08,
        "escalation": -0.20,        # escalations are inherently uncertain
        "office_hours": 0.10,
        "gamified_challenge": 0.0,
    }
    base_confidence += type_modifiers.get(intervention.intervention_type.value, 0.0)

    # Active events reduce confidence (more chaos = less certainty)
    base_confidence -= active_events * 0.08

    # High override rate is a calibration signal
    base_confidence -= recent_override_rate * 0.15

    # Target persona modifiers (VP and IT interventions are higher risk)
    if intervention.target_persona == PersonaType.RISK_AVERSE_VP:
        base_confidence -= 0.05
    elif intervention.target_persona == PersonaType.OVERWHELMED_IT_ADMIN:
        base_confidence -= 0.03

    return max(0.05, min(0.99, base_confidence))


# ── HITL Router ────────────────────────────────────────────────

class HITLRouter:
    """Routes interventions through confidence-based lanes with optional human approval."""

    def __init__(self, mode: HITLMode = HITLMode.AUTOPILOT):
        self.mode = mode
        self.audit_trail: list[RoutingDecision] = []
        self._override_count = 0
        self._total_routed = 0

    @property
    def override_rate(self) -> float:
        if self._total_routed == 0:
            return 0.0
        return self._override_count / self._total_routed

    def route(
        self,
        intervention: Intervention,
        confidence: float,
        week: int,
        orchestrator_reasoning: str = "",
    ) -> tuple[bool, Intervention]:
        """
        Route an intervention through the HITL system.

        Returns:
            tuple of (approved: bool, intervention: Intervention)
            The intervention may be modified by human input.
        """
        lane = classify_confidence(confidence)
        self._total_routed += 1

        # Determine if we need human input
        needs_human = False
        if self.mode == HITLMode.DEMO:
            needs_human = True
        elif self.mode == HITLMode.GUIDED:
            needs_human = lane in (RoutingLane.HUMAN_REVIEW, RoutingLane.ESCALATE)

        if needs_human:
            decision, modified_intervention = self._prompt_human(
                intervention, confidence, lane, orchestrator_reasoning
            )
        else:
            decision = HumanDecision.AUTO
            modified_intervention = intervention

        # Track overrides
        if decision in (HumanDecision.MODIFY, HumanDecision.REJECT):
            self._override_count += 1

        # Record audit trail
        self.audit_trail.append(RoutingDecision(
            timestamp=datetime.now().isoformat(),
            week=week,
            intervention_type=intervention.intervention_type.value,
            target_persona=intervention.target_persona.value,
            confidence_score=round(confidence, 3),
            routing_lane=lane.value,
            human_decision=decision.value,
            human_modification=(
                modified_intervention.content if decision == HumanDecision.MODIFY
                else None
            ),
            orchestrator_reasoning=orchestrator_reasoning[:200],
        ))

        approved = decision != HumanDecision.REJECT
        return approved, modified_intervention

    def _prompt_human(
        self,
        intervention: Intervention,
        confidence: float,
        lane: RoutingLane,
        reasoning: str,
    ) -> tuple[HumanDecision, Intervention]:
        """Present an intervention to the human operator for review."""
        lane_color = {
            RoutingLane.AUTO_EXECUTE: "green",
            RoutingLane.HUMAN_REVIEW: "yellow",
            RoutingLane.ESCALATE: "red",
        }[lane]

        console.print(Panel(
            f"[bold]Intervention:[/bold] {intervention.intervention_type.value}\n"
            f"[bold]Target:[/bold] {intervention.target_persona.value}\n"
            f"[bold]Confidence:[/bold] [{lane_color}]{confidence:.0%}[/{lane_color}] "
            f"→ [{lane_color}]{lane.value}[/{lane_color}]\n\n"
            f"[bold]Content:[/bold]\n{intervention.content}\n\n"
            f"[bold]Rationale:[/bold]\n{intervention.rationale}\n\n"
            f"[dim]Orchestrator reasoning: {reasoning[:300]}...[/dim]",
            title=f"HITL Review Required",
            border_style=lane_color,
        ))

        choice = Prompt.ask(
            "Decision",
            choices=["approve", "modify", "reject"],
            default="approve",
        )

        if choice == "modify":
            new_content = Prompt.ask("Enter modified intervention content")
            modified = intervention.model_copy(update={"content": new_content})
            return HumanDecision.MODIFY, modified
        elif choice == "reject":
            return HumanDecision.REJECT, intervention
        else:
            return HumanDecision.APPROVE, intervention

    def save_audit_trail(self, path: str) -> None:
        """Save the full audit trail to JSON."""
        with open(path, "w") as f:
            json.dump(
                [d.to_dict() for d in self.audit_trail],
                f, indent=2,
            )

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for the audit trail."""
        if not self.audit_trail:
            return {"total": 0}

        lane_counts = {}
        decision_counts = {}
        for d in self.audit_trail:
            lane_counts[d.routing_lane] = lane_counts.get(d.routing_lane, 0) + 1
            decision_counts[d.human_decision] = decision_counts.get(d.human_decision, 0) + 1

        return {
            "total_routed": self._total_routed,
            "override_rate": round(self.override_rate, 3),
            "lane_distribution": lane_counts,
            "decision_distribution": decision_counts,
            "avg_confidence": round(
                sum(d.confidence_score for d in self.audit_trail) / len(self.audit_trail), 3
            ),
        }
