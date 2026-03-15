# Enterprise AI Deployment Simulator

## What This Is

A multi-agent orchestration system that simulates enterprise AI rollouts. An orchestrator agent (Claude Sonnet) plans and adapts deployment strategies against persona agents (Claude Haiku) that model realistic stakeholder behavior. The project demonstrates agentic orchestration, HITL governance, and adoption measurement patterns for enterprise AI deployment roles.

Core thesis: **"The hardest problem in enterprise AI isn't the model. It's the adoption."**

## Architecture

- **Orchestrator Agent** (`src/agents/orchestrator.py`): Claude Sonnet with 3 tools (knowledge base, metrics tracker, re-planner). Uses tool_use API. Outputs interventions with confidence scores.
- **Persona Agents** (`src/agents/persona.py`): 4 archetypes (Skeptical IC, Enthusiastic Champion, Risk-Averse VP, Overwhelmed IT Admin) running on Claude Haiku. Hidden internal state (sentiment, trust, cognitive load) not visible to orchestrator.
- **Simulation Controller** (`src/simulation/controller.py`): Deterministic Python loop managing turns, state, events, termination. Not LLM-powered.
- **HITL Router** (`src/simulation/hitl_router.py`): Confidence-based routing (auto-execute ≥0.80, human review 0.50-0.79, escalate <0.50). Three modes: autopilot, guided, demo.
- **Flywheel Metrics** (`src/simulation/flywheel_metrics.py`): CS-grade metrics (activation rate, weekly engaged users, completion rate, override rate, cycle-time delta) with Pilot Scorecard output.
- **Experiment Runner** (`src/simulation/experiment_runner.py`): Batch execution with parameter sweeps, parallel runs, result aggregation.
- **Knowledge Base** (`src/tools/knowledge_base.py`): 18 pre-loaded change management tactics. Phase 1 uses keyword search; swap to ChromaDB later.

## Build Phases

### Phase 1: Orchestrator Foundation
- [x] Data models (Pydantic)
- [x] Orchestrator agent with tool use
- [x] Knowledge base with 18 tactics
- [x] Metrics tracker
- [x] Re-planner tool
- [x] 3 sample org profiles
- [x] CLI entry point
- [ ] Verify orchestrator generates coherent plans from each profile (blocked: Bedrock daily token quota)
- [ ] Test tool use loop (KB query → metrics check → plan output) (blocked: Bedrock daily token quota)
- [ ] Validate JSON intervention extraction from orchestrator output (blocked: Bedrock daily token quota)

### Phase 2: Persona Agents + HITL + Simulation Loop
- [x] Persona agent scaffolding with system prompts and hidden state
- [x] HITL router with confidence routing and audit trail
- [x] Wire HITL router into simulation controller (between orchestrator output and persona dispatch)
- [x] Integrate flywheel metrics into the controller (replaced MetricsTrackerTool with FlywheelMetricsTracker)
- [x] CLI `--mode` flag for autopilot/guided/demo HITL modes
- [x] Audit trail JSON export alongside simulation logs
- [ ] Test full simulation loop end-to-end with a short 4-week run (blocked: Bedrock daily token quota)
- [ ] Validate persona responses are differentiated by archetype (blocked: Bedrock daily token quota)
- [ ] Test guided mode (CLI pauses on review/escalate items) (blocked: Bedrock daily token quota)

### Phase 3: Events + Experiments + Flywheel Metrics
- [x] Event catalog with 7 event types
- [x] Experiment runner scaffolding
- [x] Flywheel metrics and Pilot Scorecard
- [x] Wire event injection into simulation controller (random + forced events)
- [x] Forced event support for experiment runner (DISRUPTION_RESILIENCE fires reorg/sponsor_departure/budget_freeze)
- [x] Orchestrator receives event context (Recent Organizational Events section in turn context)
- [x] Quiet mode for parallel experiment execution (no interleaved Rich output)
- [x] Comparison report with sensitivity tables, cross-variable heatmap, and best/worst configs
- [ ] Test orchestrator re-planning when events fire (blocked: Bedrock daily token quota)
- [ ] Run 3 complete simulations with different profiles, capture logs (blocked: Bedrock daily token quota)
- [ ] Execute sponsorship_sensitivity experiment, verify result aggregation (blocked: Bedrock daily token quota)

### Phase 4: Visualization + Strands/NanoClaw
- [x] Pilot Scorecard dashboard (Streamlit + Plotly): adoption curves, intervention timeline, risk flags, persona responses
- [x] HITL audit trail viewer: routing distribution, confidence over time, full audit log table
- [x] Experiment results viewer with sensitivity heatmaps
- [x] Dashboard CLI command: `python -m src.main dashboard`
- [x] Sample data generator for dashboard demo (`src/dashboard/generate_sample_data.py`)
- [x] Strands SDK refactor (opt-in via `--backend strands`)
- [x] NanoClaw + Docker Sandbox containerization (opt-in via `--backend sandbox`)
- [x] GitHub Pages interactive explorer at nomadnome.github.io/deployment-simulator
- [x] Architecture diagram
- [x] Author footer with LinkedIn

## Tech Decisions

- **Language**: Python 3.11+
- **LLM**: Anthropic API via `Anthropic` client from the `anthropic` SDK. Set `ANTHROPIC_API_KEY` in `.env`.
- **Orchestrator model**: `claude-sonnet-4-5-20250929` (swap to `claude-sonnet-4-6-20250514` when available)
- **Persona model**: `claude-haiku-4-5-20251001`
- **Bedrock fallback**: To use Bedrock instead, set `LLM_PROVIDER=bedrock` and `AWS_REGION` in `.env` (pending quota increase)
- **Agent backends**: Three options — `vanilla` (default, direct Anthropic SDK), `strands` (Strands SDK, opt-in via `--backend strands`), `sandbox` (NanoClaw + Docker, opt-in via `--backend sandbox`)
- **Vector store**: Keyword search Phase 1, ChromaDB Phase 2+
- **State**: In-memory (Phase 1-2), SQLite (Phase 3), DynamoDB adapter (Phase 4)
- **CLI**: Rich for terminal output
- **Data models**: Pydantic v2 with strict typing

## Code Conventions

- Type hints everywhere. Use `from __future__ import annotations`.
- Pydantic BaseModel for all data structures that cross boundaries.
- Docstrings on all public classes and functions.
- No print() — use Rich console for all output.
- JSON lines format for simulation logs.
- Keep modules focused: one concern per file.
- Enum values are snake_case strings.

## Key Files to Understand First

1. `src/models.py` — All data models. Read this first.
2. `src/simulation/controller.py` — The main simulation loop. This is where everything connects.
3. `src/agents/orchestrator.py` — The orchestrator's system prompt, tool definitions, and agentic loop.
4. `src/agents/persona.py` — Persona system prompts, hidden state initialization, and the intervention effect lookup table.

## Current Priority

The project is complete through Phase 4. All build phases are done.

Remaining items:
- Swap to Sonnet 4.6 when Bedrock quota clears
- Add pytest test suite

## Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Set your Anthropic API key in .env:
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

python -m src.main simulate --profile nova_tech --seed 42
```

## Reference

Full PRD with architecture details, data models, cost estimates, and interview narrative: `deployment-simulator-prd.docx` (keep in project root for reference, not committed to git).
