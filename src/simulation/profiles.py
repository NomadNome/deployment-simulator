"""Sample organization profiles for testing and demos."""

from src.models import Industry, Maturity, OrgProfile, Sponsorship


# ── Profile 1: Strong sponsor, high maturity (likely success) ──
ACME_FINANCIAL = OrgProfile(
    org_name="Acme Financial Services",
    industry=Industry.FINANCIAL_SERVICES,
    team_size=200,
    technical_maturity=Maturity.HIGH,
    executive_sponsorship=Sponsorship.STRONG,
    ai_tool_type="AI-powered code assistant for regulatory compliance automation",
    budget_weeks=24,
    success_threshold=0.70,
    competing_priorities=["SOX audit preparation"],
)

# ── Profile 2: Weak sponsor, low maturity (likely failure) ──
MERIDIAN_HEALTHCARE = OrgProfile(
    org_name="Meridian Health Systems",
    industry=Industry.HEALTHCARE,
    team_size=500,
    technical_maturity=Maturity.LOW,
    executive_sponsorship=Sponsorship.WEAK,
    ai_tool_type="Clinical documentation summarization assistant",
    budget_weeks=20,
    success_threshold=0.60,
    competing_priorities=["EHR migration", "HIPAA recertification", "staffing shortages"],
)

# ── Profile 3: Moderate everything (swing case) ──
NOVA_TECH = OrgProfile(
    org_name="Nova Technologies",
    industry=Industry.TECHNOLOGY,
    team_size=150,
    technical_maturity=Maturity.MEDIUM,
    executive_sponsorship=Sponsorship.MODERATE,
    ai_tool_type="AI-powered analytics copilot for product teams",
    budget_weeks=24,
    success_threshold=0.70,
    competing_priorities=["Q3 product launch"],
)


PROFILES = {
    "acme_financial": ACME_FINANCIAL,
    "meridian_healthcare": MERIDIAN_HEALTHCARE,
    "nova_tech": NOVA_TECH,
}
