"""In-sandbox agent HTTP server — runs inside each Docker container."""

from __future__ import annotations

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add project root to path
sys.path.insert(0, "/app")

from src.models import (
    Intervention, InterventionType, OrgProfile, PersonaState, PersonaType,
    SimulationState, AdoptionMetrics,
)


class AgentHandler(BaseHTTPRequestHandler):
    """HTTP handler that dispatches to the appropriate agent."""

    agent = None  # set at server startup

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        try:
            if self.path == "/health":
                self._respond(200, {"status": "ok", "role": os.getenv("AGENT_ROLE", "unknown")})

            elif self.path == "/generate_initial_plan":
                profile = OrgProfile(**body["org_profile"])
                plan = self.agent.generate_initial_plan(profile)
                self._respond(200, {"plan": plan})

            elif self.path == "/run_turn":
                state = _rebuild_state(body["state"])
                responses = body.get("persona_responses")
                if responses:
                    responses = {PersonaType(k): v for k, v in responses.items()}
                reasoning, interventions = self.agent.run_turn(state, responses)
                self._respond(200, {
                    "reasoning": reasoning,
                    "interventions": [iv.model_dump() for iv in interventions],
                })

            elif self.path == "/respond":
                intervention = Intervention(**body["intervention"])
                state = PersonaState(**body["state"])
                profile = OrgProfile(**body["org_profile"])
                response = self.agent.respond(intervention, state, profile)
                self._respond(200, {"response": response})

            else:
                self._respond(404, {"error": f"Unknown endpoint: {self.path}"})

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def _rebuild_state(raw: dict) -> SimulationState:
    """Rebuild SimulationState from serialized dict."""
    # Reconstruct persona_states with proper enum keys
    persona_states = {}
    for k, v in raw.get("persona_states", {}).items():
        ptype = PersonaType(k)
        persona_states[ptype] = PersonaState(**v)
    raw["persona_states"] = persona_states

    # Reconstruct metrics if present
    if raw.get("metrics"):
        raw["metrics"] = AdoptionMetrics(**raw["metrics"])

    # Reconstruct org_profile
    if raw.get("org_profile"):
        raw["org_profile"] = OrgProfile(**raw["org_profile"])

    return SimulationState(**raw)


def main():
    role = os.getenv("AGENT_ROLE", "orchestrator")
    port = int(os.getenv("AGENT_PORT", "8080"))

    if role == "orchestrator":
        from src.agents.orchestrator import OrchestratorAgent
        AgentHandler.agent = OrchestratorAgent()
        print(f"Orchestrator agent server starting on port {port}")
    elif role.startswith("persona_"):
        persona_type = PersonaType(role.replace("persona_", ""))
        from src.agents.persona import PersonaAgent
        AgentHandler.agent = PersonaAgent(persona_type)
        print(f"Persona agent server ({persona_type.value}) starting on port {port}")
    else:
        print(f"Unknown role: {role}")
        sys.exit(1)

    server = HTTPServer(("0.0.0.0", port), AgentHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
