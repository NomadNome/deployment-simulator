"""Sandboxed Persona — proxy that delegates LLM calls to a Docker sandbox."""

from __future__ import annotations

from src.agents.persona import _intervention_effect
from src.models import (
    Intervention, InterventionType, OrgProfile,
    PersonaState, PersonaType,
)
from src.sandbox.sandbox_manager import SandboxHandle, SandboxManager


class SandboxedPersonaAgent:
    """Persona proxy that forwards LLM calls to a Docker sandbox.

    State mutations (update_state) run locally on the host — never in the sandbox.
    Same interface as PersonaAgent — drop-in replacement.
    """

    def __init__(self, persona_type: PersonaType, handle: SandboxHandle, manager: SandboxManager):
        self.persona_type = persona_type
        self.handle = handle
        self.manager = manager

    def respond(
        self,
        intervention: Intervention,
        state: PersonaState,
        org_profile: OrgProfile,
    ) -> str:
        """Forward response generation to sandbox."""
        resp = self.manager.send_request(self.handle, "/respond", {
            "intervention": intervention.model_dump(mode="json"),
            "state": state.model_dump(mode="json"),
            "org_profile": org_profile.model_dump(mode="json"),
        })
        return resp["response"]

    def update_state(
        self,
        state: PersonaState,
        intervention: Intervention,
        all_states: dict[PersonaType, PersonaState],
    ) -> float:
        """Update persona hidden state. Runs on HOST, not in sandbox.

        This is pure deterministic Python — no LLM calls, no sandbox needed.
        The controller retains full authority over state mutations.
        """
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
