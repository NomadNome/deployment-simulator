"""Generate sample simulation data for dashboard demo purposes."""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def generate_sample_simulation(
    sim_id: str = "demo_run",
    weeks: int = 12,
    seed: int = 42,
    base_adoption: float = 0.30,
    growth_rate: float = 0.04,
) -> tuple[list[dict], list[dict]]:
    """Generate a mock simulation log and audit trail."""
    random.seed(seed)
    turns = []
    audit = []

    persona_types = ["skeptical_ic", "enthusiastic_champion", "risk_averse_vp", "overwhelmed_it_admin"]
    intervention_types = [
        "executive_briefing", "workshop", "one_on_one", "tool_demo",
        "peer_learning_cohort", "quick_win_session", "office_hours",
    ]
    event_catalog = [
        {"type": "reorg", "desc": "Reorganization announced, reporting structures changing."},
        {"type": "competing_tool", "desc": "Competitor AI tool demoed at internal tech talk."},
        {"type": "positive_press", "desc": "Industry publication features AI success story."},
        {"type": "security_incident", "desc": "Security vulnerability disclosed in similar AI tool."},
    ]

    adoption = base_adoption
    sentiment = {p: 0.4 + random.uniform(-0.1, 0.1) for p in persona_types}

    for week in range(1, weeks + 1):
        # Random growth with noise
        adoption = min(1.0, adoption + growth_rate + random.uniform(-0.02, 0.03))

        # Update sentiments
        for p in persona_types:
            sentiment[p] = max(0.0, min(1.0, sentiment[p] + random.uniform(-0.03, 0.05)))

        # Generate 1-3 interventions
        num_interventions = random.randint(1, 3)
        interventions = []
        for _ in range(num_interventions):
            itype = random.choice(intervention_types)
            target = random.choice(persona_types)
            interventions.append({
                "intervention_type": itype,
                "target_persona": target,
                "content": f"Week {week} {itype.replace('_', ' ')} for {target.replace('_', ' ')}",
                "rationale": f"Targeting {target.replace('_', ' ')} based on current adoption trajectory",
            })

            # Audit entry
            confidence = 0.75 + random.uniform(-0.2, 0.15)
            confidence = max(0.05, min(0.99, confidence))
            lane = "auto_execute" if confidence >= 0.80 else "human_review" if confidence >= 0.50 else "escalate"
            audit.append({
                "timestamp": datetime.now().isoformat(),
                "week": week,
                "intervention_type": itype,
                "target_persona": target,
                "confidence_score": round(confidence, 3),
                "routing_lane": lane,
                "human_decision": "auto",
                "human_modification": None,
                "orchestrator_reasoning": f"Week {week} reasoning for {itype}",
            })

        # Maybe fire an event
        events = []
        if random.random() < 0.15:
            event = random.choice(event_catalog)
            events.append({
                "event_type": event["type"],
                "trigger_week": week,
                "affected_personas": random.sample(persona_types, 2),
                "sentiment_modifiers": {},
                "description": event["desc"],
            })
            # Event dip
            adoption = max(0.0, adoption - random.uniform(0.02, 0.05))

        # Persona responses
        responses = {}
        for iv in interventions:
            target = iv["target_persona"]
            responses[target] = f"[Week {week}] Response from {target}: Acknowledged the {iv['intervention_type'].replace('_', ' ')}."

        # Risk flags
        risk_flags = []
        if adoption < 0.35:
            risk_flags.append(f"WARNING: Overall adoption below 35%")
        for p, s in sentiment.items():
            if s < 0.30:
                risk_flags.append(f"CRITICAL: {p} sentiment below 30%")

        turn = {
            "turn_id": str(uuid4())[:8],
            "week": week,
            "timestamp": datetime.now().isoformat(),
            "orchestrator_reasoning": f"Week {week}: Analyzing adoption at {adoption:.0%}. Planning interventions.",
            "interventions": interventions,
            "persona_responses": responses,
            "adoption_metrics": {
                "week": week,
                "overall_adoption_pct": round(adoption, 3),
                "login_rate": round(min(1.0, adoption * 1.2 + 0.05), 3),
                "feature_usage_depth": round(adoption * 0.7, 3),
                "nps_proxy": round((sum(sentiment.values()) / len(sentiment) - 0.5) * 2, 3),
                "risk_flags": risk_flags,
                "budget_remaining_weeks": 24 - week,
            },
            "events_fired": events,
            "replan_triggered": random.random() < 0.1,
        }
        turns.append(turn)

    return turns, audit


def main():
    """Generate sample data files for the dashboard."""
    log_dir = Path("data/simulation_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate 2 sample simulations
    for sim_name, kwargs in [
        ("demo_success", {"weeks": 12, "seed": 42, "growth_rate": 0.045}),
        ("demo_struggle", {"weeks": 16, "seed": 99, "base_adoption": 0.20, "growth_rate": 0.025}),
    ]:
        turns, audit = generate_sample_simulation(sim_id=sim_name, **kwargs)

        log_path = log_dir / f"sim_{sim_name}.jsonl"
        with open(log_path, "w") as f:
            for turn in turns:
                f.write(json.dumps(turn) + "\n")

        audit_path = log_dir / f"sim_{sim_name}_audit.json"
        with open(audit_path, "w") as f:
            json.dump(audit, f, indent=2)

        print(f"Generated: {log_path} ({len(turns)} turns)")
        print(f"Generated: {audit_path} ({len(audit)} audit entries)")

    # Generate sample experiment results
    exp_dir = Path("data/experiments/sponsorship_demo/20260314_120000")
    exp_dir.mkdir(parents=True, exist_ok=True)

    random.seed(77)  # Deterministic demo data
    results = []
    for sponsorship in ["weak", "moderate", "strong"]:
        for maturity in ["low", "medium", "high"]:
            for seed in [42, 123]:
                # Wider spread: weak+low bottoms out, strong+high soars
                s_bonus = {"weak": 0.0, "moderate": 0.18, "strong": 0.38}[sponsorship]
                m_bonus = {"low": 0.0, "medium": 0.12, "high": 0.25}[maturity]
                noise = random.uniform(-0.06, 0.06)
                # Interaction effect: weak sponsorship + low maturity is especially bad
                interaction_penalty = 0.08 if sponsorship == "weak" and maturity == "low" else 0.0
                base = 0.18 + s_bonus + m_bonus + noise - interaction_penalty
                adoption = min(0.95, max(0.08, base))
                outcome = "success" if adoption >= 0.70 else "failure_timeout"

                results.append({
                    "config_label": f"executive_sponsorship={sponsorship} | technical_maturity={maturity}",
                    "parameters": {
                        "executive_sponsorship": sponsorship,
                        "technical_maturity": maturity,
                    },
                    "seed": seed,
                    "outcome": outcome,
                    "final_adoption_pct": round(adoption, 3),
                    "weeks_elapsed": 24 if outcome != "success" else random.randint(10, 20),
                    "total_interventions": random.randint(20, 45),
                    "events_encountered": random.randint(1, 5),
                    "replans_triggered": random.randint(0, 3),
                    "persona_final_sentiments": {
                        "skeptical_ic": round(max(0, 0.2 + s_bonus * 0.6 + random.uniform(-0.1, 0.1)), 3),
                        "enthusiastic_champion": round(min(1, 0.5 + m_bonus * 0.4 + s_bonus * 0.3 + random.uniform(-0.1, 0.1)), 3),
                        "risk_averse_vp": round(max(0, 0.2 + s_bonus * 0.9 + random.uniform(-0.1, 0.1)), 3),
                        "overwhelmed_it_admin": round(max(0, 0.25 + m_bonus * 0.6 + random.uniform(-0.1, 0.1)), 3),
                    },
                    "duration_seconds": round(random.uniform(30, 120), 1),
                })

    exp_data = {
        "experiment": "sponsorship_sensitivity",
        "description": "How does executive sponsorship affect outcomes across maturity levels?",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "results": results,
    }

    results_path = exp_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(exp_data, f, indent=2)

    # Generate comparison report
    sensitivity = {}
    for var_name in ["executive_sponsorship", "technical_maturity"]:
        sensitivity[var_name] = {}
        values = set(r["parameters"][var_name] for r in results)
        for value in sorted(values):
            matching = [r for r in results if r["parameters"][var_name] == value]
            sensitivity[var_name][value] = {
                "avg_adoption": round(sum(r["final_adoption_pct"] for r in matching) / len(matching), 3),
                "success_rate": sum(1 for r in matching if r["outcome"] == "success") / len(matching),
                "runs": len(matching),
            }

    best = max(results, key=lambda r: r["final_adoption_pct"])
    worst = min(results, key=lambda r: r["final_adoption_pct"])
    comparison = {
        "experiment": "sponsorship_sensitivity",
        "sensitivity": sensitivity,
        "best": {"config": best["config_label"], "adoption": best["final_adoption_pct"]},
        "worst": {"config": worst["config_label"], "adoption": worst["final_adoption_pct"]},
    }

    comp_path = exp_dir / "comparison_report.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"Generated: {results_path} ({len(results)} runs)")
    print(f"Generated: {comp_path}")


if __name__ == "__main__":
    main()
