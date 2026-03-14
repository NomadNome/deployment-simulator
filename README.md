# Enterprise AI Deployment Simulator

A multi-agent orchestration system that simulates enterprise AI rollouts. An **orchestrator agent** (Claude Sonnet) acts as a deployment strategist — generating and adapting rollout plans in real time — while **persona agents** (Claude Haiku) model realistic stakeholder behavior: skeptical engineers, enthusiastic champions, risk-averse executives, and overwhelmed IT admins.

> **The hardest problem in enterprise AI isn't the model. It's the adoption.**

## Why This Exists

Enterprise AI deployments fail at the human layer, not the technical one. Teams resist new workflows, executives deprioritize when quarterly pressures mount, IT becomes a bottleneck, and champions burn out without support. This simulator encodes those dynamics into an agentic system that deployment teams can run scenarios against before committing real resources.

**Three use cases:**
- **Pre-deployment stress testing** — Feed in an org profile and watch how adoption unfolds. Where will resistance cluster?
- **Enablement team training** — New CSMs and engagement managers practice rollout decision-making in a safe environment.
- **Playbook validation** — Test your change management playbook against adversarial conditions.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Simulation Controller               │
│  (turn management, events, state, termination)   │
├────────────────┬────────────────────────────────┤
│  HITL Router   │     Flywheel Metrics           │
│  (confidence   │     (Pilot Scorecard,          │
│   routing,     │      CS-grade KPIs)            │
│   audit trail) │                                │
└──────┬─────────┴────────────┬───────────────────┘
       │                      │
 ┌─────▼─────┐      ┌────────▼────────┐
 │Orchestrator│      │  Persona Agents  │
 │  (Sonnet)  │      │    (Haiku x4)    │
 └─────┬─────┘      │ • Skeptical IC   │
       │             │ • Champion       │
 ┌─────▼─────┐      │ • Risk-Averse VP │
 │   Tools    │      │ • IT Admin       │
 │ • RAG KB   │      └─────────────────┘
 │  (44 tactics)
 │ • Metrics  │
 │ • Replan   │
 └───────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/NomadNome/deployment-simulator.git
cd deployment-simulator
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Set your Anthropic API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env

# Run a simulation
python -m src.main simulate --profile nova_tech --seed 42

# Launch the dashboard
python -m src.main dashboard
```

### Available Profiles

| Profile | Industry | Maturity | Sponsorship | Budget | Target | Expected Outcome |
|---------|----------|----------|-------------|--------|--------|-----------------|
| `nova_tech` | Technology | Medium | Moderate | 24 wks | 70% | Swing case |
| `acme_financial` | Financial Services | High | Strong | 24 wks | 70% | Likely success |
| `meridian_healthcare` | Healthcare | Low | Weak | 20 wks | 60% | Likely failure |

### CLI Commands

```bash
# Run a single simulation
python -m src.main simulate --profile nova_tech --seed 42
python -m src.main simulate --profile acme_financial --weeks 12
python -m src.main simulate --profile meridian_healthcare --mode guided

# Run batch experiments
python -m src.main experiment sponsorship_sensitivity --parallel 3

# Launch Streamlit dashboard
python -m src.main dashboard

# List all profiles and experiments
python -m src.main list
```

### HITL Modes

```bash
--mode autopilot   # All interventions auto-execute (default, for batch runs)
--mode guided      # Pause on review/escalate items (for training)
--mode demo        # Pause on every intervention (for interview walkthroughs)
```

## Demo Runs

### Run 1: Nova Tech — Success (73.2% adoption, 13 weeks)

The orchestrator deploys a phased strategy targeting the champion first, then pivoting to the skeptical IC with evidence-based tool demos. The VP comes onboard after seeing ROI data in week 6. The IT admin remains the weakest link (0.37 adoption) — a realistic pattern where IT deprioritizes without explicit escalation support.

```
Final Persona States
┌───────────────────────┬───────────┬──────────┬───────┬───────────────────────┐
│ Persona               │ Sentiment │ Adoption │ Trust │ Interventions Received│
├───────────────────────┼───────────┼──────────┼───────┼───────────────────────┤
│ skeptical_ic          │ 1.00      │ 0.80     │ 0.85  │ 15                    │
│ enthusiastic_champion │ 1.00      │ 1.00     │ 0.87  │ 9                     │
│ risk_averse_vp        │ 1.00      │ 0.75     │ 0.83  │ 11                    │
│ overwhelmed_it_admin  │ 0.69      │ 0.37     │ 0.57  │ 4                     │
└───────────────────────┴───────────┴──────────┴───────┴───────────────────────┘
```

### Run 2: Meridian Healthcare — Failure (59.6% adoption, 20 weeks, timed out)

A genuinely hostile environment: weak executive sponsorship, low technical maturity, VP starting at 0.8 cognitive load, sponsor departure at week 3, budget freeze at week 6, and interventions capped at 2/week. The orchestrator fought for every point of adoption — triggered 2 replans, deployed 57 interventions over 20 weeks — but fell 0.4% short of the 60% target. The VP (0.36 adoption) and IT admin (0.17 adoption) were unreachable anchors that dragged the deployment down.

```
Outcome: DEPLOYMENT FAILED (timeout)
Duration: 20 weeks | Final Adoption: 59.6% | Target: 60%
Replans Triggered: 2 | Events Encountered: 5
```

### Run 3: Nova Tech with Disruptions — Partial (70.1% adoption, 11 weeks)

Forced disruptions: competing tool demo at week 5 (tanks IC confidence), sponsor departure at week 10 (VP sentiment drops). The orchestrator recovers from the competitive threat by shifting to evidence-based bake-off tactics, but the late sponsor departure creates a confidence dip visible in the HITL audit trail. The system barely clears the 70% threshold before the disruption fully compounds.

### Knowledge Base Comparison

The simulator ships with a 44-tactic knowledge base: 18 ADKAR/Kotter framework entries plus 26 field-tested tactics derived from real enterprise deployment patterns. The field-tested entries cover stall detection, recovery tactics, champion management, industry-specific sequencing, and ADKAR reframes.

Field-tested tactics receive a 1.3x relevance boost in keyword search, so the orchestrator preferentially selects battle-tested interventions when they match the current situation.

| Profile | 18 Tactics (Generic) | 44 Tactics (Field-tested) | Delta |
|---------|---------------------|--------------------------|-------|
| Nova Tech | 73.2% in 13 wks | 71.2% in 13 wks | Comparable |
| Acme Financial | 72.2% in 10 wks | 70.6% in 13 wks | Comparable |
| Meridian Healthcare | 60.0% in 8 wks | 60.3% in 7 wks | 1 week faster |

The real delta shows in **disruption scenarios** where the orchestrator needs recovery and stall-detection tactics that the generic KB doesn't have.

## Dashboard

Launch with `python -m src.main dashboard` (Streamlit + Plotly):

**Pilot Scorecard** — Adoption curves, flywheel metrics over time, intervention timeline, persona responses by week, risk flags, event log.

**HITL Audit Trail** — Routing distribution (auto/review/escalate), confidence scores over time with threshold lines, full decision log.

**Experiment Results** — Adoption by configuration, sensitivity analysis tables, cross-variable heatmap (e.g., sponsorship x maturity), persona sentiment box plots, best/worst identification.

## How It Works

Each simulation runs a structured loop:

1. **Context Assembly** — The controller compiles current state for the orchestrator
2. **Orchestrator Planning** — The orchestrator selects 1–3 interventions using its tools (RAG knowledge base, metrics tracker, re-planner). Each intervention includes a confidence score.
3. **Confidence Routing (HITL)** — Interventions are routed by confidence: auto-execute (>=80%), human review (50–79%), or escalate (<50%). In guided mode, review/escalate items pause for human approval.
4. **Intervention Dispatch** — Approved interventions are routed to targeted persona agents
5. **Persona Response** — Each persona responds based on hidden internal state (sentiment, trust, cognitive load)
6. **Flywheel Metrics Update** — Computes activation rate, weekly engaged users, completion rate, override rate, and cycle-time delta. Generates the Pilot Scorecard.
7. **Event Check** — Random organizational events may fire (reorgs, budget freezes, competing tools, sponsor departures)
8. **Termination Check** — Success (adoption threshold), failure (timeout), or continue

The orchestrator **cannot see** persona sentiment scores directly. It must infer adoption trajectory from behavioral signals — just like a real deployment strategist.

## Adoption Flywheel Metrics

| Metric | What It Measures |
|--------|-----------------|
| Activation Rate | Users who completed a meaningful action (not just logged in) |
| Weekly Engaged Users | Retention signal — are users coming back? |
| Completion Rate | AI workflows reaching successful end state |
| Override Rate | Human modifications/rejections of orchestrator decisions |
| Cycle-Time Delta | Time improvement with AI vs. without |

These metrics are surfaced in the **Pilot Scorecard** — a traffic-light executive readout generated each turn.

## Scenario Testing

Run batch experiments to test conditions across parameter sweeps:

```bash
python -m src.main experiment sponsorship_sensitivity   # 27 runs: 3 sponsorship x 3 maturity x 3 seeds
python -m src.main experiment disruption_resilience      # Forced reorg, sponsor departure, budget freeze
python -m src.main experiment scale_effects              # 12 runs: 4 team sizes x 3 maturity levels
```

Each experiment generates:
- Sensitivity analysis tables (avg adoption, success rate per variable)
- Cross-variable adoption heatmaps
- Comparison report with best/worst configurations
- Per-run JSON logs for drill-down

## Project Structure

```
deployment-simulator/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py        # Deployment strategist (Sonnet + tool use)
│   │   └── persona.py             # 4 stakeholder personas (Haiku)
│   ├── tools/
│   │   ├── knowledge_base.py      # 44-tactic RAG (ADKAR, Kotter, field-tested)
│   │   ├── metrics_tracker.py     # Legacy adoption metrics
│   │   └── replanner.py           # Revised plan generation
│   ├── simulation/
│   │   ├── controller.py          # Turn-by-turn simulation loop
│   │   ├── events.py              # 7 organizational event types
│   │   ├── experiment_runner.py   # Batch execution + parameter sweeps
│   │   ├── flywheel_metrics.py    # CS-grade metrics + Pilot Scorecard
│   │   ├── hitl_router.py         # Confidence routing + audit trail
│   │   └── profiles.py            # 3 sample org profiles
│   ├── dashboard/
│   │   ├── app.py                 # Streamlit dashboard (3 pages)
│   │   └── generate_sample_data.py
│   ├── models.py                  # Pydantic data models
│   └── main.py                    # CLI (simulate / experiment / dashboard / list)
├── field_tested_tactics.py        # 26 field-tested KB entries
├── data/
│   ├── simulation_logs/           # JSONL logs + audit trails
│   └── experiments/               # Batch results + comparison reports
├── pyproject.toml
└── README.md
```

## Cost Estimate

| Scenario | Per Run | Monthly (10 runs) |
|----------|---------|-------------------|
| Short run (4 weeks) | $0.50–$1 | $5–$10 |
| Full run (24 weeks) | $2–$5 | $20–$50 |
| Experiment batch (27 runs) | $15–$40 | — |

## License

MIT
