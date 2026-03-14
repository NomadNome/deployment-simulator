"""Adoption Flywheel Metrics — CS-grade metrics and Pilot Scorecard."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.models import PersonaType, SimulationState

console = Console()


class HealthStatus(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class TrendDirection(str, Enum):
    UP = "\u2191"        # ↑
    FLAT = "\u2192"      # →
    DOWN = "\u2193"      # ↓


@dataclass
class FlywheelMetrics:
    """Full adoption flywheel metrics for a single simulation week."""
    week: int
    activation_rate: float       # % of users who completed a meaningful action
    weekly_engaged_users: float  # % of users with a session in trailing 7 days
    completion_rate: float       # % of AI workflows reaching successful end state
    override_rate: float         # % of interventions modified/rejected by human
    cycle_time_delta: float      # time improvement with AI vs. without (negative = faster)
    # Legacy metrics (kept for backward compatibility)
    overall_adoption_pct: float
    login_rate: float
    nps_proxy: float
    risk_flags: list[str]
    budget_remaining_weeks: int


@dataclass
class ScorecardEntry:
    """A single metric row in the Pilot Scorecard."""
    name: str
    value: float
    format_str: str  # e.g. "{:.1%}" or "{:+.1f}"
    status: HealthStatus
    trend: TrendDirection
    thresholds: tuple[float, float]  # (amber_below, red_below)


class FlywheelMetricsTracker:
    """Computes flywheel metrics from simulation state."""

    def __init__(self):
        self.history: list[FlywheelMetrics] = []

    def compute(
        self,
        state: SimulationState,
        override_rate: float = 0.0,
    ) -> FlywheelMetrics:
        """Compute flywheel metrics for the current simulation state."""
        personas = state.persona_states
        if not personas:
            metrics = FlywheelMetrics(
                week=state.current_week,
                activation_rate=0.0,
                weekly_engaged_users=0.0,
                completion_rate=0.0,
                override_rate=override_rate,
                cycle_time_delta=0.0,
                overall_adoption_pct=0.0,
                login_rate=0.0,
                nps_proxy=0.0,
                risk_flags=["No persona data"],
                budget_remaining_weeks=state.org_profile.budget_weeks - state.current_week,
            )
            self.history.append(metrics)
            return metrics

        adoption_values = [p.adoption_likelihood for p in personas.values()]
        sentiment_values = [p.sentiment_score for p in personas.values()]

        overall_adoption = sum(adoption_values) / len(adoption_values)
        avg_sentiment = sum(sentiment_values) / len(sentiment_values)

        # Activation rate: users who've done something meaningful (higher bar than login)
        # Personas with adoption > 0.4 are considered "activated"
        activated = sum(1 for p in personas.values() if p.adoption_likelihood > 0.4)
        activation_rate = activated / len(personas)

        # Weekly engaged users: personas with sentiment > 0.35 (they're at least paying attention)
        engaged = sum(1 for p in personas.values() if p.sentiment_score > 0.35)
        weekly_engaged = engaged / len(personas)

        # Completion rate: derived from adoption × trust (high adoption + high trust = completing workflows)
        completion_signals = [
            p.adoption_likelihood * p.trust_level for p in personas.values()
        ]
        completion_rate = sum(completion_signals) / len(completion_signals)

        # Cycle-time delta: negative = faster with AI. Derived from overall adoption (more adoption = more time saved)
        cycle_time_delta = -(overall_adoption * 2.5)  # at full adoption, ~2.5 hour improvement per task

        # Login rate (legacy)
        login_rate = min(1.0, overall_adoption * 1.2 + 0.05)

        # NPS proxy
        nps_proxy = (avg_sentiment - 0.5) * 2

        # Risk flags
        risk_flags = self._generate_risk_flags(state, overall_adoption, activation_rate, weekly_engaged)

        metrics = FlywheelMetrics(
            week=state.current_week,
            activation_rate=round(activation_rate, 3),
            weekly_engaged_users=round(weekly_engaged, 3),
            completion_rate=round(completion_rate, 3),
            override_rate=round(override_rate, 3),
            cycle_time_delta=round(cycle_time_delta, 2),
            overall_adoption_pct=round(overall_adoption, 3),
            login_rate=round(login_rate, 3),
            nps_proxy=round(nps_proxy, 3),
            risk_flags=risk_flags,
            budget_remaining_weeks=state.org_profile.budget_weeks - state.current_week,
        )
        self.history.append(metrics)
        return metrics

    def _generate_risk_flags(
        self,
        state: SimulationState,
        overall_adoption: float,
        activation_rate: float,
        weekly_engaged: float,
    ) -> list[str]:
        """Generate risk flags from flywheel metrics."""
        flags = []

        for ptype, pstate in state.persona_states.items():
            if pstate.sentiment_score < 0.25:
                flags.append(f"CRITICAL: {ptype.value} sentiment below 25%")
            elif pstate.sentiment_score < 0.35:
                flags.append(f"WARNING: {ptype.value} sentiment declining")
            if pstate.cognitive_load > 0.8:
                flags.append(f"WARNING: {ptype.value} at capacity")
            if pstate.trust_level < 0.3:
                flags.append(f"WARNING: {ptype.value} trust is low")

        # Flywheel-specific flags
        if activation_rate < 0.25 and state.current_week > 4:
            flags.append("CRITICAL: Activation rate below 25% after week 4")

        if weekly_engaged < activation_rate * 0.6:
            flags.append("WARNING: Engaged users dropping faster than activation — retention problem")

        if len(self.history) >= 2:
            prev = self.history[-2]
            if weekly_engaged < prev.weekly_engaged_users - 0.1:
                flags.append("TREND: Weekly engaged users declining sharply")
            if overall_adoption < prev.overall_adoption_pct - 0.03:
                flags.append("TREND: Overall adoption declining week-over-week")

        weeks_remaining = state.org_profile.budget_weeks - state.current_week
        if weeks_remaining <= 4 and overall_adoption < state.org_profile.success_threshold * 0.7:
            flags.append(
                f"CRITICAL: {weeks_remaining} weeks remaining, adoption at "
                f"{overall_adoption:.0%} vs {state.org_profile.success_threshold:.0%} target"
            )

        return flags

    def get_trend(self, metric_name: str) -> TrendDirection:
        """Compute week-over-week trend for a metric."""
        if len(self.history) < 2:
            return TrendDirection.FLAT
        current = getattr(self.history[-1], metric_name)
        previous = getattr(self.history[-2], metric_name)
        delta = current - previous
        if delta > 0.02:
            return TrendDirection.UP
        elif delta < -0.02:
            return TrendDirection.DOWN
        return TrendDirection.FLAT

    def generate_scorecard(self) -> list[ScorecardEntry]:
        """Generate the Pilot Scorecard from the latest metrics."""
        if not self.history:
            return []
        m = self.history[-1]

        entries = [
            ScorecardEntry(
                name="Activation Rate",
                value=m.activation_rate,
                format_str="{:.0%}",
                status=_health(m.activation_rate, 0.50, 0.25),
                trend=self.get_trend("activation_rate"),
                thresholds=(0.50, 0.25),
            ),
            ScorecardEntry(
                name="Weekly Engaged Users",
                value=m.weekly_engaged_users,
                format_str="{:.0%}",
                status=_health(m.weekly_engaged_users, 0.50, 0.25),
                trend=self.get_trend("weekly_engaged_users"),
                thresholds=(0.50, 0.25),
            ),
            ScorecardEntry(
                name="Completion Rate",
                value=m.completion_rate,
                format_str="{:.0%}",
                status=_health(m.completion_rate, 0.40, 0.20),
                trend=self.get_trend("completion_rate"),
                thresholds=(0.40, 0.20),
            ),
            ScorecardEntry(
                name="Override Rate",
                value=m.override_rate,
                format_str="{:.0%}",
                # For override rate, LOWER is better
                status=_health_inverted(m.override_rate, 0.30, 0.50),
                trend=self.get_trend("override_rate"),
                thresholds=(0.30, 0.50),
            ),
            ScorecardEntry(
                name="Cycle-Time Delta",
                value=m.cycle_time_delta,
                format_str="{:+.1f}h",
                # For cycle time, MORE NEGATIVE is better
                status=_health_inverted(m.cycle_time_delta, -0.5, 0.0),
                trend=self.get_trend("cycle_time_delta"),
                thresholds=(-0.5, 0.0),
            ),
            ScorecardEntry(
                name="Overall Adoption",
                value=m.overall_adoption_pct,
                format_str="{:.0%}",
                status=_health(m.overall_adoption_pct, 0.50, 0.30),
                trend=self.get_trend("overall_adoption_pct"),
                thresholds=(0.50, 0.30),
            ),
        ]
        return entries

    def display_scorecard(self) -> None:
        """Print the Pilot Scorecard to the console."""
        entries = self.generate_scorecard()
        if not entries:
            return

        m = self.history[-1]
        table = Table(
            title=f"Pilot Scorecard \u2014 Week {m.week}",
            border_style="blue",
            show_header=True,
        )
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Trend", justify="center")

        for entry in entries:
            status_icon = {
                HealthStatus.GREEN: "[green]\u25CF[/green]",   # ●
                HealthStatus.AMBER: "[yellow]\u25CF[/yellow]",
                HealthStatus.RED: "[red]\u25CF[/red]",
            }[entry.status]

            trend_icon = {
                TrendDirection.UP: "[green]\u2191[/green]",
                TrendDirection.FLAT: "[dim]\u2192[/dim]",
                TrendDirection.DOWN: "[red]\u2193[/red]",
            }[entry.trend]

            table.add_row(
                entry.name,
                entry.format_str.format(entry.value),
                status_icon,
                trend_icon,
            )

        console.print(table)

        # Risk flags
        if m.risk_flags:
            flags_text = "\n".join(f"  [red]\u2022[/red] {f}" for f in m.risk_flags)
            console.print(Panel(flags_text, title="Risk Flags", border_style="red"))


def _health(value: float, amber_below: float, red_below: float) -> HealthStatus:
    """Higher is better."""
    if value >= amber_below:
        return HealthStatus.GREEN
    elif value >= red_below:
        return HealthStatus.AMBER
    return HealthStatus.RED


def _health_inverted(value: float, amber_above: float, red_above: float) -> HealthStatus:
    """Lower is better (or more negative is better for cycle-time delta)."""
    if value <= amber_above:
        return HealthStatus.GREEN
    elif value <= red_above:
        return HealthStatus.AMBER
    return HealthStatus.RED
