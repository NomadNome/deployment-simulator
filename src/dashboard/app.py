"""Streamlit Dashboard — Pilot Scorecard, HITL Queue, and Experiment Viewer."""

from __future__ import annotations

import json
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page Config ───────────────────────────────────────────────

st.set_page_config(
    page_title="Deployment Simulator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")
SIM_LOG_DIR = DATA_DIR / "simulation_logs"
EXP_DIR = DATA_DIR / "experiments"


# ── Sidebar Navigation ───────────────────────────────────────

st.sidebar.title("Deployment Simulator")
page = st.sidebar.radio(
    "Navigate",
    ["Pilot Scorecard", "HITL Audit Trail", "Experiment Results"],
)


# ── Data Loading Helpers ──────────────────────────────────────

def load_simulation_log(log_path: Path) -> list[dict]:
    """Load a JSONL simulation log into a list of turn records."""
    turns = []
    with open(log_path) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))
    return turns


def load_audit_trail(audit_path: Path) -> list[dict]:
    """Load a JSON audit trail."""
    with open(audit_path) as f:
        return json.load(f)


def load_experiment_results(results_path: Path) -> dict:
    """Load experiment results JSON."""
    with open(results_path) as f:
        return json.load(f)


def _describe_log(log_path: Path) -> str:
    """Generate a human-readable label for a simulation log."""
    # Try metadata file first (new format)
    meta_path = log_path.parent / log_path.name.replace(".jsonl", "_meta.json")
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            org = meta.get("org_name", "Unknown")
            adoption = meta.get("final_adoption", 0)
            weeks = meta.get("weeks_elapsed", 0)
            outcome = meta.get("outcome", "unknown")
            label = "Success" if outcome == "success" else "Failed" if "failure" in outcome else outcome
            return f"{org} | {adoption:.0%} in {weeks}wks | {label} ({log_path.stem[-7:]})"
        except Exception:
            pass

    # Fallback: scan log content
    try:
        with open(log_path) as f:
            first_line = f.readline()
            last_line = first_line
            for line in f:
                if line.strip():
                    last_line = line
        last = json.loads(last_line)
        weeks = last["week"]
        adoption = last["adoption_metrics"]["overall_adoption_pct"]

        # Scan full text for profile hints
        with open(log_path) as f:
            all_text = f.read().lower()
        if "demo" in log_path.stem:
            profile = "Demo Data"
        elif any(kw in all_text for kw in ["nova", "analytics copilot", "product team"]):
            profile = "Nova Tech"
        elif any(kw in all_text for kw in ["acme", "regulatory", "sox", "compliance automation"]):
            profile = "Acme Financial"
        elif any(kw in all_text for kw in ["meridian", "clinical", "hipaa", "ehr", "documentation summarization"]):
            profile = "Meridian Healthcare"
        else:
            profile = "Simulation"

        outcome = "Success" if adoption >= 0.60 else "Failed"
        return f"{profile} | {adoption:.0%} in {weeks}wks | {outcome} ({log_path.stem[-7:]})"
    except Exception:
        return log_path.stem


def find_simulation_logs() -> dict[str, Path]:
    """Find all simulation log files with descriptive labels."""
    logs = {}
    if SIM_LOG_DIR.exists():
        for f in sorted(SIM_LOG_DIR.glob("sim_*.jsonl"), reverse=True):
            label = _describe_log(f)
            logs[label] = f
    return logs


def find_audit_trails() -> dict[str, Path]:
    """Find all audit trail files with descriptive labels."""
    trails = {}
    if SIM_LOG_DIR.exists():
        for f in sorted(SIM_LOG_DIR.glob("sim_*_audit.json"), reverse=True):
            log_path = f.parent / f.name.replace("_audit.json", ".jsonl")
            label = _describe_log(log_path) if log_path.exists() else f.stem.replace("_audit", "")
            trails[label] = f
    return trails


def find_experiments() -> dict[str, Path]:
    """Find all experiment result files."""
    experiments = {}
    if EXP_DIR.exists():
        for results_file in sorted(EXP_DIR.glob("*/*/results.json"), reverse=True):
            label = f"{results_file.parent.parent.name} / {results_file.parent.name}"
            experiments[label] = results_file
    return experiments


# ── Page: Pilot Scorecard ─────────────────────────────────────

def page_pilot_scorecard():
    st.header("Pilot Scorecard")

    logs = find_simulation_logs()
    if not logs:
        st.info("No simulation logs found. Run a simulation first:\n\n"
                "`python -m src.main simulate --profile nova_tech --seed 42`")
        return

    selected = st.sidebar.selectbox("Simulation Run", list(logs.keys()))
    turns = load_simulation_log(logs[selected])

    if not turns:
        st.warning("Empty simulation log.")
        return

    # Extract time-series metrics
    weeks = [t["week"] for t in turns]
    adoption = [t["adoption_metrics"]["overall_adoption_pct"] for t in turns]
    login_rate = [t["adoption_metrics"]["login_rate"] for t in turns]
    feature_depth = [t["adoption_metrics"]["feature_usage_depth"] for t in turns]
    nps = [t["adoption_metrics"]["nps_proxy"] for t in turns]

    # KPI cards for latest week
    latest = turns[-1]["adoption_metrics"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Adoption", f"{latest['overall_adoption_pct']:.0%}",
                delta=f"{adoption[-1] - adoption[-2]:.1%}" if len(adoption) > 1 else None)
    col2.metric("Login Rate", f"{latest['login_rate']:.0%}")
    col3.metric("Feature Depth", f"{latest['feature_usage_depth']:.0%}")
    col4.metric("NPS Proxy", f"{latest['nps_proxy']:+.2f}")

    # Risk flags
    if latest.get("risk_flags"):
        with st.expander(f"Risk Flags ({len(latest['risk_flags'])})", expanded=True):
            for flag in latest["risk_flags"]:
                if flag.startswith("CRITICAL"):
                    st.error(flag)
                elif flag.startswith("WARNING"):
                    st.warning(flag)
                else:
                    st.info(flag)

    # Adoption curve
    st.subheader("Adoption Over Time")
    fig_adoption = go.Figure()
    fig_adoption.add_trace(go.Scatter(
        x=weeks, y=adoption, mode="lines+markers", name="Overall Adoption",
        line=dict(color="#2ecc71", width=3),
    ))
    fig_adoption.add_trace(go.Scatter(
        x=weeks, y=login_rate, mode="lines", name="Login Rate",
        line=dict(color="#3498db", dash="dot"),
    ))
    fig_adoption.add_trace(go.Scatter(
        x=weeks, y=feature_depth, mode="lines", name="Feature Depth",
        line=dict(color="#9b59b6", dash="dash"),
    ))
    fig_adoption.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        xaxis_title="Week",
        yaxis_title="Rate",
        height=400,
        margin=dict(l=40, r=20, t=30, b=40),
    )
    st.plotly_chart(fig_adoption, use_container_width=True)

    # Intervention timeline
    st.subheader("Intervention Timeline")
    intervention_data = []
    for turn in turns:
        for iv in turn["interventions"]:
            intervention_data.append({
                "Week": turn["week"],
                "Type": iv["intervention_type"],
                "Target": iv["target_persona"],
                "Rationale": iv["rationale"][:80],
            })

    if intervention_data:
        fig_timeline = px.scatter(
            intervention_data,
            x="Week",
            y="Target",
            color="Type",
            hover_data=["Rationale"],
            height=300,
        )
        fig_timeline.update_traces(marker=dict(size=12))
        fig_timeline.update_layout(margin=dict(l=40, r=20, t=30, b=40))
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No interventions recorded.")

    # Persona responses — full text, organized by week
    st.subheader("Persona Responses")
    weeks_with_responses = [
        t for t in turns if t.get("persona_responses")
    ]
    if weeks_with_responses:
        week_tabs = st.tabs([f"Week {t['week']}" for t in weeks_with_responses])
        for tab, turn in zip(week_tabs, weeks_with_responses):
            with tab:
                for persona, response in turn["persona_responses"].items():
                    persona_label = persona.replace("_", " ").title()
                    response_text = response if isinstance(response, str) else str(response)
                    # Color-code by persona
                    colors = {
                        "skeptical_ic": "🔴",
                        "enthusiastic_champion": "🟢",
                        "risk_averse_vp": "🟡",
                        "overwhelmed_it_admin": "🟠",
                    }
                    icon = colors.get(persona, "⚪")
                    st.markdown(f"### {icon} {persona_label}")
                    st.markdown(response_text)
                    st.divider()
    else:
        st.info("No persona responses recorded.")

    # Events
    events_data = []
    for turn in turns:
        for event in turn.get("events_fired", []):
            events_data.append({
                "Week": turn["week"],
                "Event": event["event_type"],
                "Description": event["description"][:100],
            })
    if events_data:
        st.subheader("Events Fired")
        st.dataframe(events_data, use_container_width=True)


# ── Page: HITL Audit Trail ────────────────────────────────────

def page_hitl_audit():
    st.header("HITL Audit Trail")

    trails = find_audit_trails()
    if not trails:
        st.info("No audit trails found. Run a simulation first:\n\n"
                "`python -m src.main simulate --profile nova_tech --seed 42`")
        return

    selected = st.sidebar.selectbox("Simulation Run", list(trails.keys()))
    audit = load_audit_trail(trails[selected])

    if not audit:
        st.warning("Empty audit trail.")
        return

    # Summary metrics
    total = len(audit)
    auto_count = sum(1 for d in audit if d["routing_lane"] == "auto_execute")
    review_count = sum(1 for d in audit if d["routing_lane"] == "human_review")
    escalate_count = sum(1 for d in audit if d["routing_lane"] == "escalate")
    override_count = sum(1 for d in audit if d["human_decision"] in ("modify", "reject"))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Routed", total)
    col2.metric("Auto-Execute", auto_count)
    col3.metric("Human Review", review_count)
    col4.metric("Escalated", escalate_count)
    col5.metric("Override Rate", f"{override_count / total:.0%}" if total > 0 else "0%")

    # Lane distribution chart
    st.subheader("Routing Distribution")
    lane_data = [
        {"Lane": "Auto-Execute", "Count": auto_count, "Color": "green"},
        {"Lane": "Human Review", "Count": review_count, "Color": "orange"},
        {"Lane": "Escalate", "Count": escalate_count, "Color": "red"},
    ]
    fig_lanes = px.bar(
        lane_data, x="Lane", y="Count", color="Lane",
        color_discrete_map={"Auto-Execute": "#2ecc71", "Human Review": "#f39c12", "Escalate": "#e74c3c"},
        height=300,
    )
    fig_lanes.update_layout(showlegend=False, margin=dict(l=40, r=20, t=30, b=40))
    st.plotly_chart(fig_lanes, use_container_width=True)

    # Confidence over time
    st.subheader("Confidence Scores Over Time")
    conf_data = [
        {"Week": d["week"], "Confidence": d["confidence_score"],
         "Lane": d["routing_lane"], "Type": d["intervention_type"]}
        for d in audit
    ]
    fig_conf = px.scatter(
        conf_data, x="Week", y="Confidence", color="Lane",
        color_discrete_map={"auto_execute": "#2ecc71", "human_review": "#f39c12", "escalate": "#e74c3c"},
        hover_data=["Type"],
        height=350,
    )
    fig_conf.add_hline(y=0.80, line_dash="dash", line_color="green", annotation_text="Auto threshold")
    fig_conf.add_hline(y=0.50, line_dash="dash", line_color="red", annotation_text="Escalate threshold")
    fig_conf.update_layout(margin=dict(l=40, r=20, t=30, b=40))
    st.plotly_chart(fig_conf, use_container_width=True)

    # Full audit table
    st.subheader("Full Audit Log")
    display_data = []
    for d in audit:
        display_data.append({
            "Week": d["week"],
            "Intervention": d["intervention_type"],
            "Target": d["target_persona"],
            "Confidence": f"{d['confidence_score']:.0%}",
            "Lane": d["routing_lane"],
            "Decision": d["human_decision"],
        })
    st.dataframe(display_data, use_container_width=True)


# ── Page: Experiment Results ──────────────────────────────────

def page_experiment_results():
    st.header("Experiment Results")

    experiments = find_experiments()
    if not experiments:
        st.info("No experiment results found. Run an experiment first:\n\n"
                "`python -m src.main experiment sponsorship_sensitivity`")
        return

    selected = st.sidebar.selectbox("Experiment", list(experiments.keys()))
    data = load_experiment_results(experiments[selected])

    st.subheader(data.get("experiment", "Unknown"))
    st.caption(data.get("description", ""))
    st.metric("Total Runs", data.get("total_runs", 0))

    results = data.get("results", [])
    if not results:
        st.warning("No results in this experiment.")
        return

    # Adoption curve overlay
    st.subheader("Adoption by Configuration")
    fig_adoption = go.Figure()
    for r in results:
        label = f"{r['config_label']} (s={r['seed']})"
        color = "#2ecc71" if r["outcome"] == "success" else "#e74c3c"
        fig_adoption.add_trace(go.Bar(
            x=[label], y=[r["final_adoption_pct"]],
            name=label,
            marker_color=color,
            showlegend=False,
        ))
    fig_adoption.update_layout(
        yaxis=dict(tickformat=".0%", title="Final Adoption"),
        xaxis_title="Configuration",
        height=400,
        margin=dict(l=40, r=20, t=30, b=100),
    )
    fig_adoption.update_xaxes(tickangle=45)
    st.plotly_chart(fig_adoption, use_container_width=True)

    # Sensitivity heatmap (if comparison report exists)
    comparison_path = experiments[selected].parent / "comparison_report.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text())
        sensitivity = comparison.get("sensitivity", {})

        if sensitivity:
            st.subheader("Sensitivity Analysis")

            # Per-variable tables
            for var_name, var_data in sensitivity.items():
                st.markdown(f"**{var_name}**")
                rows = []
                for value, stats in var_data.items():
                    rows.append({
                        var_name: value,
                        "Avg Adoption": f"{stats['avg_adoption']:.0%}",
                        "Success Rate": f"{stats['success_rate']:.0%}",
                        "Runs": stats["runs"],
                    })
                st.dataframe(rows, use_container_width=True)

            # Cross-variable heatmap (if exactly 2 variables)
            sweep_vars = list(sensitivity.keys())
            if len(sweep_vars) == 2:
                var_a, var_b = sweep_vars
                vals_a = list(sensitivity[var_a].keys())
                vals_b = list(sensitivity[var_b].keys())

                # Build matrix from results
                z_data = []
                for va in vals_a:
                    row = []
                    for vb in vals_b:
                        matching = [
                            r for r in results
                            if str(r["parameters"].get(var_a)) == va
                            and str(r["parameters"].get(var_b)) == vb
                        ]
                        if matching:
                            avg = sum(r["final_adoption_pct"] for r in matching) / len(matching)
                            row.append(avg)
                        else:
                            row.append(None)
                    z_data.append(row)

                st.subheader(f"Adoption Heatmap: {var_a} x {var_b}")
                fig_heat = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=vals_b,
                    y=vals_a,
                    colorscale=[[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#2ecc71"]],
                    zmin=0, zmax=1,
                    text=[[f"{v:.0%}" if v else "-" for v in row] for row in z_data],
                    texttemplate="%{text}",
                    hovertemplate=f"{var_a}: %{{y}}<br>{var_b}: %{{x}}<br>Adoption: %{{z:.0%}}<extra></extra>",
                ))
                fig_heat.update_layout(
                    xaxis_title=var_b,
                    yaxis_title=var_a,
                    height=350,
                    margin=dict(l=40, r=20, t=30, b=40),
                )
                st.plotly_chart(fig_heat, use_container_width=True)

        # Best/worst
        best = comparison.get("best")
        worst = comparison.get("worst")
        if best and worst:
            col1, col2 = st.columns(2)
            col1.success(f"**Best:** {best['config']} — {best['adoption']:.0%}")
            col2.error(f"**Worst:** {worst['config']} — {worst['adoption']:.0%}")

    # Persona sentiment breakdown
    st.subheader("Persona Final Sentiments")
    persona_data = []
    for r in results:
        for persona, sentiment in r.get("persona_final_sentiments", {}).items():
            persona_data.append({
                "Config": r["config_label"],
                "Seed": r["seed"],
                "Persona": persona,
                "Sentiment": sentiment,
            })
    if persona_data:
        fig_persona = px.box(
            persona_data, x="Persona", y="Sentiment", color="Persona",
            height=350,
        )
        fig_persona.update_layout(
            yaxis=dict(range=[0, 1]),
            showlegend=False,
            margin=dict(l=40, r=20, t=30, b=40),
        )
        st.plotly_chart(fig_persona, use_container_width=True)

    # Raw results table
    with st.expander("Raw Results"):
        display = []
        for r in results:
            display.append({
                "Config": r["config_label"],
                "Seed": r["seed"],
                "Outcome": r["outcome"],
                "Adoption": f"{r['final_adoption_pct']:.1%}",
                "Weeks": r["weeks_elapsed"],
                "Interventions": r["total_interventions"],
                "Events": r["events_encountered"],
                "Replans": r["replans_triggered"],
                "Duration": f"{r['duration_seconds']:.1f}s",
            })
        st.dataframe(display, use_container_width=True)


# ── Page Router ───────────────────────────────────────────────

if page == "Pilot Scorecard":
    page_pilot_scorecard()
elif page == "HITL Audit Trail":
    page_hitl_audit()
elif page == "Experiment Results":
    page_experiment_results()
