# Test Coverage Analysis

## Current State

The project has **9 test files with ~69 test functions** in `tests/`, covering 8 of ~23 source modules — roughly **22% module coverage** and an estimated **~12% line coverage**.

### Covered Modules

| Module | Test File | What's Tested |
|--------|-----------|---------------|
| `src/models.py` | `test_models.py` | Data model validation, enum existence, serialization |
| `src/tools/knowledge_base.py` | `test_knowledge_base.py` | Queries, field-tested boost, industry-specific results |
| `src/simulation/hitl_router.py` | `test_hitl_router.py` | Confidence classification, routing lanes, audit trail |
| `src/simulation/flywheel_metrics.py` | `test_flywheel_metrics.py` | Metrics computation, trend detection, risk flags, scorecard |
| `src/agents/persona.py` | `test_personas.py` | Initialization, state updates, intervention effects, cognitive load |
| `src/simulation/profiles.py` | `test_profiles.py` | Organization profile validation and field checking |
| `src/agents/provider.py` | `test_agent_factory.py` | Backend switching (vanilla, strands, default) |
| `src/simulation/events.py` | `test_events.py` | Event catalog, determinism, forced events, deduplication |

### Uncovered Modules

| Module | Lines | Key Untested Logic |
|--------|-------|--------------------|
| `src/simulation/controller.py` | 485 | Main simulation loop, turn management, event application, persona dispatching, friction/blind-spot integration, termination checks, log persistence |
| `src/agents/orchestrator.py` | 396 | Tool-use loop, JSON intervention extraction (4 regex patterns), context building, tool call routing |
| `src/simulation/realism.py` | 208 | Friction rolling, fatigue multipliers, blind spot probability, grudge accumulation/decay |
| `src/simulation/experiment_runner.py` | 473 | Scenario matrix generation, parallel execution, result aggregation, sensitivity analysis |
| `src/tools/metrics_tracker.py` | 72 | Adoption aggregation, risk flag generation |
| `src/tools/replanner.py` | 96 | Re-planning prompt construction |
| `src/main.py` | 156 | CLI parsing and command routing |
| `src/agents/sandboxed_orchestrator.py` | — | Sandboxed agent backend |
| `src/agents/strands_orchestrator.py` | — | Strands SDK backend |
| `src/agents/sandboxed_persona.py` | — | Sandboxed persona backend |
| `src/agents/strands_persona.py` | — | Strands SDK persona backend |
| `src/sandbox/sandbox_manager.py` | — | Docker sandbox management |
| `src/sandbox/agent_server.py` | — | Sandbox agent server |
| `src/dashboard/app.py` | — | Streamlit dashboard |
| `src/dashboard/generate_sample_data.py` | — | Sample data generation |

### Missing Infrastructure

- **No `conftest.py`** — No shared fixtures for mock Anthropic client, test profiles, or persona states
- **No pytest markers** — No way to separate unit/integration/slow tests
- **No CI workflow** — No `.github/workflows/` for automated test runs
- **No LLM mocking patterns** — Orchestrator and replanner call the Anthropic API with no mock layer

---

## Recommended Improvements

### Phase 1: Pure Logic Tests (no mocking needed)

**`src/simulation/realism.py`** — Highly testable deterministic math:
- `roll_friction()`: Verify determinism with seeds, outcome distribution over many runs
- `fatigue_multiplier()`: Test progression (1.0 → 0.7 → 0.4 → 0.2) and reset on variety
- `roll_blind_spot()`: Test base probability, tunnel vision escalation, type distribution
- `apply_blind_spot()`: Verify persona omission and metrics lag behavior
- `update_grudge()`: Test accumulation paths (backfire, cancelled, no-contact) and decay rates per persona
- `grudge_effect_multiplier()`: Verify bounds (1.0 to 0.5)

**`src/agents/orchestrator.py` — JSON extraction only**:
- `_extract_interventions()`: Test all 4 regex patterns, malformed JSON, invalid enums, empty arrays
- `_find_json_array()`: Test each pattern (fenced code blocks, bare arrays) and precedence
- `_extract_json_objects()`: Test multiple objects, nested braces, control character cleanup

**`src/tools/metrics_tracker.py`**:
- `compute_metrics()`: Verify adoption/sentiment aggregation formulas
- Risk flag thresholds (low adoption, declining sentiment, resistance, fatigue, etc.)
- Trend detection from metrics history

**`src/simulation/experiment_runner.py` — Data transforms**:
- `generate_scenario_matrix()`: Empty sweeps, single variable, multi-variable cartesian products
- `apply_scenario_to_profile()`: Enum conversion (Industry, Maturity, Sponsorship), invalid field rejection

### Phase 2: Tests Requiring Mocking

**Create `tests/conftest.py`** with shared fixtures:
- Mock `Anthropic` client that returns configurable responses
- `OrgProfile` factory with sensible defaults
- `SimulationState` factory at various week stages
- `PersonaState` factory for each archetype

**`src/agents/orchestrator.py` — Tool loop**:
- Mock API to return tool_use blocks, verify routing to KB/metrics/replanner
- Test stop condition (end_turn tool or max iterations)
- Test multi-turn tool accumulation
- Test context building from simulation state

**`src/simulation/controller.py`** — Integration tests:
- Mock orchestrator and persona agents
- Run 2-3 week simulations, verify state evolution
- Test event application (sentiment modifiers, grudge increases)
- Test `_check_termination()` boundary conditions (success at threshold, timeout at budget)
- Test friction outcomes (delayed, degraded, cancelled, backfire effects on state)
- Test `_flywheel_to_adoption_metrics()` field mapping
- Test log persistence (JSON lines format, audit trail)

**`src/tools/replanner.py`**:
- Test prompt construction from state (last 6 weeks summary, persona health)
- Mock API call, verify response handling

### Phase 3: CLI and End-to-End

**`src/main.py`**:
- Test argument parsing for simulate/experiment/dashboard commands
- Test profile loading and override logic
- Test backend flag routing
- Test exit code logic

**End-to-end test**:
- Single deterministic 4-week simulation with fully mocked LLM calls
- Verify complete flow: plan → turns → events → metrics → termination → logs

**CI Pipeline**:
- GitHub Actions workflow running `pytest` on push/PR
- Separate markers for fast unit tests vs slower integration tests
