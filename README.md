# Enterprise AI Deployment Simulator

A decision-support simulator for AI rollout strategy under organizational disruption. An **orchestrator agent** (Claude Sonnet) acts as a deployment strategist — generating and adapting rollout plans in real time — while **persona agents** (Claude Haiku) model realistic stakeholder behavior: skeptical engineers, enthusiastic champions, risk-averse executives, and overwhelmed IT admins. Feed in an org profile, inject disruptions, and watch where adoption breaks.

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

### Headline Result: Field-Tested Knowledge Base Under Disruption

The simulator ships with a 44-tactic knowledge base: 18 ADKAR/Kotter framework entries plus 26 field-tested tactics derived from real enterprise deployment patterns. The field-tested entries cover stall detection, recovery playbooks, champion burnout prevention, competitive response (bake-off tactics), silent VP pattern recognition, and ADKAR reframes prioritizing Desire over Knowledge.

Field-tested tactics receive a 1.3x relevance boost in keyword search, so the orchestrator preferentially selects battle-tested interventions when they match the current situation.

**In stable conditions**, both knowledge bases produce comparable outcomes:

| Profile | 18 Tactics (Generic) | 44 Tactics (Field-tested) | Delta |
|---------|---------------------|--------------------------|-------|
| Nova Tech | 73.2% in 13 wks | 71.2% in 13 wks | Comparable |
| Acme Financial | 72.2% in 10 wks | 70.6% in 13 wks | Comparable |
| Meridian Healthcare | 60.0% in 8 wks | 60.3% in 7 wks | 1 week faster |

**Under disruption, the difference is clear.** Same scenario — Nova Tech with a competing tool demo at week 5 and sponsor departure at week 10:

| | Generic KB (18 tactics) | Field-tested KB (44 tactics) | Delta |
|---|---|---|---|
| **Weeks to target** | 13 | **12** | **1 week faster** |
| **Total interventions** | 39 | **35** | **4 fewer** |
| **Final adoption** | 71.0% | 70.2% | Same outcome |
| **Events weathered** | 5 | 5 | Same conditions |

**1 week faster. 4 fewer interventions. Same outcome.** The orchestrator with field-tested tactics didn't just know more — it wasted less. It reached the same target with fewer moves because it had the stall detection patterns, the competitive bake-off response, and the silent VP escalation playbook. That's the difference between a junior strategist who throws everything at the wall and a senior one who makes precise, well-timed interventions because they've seen the patterns before.

> *"I added 26 field-tested tactics from real enterprise deployment experience and reran the same disruption scenario. The orchestrator hit the adoption target one week faster with four fewer interventions. It didn't just know more — it wasted less. That's what domain expertise does: it's not about having more options, it's about knowing which options to skip."*

## Sample Run Artifact

A complete canonical run is committed at [`examples/canonical_run/`](examples/canonical_run/) so reviewers can inspect the full mechanics without an API key.

**Nova Technologies — 72.6% adoption in 19 weeks (success)**

| File | What It Contains |
|------|-----------------|
| [`simulation_log.jsonl`](examples/canonical_run/simulation_log.jsonl) | 19 turns of JSONL: orchestrator reasoning (ASSESS → DIAGNOSE → SELECT), interventions, persona responses, adoption metrics, events fired |
| [`hitl_audit_trail.json`](examples/canonical_run/hitl_audit_trail.json) | 57 HITL routing decisions: 18 auto-execute, 39 human review, 0 escalated |
| [`metadata.json`](examples/canonical_run/metadata.json) | Run summary: outcome, final adoption, weeks elapsed |

This run includes 7 organizational disruptions (sponsor departure week 5, budget freeze weeks 7-8, reorg week 11, competing tool weeks 9 and 14, security incident week 17) and demonstrates the orchestrator's adaptive re-planning through each crisis.

## Dashboard

Launch with `python -m src.main dashboard` (Streamlit + Plotly):

**Pilot Scorecard** — Adoption curves, flywheel metrics over time, intervention timeline, persona responses by week, risk flags, event log.

**HITL Audit Trail** — Routing distribution (auto/review/escalate), confidence scores over time with threshold lines, full decision log.

**Experiment Results** — Adoption by configuration, sensitivity analysis tables, cross-variable heatmap (e.g., sponsorship x maturity), persona sentiment box plots, best/worst identification.

## What Is Simulated vs. What Is Measured

Not everything in this system comes from the same place. Understanding the boundary between hard-coded dynamics, LLM-generated behavior, and experimental observations is critical to evaluating the results.

| Layer | What It Does | Source |
|-------|-------------|--------|
| **Org profiles** | Team size, maturity, sponsorship level, budget, adoption target | Hard-coded inputs (`src/simulation/profiles.py`) |
| **Adoption metrics** | `overall_adoption_pct`, `login_rate`, `feature_usage_depth`, `nps_proxy` | Deterministic Python — computed from persona states each turn (`src/simulation/flywheel_metrics.py`) |
| **Persona hidden state** | Sentiment, trust, cognitive load, grudge score, adoption likelihood | Deterministic update rules with stochastic noise (`src/agents/persona.py:update_state()`, `src/simulation/realism.py`) |
| **Orchestrator strategy** | Which interventions to deploy, to whom, with what rationale | LLM-generated (Claude Sonnet via tool use) — the orchestrator sees metrics but NOT persona hidden state |
| **Persona responses** | Natural-language reactions to interventions | LLM-generated (Claude Haiku) — conditioned on hidden state the orchestrator cannot see |
| **Intervention effects** | How much an intervention moves sentiment/trust/adoption | Lookup table with fatigue multipliers, friction rolls, and grudge dampening (`src/agents/persona.py:EFFECT_TABLE`, `src/simulation/realism.py`) |
| **Organizational events** | Reorgs, sponsor departures, budget freezes, competing tools | Stochastic (probability per week) or forced via experiment config (`src/simulation/events.py`) |
| **HITL routing** | Auto-execute / human review / escalate decisions | Deterministic threshold on orchestrator confidence scores (`src/simulation/hitl_router.py`) |
| **Experimental observations** | Final adoption, weeks to target, success/failure, sensitivity analysis | Measured outputs from batch runs — these are the results, not inputs |

**Key implication:** The orchestrator and personas are the only LLM-powered components. Everything else — metrics, state updates, event firing, routing — is deterministic Python. This means simulation outcomes are reproducible given the same seed, and variation between runs comes from (a) LLM response stochasticity and (b) event randomness.

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

## Validated Failure Patterns

The simulator intentionally reproduces five enterprise deployment failure patterns observed in real rollouts. Each pattern maps to specific mechanics in the codebase.

| # | Failure Pattern | What Happens in the Real World | How the Simulator Produces It |
|---|----------------|-------------------------------|------------------------------|
| 1 | **Champion burnout** | Early adopters burn out evangelizing without air cover. They stop doing the work while still saying the right things. | Fatigue multiplier degrades repeated interventions to the same persona: `[1.0, 0.7, 0.4, 0.2]` (`realism.py:59`). Champion system prompt: *"If burnout is high (7+), your enthusiasm becomes performative"* (`persona.py:49`). |
| 2 | **Silent VP** | The executive doesn't reject the initiative — they just go quiet. Meetings get rescheduled, decisions get deferred, budget discussions stall. | VP system prompt: *"If competing priorities are high (7+), you will deprioritize without warning. You just go quiet"* (`persona.py:66`). Grudge system tracks `weeks_since_contact` and penalizes non-contacted personas (`realism.py:193-198`). |
| 3 | **IT bottleneck** | IT is the invisible anchor. They're not opposed — they just have 47 other things to do. The rollout stalls on provisioning, SSO, or security review. | Cognitive load > 0.7 dampens ALL intervention effects by 70% (`persona.py:189-191`). IT admin prompt: *"You become the silent bottleneck that nobody notices until the rollout stalls"* (`persona.py:83`). |
| 4 | **Sponsor departure shock** | When the executive sponsor leaves, momentum collapses across all stakeholders. The replacement has their own priorities. | `SPONSOR_DEPARTURE` event fires -0.20 sentiment to VP, -0.12 to champion, plus grudge accumulation (`events.py:46-61`). This is the single largest negative sentiment modifier in the event catalog. |
| 5 | **Competing tool anxiety** | A competitor demo at an internal tech talk creates doubt, especially among already-skeptical engineers. | `COMPETING_TOOL` event fires -0.10 to skeptical IC, -0.08 to VP (`events.py:29-44`). The IC's low base sentiment (starting ~0.30) means this can push them below the trust threshold where they stop sharing real concerns (`persona.py:33`). |

These patterns emerge naturally from the interaction of deterministic state mechanics and LLM-generated persona behavior. They are not scripted outcomes — the orchestrator can recover from any of them with the right interventions at the right time. Whether it does is the experimental question.

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
├── examples/
│   └── canonical_run/              # Complete run artifact (inspectable without API key)
│       ├── simulation_log.jsonl    # 19-turn JSONL log
│       ├── hitl_audit_trail.json   # 57 HITL routing decisions
│       └── metadata.json           # Run summary
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
