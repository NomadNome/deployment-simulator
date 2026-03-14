"""Replanner Tool — generates revised rollout plans when the current strategy fails."""

from __future__ import annotations

from anthropic import Anthropic
from dotenv import load_dotenv

from src.models import SimulationState

load_dotenv()

ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250929"


class ReplannerTool:
    """Generates a revised deployment plan when the orchestrator detects failure."""

    def __init__(self, model: str = ORCHESTRATOR_MODEL):
        self.client = Anthropic()
        self.model = model

    def generate(
        self,
        failure_diagnosis: str,
        constraints: str,
        state: SimulationState,
    ) -> str:
        """Generate a revised rollout plan based on what went wrong."""
        # Summarize what's been tried
        intervention_summary = []
        for turn in state.turn_history[-6:]:  # last 6 weeks
            for iv in turn.interventions:
                intervention_summary.append(
                    f"  Week {turn.week}: {iv.intervention_type.value} → {iv.target_persona.value}"
                )

        history_text = "\n".join(intervention_summary) if intervention_summary else "  (no interventions yet)"

        # Summarize current persona health
        persona_summary = []
        for ptype, pstate in state.persona_states.items():
            # Orchestrator gets approximate signals, not exact scores
            if pstate.sentiment_score > 0.6:
                status = "engaged"
            elif pstate.sentiment_score > 0.4:
                status = "neutral"
            elif pstate.sentiment_score > 0.25:
                status = "at risk"
            else:
                status = "disengaged"
            persona_summary.append(f"  {ptype.value}: {status}")

        persona_text = "\n".join(persona_summary)
        weeks_left = state.org_profile.budget_weeks - state.current_week

        prompt = f"""You are an expert deployment strategist. The current rollout plan is failing and needs revision.

## Failure Diagnosis
{failure_diagnosis}

## Constraints
{constraints or "None specified"}

## Current State
- Week: {state.current_week} of {state.org_profile.budget_weeks}
- Weeks remaining: {weeks_left}
- Current adoption: {state.metrics.overall_adoption_pct:.1%} (target: {state.org_profile.success_threshold:.0%})

## Persona Status
{persona_text}

## Recent Intervention History
{history_text}

## Organization Context
- {state.org_profile.org_name} ({state.org_profile.industry.value})
- Team size: {state.org_profile.team_size}
- Technical maturity: {state.org_profile.technical_maturity.value}
- Executive sponsorship: {state.org_profile.executive_sponsorship.value}

Generate a revised 4-week plan that addresses the diagnosed failure. Be specific about:
1. Which personas to prioritize and why
2. What intervention types to use (different from what hasn't worked)
3. The sequence and dependencies between interventions
4. What signals you'll watch to know if the new plan is working

Keep the plan concise and actionable — no more than 300 words."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
