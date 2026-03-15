"""Strands-based Orchestrator Agent — drop-in replacement using @tool decorators."""

from __future__ import annotations

import json
import re
from typing import Any

from rich.console import Console
from strands import Agent, tool

from src.agents.orchestrator import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    _build_turn_context,
)
from src.agents.provider import get_strands_model
from src.models import (
    Intervention, InterventionType, OrgProfile,
    PersonaType, SimulationState,
)
from src.tools.knowledge_base import KnowledgeBaseTool
from src.tools.metrics_tracker import MetricsTrackerTool
from src.tools.replanner import ReplannerTool

console = Console()

# Module-level state context — set before each agent invocation
_current_state: SimulationState | None = None
_kb_tool = KnowledgeBaseTool()
_metrics_tool = MetricsTrackerTool()
_replan_tool = ReplannerTool()


# ── Strands Tool Definitions ─────────────────────────────────

@tool
def query_knowledge_base(query: str, max_results: int = 3) -> str:
    """Search the change management knowledge base for relevant tactics and frameworks.

    Args:
        query: Describe the adoption challenge or persona situation you need tactics for.
        max_results: Number of results to return (1-5).
    """
    results = _kb_tool.query(query=query, max_results=max_results)
    return json.dumps(results, indent=2)


@tool
def check_adoption_metrics() -> str:
    """Retrieve the current adoption metrics dashboard including overall adoption, login rate, feature usage, NPS proxy, and risk flags."""
    if _current_state and _current_state.metrics:
        return _current_state.metrics.model_dump_json(indent=2)
    return json.dumps({"error": "No metrics available yet (week 0)"})


@tool
def trigger_replan(failure_diagnosis: str, constraints: str = "") -> str:
    """Generate a revised rollout plan when the current strategy is failing.

    Args:
        failure_diagnosis: Your analysis of why the current plan is underperforming.
        constraints: Any constraints on the new plan (budget, timeline, etc).
    """
    if not _current_state:
        return json.dumps({"error": "No simulation state available"})
    new_plan = _replan_tool.generate(failure_diagnosis, constraints, _current_state)
    return json.dumps({"revised_plan": new_plan})


# ── Strands Orchestrator Agent ────────────────────────────────

class StrandsOrchestratorAgent:
    """Deployment strategist agent using Strands SDK.

    Drop-in replacement for OrchestratorAgent with the same public interface.
    """

    def __init__(self):
        model = get_strands_model("orchestrator")
        self.agent = Agent(
            model=model,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=[query_knowledge_base, check_adoption_metrics, trigger_replan],
        )
        self.kb_tool = _kb_tool
        self.metrics_tool = _metrics_tool
        self.replan_tool = _replan_tool

    def generate_initial_plan(self, org_profile: OrgProfile) -> str:
        """Generate the initial rollout plan before simulation begins."""
        prompt = (
            f"Generate a rollout plan for this organization:\n\n"
            f"Name: {org_profile.org_name}\n"
            f"Industry: {org_profile.industry.value}\n"
            f"Team size: {org_profile.team_size}\n"
            f"Technical maturity: {org_profile.technical_maturity.value}\n"
            f"Executive sponsorship: {org_profile.executive_sponsorship.value}\n"
            f"AI tool: {org_profile.ai_tool_type}\n"
            f"Budget: {org_profile.budget_weeks} weeks\n"
            f"Success threshold: {org_profile.success_threshold:.0%}\n"
            f"Competing priorities: {', '.join(org_profile.competing_priorities) or 'None identified'}"
        )
        # Use a simple agent call (no tools needed for initial plan)
        plan_agent = Agent(
            model=get_strands_model("orchestrator"),
            system_prompt=(
                "You are an expert enterprise AI deployment strategist. "
                "Given an organization profile, generate a phased rollout plan "
                "for the first 4 weeks. Be specific about which personas to "
                "target in which order and why. Output the plan as clear prose."
            ),
        )
        result = plan_agent(prompt)
        return str(result)

    def run_turn(
        self,
        state: SimulationState,
        persona_responses: dict[PersonaType, str] | None = None,
    ) -> tuple[str, list[Intervention]]:
        """Execute one turn of orchestrator reasoning.

        Returns:
            tuple of (orchestrator_reasoning, list of interventions)
        """
        global _current_state
        _current_state = state

        context = _build_turn_context(state, persona_responses)
        result = self.agent(context)
        reasoning = str(result)

        _current_state = None

        interventions = self._extract_interventions(reasoning)
        return reasoning, interventions

    def _extract_interventions(self, reasoning: str) -> list[Intervention]:
        """Parse interventions from the orchestrator's reasoning output."""
        raw_json = self._find_json_array(reasoning)
        if not raw_json:
            return []

        raw_json = re.sub(r'[\x00-\x1f\x7f]', ' ', raw_json)
        raw_json = re.sub(r',\s*([}\]])', r'\1', raw_json)

        try:
            raw = json.loads(raw_json)
        except json.JSONDecodeError:
            raw = self._extract_json_objects(raw_json)
            if not raw:
                console.print("[yellow]WARN: Could not parse intervention JSON[/yellow]")
                return []

        interventions = []
        for item in raw:
            try:
                interventions.append(Intervention(
                    intervention_type=InterventionType(item["intervention_type"]),
                    target_persona=PersonaType(item["target_persona"]),
                    content=item.get("content", ""),
                    rationale=item.get("rationale", ""),
                ))
            except (KeyError, ValueError) as e:
                console.print(f"[yellow]WARN: Skipping invalid intervention: {e}[/yellow]")
                continue

        return interventions

    @staticmethod
    def _find_json_array(text: str) -> str | None:
        """Find a JSON array in text, trying multiple patterns."""
        match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r'```\s*(\[.*?intervention_type.*?\])\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r'(\[\s*\{[^`]*?"intervention_type".*?\}\s*\])', text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_json_objects(raw: str) -> list[dict]:
        """Extract individual JSON objects from a malformed array."""
        objects = []
        for match in re.finditer(r'\{[^{}]*?"intervention_type"[^{}]*?\}', raw, re.DOTALL):
            try:
                cleaned = re.sub(r'[\x00-\x1f\x7f]', ' ', match.group(0))
                cleaned = re.sub(r',\s*\}', '}', cleaned)
                obj = json.loads(cleaned)
                objects.append(obj)
            except json.JSONDecodeError:
                continue
        return objects
