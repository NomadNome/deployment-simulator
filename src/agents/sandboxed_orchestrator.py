"""Sandboxed Orchestrator — proxy that delegates to a Docker sandbox."""

from __future__ import annotations

from src.models import (
    Intervention, InterventionType, OrgProfile,
    PersonaType, SimulationState,
)
from src.sandbox.sandbox_manager import SandboxHandle, SandboxManager


class SandboxedOrchestratorAgent:
    """Orchestrator proxy that forwards calls to a Docker sandbox.

    Same interface as OrchestratorAgent — drop-in replacement.
    """

    def __init__(self, handle: SandboxHandle, manager: SandboxManager):
        self.handle = handle
        self.manager = manager

    def generate_initial_plan(self, org_profile: OrgProfile) -> str:
        """Forward initial plan generation to sandbox."""
        resp = self.manager.send_request(self.handle, "/generate_initial_plan", {
            "org_profile": org_profile.model_dump(mode="json"),
        })
        return resp["plan"]

    def run_turn(
        self,
        state: SimulationState,
        persona_responses: dict[PersonaType, str] | None = None,
    ) -> tuple[str, list[Intervention]]:
        """Forward turn execution to sandbox."""
        serialized_responses = None
        if persona_responses:
            serialized_responses = {k.value: v for k, v in persona_responses.items()}

        resp = self.manager.send_request(self.handle, "/run_turn", {
            "state": _serialize_state(state),
            "persona_responses": serialized_responses,
        })

        interventions = []
        for iv_data in resp.get("interventions", []):
            try:
                interventions.append(Intervention(
                    intervention_type=InterventionType(iv_data["intervention_type"]),
                    target_persona=PersonaType(iv_data["target_persona"]),
                    content=iv_data.get("content", ""),
                    rationale=iv_data.get("rationale", ""),
                ))
            except (KeyError, ValueError):
                continue

        return resp.get("reasoning", ""), interventions


def _serialize_state(state: SimulationState) -> dict:
    """Serialize SimulationState for transmission to sandbox."""
    data = state.model_dump(mode="json")
    # Convert enum keys to strings for JSON
    persona_states = {}
    for ptype, pstate in state.persona_states.items():
        persona_states[ptype.value] = pstate.model_dump(mode="json")
    data["persona_states"] = persona_states
    return data
