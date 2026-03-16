"""Experiment Runner — batch simulation execution with parameter sweeps."""

from __future__ import annotations

import itertools
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from src.models import (
    Industry, Maturity, OrgProfile, PersonaType, SimulationOutcome,
    SimulationState, Sponsorship,
)
from src.simulation.controller import SimulationController

console = Console()


# ── Experiment Configuration ────────────────────────────────────

@dataclass
class ExperimentConfig:
    """Defines a parameter sweep experiment."""
    name: str
    description: str
    base_profile: OrgProfile
    sweeps: dict[str, list[Any]]                    # variable_name → list of values
    forced_events: list[dict] = field(default_factory=list)   # [{event_type, week}]
    orchestrator_prompt_variants: dict[str, str] = field(default_factory=dict)  # label → prompt override
    persona_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)  # persona → {field: value}
    seeds: list[int] = field(default_factory=lambda: [42])    # random seeds for each config
    max_parallel: int = 3


@dataclass
class RunResult:
    """Outcome of a single simulation run."""
    config_label: str
    parameters: dict[str, Any]
    seed: int
    outcome: str
    final_adoption_pct: float
    weeks_elapsed: int
    total_interventions: int
    events_encountered: int
    replans_triggered: int
    persona_final_sentiments: dict[str, float]
    duration_seconds: float
    log_path: str


# ── Scenario Matrix Generator ──────────────────────────────────

def generate_scenario_matrix(config: ExperimentConfig) -> list[dict[str, Any]]:
    """
    Produce the Cartesian product of all sweep variables.
    Each item is a dict of {variable_name: value} for one simulation run.
    """
    if not config.sweeps:
        return [{}]

    keys = list(config.sweeps.keys())
    value_lists = [config.sweeps[k] for k in keys]

    scenarios = []
    for combo in itertools.product(*value_lists):
        scenarios.append(dict(zip(keys, combo)))

    return scenarios


def apply_scenario_to_profile(
    base: OrgProfile,
    scenario: dict[str, Any],
    persona_overrides: dict[str, dict[str, Any]] | None = None,
) -> OrgProfile:
    """Apply a scenario's parameter values to a base org profile."""
    overrides = {}
    for key, value in scenario.items():
        # Handle enum conversions
        if key == "industry" and isinstance(value, str):
            value = Industry(value)
        elif key == "technical_maturity" and isinstance(value, str):
            value = Maturity(value)
        elif key == "executive_sponsorship" and isinstance(value, str):
            value = Sponsorship(value)

        # Only apply if it's a valid OrgProfile field
        if key in OrgProfile.model_fields:
            overrides[key] = value

    return base.model_copy(update=overrides)


# ── Experiment Runner ──────────────────────────────────────────

class ExperimentRunner:
    """Executes a full experiment: matrix generation, parallel runs, aggregation."""

    def __init__(self, config: ExperimentConfig, output_dir: str = "data/experiments"):
        self.config = config
        self.output_dir = Path(output_dir) / config.name / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[RunResult] = []

    def run(self) -> list[RunResult]:
        """Execute all scenarios and return results."""
        scenarios = generate_scenario_matrix(self.config)
        total_runs = len(scenarios) * len(self.config.seeds)

        console.print(f"\n[bold]Experiment: {self.config.name}[/bold]")
        console.print(f"[dim]{self.config.description}[/dim]")
        console.print(f"Scenarios: {len(scenarios)} | Seeds: {len(self.config.seeds)} | Total runs: {total_runs}")
        console.print(f"Output: {self.output_dir}\n")

        # Build run queue
        run_queue: list[tuple[str, OrgProfile, dict[str, Any], int]] = []
        for scenario in scenarios:
            profile = apply_scenario_to_profile(self.config.base_profile, scenario)
            label = " | ".join(f"{k}={v}" for k, v in scenario.items()) or "baseline"

            for seed in self.config.seeds:
                run_queue.append((label, profile, scenario, seed))

        # Execute with parallelism
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running simulations...", total=total_runs)

            with ThreadPoolExecutor(max_workers=self.config.max_parallel) as executor:
                futures = {
                    executor.submit(self._run_single, label, profile, scenario, seed): (label, seed)
                    for label, profile, scenario, seed in run_queue
                }

                for future in as_completed(futures):
                    label, seed = futures[future]
                    try:
                        result = future.result()
                        self.results.append(result)
                        status = "[green]✓[/green]" if result.outcome == "success" else "[red]✗[/red]"
                        progress.console.print(
                            f"  {status} {result.config_label} (seed={seed}) → "
                            f"{result.final_adoption_pct:.1%} in {result.weeks_elapsed}w"
                        )
                    except Exception as e:
                        progress.console.print(f"  [red]ERROR[/red] {label} (seed={seed}): {e}")
                    progress.advance(task)

        # Save and display results
        self._save_results()
        self._display_summary()
        self._display_comparison_report()

        return self.results

    def _run_single(
        self,
        label: str,
        profile: OrgProfile,
        scenario: dict[str, Any],
        seed: int,
    ) -> RunResult:
        """Execute a single simulation run (called in thread pool)."""
        start = time.time()

        log_subdir = self.output_dir / f"{label.replace(' | ', '__').replace('=', '_')}_seed{seed}"
        log_subdir.mkdir(parents=True, exist_ok=True)

        # Determine forced events — support per-scenario disruption levels
        forced_events = list(self.config.forced_events)
        disruption_level = scenario.get("disruption_level")
        if disruption_level is not None:
            forced_events = DISRUPTION_LEVELS.get(disruption_level, [])

        controller = SimulationController(
            org_profile=profile,
            event_seed=seed,
            log_dir=str(log_subdir),
            forced_events=forced_events,
            quiet=True,
        )

        state = controller.run()

        elapsed = time.time() - start

        return RunResult(
            config_label=label,
            parameters=scenario,
            seed=seed,
            outcome=state.outcome.value,
            final_adoption_pct=state.metrics.overall_adoption_pct if state.metrics else 0.0,
            weeks_elapsed=state.current_week,
            total_interventions=sum(len(t.interventions) for t in state.turn_history),
            events_encountered=sum(len(t.events_fired) for t in state.turn_history),
            replans_triggered=sum(1 for t in state.turn_history if t.replan_triggered),
            persona_final_sentiments={
                pt.value: round(ps.sentiment_score, 3)
                for pt, ps in state.persona_states.items()
            },
            duration_seconds=round(elapsed, 1),
            log_path=str(log_subdir),
        )

    def _save_results(self) -> None:
        """Save aggregated results to JSON."""
        results_path = self.output_dir / "results.json"
        data = {
            "experiment": self.config.name,
            "description": self.config.description,
            "timestamp": datetime.now().isoformat(),
            "total_runs": len(self.results),
            "results": [
                {
                    "config_label": r.config_label,
                    "parameters": r.parameters,
                    "seed": r.seed,
                    "outcome": r.outcome,
                    "final_adoption_pct": r.final_adoption_pct,
                    "weeks_elapsed": r.weeks_elapsed,
                    "total_interventions": r.total_interventions,
                    "events_encountered": r.events_encountered,
                    "replans_triggered": r.replans_triggered,
                    "persona_final_sentiments": r.persona_final_sentiments,
                    "duration_seconds": r.duration_seconds,
                }
                for r in self.results
            ],
        }
        with open(results_path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"\n[dim]Results saved: {results_path}[/dim]")

    def _display_summary(self) -> None:
        """Display experiment summary table."""
        if not self.results:
            return

        table = Table(title=f"Experiment Results: {self.config.name}", border_style="blue")
        table.add_column("Configuration")
        table.add_column("Seed")
        table.add_column("Outcome")
        table.add_column("Adoption")
        table.add_column("Weeks")
        table.add_column("Interventions")
        table.add_column("Events")
        table.add_column("Duration")

        for r in sorted(self.results, key=lambda x: (x.config_label, x.seed)):
            outcome_style = "green" if r.outcome == "success" else "red"
            adoption_style = "green" if r.final_adoption_pct > 0.6 else "yellow" if r.final_adoption_pct > 0.35 else "red"
            table.add_row(
                r.config_label,
                str(r.seed),
                f"[{outcome_style}]{r.outcome}[/{outcome_style}]",
                f"[{adoption_style}]{r.final_adoption_pct:.1%}[/{adoption_style}]",
                str(r.weeks_elapsed),
                str(r.total_interventions),
                str(r.events_encountered),
                f"{r.duration_seconds:.1f}s",
            )
        console.print(table)

        # Summary stats
        success_count = sum(1 for r in self.results if r.outcome == "success")
        avg_adoption = sum(r.final_adoption_pct for r in self.results) / len(self.results)
        console.print(f"\n[bold]Success rate:[/bold] {success_count}/{len(self.results)} ({success_count/len(self.results):.0%})")
        console.print(f"[bold]Avg adoption:[/bold] {avg_adoption:.1%}")

    def _display_comparison_report(self) -> None:
        """Display sensitivity analysis and comparison across swept variables."""
        if not self.results or not self.config.sweeps:
            return

        console.print("\n")

        # Sensitivity analysis: for each swept variable, compute avg adoption per value
        for var_name, var_values in self.config.sweeps.items():
            table = Table(
                title=f"Sensitivity: {var_name}",
                border_style="cyan",
            )
            table.add_column(var_name, style="bold")
            table.add_column("Avg Adoption", justify="right")
            table.add_column("Success Rate", justify="right")
            table.add_column("Avg Weeks", justify="right")
            table.add_column("Runs", justify="right")

            for value in var_values:
                matching = [
                    r for r in self.results
                    if str(r.parameters.get(var_name)) == str(value)
                ]
                if not matching:
                    continue

                avg_adopt = sum(r.final_adoption_pct for r in matching) / len(matching)
                successes = sum(1 for r in matching if r.outcome == "success")
                avg_weeks = sum(r.weeks_elapsed for r in matching) / len(matching)

                adopt_color = "green" if avg_adopt > 0.6 else "yellow" if avg_adopt > 0.35 else "red"
                rate_color = "green" if successes / len(matching) > 0.5 else "red"

                table.add_row(
                    str(value),
                    f"[{adopt_color}]{avg_adopt:.1%}[/{adopt_color}]",
                    f"[{rate_color}]{successes}/{len(matching)}[/{rate_color}]",
                    f"{avg_weeks:.0f}",
                    str(len(matching)),
                )

            console.print(table)

        # Cross-variable heatmap (if exactly 2 sweep variables)
        sweep_keys = list(self.config.sweeps.keys())
        if len(sweep_keys) == 2:
            var_a, var_b = sweep_keys
            vals_a, vals_b = self.config.sweeps[var_a], self.config.sweeps[var_b]

            table = Table(
                title=f"Adoption Heatmap: {var_a} x {var_b}",
                border_style="cyan",
            )
            table.add_column(f"{var_a} \\ {var_b}", style="bold")
            for vb in vals_b:
                table.add_column(str(vb), justify="center")

            for va in vals_a:
                row = [str(va)]
                for vb in vals_b:
                    matching = [
                        r for r in self.results
                        if str(r.parameters.get(var_a)) == str(va)
                        and str(r.parameters.get(var_b)) == str(vb)
                    ]
                    if matching:
                        avg = sum(r.final_adoption_pct for r in matching) / len(matching)
                        color = "green" if avg > 0.6 else "yellow" if avg > 0.35 else "red"
                        row.append(f"[{color}]{avg:.0%}[/{color}]")
                    else:
                        row.append("-")
                table.add_row(*row)

            console.print(table)

        # Best and worst configurations
        if len(self.results) > 1:
            best = max(self.results, key=lambda r: r.final_adoption_pct)
            worst = min(self.results, key=lambda r: r.final_adoption_pct)
            console.print(f"\n[bold green]Best:[/bold green] {best.config_label} (seed={best.seed}) → {best.final_adoption_pct:.1%}")
            console.print(f"[bold red]Worst:[/bold red] {worst.config_label} (seed={worst.seed}) → {worst.final_adoption_pct:.1%}")

        # Save comparison report
        report_path = self.output_dir / "comparison_report.json"
        report = {
            "experiment": self.config.name,
            "sensitivity": {},
            "best": None,
            "worst": None,
        }
        for var_name, var_values in self.config.sweeps.items():
            report["sensitivity"][var_name] = {}
            for value in var_values:
                matching = [
                    r for r in self.results
                    if str(r.parameters.get(var_name)) == str(value)
                ]
                if matching:
                    report["sensitivity"][var_name][str(value)] = {
                        "avg_adoption": round(sum(r.final_adoption_pct for r in matching) / len(matching), 3),
                        "success_rate": sum(1 for r in matching if r.outcome == "success") / len(matching),
                        "runs": len(matching),
                    }
        if self.results:
            best = max(self.results, key=lambda r: r.final_adoption_pct)
            worst = min(self.results, key=lambda r: r.final_adoption_pct)
            report["best"] = {"config": best.config_label, "adoption": best.final_adoption_pct}
            report["worst"] = {"config": worst.config_label, "adoption": worst.final_adoption_pct}

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        console.print(f"\n[dim]Comparison report saved: {report_path}[/dim]")


# ── Disruption Levels for Experiments ──────────────────────────

DISRUPTION_LEVELS = {
    "none": [],
    "single": [
        {"event_type": "sponsor_departure", "week": 8},
    ],
    "multi": [
        {"event_type": "competing_tool", "week": 5},
        {"event_type": "sponsor_departure", "week": 8},
        {"event_type": "budget_freeze", "week": 12},
    ],
}


# ── Pre-built Experiment Configs ───────────────────────────────

from src.simulation.profiles import NOVA_TECH

SPONSORSHIP_SENSITIVITY = ExperimentConfig(
    name="sponsorship_sensitivity",
    description="How does executive sponsorship affect outcomes across maturity levels?",
    base_profile=NOVA_TECH,
    sweeps={
        "executive_sponsorship": ["weak", "moderate", "strong"],
        "technical_maturity": ["low", "medium", "high"],
    },
    seeds=[42, 123, 456],
)

DISRUPTION_RESILIENCE = ExperimentConfig(
    name="disruption_resilience",
    description="Which organizational disruptions are hardest to recover from?",
    base_profile=NOVA_TECH,
    sweeps={
        "executive_sponsorship": ["weak", "strong"],
    },
    forced_events=[
        {"event_type": "reorg", "week": 4},
        {"event_type": "sponsor_departure", "week": 6},
        {"event_type": "budget_freeze", "week": 8},
    ],
    seeds=[42, 123],
)

SCALE_EFFECTS = ExperimentConfig(
    name="scale_effects",
    description="How does team size interact with technical maturity?",
    base_profile=NOVA_TECH,
    sweeps={
        "team_size": [50, 150, 500, 2000],
        "technical_maturity": ["low", "medium", "high"],
    },
    seeds=[42],
)

SPONSORSHIP_VS_DISRUPTION = ExperimentConfig(
    name="sponsorship_vs_disruption",
    description="When does sponsorship matter? Sponsorship × disruption severity.",
    base_profile=NOVA_TECH.model_copy(update={"budget_weeks": 20}),
    sweeps={
        "executive_sponsorship": ["weak", "moderate", "strong"],
        "disruption_level": ["none", "single", "multi"],
    },
    seeds=[42, 123],
)

EXPERIMENTS = {
    "sponsorship_sensitivity": SPONSORSHIP_SENSITIVITY,
    "disruption_resilience": DISRUPTION_RESILIENCE,
    "scale_effects": SCALE_EFFECTS,
    "sponsorship_vs_disruption": SPONSORSHIP_VS_DISRUPTION,
}
