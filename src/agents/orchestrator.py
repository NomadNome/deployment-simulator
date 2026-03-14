"""Orchestrator Agent — the deployment strategist that plans and adapts."""

from __future__ import annotations

import json
import re
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console

from src.models import (
    AdoptionMetrics, Intervention, InterventionType, OrgProfile,
    PersonaType, SimulationState,
)
from src.tools.knowledge_base import KnowledgeBaseTool
from src.tools.metrics_tracker import MetricsTrackerTool
from src.tools.replanner import ReplannerTool

load_dotenv()
console = Console()

ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250929"


# ── Tool Definitions (Claude tool_use schema) ─────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "query_knowledge_base",
        "description": (
            "Search the change management knowledge base for relevant tactics, "
            "frameworks, and intervention templates. Use this when you need to "
            "find the right approach for a specific adoption challenge. Query "
            "should describe the problem you're trying to solve, not the "
            "solution you want."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Describe the adoption challenge or persona situation"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-5)",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_adoption_metrics",
        "description": (
            "Retrieve the current adoption metrics dashboard. Returns login rates, "
            "feature usage depth, NPS proxy, and active risk flags. Always check "
            "metrics BEFORE planning interventions so your decisions are data-informed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "trigger_replan",
        "description": (
            "Generate a revised rollout plan when the current strategy is failing. "
            "Only invoke this when metrics show a clear downward trend or a major "
            "organizational event has disrupted your plan. Provide your diagnosis "
            "of why the current plan is failing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "failure_diagnosis": {
                    "type": "string",
                    "description": "Your analysis of why the current plan is underperforming"
                },
                "constraints": {
                    "type": "string",
                    "description": "Any constraints on the new plan (budget, time, personas to prioritize)"
                }
            },
            "required": ["failure_diagnosis"]
        }
    }
]


# ── System Prompt ──────────────────────────────────────────────

ORCHESTRATOR_SYSTEM_PROMPT = """You are an expert enterprise AI deployment strategist. Your job is to drive adoption of an AI tool across a complex organization by planning and executing the right interventions for the right stakeholders at the right time.

## Your Decision Framework

Every turn, follow this sequence:
1. ASSESS — What do the current metrics and persona responses tell you about adoption trajectory? Who is at risk?
2. DIAGNOSE — What is the root cause of any stalled adoption? Map to ADKAR: Awareness, Desire, Knowledge, Ability, or Reinforcement.
3. SELECT — Which intervention from your toolkit best addresses the diagnosed root cause for the at-risk persona?
4. SEQUENCE — What order should you execute interventions? Are there dependencies?
5. ADAPT — Based on responses, should you adjust, escalate, pivot, or double down?

## Rules
- Always check adoption metrics BEFORE planning interventions.
- Never propose more than 3 interventions per week (organizations have absorption limits).
- Pay close attention to persona responses — they contain signals about hidden sentiment you can't observe directly.
- If a persona has gone quiet or is giving short/dismissive responses, that is a risk signal.
- Vary your intervention types. Repeating the same approach signals lack of creativity.
- When metrics show a sustained downward trend (2+ weeks), invoke the re-planning tool.

## Intervention Types Available
- executive_briefing: For VP-level stakeholders. ROI-focused, strategic framing.
- workshop: Hands-on group session. Good for building knowledge and ability.
- one_on_one: Personal meeting. Best for addressing individual concerns and building trust.
- async_communication: Email, Slack message, or shared document. Low-touch but scalable.
- tool_demo: Live demonstration of the AI tool on real use cases. Evidence-based persuasion.
- peer_learning_cohort: Small group of peers learning together. Builds social proof.
- quick_win_session: Focused session to achieve one concrete success. Builds momentum.
- escalation: Raise an issue to executive sponsor. Use sparingly — signals the strategist can't resolve it alone.
- office_hours: Open drop-in session. Low-pressure, high-accessibility.
- gamified_challenge: Team competition or challenge using the tool. Builds engagement through play.

## Target Personas (use EXACTLY these values for target_persona)
- skeptical_ic: Senior engineer. Technically competent, skeptical of AI hype, needs evidence.
- enthusiastic_champion: Early adopter who loves the tool. Risk of burnout without support.
- risk_averse_vp: Executive stakeholder. Cares about ROI, risk, and optics. Controls budget.
- overwhelmed_it_admin: Handles integration and access. Already overloaded with tickets.

## Output Format
CRITICAL: You MUST end EVERY response with a JSON code block containing your interventions. No exceptions.
- target_persona MUST be exactly one of: skeptical_ic, enthusiastic_champion, risk_averse_vp, overwhelmed_it_admin
- intervention_type MUST be exactly one of: executive_briefing, workshop, one_on_one, async_communication, tool_demo, peer_learning_cohort, quick_win_session, escalation, office_hours, gamified_challenge
- Keep content and rationale concise (under 200 characters each). Do not include newlines or special characters in string values.

```json
[
  {
    "intervention_type": "workshop",
    "target_persona": "skeptical_ic",
    "content": "Hands-on session with real codebase examples showing AI tool capabilities",
    "rationale": "IC needs evidence-based persuasion through direct experience"
  }
]
```
"""


def _build_turn_context(state: SimulationState, persona_responses: dict[PersonaType, str] | None = None) -> str:
    """Compile current simulation state into a context message for the orchestrator."""
    parts = [
        f"## Organization Profile",
        f"- Name: {state.org_profile.org_name}",
        f"- Industry: {state.org_profile.industry.value}",
        f"- Team size: {state.org_profile.team_size}",
        f"- Technical maturity: {state.org_profile.technical_maturity.value}",
        f"- Executive sponsorship: {state.org_profile.executive_sponsorship.value}",
        f"- AI tool: {state.org_profile.ai_tool_type}",
        f"- Budget remaining: {state.org_profile.budget_weeks - state.current_week} weeks",
        f"- Success threshold: {state.org_profile.success_threshold:.0%}",
        f"\n## Current Week: {state.current_week}",
    ]

    if state.metrics:
        parts.append(f"\n## Latest Metrics (auto-loaded)")
        parts.append(f"- Overall adoption: {state.metrics.overall_adoption_pct:.1%}")
        parts.append(f"- Login rate: {state.metrics.login_rate:.1%}")
        parts.append(f"- Feature usage depth: {state.metrics.feature_usage_depth:.1%}")
        parts.append(f"- NPS proxy: {state.metrics.nps_proxy:+.2f}")
        if state.metrics.risk_flags:
            parts.append(f"- Risk flags: {', '.join(state.metrics.risk_flags)}")

    if state.orchestrator_plan:
        parts.append(f"\n## Your Current Plan\n{state.orchestrator_plan}")

    if persona_responses:
        parts.append(f"\n## Persona Responses from Last Week")
        for persona, response in persona_responses.items():
            parts.append(f"\n### {persona.value}\n{response}")

    # Include events from this week and recent turns
    current_turn_events = [t for t in state.turn_history if t.week == state.current_week]
    recent_events = []
    for turn in state.turn_history[-3:]:
        recent_events.extend(turn.events_fired)
    if recent_events:
        parts.append(f"\n## Recent Organizational Events")
        for event in recent_events:
            parts.append(f"- Week {event.trigger_week}: **{event.event_type.value}** — {event.description}")

    # Include last 3 turns of history for context
    recent = state.turn_history[-3:]
    if recent:
        parts.append(f"\n## Recent Intervention History")
        for turn in recent:
            parts.append(f"\nWeek {turn.week}:")
            for iv in turn.interventions:
                parts.append(f"  - {iv.intervention_type.value} → {iv.target_persona.value}: {iv.rationale}")

    return "\n".join(parts)


class OrchestratorAgent:
    """The deployment strategist agent that plans and adapts rollout strategy."""

    def __init__(self, model: str = ORCHESTRATOR_MODEL):
        self.client = Anthropic()
        self.model = model
        self.kb_tool = KnowledgeBaseTool()
        self.metrics_tool = MetricsTrackerTool()
        self.replan_tool = ReplannerTool()

    def generate_initial_plan(self, org_profile: OrgProfile) -> str:
        """Generate the initial rollout plan before simulation begins."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=(
                "You are an expert enterprise AI deployment strategist. "
                "Given an organization profile, generate a phased rollout plan "
                "for the first 4 weeks. Be specific about which personas to "
                "target in which order and why. Output the plan as clear prose."
            ),
            messages=[{
                "role": "user",
                "content": (
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
            }]
        )
        return message.content[0].text

    def run_turn(
        self,
        state: SimulationState,
        persona_responses: dict[PersonaType, str] | None = None
    ) -> tuple[str, list[Intervention]]:
        """
        Execute one turn of orchestrator reasoning.

        Returns:
            tuple of (orchestrator_reasoning, list of interventions)
        """
        context = _build_turn_context(state, persona_responses)
        messages = [{"role": "user", "content": context}]

        # Run the agentic tool-use loop
        reasoning_parts = []
        max_iterations = 5  # prevent runaway tool loops

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=ORCHESTRATOR_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Collect text blocks and handle all tool use blocks
            tool_results = []
            for block in response.content:
                if block.type == "text":
                    reasoning_parts.append(block.text)
                elif block.type == "tool_use":
                    result = self._handle_tool_call(block, state)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # If no more tool calls, we're done
            if response.stop_reason == "end_turn":
                break

            # Append assistant response + all tool results for next iteration
            if tool_results:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        reasoning = "\n".join(reasoning_parts)
        interventions = self._extract_interventions(reasoning)

        return reasoning, interventions

    def _handle_tool_call(self, tool_block: Any, state: SimulationState) -> str:
        """Route a tool call to the appropriate handler."""
        name = tool_block.name
        inputs = tool_block.input

        if name == "query_knowledge_base":
            results = self.kb_tool.query(
                query=inputs["query"],
                max_results=inputs.get("max_results", 3)
            )
            return json.dumps(results)

        elif name == "check_adoption_metrics":
            if state.metrics:
                return state.metrics.model_dump_json()
            return json.dumps({"error": "No metrics available yet (week 0)"})

        elif name == "trigger_replan":
            new_plan = self.replan_tool.generate(
                failure_diagnosis=inputs["failure_diagnosis"],
                constraints=inputs.get("constraints", ""),
                state=state
            )
            return json.dumps({"revised_plan": new_plan})

        return json.dumps({"error": f"Unknown tool: {name}"})

    def _extract_interventions(self, reasoning: str) -> list[Intervention]:
        """Parse interventions from the orchestrator's reasoning output."""
        raw_json = self._find_json_array(reasoning)
        if not raw_json:
            return []

        # Clean control characters that LLMs sometimes embed in strings
        raw_json = re.sub(r'[\x00-\x1f\x7f]', ' ', raw_json)

        # Fix common LLM JSON issues: trailing commas before ] or }
        raw_json = re.sub(r',\s*([}\]])', r'\1', raw_json)

        try:
            raw = json.loads(raw_json)
        except json.JSONDecodeError:
            # Try extracting individual objects if the array is malformed
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
        # Pattern 1: ```json ... ```
        match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
        if match:
            return match.group(1)

        # Pattern 2: ``` ... ``` containing intervention_type
        match = re.search(r'```\s*(\[.*?intervention_type.*?\])\s*```', text, re.DOTALL)
        if match:
            return match.group(1)

        # Pattern 3: Bare JSON array with intervention_type
        match = re.search(r'(\[\s*\{[^`]*?"intervention_type".*?\}\s*\])', text, re.DOTALL)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def _extract_json_objects(raw: str) -> list[dict]:
        """Extract individual JSON objects from a malformed array."""
        objects = []
        # Find each {...} block
        for match in re.finditer(r'\{[^{}]*?"intervention_type"[^{}]*?\}', raw, re.DOTALL):
            try:
                cleaned = re.sub(r'[\x00-\x1f\x7f]', ' ', match.group(0))
                cleaned = re.sub(r',\s*\}', '}', cleaned)
                obj = json.loads(cleaned)
                objects.append(obj)
            except json.JSONDecodeError:
                continue
        return objects
