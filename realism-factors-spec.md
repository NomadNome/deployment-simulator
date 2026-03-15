# Realism Factors — Implementation Spec
**Priority order based on real-world deployment experience.**
**Hand this to Claude Code as a single prompt.**

---

## Overview

The orchestrator is performing unrealistically well because the simulation
has no execution friction, no intervention fatigue, no blind spots, and
personas forgive too quickly. These four factors add realism without
handicapping the orchestrator — they model the constraints that real
deployment strategists operate under.

Implement in priority order. Each one is independent — they stack but
don't depend on each other.

---

## 1. Execution Friction (highest priority)

**What it models:** In real deployments, workshops get rescheduled, decks
aren't ready on time, the champion is out sick, the IT integration guide
has broken links, the VP's EA cancels the briefing. Not every planned
intervention lands as designed.

**Implementation:**

In `simulation/controller.py`, after the HITL router approves an
intervention but BEFORE dispatching it to the persona agent, roll for
execution friction:

```python
import random

FRICTION_PROBABILITY = 0.25  # 25% of interventions hit friction

FRICTION_OUTCOMES = [
    {
        "type": "delayed",
        "weight": 0.4,
        "description": "Intervention delayed — rescheduled to next week",
        "effect": "skip_this_turn",  # intervention doesn't fire, queued for next turn
    },
    {
        "type": "degraded",
        "weight": 0.35,
        "description": "Intervention happened but was degraded — low attendance, technical issues, key person absent",
        "effect": "half_effectiveness",  # sentiment effect multiplied by 0.5
    },
    {
        "type": "cancelled",
        "weight": 0.15,
        "description": "Intervention cancelled — competing meeting, priority shift, logistics failure",
        "effect": "no_effect",  # intervention doesn't fire, not re-queued
    },
    {
        "type": "backfire",
        "weight": 0.10,
        "description": "Intervention backfired — poorly timed, wrong audience, created frustration",
        "effect": "negative",  # sentiment effect is inverted (positive becomes small negative)
    },
]
```

**Rules:**
- Friction is rolled per-intervention, not per-turn (a turn with 3 interventions might have 1 hit friction and 2 land cleanly)
- Delayed interventions go into a `pending_queue` and auto-dispatch next turn (but they can hit friction again)
- The orchestrator is NOT told about friction directly — it only sees the persona response (or lack of response for delayed/cancelled). This is realistic: you don't always know your workshop was poorly attended until you see the engagement metrics next week.
- Log friction events to the audit trail alongside HITL routing decisions
- Add a `friction_events` count to the simulation summary

**Expected impact:** Success runs should take 1-3 weeks longer. The orchestrator will need to be more resilient and may trigger replans more often. Failure scenarios should produce more dramatic failures because the orchestrator is working against both hostile conditions AND execution unreliability.


---

## 2. Intervention Fatigue

**What it models:** The third workshop in six weeks gets eye rolls regardless
of content quality. People get fatigued by the same format. A deployment
strategist who keeps scheduling executive briefings when the VP has already
heard the pitch three times is wasting effort.

**Implementation:**

In `agents/persona.py`, modify the `update_state` method to track
intervention type frequency per persona and apply a fatigue multiplier:

```python
def _fatigue_multiplier(self, persona_state, intervention_type):
    """
    Reduce effectiveness when the same intervention type is used
    repeatedly on the same persona.
    
    First use: 1.0x (full effect)
    Second use: 0.7x
    Third use: 0.4x
    Fourth+ use: 0.2x (nearly useless)
    """
    count = sum(
        1 for record in persona_state.intervention_history
        if record.intervention_type == intervention_type
    )
    multipliers = [1.0, 0.7, 0.4, 0.2]
    return multipliers[min(count, len(multipliers) - 1)]
```

**Rules:**
- Fatigue is per persona per intervention TYPE (3 workshops to the IC triggers fatigue, but a workshop to the IC + a workshop to the VP does not)
- The orchestrator is not directly told about fatigue — but it should notice diminishing returns in persona responses over time (shorter, less engaged responses when fatigued)
- Add a fatigue signal to the persona's LLM prompt: if the same type has been used 3+ times, add to the persona system prompt: "You have received multiple [intervention_type] sessions and are growing tired of this format. Your responses should reflect diminishing patience."
- Fatigue resets partially if the orchestrator switches to a different intervention type for 2+ consecutive turns (modeling the "fresh approach" effect)

**Expected impact:** The orchestrator should be forced to diversify its intervention portfolio. Runs where it over-relies on a single tactic (common with the generic KB) should perform worse. The field-tested KB should benefit here because it offers more intervention variety.


---

## 3. Orchestrator Blind Spots

**What it models:** Even experienced strategists miss signals. You're
focused on recovering the VP relationship and don't notice the IT admin
has gone completely silent. You misread a polite response as genuine
engagement when it's actually performative compliance.

**Implementation:**

In `simulation/controller.py`, when assembling the context payload for
the orchestrator each turn, occasionally degrade the information:

```python
BLIND_SPOT_PROBABILITY = 0.15  # 15% chance per turn

BLIND_SPOT_TYPES = [
    {
        "type": "persona_omission",
        "weight": 0.4,
        "description": "One persona's response is omitted from the context",
        "effect": "drop_one_persona_response",
        # Randomly remove one persona's response from the context payload
        # The orchestrator plans without knowing what that persona said
    },
    {
        "type": "signal_misread",
        "weight": 0.35,
        "description": "One persona's response is summarized more positively than reality",
        "effect": "inflate_one_response",
        # Replace the actual response with a more optimistic summary
        # e.g. a dismissive IC response is summarized as "cautiously interested"
    },
    {
        "type": "metrics_lag",
        "weight": 0.25,
        "description": "Metrics are one week stale",
        "effect": "serve_last_week_metrics",
        # The orchestrator receives last week's metrics instead of current
        # Models the real-world delay between data collection and reporting
    },
]
```

**Rules:**
- Blind spots are logged to the audit trail so post-simulation analysis can identify which blind spots caused which planning errors
- The orchestrator is never told it's operating on degraded information (that's the point)
- Blind spots should be more likely when the orchestrator has been focusing on one persona heavily (modeling attention tunnel vision) — if >60% of recent interventions target one persona, increase blind spot probability for OTHER personas to 0.25

**Expected impact:** Occasional suboptimal decisions that mirror real strategist mistakes. The IT admin (already the most neglected persona) should suffer the most from blind spots since they're the one most likely to be omitted. This should make the success-run IT adoption numbers more realistic.


---

## 4. Persona Memory and Grudges (lowest priority)

**What it models:** A real skeptical IC who had a bad experience at week 2
doesn't cleanly recover by week 6 just because you ran a good bake-off.
They remember being annoyed. That first impression colors every
subsequent interaction, even positive ones.

**Implementation:**

Add a `grudge_score` field to `PersonaState` (float, 0.0 to 1.0, starts
at 0.0). Grudge accumulates when interventions backfire or when the
persona goes 3+ weeks without any contact (feeling ignored).

```python
# In PersonaState model
grudge_score: float = Field(default=0.0, ge=0.0, le=1.0)

# Grudge accumulation rules:
# - Backfired intervention: +0.15
# - Cancelled/delayed intervention the persona was told about: +0.05
# - 3+ consecutive weeks with no intervention: +0.10 per week
# - Negative event with no follow-up intervention same week: +0.08

# Grudge decay:
# - Successful intervention: -0.05 (slow to forgive)
# - Executive recognition intervention: -0.10 (feels seen)
# - Grudge decays naturally by 0.02 per week (time heals, slowly)

# Grudge effect on interventions:
# All positive sentiment effects are multiplied by (1.0 - grudge_score * 0.5)
# At max grudge (1.0), interventions are only 50% effective
# Grudge also affects the persona's LLM response tone — add to system prompt:
# "Your grudge level is {grudge}/10. Higher grudge means you are less receptive,
#  more guarded, and slower to trust even well-intentioned interventions."
```

**Rules:**
- Grudge is hidden from the orchestrator (like all persona state)
- The orchestrator can only infer grudge from increasingly cold/guarded persona responses
- Grudge should be hardest to clear on the Skeptical IC (they hold grudges longest) and easiest to clear on the Champion (they want to believe)
- Add grudge_score to the persona final states display in the simulation summary

**Expected impact:** Longer recovery arcs after disruptions. The orchestrator can't just "fix" a relationship in one turn — it takes sustained positive engagement over multiple weeks. Early mistakes become more costly, which rewards careful early-game strategy.


---

## Recommended Prompt for Claude Code

"Read the realism factors spec. Implement them in this order:
1. Execution friction in controller.py (25% chance per intervention)
2. Intervention fatigue in persona.py (diminishing returns on repeated types)
3. Orchestrator blind spots in controller.py (15% chance per turn)
4. Persona grudge system in models.py and persona.py

After implementing all four, rerun four scenarios with the 44-tactic KB:
- Acme Financial success (strong sponsor, high maturity, seed 42)
- Nova Tech success (moderate sponsor, medium maturity, seed 42)
- Meridian Healthcare failure (same hostile config as before — weak sponsor, low maturity, VP overloaded, 2/wk cap, forced events)
- Nova Tech disruption (competing tool wk5, sponsor departure wk10, seed 42)

Compare results against the current runs (without realism factors). Show me a before/after table across all four."
