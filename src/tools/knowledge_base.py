"""Knowledge Base Tool — RAG over change management frameworks and tactics."""

from __future__ import annotations

from field_tested_tactics import FIELD_TESTED_TACTICS

# In Phase 1, this is a simple in-memory lookup. In Phase 2+, swap in ChromaDB.

TACTICS_LIBRARY: list[dict[str, str]] = [
    {
        "id": "adkar_awareness",
        "framework": "Prosci ADKAR",
        "stage": "Awareness",
        "tactic": "Executive sponsor kickoff communication explaining why the change is happening, what business problem it solves, and what happens if the organization does not adapt.",
        "best_for": "Early-stage initiatives where stakeholders do not yet understand the reason for change."
    },
    {
        "id": "adkar_desire",
        "framework": "Prosci ADKAR",
        "stage": "Desire",
        "tactic": "Peer testimonial sessions where early adopters share concrete time savings and workflow improvements. Focus on 'what's in it for me' framing for each persona.",
        "best_for": "Stakeholders who understand the change but are not motivated to participate."
    },
    {
        "id": "adkar_knowledge",
        "framework": "Prosci ADKAR",
        "stage": "Knowledge",
        "tactic": "Hands-on workshop using the stakeholder's actual work artifacts. No synthetic demos. Pair each participant with a buddy who has already adopted the tool.",
        "best_for": "Stakeholders who are willing but lack the skills or knowledge to use the tool effectively."
    },
    {
        "id": "adkar_ability",
        "framework": "Prosci ADKAR",
        "stage": "Ability",
        "tactic": "Weekly office hours and async support channel. Reduce friction by embedding the tool into existing workflows rather than creating new ones. Quick-win sessions targeting one specific task.",
        "best_for": "Stakeholders who have been trained but struggle to apply the tool in daily work."
    },
    {
        "id": "adkar_reinforcement",
        "framework": "Prosci ADKAR",
        "stage": "Reinforcement",
        "tactic": "Public recognition of adoption milestones. Gamified challenges with team leaderboards. Executive shout-outs in all-hands meetings. Tie usage metrics to team OKRs.",
        "best_for": "Sustaining adoption after initial rollout. Preventing regression to old behaviors."
    },
    {
        "id": "kotter_urgency",
        "framework": "Kotter's 8-Step",
        "stage": "Create Urgency",
        "tactic": "Share competitive intelligence showing peer companies already deploying similar tools. Quantify the cost of inaction: hours lost, competitive disadvantage, talent attrition risk.",
        "best_for": "Risk-averse executives who need business justification before committing resources."
    },
    {
        "id": "kotter_coalition",
        "framework": "Kotter's 8-Step",
        "stage": "Build Coalition",
        "tactic": "Identify and activate 3-5 internal champions across different functions. Give them early access, dedicated support, and a direct line to the deployment team. They become your distributed change network.",
        "best_for": "Scaling adoption beyond the initial pilot group."
    },
    {
        "id": "kotter_quick_wins",
        "framework": "Kotter's 8-Step",
        "stage": "Generate Quick Wins",
        "tactic": "Identify the single highest-value, lowest-friction use case for each team. Run a focused 2-hour session to achieve one measurable success. Document and broadcast the result.",
        "best_for": "Building momentum in the first 4 weeks. Countering skepticism with evidence."
    },
    {
        "id": "tactic_skeptic_conversion",
        "framework": "Custom",
        "stage": "Resistance Management",
        "tactic": "For vocal skeptics: schedule a 1:1 where you ask them to identify the tool's weaknesses. Then address each one. Skeptics who feel heard become the strongest advocates because their endorsement carries credibility.",
        "best_for": "Individual contributors who are technically competent and actively resisting."
    },
    {
        "id": "tactic_champion_support",
        "framework": "Custom",
        "stage": "Champion Enablement",
        "tactic": "Champions burn out when they feel used as props. Provide them with: executive air cover (their VP publicly thanks them), dedicated Slack channel with the deployment team, preview access to new features, and monthly recognition.",
        "best_for": "Preventing champion burnout in month 2-4 of a rollout."
    },
    {
        "id": "tactic_vp_roi_framework",
        "framework": "Custom",
        "stage": "Executive Engagement",
        "tactic": "For VP-level stakeholders, present a one-page ROI dashboard: hours saved per week per user × team size × fully loaded cost. Include a competitive benchmark section showing peer adoption rates.",
        "best_for": "Re-engaging executives who have gone quiet or started deprioritizing."
    },
    {
        "id": "tactic_it_unblock",
        "framework": "Custom",
        "stage": "IT Enablement",
        "tactic": "Provide IT with a pre-built integration runbook: SSO config steps, security review checklist, SCIM provisioning guide. Reduce the ask to 'follow these 12 steps' not 'figure out how to integrate this.'",
        "best_for": "Overloaded IT teams who are bottlenecking the rollout."
    },
    {
        "id": "tactic_cohort_learning",
        "framework": "Custom",
        "stage": "Social Learning",
        "tactic": "Form small peer cohorts (5-8 people, same function) who meet weekly for 30 minutes to share what they tried, what worked, and what didn't. Peer accountability and social proof in one format.",
        "best_for": "Moving from individual adoption to team-level norms."
    },
    {
        "id": "tactic_reorg_response",
        "framework": "Custom",
        "stage": "Crisis Response",
        "tactic": "When a reorg hits, immediately schedule a 15-minute call with the new decision-maker. Reframe the initiative in terms of their priorities. Do not assume continuity — treat it as a new executive briefing.",
        "best_for": "Surviving organizational disruptions mid-rollout."
    },
    {
        "id": "tactic_competing_tool",
        "framework": "Custom",
        "stage": "Competitive Response",
        "tactic": "When a competing tool is demoed internally, do not dismiss it. Instead, run a structured bake-off on the team's actual use cases. Let the tool's results speak. This converts a threat into a validation opportunity.",
        "best_for": "Responding to competitive pressure without appearing defensive."
    },
    {
        "id": "antipattern_spray_pray",
        "framework": "Anti-pattern",
        "stage": "Avoidance",
        "tactic": "WARNING: Sending mass emails and scheduling organization-wide trainings without persona-specific targeting is the most common deployment failure mode. It feels productive but produces low engagement and high fatigue.",
        "best_for": "Recognizing when the orchestrator is falling into a one-size-fits-all approach."
    },
    {
        "id": "antipattern_champion_overload",
        "framework": "Anti-pattern",
        "stage": "Avoidance",
        "tactic": "WARNING: Relying on a single champion to drive all internal advocacy leads to burnout by week 6-8. Distribute the load across 3-5 champions minimum and provide each with explicit support.",
        "best_for": "Recognizing champion burnout risk before it manifests."
    },
    {
        "id": "antipattern_silent_vp",
        "framework": "Anti-pattern",
        "stage": "Avoidance",
        "tactic": "WARNING: When an executive sponsor goes quiet (no responses for 2+ weeks), this is the highest-risk signal in a deployment. It means they have mentally deprioritized. Immediate 1:1 re-engagement with refreshed ROI data is critical.",
        "best_for": "Detecting and responding to executive disengagement."
    },
]

# Append field-tested tactics from real deployment patterns
TACTICS_LIBRARY.extend(FIELD_TESTED_TACTICS)

# IDs of field-tested entries for scoring boost
_FIELD_TESTED_IDS = {t["id"] for t in FIELD_TESTED_TACTICS}


class KnowledgeBaseTool:
    """Simple keyword-based knowledge base. Replace with ChromaDB in Phase 2."""

    def __init__(self):
        self.tactics = TACTICS_LIBRARY

    def query(self, query: str, max_results: int = 3) -> list[dict[str, str]]:
        """Search tactics by keyword relevance.

        Field-tested entries receive a 1.3x scoring boost since they
        encode patterns validated across real enterprise deployments.
        """
        query_terms = set(query.lower().split())
        scored = []

        for tactic in self.tactics:
            searchable = (
                tactic["tactic"].lower() + " " +
                tactic["best_for"].lower() + " " +
                tactic["stage"].lower() + " " +
                tactic["framework"].lower()
            )
            score = sum(1 for term in query_terms if term in searchable)
            if score > 0:
                # Field-tested tactics get a 1.3x relevance boost
                if tactic["id"] in _FIELD_TESTED_IDS:
                    score *= 1.3
                scored.append((score, tactic))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:max_results]]
