"""
Research-backed knowledge base entries — AI-specific adoption patterns.

These supplement the existing generic (ADKAR/Kotter) and field-tested
tactics with findings from 2025-2026 enterprise AI adoption research
(Deloitte State of AI, McKinsey, Writer/Workplace Intelligence, Larridin).

Tagged "Research-backed" to distinguish from field-tested and generic.
Merge into TACTICS_LIBRARY in knowledge_base.py alongside the other entries.
"""

RESEARCH_BACKED_TACTICS = [

    # ── PILOT PURGATORY ──────────────────────────────────────

    {
        "id": "research_pilot_purgatory",
        "framework": "Research-backed",
        "stage": "Scale Strategy",
        "tactic": (
            "88% of enterprises use AI in at least one function, but fewer "
            "than 40% have scaled beyond pilot. This pilot purgatory is a "
            "distinct failure mode from low adoption: the pilot succeeds "
            "with 20-50 users, leadership declares victory, and then the "
            "initiative stalls because nobody planned the graduation path. "
            "The symptoms are: a successful pilot team with no rollout "
            "timeline, no budget allocated for scaling, and no designated "
            "owner for the next phase. The fix is to define exit criteria "
            "and a scale plan before the pilot starts, not after it "
            "succeeds. Include in the pilot charter: what adoption rate "
            "triggers expansion, who funds the next phase, what "
            "infrastructure changes are needed for 10x the users, and "
            "who owns the transition from pilot to production."
        ),
        "best_for": (
            "Mid-stage deployments (weeks 8-16) where early adoption "
            "metrics look strong but there is no visible plan for "
            "expanding beyond the initial cohort. The orchestrator should "
            "flag pilot purgatory risk when activation rate exceeds 50% "
            "in the pilot group but overall organizational adoption "
            "remains below 20%."
        ),
    },

    # ── SHADOW AI ────────────────────────────────────────────

    {
        "id": "research_shadow_ai_signal",
        "framework": "Research-backed",
        "stage": "Stall Detection",
        "tactic": (
            "When official adoption metrics are low but employees are "
            "clearly using AI (visible in their outputs, mentioned in "
            "meetings, evident in workflow changes), the likely cause is "
            "shadow AI: employees using unauthorized tools with personal "
            "accounts and pasting proprietary data into unvetted models. "
            "This is not a deployment failure. It is a demand signal "
            "disguised as a compliance risk. The correct response is not "
            "to crack down on shadow AI but to understand what it reveals "
            "about user needs that the official tool is not meeting. "
            "Interview shadow AI users: what tool are they using, what "
            "use case does it serve, and what does the sanctioned tool "
            "lack? Then close the gap. If the sanctioned tool cannot "
            "match the shadow alternative, the deployment has a product "
            "problem, not an adoption problem."
        ),
        "best_for": (
            "Any deployment where engagement metrics are low but "
            "qualitative signals suggest AI is being used informally. "
            "The orchestrator should consider shadow AI as a hypothesis "
            "when activation rate is below 25% despite high awareness "
            "and completed training. A good diagnostic question for "
            "persona agents: are they using other AI tools outside the "
            "sanctioned one?"
        ),
    },

    # ── CROSS-DEPARTMENT OWNERSHIP CONFLICT ──────────────────

    {
        "id": "research_ai_ownership_conflict",
        "framework": "Research-backed",
        "stage": "Stakeholder Dynamics",
        "tactic": (
            "42% of C-suite executives report that AI adoption is creating "
            "internal conflict, including power struggles between "
            "departments, siloed development, and in some cases active "
            "sabotage. 68% report tension between IT and other business "
            "units over AI ownership. This is an AI-specific dynamic that "
            "does not typically occur with standard software rollouts "
            "because AI touches workflows across functions in ways that "
            "traditional tools do not. The deployment strategist must "
            "identify the ownership dynamic early: is this a top-down "
            "mandate from a single VP, a grassroots movement from ICs, "
            "or a contested space where multiple leaders claim the AI "
            "agenda? For contested ownership, the intervention is to "
            "facilitate a governance alignment session before launching "
            "the deployment, establishing a single accountable sponsor "
            "and a cross-functional steering committee with clear "
            "decision rights."
        ),
        "best_for": (
            "Pre-deployment and early deployment in organizations where "
            "multiple departments have competing AI initiatives or where "
            "the orchestrator detects conflicting signals from the VP "
            "persona and other stakeholders about priorities and "
            "direction. The orchestrator should probe for ownership "
            "conflict when the VP persona gives mixed signals about "
            "commitment despite strong stated support."
        ),
    },

    # ── SKILLS-FIRST ANTI-PATTERN ────────────────────────────

    {
        "id": "research_skills_first_antipattern",
        "framework": "Research-backed",
        "stage": "Avoidance",
        "tactic": (
            "WARNING: The most common enterprise response to AI adoption "
            "challenges is to invest in training and education. Research "
            "shows that education is the number one way companies adjust "
            "their talent strategies for AI, ahead of role redesign or "
            "workflow integration. This is backwards. Training builds "
            "Knowledge (the K in ADKAR) but does not build Desire (the "
            "D). Organizations that lead with training produce employees "
            "who know how to use the tool but choose not to, because "
            "their workflows have not been redesigned to make the tool "
            "valuable and nobody has shown them why they should care. "
            "The correct sequence is: demonstrate value through a quick "
            "win (Desire), then provide training (Knowledge), then "
            "redesign the workflow to embed the tool (Ability). Training "
            "without prior Desire-building is the most expensive way to "
            "achieve low adoption."
        ),
        "best_for": (
            "Any deployment where the customer's first instinct is to "
            "schedule organization-wide training. The orchestrator should "
            "recognize when its plan over-indexes on workshop and "
            "training interventions without first establishing Desire "
            "through champions, quick wins, and use case showcases. "
            "This tactic reinforces the Desire-first ADKAR reframe."
        ),
    },

    # ── GOVERNANCE AS ACCELERATOR ────────────────────────────

    {
        "id": "research_governance_accelerator",
        "framework": "Research-backed",
        "stage": "Executive Engagement",
        "tactic": (
            "Counterintuitively, enterprises where senior leadership "
            "actively shapes AI governance achieve significantly greater "
            "business value than those delegating governance to technical "
            "teams alone. Governance is not a brake on adoption. It is "
            "an accelerator. When executives visibly own AI oversight "
            "and embed it into performance rubrics, it signals that AI "
            "is a strategic priority, not an experiment. This gives "
            "middle managers permission to invest time in adoption and "
            "gives ICs confidence that the tool will be supported long "
            "term. The deployment strategist should frame governance "
            "conversations not as compliance overhead but as executive "
            "commitment signals. Help the VP establish a lightweight "
            "governance structure (usage policy, data handling "
            "guidelines, review cadence) and make it visible. The act "
            "of governing communicates permanence."
        ),
        "best_for": (
            "VP and executive persona engagement, especially in "
            "regulated industries (financial services, healthcare) "
            "where governance concerns can stall adoption entirely. "
            "The orchestrator should recommend governance setup as an "
            "early VP intervention rather than treating it as a late "
            "stage compliance task."
        ),
    },

    # ── STRATEGY GAP ─────────────────────────────────────────

    {
        "id": "research_strategy_doubles_success",
        "framework": "Research-backed",
        "stage": "Pre-deployment",
        "tactic": (
            "Enterprises with a formal AI strategy report 80% success "
            "in adoption, compared to 37% for those without one. Having "
            "any documented strategy nearly doubles the success rate. "
            "The strategy does not need to be elaborate. A one-page "
            "document covering four questions is sufficient: what is "
            "the business goal this AI deployment serves, who is the "
            "accountable executive sponsor, what does success look like "
            "in 90 days, and what is the rollout sequence (which teams "
            "first, which use cases, what milestones). Organizations "
            "that skip this step and jump straight to tool deployment "
            "are in the 37% bucket. The deployment strategist should "
            "refuse to launch a full rollout without a documented "
            "strategy, even a minimal one. If the customer cannot "
            "answer the four questions, they are not ready."
        ),
        "best_for": (
            "Pre-deployment planning and initial orchestrator strategy "
            "generation. The orchestrator should check whether the org "
            "profile implies an existing strategy (strong sponsorship "
            "and clear competing priorities suggest strategic thinking) "
            "or ad-hoc experimentation (weak sponsorship and no stated "
            "goals suggest strategy gap). If no strategy is evident, "
            "the first intervention should be helping create one, not "
            "scheduling workshops."
        ),
    },
]
