"""Simulation Controller — the deterministic loop that drives the simulation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.agents import create_orchestrator_agent, create_persona_agent
from src.agents.persona import initialize_persona_states
from src.models import (
    AdoptionMetrics, Intervention, InterventionRecord, OrgProfile, PersonaType,
    SimulationOutcome, SimulationState, TurnRecord,
)
from src.simulation.events import roll_events
from src.simulation.flywheel_metrics import FlywheelMetricsTracker
from src.simulation.hitl_router import HITLMode, HITLRouter, estimate_confidence
from src.simulation.realism import (
    apply_blind_spot, fatigue_multiplier, fatigue_prompt_addition,
    grudge_effect_multiplier, roll_blind_spot, roll_friction, update_grudge,
)

console = Console()


class SimulationController:
    """Manages the turn-by-turn simulation loop."""

    def __init__(
        self,
        org_profile: OrgProfile,
        event_seed: int | None = None,
        log_dir: str = "data/simulation_logs",
        hitl_mode: HITLMode = HITLMode.AUTOPILOT,
        forced_events: list[dict] | None = None,
        quiet: bool = False,
        max_interventions_per_week: int = 3,
        persona_overrides: dict[PersonaType, dict] | None = None,
    ):
        self.org_profile = org_profile
        self.event_seed = event_seed
        self.forced_events = forced_events or []
        self.quiet = quiet
        self.max_interventions_per_week = max_interventions_per_week
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize agents (factory switches between vanilla/strands/sandbox)
        self.orchestrator = create_orchestrator_agent()
        self.persona_agents = {
            pt: create_persona_agent(pt) for pt in PersonaType
        }
        self.flywheel = FlywheelMetricsTracker()
        self.router = HITLRouter(mode=hitl_mode)

        # Realism tracking
        self._active_events_this_week: int = 0
        self._friction_count: int = 0
        self._blind_spot_count: int = 0
        self._pending_queue: list[Intervention] = []  # delayed interventions

        # Initialize simulation state
        self.state = SimulationState(
            org_profile=org_profile,
            persona_states=initialize_persona_states(org_profile),
        )

        # Apply persona state overrides (e.g. higher cognitive load)
        if persona_overrides:
            for ptype, overrides in persona_overrides.items():
                if ptype in self.state.persona_states:
                    for field, value in overrides.items():
                        setattr(self.state.persona_states[ptype], field, value)

    def _print(self, *args, **kwargs) -> None:
        """Print only if not in quiet mode."""
        if not self.quiet:
            console.print(*args, **kwargs)

    def _rule(self, *args, **kwargs) -> None:
        """Print rule only if not in quiet mode."""
        if not self.quiet:
            console.rule(*args, **kwargs)

    def run(self) -> SimulationState:
        """Execute the full simulation loop."""
        self._print(Panel(
            f"[bold]Deployment Simulator[/bold]\n"
            f"{self.org_profile.org_name} | {self.org_profile.industry.value} | "
            f"Team: {self.org_profile.team_size} | "
            f"Target: {self.org_profile.success_threshold:.0%} adoption in "
            f"{self.org_profile.budget_weeks} weeks",
            title="Simulation Starting",
            border_style="blue",
        ))

        # Phase 0: Generate initial plan
        self._print("\n[dim]Generating initial rollout plan...[/dim]")
        self.state.orchestrator_plan = self.orchestrator.generate_initial_plan(self.org_profile)
        self._print(Panel(self.state.orchestrator_plan, title="Initial Plan", border_style="green"))

        # Compute initial metrics (flywheel)
        initial_flywheel = self.flywheel.compute(self.state)
        self.state.metrics = self._flywheel_to_adoption_metrics(initial_flywheel)

        persona_responses: dict[PersonaType, str] | None = None

        # Main simulation loop
        for week in range(1, self.org_profile.budget_weeks + 1):
            self.state.current_week = week
            self._rule(f"[bold blue]Week {week}[/bold blue]")

            # Step 1: Check for random and forced events
            events = roll_events(
                week,
                seed=self.event_seed,
                forced_events=self.forced_events,
            )
            self._active_events_this_week = len(events)
            if events:
                for event in events:
                    self._apply_event(event)
                    # Events without follow-up increase grudge for affected personas
                    for ptype in event.affected_personas:
                        if ptype in self.state.persona_states:
                            modifier = event.sentiment_modifiers.get(ptype, 0)
                            if modifier < 0:
                                self.state.persona_states[ptype].grudge_score = min(
                                    1.0, self.state.persona_states[ptype].grudge_score + 0.08
                                )

            # Step 2: Orchestrator blind spot — degrade info before orchestrator sees it
            blind_spot = roll_blind_spot(self.state, seed=self.event_seed, week=week)
            orchestrator_responses = persona_responses
            if blind_spot.hit:
                self._blind_spot_count += 1
                orchestrator_responses = apply_blind_spot(blind_spot, persona_responses, self.state)
                self._print(f"  [dim magenta]Blind spot: {blind_spot.spot_type}[/dim magenta]")

            # If metrics_lag blind spot, serve stale metrics
            stale_metrics = None
            if blind_spot.hit and blind_spot.spot_type == "metrics_lag" and len(self.state.turn_history) >= 2:
                stale_metrics = self.state.metrics
                self.state.metrics = self.state.turn_history[-2].adoption_metrics

            # Step 3: Orchestrator plans interventions
            self._print("[dim]Orchestrator reasoning...[/dim]")
            reasoning, interventions = self.orchestrator.run_turn(
                self.state, orchestrator_responses
            )

            # Restore real metrics if we served stale ones
            if stale_metrics is not None:
                self.state.metrics = stale_metrics

            # Step 4: Merge delayed interventions from pending queue
            requeued = list(self._pending_queue)
            self._pending_queue.clear()
            all_interventions = requeued + interventions

            # Cap interventions per week
            capped_interventions = all_interventions[:self.max_interventions_per_week]

            # Step 5: Route through HITL, apply friction, dispatch to personas
            persona_responses = {}
            contacted_personas: set[PersonaType] = set()

            for intervention in capped_interventions:
                # HITL routing
                confidence = estimate_confidence(
                    intervention=intervention,
                    week=week,
                    recent_override_rate=self.router.override_rate,
                    active_events=self._active_events_this_week,
                )
                approved, routed_intervention = self.router.route(
                    intervention=intervention,
                    confidence=confidence,
                    week=week,
                    orchestrator_reasoning=reasoning or "",
                )

                if not approved:
                    self._print(
                        f"  [red]✗[/red] {intervention.intervention_type.value} "
                        f"→ {intervention.target_persona.value} [dim](rejected)[/dim]"
                    )
                    continue

                target = routed_intervention.target_persona

                # Execution friction roll
                friction = roll_friction(seed=self.event_seed, week=week)
                if friction.hit:
                    self._friction_count += 1
                    if friction.outcome_type == "delayed":
                        self._pending_queue.append(routed_intervention)
                        self._print(
                            f"  [yellow]⏳[/yellow] {routed_intervention.intervention_type.value} "
                            f"→ {target.value} [dim](delayed — rescheduled)[/dim]"
                        )
                        update_grudge(self.state.persona_states[target], "delayed", had_contact=False)
                        continue
                    elif friction.outcome_type == "cancelled":
                        self._print(
                            f"  [red]✕[/red] {routed_intervention.intervention_type.value} "
                            f"→ {target.value} [dim](cancelled — {friction.description})[/dim]"
                        )
                        update_grudge(self.state.persona_states[target], "cancelled", had_contact=False)
                        continue
                    elif friction.outcome_type == "backfire":
                        self._print(
                            f"  [red]💥[/red] {routed_intervention.intervention_type.value} "
                            f"→ {target.value} [dim](backfired!)[/dim]"
                        )
                        update_grudge(self.state.persona_states[target], "backfire", had_contact=True)
                    elif friction.outcome_type == "degraded":
                        self._print(
                            f"  [yellow]▽[/yellow] {routed_intervention.intervention_type.value} "
                            f"→ {target.value} [dim](degraded — {friction.description})[/dim]"
                        )

                if target in self.persona_agents:
                    contacted_personas.add(target)
                    lane_indicator = (
                        "[green]●[/green]" if confidence >= 0.80
                        else "[yellow]●[/yellow]" if confidence >= 0.50
                        else "[red]●[/red]"
                    )
                    if not friction.hit:
                        self._print(
                            f"  {lane_indicator} {routed_intervention.intervention_type.value} "
                            f"→ {target.value} [dim](conf: {confidence:.0%})[/dim]"
                        )

                    # Get persona response
                    response = self.persona_agents[target].respond(
                        intervention=routed_intervention,
                        state=self.state.persona_states[target],
                        org_profile=self.org_profile,
                    )
                    persona_responses[target] = response

                    # Compute effect with realism factors
                    base_effect = self.persona_agents[target].update_state(
                        state=self.state.persona_states[target],
                        intervention=routed_intervention,
                        all_states=self.state.persona_states,
                    )

                    # Apply fatigue multiplier
                    fatigue_mult = fatigue_multiplier(
                        self.state.persona_states[target],
                        routed_intervention.intervention_type,
                    )

                    # Apply grudge dampening
                    grudge_mult = grudge_effect_multiplier(self.state.persona_states[target])

                    # Apply friction effect
                    friction_mult = friction.effect_multiplier

                    # Combined realism adjustment (apply to the delta already applied by update_state)
                    combined_mult = fatigue_mult * grudge_mult * friction_mult
                    if combined_mult != 1.0 and base_effect != 0:
                        # Undo the original effect and reapply with realism multipliers
                        correction = base_effect * (combined_mult - 1.0)
                        self.state.persona_states[target].apply_sentiment_modifier(correction)

                    # Update grudge (successful contact)
                    update_grudge(self.state.persona_states[target], None, had_contact=True)
                    # Successful intervention reduces grudge slightly
                    if base_effect > 0:
                        self.state.persona_states[target].grudge_score = max(
                            0.0, self.state.persona_states[target].grudge_score - 0.05
                        )

                    # Record intervention
                    effective_effect = round(base_effect * combined_mult, 4)
                    self.state.persona_states[target].intervention_history.append(
                        InterventionRecord(
                            week=week,
                            intervention_type=routed_intervention.intervention_type,
                            content_summary=routed_intervention.content[:100],
                            sentiment_effect=effective_effect,
                        )
                    )

                    self._print(f"    [dim]{response}[/dim]")

            # Update grudge for personas NOT contacted this turn
            for ptype, pstate in self.state.persona_states.items():
                if ptype not in contacted_personas:
                    update_grudge(pstate, None, had_contact=False)

            # Step 6: Update flywheel metrics
            flywheel = self.flywheel.compute(self.state, override_rate=self.router.override_rate)
            self.state.metrics = self._flywheel_to_adoption_metrics(flywheel)

            # Step 7: Log the turn
            replan_triggered = "trigger_replan" in (reasoning or "")
            turn = TurnRecord(
                week=week,
                orchestrator_reasoning=reasoning,
                interventions=interventions,
                persona_responses=persona_responses,
                adoption_metrics=self.state.metrics,
                events_fired=events,
                replan_triggered=replan_triggered,
            )
            self.state.turn_history.append(turn)

            # Display metrics
            self._display_metrics()

            # Step 8: Check termination
            outcome = self._check_termination()
            if outcome != SimulationOutcome.IN_PROGRESS:
                self.state.outcome = outcome
                break

        # Final summary
        self._display_summary()
        self._save_log()

        # Cleanup sandboxes if running in sandbox mode
        from src.agents import cleanup_sandboxes
        cleanup_sandboxes()

        return self.state

    def _apply_event(self, event) -> None:
        """Apply a simulation event to persona states."""
        self._print(Panel(
            event.description,
            title=f"EVENT: {event.event_type.value}",
            border_style="red" if any(v < 0 for v in event.sentiment_modifiers.values()) else "green",
        ))
        for persona_type, modifier in event.sentiment_modifiers.items():
            if persona_type in self.state.persona_states:
                self.state.persona_states[persona_type].apply_sentiment_modifier(modifier)

    def _check_termination(self) -> SimulationOutcome:
        """Evaluate termination conditions."""
        if self.state.metrics and self.state.metrics.overall_adoption_pct >= self.org_profile.success_threshold:
            self._print(Panel(
                f"[bold green]Adoption target reached: "
                f"{self.state.metrics.overall_adoption_pct:.1%}[/bold green]",
                border_style="green",
            ))
            return SimulationOutcome.SUCCESS

        if self.state.current_week >= self.org_profile.budget_weeks:
            self._print(Panel(
                f"[bold red]Budget exhausted. Final adoption: "
                f"{self.state.metrics.overall_adoption_pct:.1%} "
                f"(target: {self.org_profile.success_threshold:.0%})[/bold red]",
                border_style="red",
            ))
            return SimulationOutcome.FAILURE_TIMEOUT

        return SimulationOutcome.IN_PROGRESS

    def _display_metrics(self) -> None:
        """Display the Pilot Scorecard (flywheel metrics)."""
        if not self.quiet:
            self.flywheel.display_scorecard()

    def _flywheel_to_adoption_metrics(self, fw) -> AdoptionMetrics:
        """Convert FlywheelMetrics to AdoptionMetrics for backward compatibility."""
        return AdoptionMetrics(
            week=fw.week,
            overall_adoption_pct=fw.overall_adoption_pct,
            login_rate=fw.login_rate,
            feature_usage_depth=fw.completion_rate,
            nps_proxy=fw.nps_proxy,
            risk_flags=fw.risk_flags,
            budget_remaining_weeks=fw.budget_remaining_weeks,
        )

    def _display_summary(self) -> None:
        """Display final simulation summary."""
        outcome_style = {
            SimulationOutcome.SUCCESS: ("green", "DEPLOYMENT SUCCEEDED"),
            SimulationOutcome.FAILURE_TIMEOUT: ("red", "DEPLOYMENT FAILED (timeout)"),
            SimulationOutcome.FAILURE_BUDGET: ("red", "DEPLOYMENT FAILED (budget)"),
            SimulationOutcome.IN_PROGRESS: ("yellow", "SIMULATION ENDED (in progress)"),
        }
        color, label = outcome_style.get(self.state.outcome, ("white", "UNKNOWN"))

        hitl_summary = self.router.get_summary()
        hitl_line = (
            f"HITL: {hitl_summary.get('total_routed', 0)} routed, "
            f"override rate {hitl_summary.get('override_rate', 0):.0%}"
        )

        self._print("\n")
        self._print(Panel(
            f"[bold {color}]{label}[/bold {color}]\n\n"
            f"Duration: {self.state.current_week} weeks\n"
            f"Final Adoption: {self.state.metrics.overall_adoption_pct:.1%}\n"
            f"Total Interventions: {sum(len(t.interventions) for t in self.state.turn_history)}\n"
            f"Events Encountered: {sum(len(t.events_fired) for t in self.state.turn_history)}\n"
            f"Replans Triggered: {sum(1 for t in self.state.turn_history if t.replan_triggered)}\n"
            f"Friction Events: {self._friction_count}\n"
            f"Blind Spots: {self._blind_spot_count}\n"
            f"{hitl_line}",
            title="Simulation Summary",
            border_style=color,
        ))

        # Persona final states
        table = Table(title="Final Persona States", border_style="dim")
        table.add_column("Persona")
        table.add_column("Sentiment")
        table.add_column("Adoption")
        table.add_column("Trust")
        table.add_column("Grudge")
        table.add_column("Interventions")

        for ptype, pstate in self.state.persona_states.items():
            s_color = "green" if pstate.sentiment_score > 0.6 else "yellow" if pstate.sentiment_score > 0.35 else "red"
            g_color = "green" if pstate.grudge_score < 0.2 else "yellow" if pstate.grudge_score < 0.5 else "red"
            table.add_row(
                ptype.value,
                f"[{s_color}]{pstate.sentiment_score:.2f}[/{s_color}]",
                f"{pstate.adoption_likelihood:.2f}",
                f"{pstate.trust_level:.2f}",
                f"[{g_color}]{pstate.grudge_score:.2f}[/{g_color}]",
                str(len(pstate.intervention_history)),
            )
        self._print(table)

    def _save_log(self) -> None:
        """Save simulation log, metadata, and HITL audit trail."""
        sim_id = self.state.simulation_id
        log_path = self.log_dir / f"sim_{sim_id}.jsonl"
        with open(log_path, "w") as f:
            for turn in self.state.turn_history:
                f.write(turn.model_dump_json() + "\n")
        self._print(f"\n[dim]Log saved: {log_path}[/dim]")

        # Save metadata for dashboard labeling
        meta_path = self.log_dir / f"sim_{sim_id}_meta.json"
        meta = {
            "org_name": self.org_profile.org_name,
            "industry": self.org_profile.industry.value,
            "maturity": self.org_profile.technical_maturity.value,
            "sponsorship": self.org_profile.executive_sponsorship.value,
            "team_size": self.org_profile.team_size,
            "budget_weeks": self.org_profile.budget_weeks,
            "target": self.org_profile.success_threshold,
            "outcome": self.state.outcome.value,
            "final_adoption": self.state.metrics.overall_adoption_pct if self.state.metrics else 0.0,
            "weeks_elapsed": self.state.current_week,
            "total_interventions": sum(len(t.interventions) for t in self.state.turn_history),
            "events_encountered": sum(len(t.events_fired) for t in self.state.turn_history),
            "friction_events": self._friction_count,
            "blind_spots": self._blind_spot_count,
            "persona_final_states": {
                ptype.value: {
                    "sentiment": round(pstate.sentiment_score, 3),
                    "adoption": round(pstate.adoption_likelihood, 3),
                    "trust": round(pstate.trust_level, 3),
                    "cognitive_load": round(pstate.cognitive_load, 3),
                    "grudge": round(pstate.grudge_score, 3),
                    "interventions_received": len(pstate.intervention_history),
                }
                for ptype, pstate in self.state.persona_states.items()
            },
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Save HITL audit trail
        if self.router.audit_trail:
            audit_path = self.log_dir / f"sim_{sim_id}_audit.json"
            self.router.save_audit_trail(str(audit_path))
            self._print(f"[dim]Audit trail saved: {audit_path}[/dim]")
