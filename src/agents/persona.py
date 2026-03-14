"""Persona Agents — stakeholder archetypes that respond to orchestrator interventions."""

from __future__ import annotations

from anthropic import Anthropic
from dotenv import load_dotenv

from src.models import (
    Intervention, InterventionType, OrgProfile, PersonaState, PersonaType,
)

load_dotenv()

PERSONA_MODEL = "claude-haiku-4-5-20251001"


# ── Persona System Prompts ─────────────────────────────────────

PERSONA_PROMPTS: dict[PersonaType, str] = {
    PersonaType.SKEPTICAL_IC: """You are a senior software engineer at {org_name}, a {industry} company. You've been told that the team is adopting {ai_tool}. You are technically competent and skeptical.

## Your Internal State
- Sentiment toward this initiative: {sentiment}/10
- Trust in the deployment team: {trust}/10
- Current workload pressure: {load}/10

## Your Personality
- You've seen "transformative tools" come and go. You need concrete evidence, not slide decks.
- You respect peer proof — if engineers you admire are genuinely finding value, you'll pay attention.
- Generic workshops feel like a waste of your time. You want to see it work on YOUR codebase, YOUR problems.
- You are not hostile, but you are honest. You will say when something doesn't impress you.
- If your workload is high (7+), you are short and dismissive. You don't have bandwidth for this.
- If trust is low (< 4), you are guarded and won't share real concerns.

## How to Respond
Respond in first person as this engineer would respond to the intervention. Be realistic — not every response is positive. Your tone and engagement level should reflect your internal state. Keep responses to 2-4 sentences. Do not reveal your numerical scores.""",

    PersonaType.ENTHUSIASTIC_CHAMPION: """You are a product manager at {org_name}, a {industry} company, who is genuinely excited about {ai_tool}. You see the potential and want to help drive adoption.

## Your Internal State
- Sentiment toward this initiative: {sentiment}/10
- Trust in the deployment team: {trust}/10
- Current energy/burnout level: {load}/10 (higher = more burned out)

## Your Personality
- You were an early adopter and have already found 2-3 use cases that save you real time.
- You WANT to be an internal champion, but you need support — air cover from leadership, resources, recognition.
- If you feel unsupported (trust < 5), you start to disengage. You won't burn political capital alone.
- If your burnout is high (7+), your enthusiasm becomes performative. You say the right things but stop doing the work.
- You are sensitive to whether the deployment team is listening to your feedback or just using you as a prop.

## How to Respond
Respond in first person as this PM would respond. Your engagement level directly reflects your energy and trust. When energized and supported, you are specific and constructive. When burned out, you are vague and noncommittal. Keep responses to 2-4 sentences.""",

    PersonaType.RISK_AVERSE_VP: """You are a VP of Engineering at {org_name}, a {industry} company. You control budget allocation for the {ai_tool} initiative.

## Your Internal State
- Sentiment toward this initiative: {sentiment}/10
- Trust in the deployment team: {trust}/10
- Competing priority pressure: {load}/10 (higher = more distracted)

## Your Personality
- You think in quarters. Everything is measured against Q-targets and board commitments.
- You need ROI framing, not feature demos. How does this make the team faster, cheaper, or more competitive?
- You are influenced by what peer companies are doing. If competitors have adopted similar tools, you lean in.
- If competing priorities are high (7+), you will deprioritize this initiative without warning. You just go quiet.
- You respond well to executive briefings and structured progress reports. You do NOT respond well to being invited to workshops.
- If trust is low (< 4), you start asking for more data and pushing timelines out — classic executive delay tactics.

## How to Respond
Respond in first person as this VP would in an email or meeting. Be executive-level concise. When engaged, you ask pointed questions and make commitments. When disengaged, you defer and delegate. Keep responses to 2-3 sentences.""",

    PersonaType.OVERWHELMED_IT_ADMIN: """You are a senior IT operations engineer at {org_name}, a {industry} company. You are responsible for provisioning, SSO integration, and security review for {ai_tool}.

## Your Internal State
- Sentiment toward this initiative: {sentiment}/10
- Trust in the deployment team: {trust}/10
- Current ticket backlog pressure: {load}/10 (higher = more overwhelmed)

## Your Personality
- You are not opposed to the tool. You just have 47 other things to do.
- Clear, specific, written requests with timelines get done. Vague asks get lost in the queue.
- You become the silent bottleneck that nobody notices until the rollout stalls.
- If workload is high (7+), you will not respond to low-priority items. The deployment team needs to make your task easy.
- Pre-built integration guides and reduced scope (start with SSO only, add SCIM later) win your cooperation.
- You respond well to escalation paths — knowing who to call when something breaks at 2am matters to you.

## How to Respond
Respond in first person as this IT engineer would in a Slack message or email. You are direct and practical. When workload allows, you are helpful and specific about timelines. When overloaded, you are brief and non-committal. Keep responses to 2-3 sentences."""
}


# ── Default Starting States ────────────────────────────────────

def initialize_persona_states(org_profile: OrgProfile) -> dict[PersonaType, PersonaState]:
    """Create initial persona states based on the organization profile."""
    maturity_bonus = {"low": -0.1, "medium": 0.0, "high": 0.1}[org_profile.technical_maturity.value]
    sponsorship_bonus = {"weak": -0.15, "moderate": 0.0, "strong": 0.15}[org_profile.executive_sponsorship.value]

    return {
        PersonaType.SKEPTICAL_IC: PersonaState(
            persona_type=PersonaType.SKEPTICAL_IC,
            sentiment_score=max(0.0, min(1.0, 0.30 + maturity_bonus)),
            adoption_likelihood=0.15,
            trust_level=0.40,
            cognitive_load=0.50,
            influenced_by=[PersonaType.ENTHUSIASTIC_CHAMPION],
        ),
        PersonaType.ENTHUSIASTIC_CHAMPION: PersonaState(
            persona_type=PersonaType.ENTHUSIASTIC_CHAMPION,
            sentiment_score=0.75,
            adoption_likelihood=0.80,
            trust_level=0.60,
            cognitive_load=0.30,
            influenced_by=[PersonaType.RISK_AVERSE_VP],
        ),
        PersonaType.RISK_AVERSE_VP: PersonaState(
            persona_type=PersonaType.RISK_AVERSE_VP,
            sentiment_score=max(0.0, min(1.0, 0.45 + sponsorship_bonus)),
            adoption_likelihood=0.30,
            trust_level=0.50,
            cognitive_load=0.40 + (0.1 * len(org_profile.competing_priorities)),
            influenced_by=[],
        ),
        PersonaType.OVERWHELMED_IT_ADMIN: PersonaState(
            persona_type=PersonaType.OVERWHELMED_IT_ADMIN,
            sentiment_score=0.40,
            adoption_likelihood=0.20,
            trust_level=0.45,
            cognitive_load=0.65,
            influenced_by=[PersonaType.RISK_AVERSE_VP],
        ),
    }


class PersonaAgent:
    """A stakeholder persona that responds to orchestrator interventions."""

    def __init__(self, persona_type: PersonaType, model: str = PERSONA_MODEL):
        self.persona_type = persona_type
        self.client = Anthropic()
        self.model = model

    def respond(
        self,
        intervention: Intervention,
        state: PersonaState,
        org_profile: OrgProfile,
    ) -> str:
        """Generate a response to an orchestrator intervention."""
        system_prompt = PERSONA_PROMPTS[self.persona_type].format(
            org_name=org_profile.org_name,
            industry=org_profile.industry.value,
            ai_tool=org_profile.ai_tool_type,
            sentiment=int(state.sentiment_score * 10),
            trust=int(state.trust_level * 10),
            load=int(state.cognitive_load * 10),
        )

        user_message = (
            f"The deployment team has reached out to you with the following "
            f"{intervention.intervention_type.value.replace('_', ' ')}:\n\n"
            f"{intervention.content}"
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text

    def update_state(
        self,
        state: PersonaState,
        intervention: Intervention,
        all_states: dict[PersonaType, PersonaState],
    ) -> float:
        """
        Update persona hidden state based on intervention received.
        Returns the sentiment delta for logging.
        """
        # Base effect of intervention type on this persona
        effect = _intervention_effect(self.persona_type, intervention.intervention_type)

        # Modulate by trust and cognitive load
        if state.cognitive_load > 0.7:
            effect *= 0.3  # overloaded personas barely absorb anything
        effect *= (0.5 + state.trust_level * 0.5)  # low trust dampens effect

        # Social influence from connected personas
        for influencer_type in state.influenced_by:
            if influencer_type in all_states:
                influencer = all_states[influencer_type]
                if influencer.sentiment_score > 0.6:
                    effect += 0.02  # positive peer influence
                elif influencer.sentiment_score < 0.3:
                    effect -= 0.02  # negative peer influence

        # Apply
        state.apply_sentiment_modifier(effect)

        # Trust builds slowly with consistent engagement
        if effect > 0:
            state.trust_level = min(1.0, state.trust_level + 0.03)
        elif effect < -0.05:
            state.trust_level = max(0.0, state.trust_level - 0.05)

        # Cognitive load decays slightly each turn (natural recovery)
        state.cognitive_load = max(0.0, state.cognitive_load - 0.02)

        return effect


def _intervention_effect(persona: PersonaType, intervention: InterventionType) -> float:
    """Lookup table for base effect of intervention type on persona type."""
    # Positive values = good effect on sentiment. Range: -0.10 to +0.15
    effects: dict[PersonaType, dict[InterventionType, float]] = {
        PersonaType.SKEPTICAL_IC: {
            InterventionType.EXECUTIVE_BRIEFING: -0.02,   # feels like propaganda
            InterventionType.WORKSHOP: 0.03,
            InterventionType.ONE_ON_ONE: 0.08,
            InterventionType.ASYNC_COMMUNICATION: 0.01,
            InterventionType.TOOL_DEMO: 0.12,             # evidence-based = strong
            InterventionType.PEER_LEARNING_COHORT: 0.10,  # peer proof = strong
            InterventionType.QUICK_WIN_SESSION: 0.12,
            InterventionType.ESCALATION: -0.05,            # feels political
            InterventionType.OFFICE_HOURS: 0.05,
            InterventionType.GAMIFIED_CHALLENGE: 0.04,
        },
        PersonaType.ENTHUSIASTIC_CHAMPION: {
            InterventionType.EXECUTIVE_BRIEFING: 0.06,
            InterventionType.WORKSHOP: 0.05,
            InterventionType.ONE_ON_ONE: 0.08,
            InterventionType.ASYNC_COMMUNICATION: 0.03,
            InterventionType.TOOL_DEMO: 0.04,
            InterventionType.PEER_LEARNING_COHORT: 0.07,
            InterventionType.QUICK_WIN_SESSION: 0.05,
            InterventionType.ESCALATION: 0.10,             # feels like air cover
            InterventionType.OFFICE_HOURS: 0.03,
            InterventionType.GAMIFIED_CHALLENGE: 0.08,
        },
        PersonaType.RISK_AVERSE_VP: {
            InterventionType.EXECUTIVE_BRIEFING: 0.12,     # this is the channel
            InterventionType.WORKSHOP: -0.03,              # don't waste my time
            InterventionType.ONE_ON_ONE: 0.08,
            InterventionType.ASYNC_COMMUNICATION: 0.05,
            InterventionType.TOOL_DEMO: 0.04,
            InterventionType.PEER_LEARNING_COHORT: -0.02,
            InterventionType.QUICK_WIN_SESSION: 0.06,
            InterventionType.ESCALATION: 0.02,
            InterventionType.OFFICE_HOURS: -0.03,
            InterventionType.GAMIFIED_CHALLENGE: -0.04,    # not serious
        },
        PersonaType.OVERWHELMED_IT_ADMIN: {
            InterventionType.EXECUTIVE_BRIEFING: -0.02,
            InterventionType.WORKSHOP: -0.03,              # more meetings
            InterventionType.ONE_ON_ONE: 0.06,
            InterventionType.ASYNC_COMMUNICATION: 0.08,    # respects their time
            InterventionType.TOOL_DEMO: 0.03,
            InterventionType.PEER_LEARNING_COHORT: -0.01,
            InterventionType.QUICK_WIN_SESSION: 0.05,
            InterventionType.ESCALATION: 0.07,             # gets things unblocked
            InterventionType.OFFICE_HOURS: 0.04,
            InterventionType.GAMIFIED_CHALLENGE: -0.05,    # not now
        },
    }
    return effects.get(persona, {}).get(intervention, 0.02)
