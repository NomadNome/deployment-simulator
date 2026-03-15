"""Tests for agent factory backend switching."""

import os

from src.models import PersonaType


def test_vanilla_backend(monkeypatch):
    monkeypatch.setenv("AGENT_BACKEND", "vanilla")
    # Force reimport
    import importlib
    import src.agents
    importlib.reload(src.agents)
    from src.agents import create_orchestrator_agent, create_persona_agent

    orch = create_orchestrator_agent()
    assert type(orch).__name__ == "OrchestratorAgent"

    persona = create_persona_agent(PersonaType.SKEPTICAL_IC)
    assert type(persona).__name__ == "PersonaAgent"


def test_strands_backend(monkeypatch):
    monkeypatch.setenv("AGENT_BACKEND", "strands")
    import importlib
    import src.agents
    importlib.reload(src.agents)
    from src.agents import create_orchestrator_agent, create_persona_agent

    orch = create_orchestrator_agent()
    assert type(orch).__name__ == "StrandsOrchestratorAgent"

    persona = create_persona_agent(PersonaType.SKEPTICAL_IC)
    assert type(persona).__name__ == "StrandsPersonaAgent"


def test_default_is_vanilla(monkeypatch):
    monkeypatch.delenv("AGENT_BACKEND", raising=False)
    import importlib
    import src.agents
    importlib.reload(src.agents)
    from src.agents import create_orchestrator_agent

    orch = create_orchestrator_agent()
    assert type(orch).__name__ == "OrchestratorAgent"
