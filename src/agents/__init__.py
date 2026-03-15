"""Agent factory — creates vanilla, Strands, or sandboxed agents based on configuration."""

from __future__ import annotations

import os

from src.models import PersonaType

# Singleton sandbox manager (created once, shared across all sandboxed agents)
_sandbox_manager = None


def _get_sandbox_manager():
    global _sandbox_manager
    if _sandbox_manager is None:
        from src.sandbox.sandbox_manager import SandboxManager
        _sandbox_manager = SandboxManager()
    return _sandbox_manager


def create_orchestrator_agent():
    """Create the orchestrator agent using the configured backend."""
    backend = os.getenv("AGENT_BACKEND", "vanilla")

    if backend == "sandbox":
        from src.agents.sandboxed_orchestrator import SandboxedOrchestratorAgent
        manager = _get_sandbox_manager()
        handle = manager.create_sandbox("orchestrator")
        return SandboxedOrchestratorAgent(handle, manager)

    if backend == "strands":
        from src.agents.strands_orchestrator import StrandsOrchestratorAgent
        return StrandsOrchestratorAgent()

    from src.agents.orchestrator import OrchestratorAgent
    return OrchestratorAgent()


def create_persona_agent(persona_type: PersonaType):
    """Create a persona agent using the configured backend."""
    backend = os.getenv("AGENT_BACKEND", "vanilla")

    if backend == "sandbox":
        from src.agents.sandboxed_persona import SandboxedPersonaAgent
        manager = _get_sandbox_manager()
        handle = manager.create_sandbox(f"persona_{persona_type.value}")
        return SandboxedPersonaAgent(persona_type, handle, manager)

    if backend == "strands":
        from src.agents.strands_persona import StrandsPersonaAgent
        return StrandsPersonaAgent(persona_type)

    from src.agents.persona import PersonaAgent
    return PersonaAgent(persona_type)


def cleanup_sandboxes():
    """Destroy all running sandboxes. Call at simulation end."""
    global _sandbox_manager
    if _sandbox_manager:
        _sandbox_manager.destroy_all()
        _sandbox_manager = None
