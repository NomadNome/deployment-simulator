"""Strands-based Persona Agent — drop-in replacement using Strands Agent."""

from __future__ import annotations

from strands import Agent

from src.agents.persona import (
    PERSONA_PROMPTS,
    PersonaAgent,
    _intervention_effect,
)
from src.agents.provider import get_strands_model
from src.models import (
    Intervention, InterventionType, OrgProfile, PersonaState, PersonaType,
)


class StrandsPersonaAgent:
    """A stakeholder persona using Strands SDK.

    Drop-in replacement for PersonaAgent. The update_state method is
    inherited as-is since it's pure Python (no LLM calls).
    """

    def __init__(self, persona_type: PersonaType):
        self.persona_type = persona_type
        self._model = get_strands_model("persona")

    def respond(
        self,
        intervention: Intervention,
        state: PersonaState,
        org_profile: OrgProfile,
    ) -> str:
        """Generate a response to an orchestrator intervention."""
        system_prompt = PERSONA_PROMPTS[self.persona_type].format(
            org_name=org_profile.org_name,
            industry=org_profile.industry.value,
            ai_tool=org_profile.ai_tool_type,
            sentiment=int(state.sentiment_score * 10),
            trust=int(state.trust_level * 10),
            load=int(state.cognitive_load * 10),
        )

        # Create a fresh agent per call (system prompt changes with state)
        agent = Agent(
            model=self._model,
            system_prompt=system_prompt,
        )

        user_message = (
            f"The deployment team has reached out to you with the following "
            f"{intervention.intervention_type.value.replace('_', ' ')}:\n\n"
            f"{intervention.content}"
        )

        result = agent(user_message)
        return str(result)

    def update_state(
        self,
        state: PersonaState,
        intervention: Intervention,
        all_states: dict[PersonaType, PersonaState],
    ) -> float:
        """Update persona hidden state. Pure Python — no LLM, no sandbox."""
        effect = _intervention_effect(self.persona_type, intervention.intervention_type)

        if state.cognitive_load > 0.7:
            effect *= 0.3
        effect *= (0.5 + state.trust_level * 0.5)

        for influencer_type in state.influenced_by:
            if influencer_type in all_states:
                influencer = all_states[influencer_type]
                if influencer.sentiment_score > 0.6:
                    effect += 0.02
                elif influencer.sentiment_score < 0.3:
                    effect -= 0.02

        state.apply_sentiment_modifier(effect)

        if effect > 0:
            state.trust_level = min(1.0, state.trust_level + 0.03)
        elif effect < -0.05:
            state.trust_level = max(0.0, state.trust_level - 0.05)

        state.cognitive_load = max(0.0, state.cognitive_load - 0.02)

        return effect
