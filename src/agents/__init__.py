"""Agent factory — creates vanilla or Strands agents based on configuration."""

from __future__ import annotations

import os

from src.models import PersonaType


def create_orchestrator_agent():
    """Create the orchestrator agent using the configured backend."""
    backend = os.getenv("AGENT_BACKEND", "vanilla")

    if backend == "strands":
        from src.agents.strands_orchestrator import StrandsOrchestratorAgent
        return StrandsOrchestratorAgent()

    from src.agents.orchestrator import OrchestratorAgent
    return OrchestratorAgent()


def create_persona_agent(persona_type: PersonaType):
    """Create a persona agent using the configured backend."""
    backend = os.getenv("AGENT_BACKEND", "vanilla")

    if backend == "strands":
        from src.agents.strands_persona import StrandsPersonaAgent
        return StrandsPersonaAgent(persona_type)

    from src.agents.persona import PersonaAgent
    return PersonaAgent(persona_type)
