"""Metrics Tracker Tool — computes adoption metrics from persona states."""

from __future__ import annotations

from src.models import AdoptionMetrics, PersonaState, PersonaType, SimulationState


class MetricsTrackerTool:
    """Computes observable adoption metrics from hidden persona states."""

    def compute_metrics(self, state: SimulationState) -> AdoptionMetrics:
        """Generate adoption metrics for the current simulation state."""
        personas = state.persona_states
        if not personas:
            return AdoptionMetrics(
                week=state.current_week,
                overall_adoption_pct=0.0,
                login_rate=0.0,
                feature_usage_depth=0.0,
                nps_proxy=0.0,
                risk_flags=["No persona data available"],
                budget_remaining_weeks=state.org_profile.budget_weeks - state.current_week,
            )

        # Aggregate from hidden states (the orchestrator sees the output, not the inputs)
        adoption_values = [p.adoption_likelihood for p in personas.values()]
        sentiment_values = [p.sentiment_score for p in personas.values()]

        overall_adoption = sum(adoption_values) / len(adoption_values)

        # Login rate correlates with adoption but has noise
        login_rate = min(1.0, overall_adoption * 1.2 + 0.05)

        # Feature depth is lower than adoption (people log in but don't go deep)
        feature_depth = overall_adoption * 0.7

        # NPS proxy: mapped from average sentiment (-1 to +1 scale)
        avg_sentiment = sum(sentiment_values) / len(sentiment_values)
        nps_proxy = (avg_sentiment - 0.5) * 2  # 0.5 sentiment = 0 NPS, 1.0 = +1.0

        # Generate risk flags
        risk_flags = []
        for ptype, pstate in personas.items():
            if pstate.sentiment_score < 0.25:
                risk_flags.append(f"CRITICAL: {ptype.value} sentiment below 25%")
            elif pstate.sentiment_score < 0.35:
                risk_flags.append(f"WARNING: {ptype.value} sentiment declining")
            if pstate.cognitive_load > 0.8:
                risk_flags.append(f"WARNING: {ptype.value} at capacity, may not absorb interventions")
            if pstate.trust_level < 0.3:
                risk_flags.append(f"WARNING: {ptype.value} trust is low — engagement may be performative")

        # Trend detection from history
        if len(state.turn_history) >= 2:
            prev_adoption = state.turn_history[-1].adoption_metrics.overall_adoption_pct
            if overall_adoption < prev_adoption - 0.03:
                risk_flags.append("TREND: Overall adoption declining week-over-week")

        weeks_remaining = state.org_profile.budget_weeks - state.current_week
        if weeks_remaining <= 4 and overall_adoption < state.org_profile.success_threshold * 0.7:
            risk_flags.append(f"CRITICAL: {weeks_remaining} weeks remaining, adoption at {overall_adoption:.0%} vs {state.org_profile.success_threshold:.0%} target")

        return AdoptionMetrics(
            week=state.current_week,
            overall_adoption_pct=round(overall_adoption, 3),
            login_rate=round(login_rate, 3),
            feature_usage_depth=round(feature_depth, 3),
            nps_proxy=round(nps_proxy, 3),
            risk_flags=risk_flags,
            budget_remaining_weeks=weeks_remaining,
        )
