"""Knowledge Base Tool — semantic retrieval over change management tactics."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from field_tested_tactics import FIELD_TESTED_TACTICS
from research_backed_tactics import RESEARCH_BACKED_TACTICS

console = Console()

# ── Tactic Library (source of truth) ─────────────────────────

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

# Append field-tested and research-backed tactics
TACTICS_LIBRARY.extend(FIELD_TESTED_TACTICS)
TACTICS_LIBRARY.extend(RESEARCH_BACKED_TACTICS)

# IDs of field-tested and research-backed entries for scoring boost
_BOOSTED_IDS = {t["id"] for t in FIELD_TESTED_TACTICS} | {t["id"] for t in RESEARCH_BACKED_TACTICS}

# ChromaDB paths
CHROMA_PATH = Path("data/knowledge_base/chroma_db")
COLLECTION_NAME = "deployment_tactics"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ── ChromaDB Knowledge Base ──────────────────────────────────

class KnowledgeBaseTool:
    """Semantic search over change management tactics using ChromaDB.

    Falls back to keyword search if ChromaDB or sentence-transformers
    are unavailable.
    """

    def __init__(self, reindex: bool = False):
        self._chromadb_available = False
        self.tactics = TACTICS_LIBRARY

        try:
            import chromadb
            from chromadb.utils import embedding_functions

            CHROMA_PATH.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
            self.collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )

            if self.collection.count() == 0 or reindex:
                self._index_tactics()

            self._chromadb_available = True
        except Exception as e:
            console.print(f"[dim]ChromaDB unavailable, using keyword fallback: {e}[/dim]")

    def _index_tactics(self):
        """Index all tactics into ChromaDB."""
        # Clear existing
        if self.collection.count() > 0:
            existing = self.collection.get()
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])

        ids = []
        documents = []
        metadatas = []

        for tactic in TACTICS_LIBRARY:
            ids.append(tactic["id"])
            doc = (
                f"{tactic['tactic']} "
                f"{tactic['best_for']} "
                f"{tactic['stage']} "
                f"{tactic['framework']}"
            )
            documents.append(doc)
            metadatas.append({
                "id": tactic["id"],
                "framework": tactic["framework"],
                "stage": tactic["stage"],
                "is_field_tested": tactic["id"] in _BOOSTED_IDS,
                "tactic": tactic["tactic"][:500],  # ChromaDB metadata size limit
                "best_for": tactic["best_for"][:500],
            })

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        console.print(f"[dim]Indexed {len(ids)} tactics into ChromaDB[/dim]")

    def query(self, query: str, max_results: int = 3) -> list[dict[str, str]]:
        """Search tactics — semantic if ChromaDB available, keyword fallback otherwise."""
        if self._chromadb_available:
            return self._semantic_query(query, max_results)
        return self._keyword_query(query, max_results)

    def _semantic_query(self, query: str, max_results: int) -> list[dict[str, str]]:
        """Semantic search with ChromaDB + field-tested relevance boost."""
        fetch_n = min(max_results * 3, self.collection.count())

        results = self.collection.query(
            query_texts=[query],
            n_results=fetch_n,
            include=["metadatas", "distances"],
        )

        if not results["metadatas"] or not results["metadatas"][0]:
            return []

        scored = []
        for meta, distance in zip(results["metadatas"][0], results["distances"][0]):
            # Cosine distance: 0 = identical, 2 = opposite → similarity
            similarity = 1 - (distance / 2)

            if meta.get("is_field_tested"):
                similarity *= 1.3

            # Reconstruct full tactic from library (metadata may be truncated)
            full_tactic = next((t for t in TACTICS_LIBRARY if t["id"] == meta["id"]), None)
            if full_tactic:
                scored.append((similarity, full_tactic))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [tactic for _, tactic in scored[:max_results]]

    def _keyword_query(self, query: str, max_results: int) -> list[dict[str, str]]:
        """Fallback keyword search."""
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
                if tactic["id"] in _BOOSTED_IDS:
                    score *= 1.3
                scored.append((score, tactic))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:max_results]]

    def reindex(self):
        """Force reindex all tactics."""
        if self._chromadb_available:
            self._index_tactics()
