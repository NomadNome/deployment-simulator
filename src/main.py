"""Main entry point for the Enterprise AI Deployment Simulator."""

from __future__ import annotations

import argparse
import os
import sys

from rich.console import Console

from src.simulation.controller import SimulationController
from src.simulation.hitl_router import HITLMode
from src.simulation.profiles import PROFILES

console = Console()


def run_simulation(args):
    """Run a single simulation."""
    profile = PROFILES[args.profile]
    if args.weeks:
        profile = profile.model_copy(update={"budget_weeks": args.weeks})

    # Set agent backend from CLI flag
    if hasattr(args, "backend") and args.backend:
        os.environ["AGENT_BACKEND"] = args.backend

    console.print(f"\n[bold]Loading profile:[/bold] {args.profile}")
    console.print(f"[bold]Event seed:[/bold] {args.seed or 'random'}")
    console.print(f"[bold]Backend:[/bold] {os.getenv('AGENT_BACKEND', 'vanilla')}\n")

    hitl_mode = HITLMode(args.mode) if hasattr(args, "mode") and args.mode else HITLMode.AUTOPILOT
    controller = SimulationController(
        org_profile=profile,
        event_seed=args.seed,
        hitl_mode=hitl_mode,
    )

    try:
        state = controller.run()
        sys.exit(0 if state.outcome.value == "success" else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Simulation interrupted by user.[/yellow]")
        sys.exit(130)


def run_experiment(args):
    """Run a batch experiment with parameter sweeps."""
    from src.simulation.experiment_runner import EXPERIMENTS, ExperimentRunner

    if args.experiment not in EXPERIMENTS:
        console.print(f"[red]Unknown experiment: {args.experiment}[/red]")
        console.print(f"Available: {', '.join(EXPERIMENTS.keys())}")
        sys.exit(1)

    config = EXPERIMENTS[args.experiment]
    if args.parallel:
        config.max_parallel = args.parallel

    runner = ExperimentRunner(config)

    try:
        results = runner.run()
        success_count = sum(1 for r in results if r.outcome == "success")
        sys.exit(0 if success_count > 0 else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Experiment interrupted by user.[/yellow]")
        sys.exit(130)


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise AI Deployment Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── simulate command ──
    sim_parser = subparsers.add_parser("simulate", help="Run a single simulation")
    sim_parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()),
        default="nova_tech",
        help="Organization profile to simulate (default: nova_tech)",
    )
    sim_parser.add_argument("--seed", type=int, default=None, help="Random seed for events")
    sim_parser.add_argument("--weeks", type=int, default=None, help="Override budget_weeks")
    sim_parser.add_argument(
        "--mode",
        choices=["autopilot", "guided", "demo"],
        default="autopilot",
        help="HITL mode: autopilot (auto-execute all), guided (pause on review/escalate), demo (pause on everything)",
    )
    sim_parser.add_argument(
        "--backend",
        choices=["vanilla", "strands", "sandbox"],
        default=None,
        help="Agent backend: vanilla (direct API), strands (Strands SDK), or sandbox (Docker isolation)",
    )

    # ── experiment command ──
    exp_parser = subparsers.add_parser("experiment", help="Run a batch experiment")
    exp_parser.add_argument(
        "experiment",
        help="Experiment name (sponsorship_sensitivity, disruption_resilience, scale_effects)",
    )
    exp_parser.add_argument("--parallel", type=int, default=None, help="Max parallel simulations")

    # ── dashboard command ──
    subparsers.add_parser("dashboard", help="Launch the Streamlit visualization dashboard")

    # ── list command ──
    subparsers.add_parser("list", help="List available profiles and experiments")

    args = parser.parse_args()

    if args.command == "simulate":
        run_simulation(args)
    elif args.command == "experiment":
        run_experiment(args)
    elif args.command == "dashboard":
        import subprocess
        console.print("\n[bold]Launching dashboard...[/bold]")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/dashboard/app.py",
            "--server.headless", "true",
        ])
    elif args.command == "list":
        console.print("\n[bold]Profiles:[/bold]")
        for name, p in PROFILES.items():
            console.print(f"  {name}: {p.org_name} ({p.industry.value}, {p.technical_maturity.value} maturity, {p.executive_sponsorship.value} sponsorship)")
        console.print("\n[bold]Experiments:[/bold]")
        from src.simulation.experiment_runner import EXPERIMENTS
        for name, e in EXPERIMENTS.items():
            scenarios = 1
            for vals in e.sweeps.values():
                scenarios *= len(vals)
            total = scenarios * len(e.seeds)
            console.print(f"  {name}: {e.description} ({total} runs)")
        console.print()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
