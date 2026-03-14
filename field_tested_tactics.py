"""
Field-tested knowledge base entries — derived from real deployment patterns.

These supplement the existing ADKAR/Kotter tactics in knowledge_base.py.
Review each one, adjust language or details, then merge into TACTICS_LIBRARY.

Format matches the existing KB structure so they drop in directly.
"""

FIELD_TESTED_TACTICS = [

    # ── STALL DETECTION ──────────────────────────────────────

    {
        "id": "field_metrics_first_signal",
        "framework": "Field-tested",
        "stage": "Stall Detection",
        "tactic": (
            "The first reliable signal of a stalling deployment is a drop in "
            "login and usage metrics, not anecdotal feedback. By the time a "
            "champion tells you things are slowing down, metrics have already "
            "been declining for 1-2 weeks. Set up a weekly metrics check as a "
            "non-negotiable ritual starting week 1. If logins drop more than "
            "15% week-over-week, treat it as an early warning regardless of "
            "what stakeholders are saying verbally."
        ),
        "best_for": (
            "Any deployment past week 2. The orchestrator should check metrics "
            "BEFORE reading persona responses each turn to avoid anchoring on "
            "optimistic self-reporting."
        ),
    },

    {
        "id": "field_week8_engagement_dip",
        "framework": "Field-tested",
        "stage": "Stall Detection",
        "tactic": (
            "In 6-month org-wide enablement programs, engagement reliably drops "
            "around week 8 when the novelty wears off and day-job pressures "
            "reassert. This is predictable, not a crisis. Pre-schedule a "
            "re-engagement intervention for week 7-8: a quick-win session "
            "showcasing new use cases, a peer showcase where top users demo "
            "their workflows, or a gamified challenge with visible leaderboard. "
            "The key is to have this planned before the dip, not scrambled "
            "together after you notice it."
        ),
        "best_for": (
            "Longer deployments (12+ weeks). If the simulation is running a "
            "24-week budget, the orchestrator should proactively plan a "
            "re-engagement around week 7-8 even if metrics look healthy."
        ),
    },

    # ── RECOVERY TACTICS ─────────────────────────────────────

    {
        "id": "field_workshops_to_1on1s",
        "framework": "Field-tested",
        "stage": "Recovery",
        "tactic": (
            "When group workshops stop generating engagement, switch to 1:1 "
            "meetings. Group formats let skeptics hide in the crowd and give "
            "polite non-answers. A 1:1 forces honest conversation about what "
            "is actually blocking adoption for that individual. Common findings "
            "from the 1:1 pivot: the tool does not solve their specific "
            "workflow, they had a bad first experience and wrote it off, or "
            "their manager has not signaled that using the tool is a priority. "
            "None of these surface in a group workshop."
        ),
        "best_for": (
            "Recovering stalled ICs and mid-level managers. Especially "
            "effective for the skeptical IC persona after a group workshop "
            "produced low engagement. Do not use for VPs — they need executive "
            "briefings, not 1:1 coaching sessions."
        ),
    },

    {
        "id": "field_peer_company_proof",
        "framework": "Field-tested",
        "stage": "Recovery",
        "tactic": (
            "When internal enthusiasm is low, bring in an external peer proof "
            "point: a success story from a comparable company in the same "
            "industry or of similar size. This works because skeptics discount "
            "internal cheerleading but pay attention to what their competitors "
            "or peers are doing. Frame it as a case study, not a sales pitch. "
            "Include specific metrics if possible: hours saved per week, "
            "reduction in review cycles, adoption curve timeline. The implicit "
            "message is 'they figured it out and you are falling behind.'"
        ),
        "best_for": (
            "Re-engaging risk-averse VPs who have gone quiet and skeptical ICs "
            "who dismiss internal success stories. Most effective when the peer "
            "company is in the same industry vertical."
        ),
    },

    # ── CHAMPION MANAGEMENT ──────────────────────────────────

    {
        "id": "field_champion_isolation",
        "framework": "Field-tested",
        "stage": "Champion Enablement",
        "tactic": (
            "A single internal champion without executive air cover burns out "
            "by week 6-8. The pattern: they evangelize early, spend political "
            "capital advocating, get no visible support from leadership, and "
            "quietly disengage. Prevention requires three things delivered "
            "together: (1) explicit executive recognition in a visible forum "
            "like an all-hands or team meeting, (2) a direct communication "
            "channel between the champion and the deployment team so they do "
            "not feel alone, and (3) a second champion identified early so the "
            "load is shared. If you only do one, do the executive recognition "
            "— it costs nothing and signals that the initiative matters."
        ),
        "best_for": (
            "Any deployment relying on a single champion. The orchestrator "
            "should check: has the champion received executive recognition by "
            "week 4? If not, flag it as a risk."
        ),
    },

    # ── PROGRAM SEQUENCING ───────────────────────────────────

    {
        "id": "field_diagnostic_before_deployment",
        "framework": "Field-tested",
        "stage": "Pre-deployment",
        "tactic": (
            "Before launching a full deployment, run a 1-month diagnostic with "
            "stakeholder interviews and readiness scorecards. The diagnostic "
            "reveals three things you cannot see from the outside: who the real "
            "decision-maker is (often not the person who signed the contract), "
            "what competing initiatives will fight for attention, and how the "
            "organization actually makes technology adoption decisions. Skip "
            "the diagnostic and you are guessing at all three."
        ),
        "best_for": (
            "Pre-deployment planning. The orchestrator should treat the org "
            "profile as a diagnostic output — if the profile shows weak "
            "sponsorship and multiple competing priorities, that is diagnostic "
            "data that should shape the entire rollout strategy."
        ),
    },

    {
        "id": "field_competitive_cohort_dynamics",
        "framework": "Field-tested",
        "stage": "Engagement",
        "tactic": (
            "Structure the rollout as a competitive learning cohort: 4-6 teams "
            "of 10-25 people compete on adoption metrics, use case quality, "
            "and peer-voted showcases over a 4-month period. Competition "
            "activates social dynamics that training alone cannot — teams do "
            "not want to be the one that falls behind. Visible leaderboards "
            "and weekly standups where teams share progress create natural "
            "accountability. This format works because it shifts adoption from "
            "an individual choice to a team commitment."
        ),
        "best_for": (
            "Mid-size deployments (50-150 users) where team identity is "
            "strong. Less effective in very large rollouts where teams do not "
            "interact, or very small ones where competition feels forced."
        ),
    },

    # ── INDUSTRY-SPECIFIC ────────────────────────────────────

    {
        "id": "field_fs_compliance_gate",
        "framework": "Field-tested",
        "stage": "Industry-specific",
        "tactic": (
            "In financial services, the compliance and security review is the "
            "first gate, not the last. Do not schedule user-facing workshops "
            "until the security team has signed off. If you launch workshops "
            "before approval, you create enthusiasm you cannot deliver on, "
            "which destroys trust faster than starting slowly. Sequence: "
            "security review and compliance approval first, then IT "
            "provisioning, then executive briefing, then user enablement. "
            "Budget 2-4 extra weeks for this gate compared to a tech company "
            "deployment."
        ),
        "best_for": (
            "Financial services, insurance, and regulated industry "
            "deployments. The orchestrator should detect industry=financial_services "
            "and front-load IT admin and compliance interventions before "
            "any IC or champion engagement."
        ),
    },

    {
        "id": "field_fs_vs_tech_pacing",
        "framework": "Field-tested",
        "stage": "Industry-specific",
        "tactic": (
            "Financial services and technology companies adopt at fundamentally "
            "different rhythms. Tech companies move faster but have higher "
            "competing tool risk — engineers will evaluate three alternatives "
            "before committing. Financial services moves slower due to "
            "compliance gates but once approved, adoption is more durable "
            "because switching costs are higher. Calibrate the orchestrator's "
            "patience: in tech, expect visible adoption signals by week 3 or "
            "escalate. In financial services, do not panic until week 6 — the "
            "early weeks are compliance overhead, not resistance."
        ),
        "best_for": (
            "Setting expectations for deployment timeline. The orchestrator "
            "should adjust its re-planning triggers based on industry: "
            "earlier in tech, later in financial services."
        ),
    },

    # ── STAKEHOLDER DYNAMICS ─────────────────────────────────

    {
        "id": "field_silent_vp_pattern",
        "framework": "Field-tested",
        "stage": "Executive Engagement",
        "tactic": (
            "When an executive sponsor goes silent — no responses for 2 or "
            "more weeks — this is the single highest-risk signal in a "
            "deployment. It almost always means they have mentally "
            "deprioritized the initiative in favor of something with more "
            "immediate board or quarterly visibility. Do not send another "
            "email. Schedule a 15-minute call, bring refreshed ROI data tied "
            "to their current quarterly priorities, and explicitly ask whether "
            "the initiative still has their sponsorship. A direct question "
            "forces a direct answer. Ambiguity at this stage is worse than "
            "a no."
        ),
        "best_for": (
            "VP or C-level personas who have gone quiet after initial "
            "engagement. The orchestrator should track consecutive weeks "
            "without VP interaction and escalate at 2 weeks of silence."
        ),
    },

    {
        "id": "field_it_as_silent_bottleneck",
        "framework": "Field-tested",
        "stage": "IT Enablement",
        "tactic": (
            "IT is the persona most likely to bottleneck a deployment without "
            "anyone noticing. They do not push back loudly — they just "
            "deprioritize your request in a queue of 47 other tickets. The "
            "fix is not escalation (that burns trust). The fix is making their "
            "job as easy as possible: pre-built integration runbooks, a clear "
            "checklist of exactly what you need from them, a realistic "
            "timeline you agree on together, and a standing 15-minute weekly "
            "check-in so blockers surface early. Treat IT as a partner, not "
            "a dependency."
        ),
        "best_for": (
            "Any deployment where IT provisioning, SSO integration, or "
            "security review is required. The orchestrator should ensure IT "
            "receives at least one intervention in the first 2 weeks, even "
            "if just an async message with a clear scope document."
        ),
    },

    # ── SCALE AND SEGMENTATION ───────────────────────────────

    {
        "id": "field_150_user_threshold",
        "framework": "Field-tested",
        "stage": "Scale Strategy",
        "tactic": (
            "Below 150 users, you can drive adoption through direct personal "
            "engagement — 1:1s, small workshops, named champions. Above 150, "
            "you need systems: automated onboarding sequences, peer cohort "
            "structures, self-serve resources, and metric dashboards that "
            "surface risk without requiring manual monitoring. The transition "
            "point is not gradual. Deployments that try to maintain a "
            "high-touch model above 150 users exhaust the deployment team "
            "and produce inconsistent experiences."
        ),
        "best_for": (
            "Determining the right intervention density based on team_size. "
            "For simulations with team_size above 150, the orchestrator should "
            "favor scalable interventions (async, peer cohorts, gamified "
            "challenges) over individual ones (1:1s, personal demos)."
        ),
    },

    {
        "id": "field_quick_win_before_strategy",
        "framework": "Field-tested",
        "stage": "Early Momentum",
        "tactic": (
            "In the first 2 weeks, prioritize one visible quick win over a "
            "comprehensive rollout strategy. Find the single highest-value, "
            "lowest-friction use case for one team, run a focused session to "
            "achieve a measurable result, and broadcast it. This produces a "
            "concrete proof point that shifts the conversation from 'will this "
            "work' to 'how do we scale what worked.' A strategy without an "
            "early proof point is just a slide deck. A proof point without a "
            "strategy is just a demo. Do the proof point first."
        ),
        "best_for": (
            "Week 1-2 of any deployment. The orchestrator should plan at "
            "least one quick-win intervention in the first 2 turns regardless "
            "of what the knowledge base returns."
        ),
    },

    # ── SCOPE AND PACING ─────────────────────────────────────

    {
        "id": "field_scope_discipline",
        "framework": "Field-tested",
        "stage": "Scope Management",
        "tactic": (
            "The most common deployment failure mode is scope overreach: "
            "trying to roll out to 500 users across 8 teams simultaneously "
            "in month one. Customers who bite off more than they can chew "
            "spread their enablement resources thin, produce shallow "
            "engagement everywhere, and deep adoption nowhere. Constrain the "
            "initial scope to 1-2 teams or one business function. Get to "
            "measurable success there first, then expand. A deployment that "
            "succeeds with 30 users and scales is worth more than one that "
            "touches 500 and stalls at 15% adoption."
        ),
        "best_for": (
            "Pre-deployment scoping and any simulation where team_size "
            "exceeds 200. The orchestrator should recognize when the org "
            "profile implies an unrealistically broad rollout and recommend "
            "a phased approach in its initial plan."
        ),
    },

    {
        "id": "field_staggered_flywheel",
        "framework": "Field-tested",
        "stage": "Scale Strategy",
        "tactic": (
            "Build adoption as a flywheel, not a big bang. Start with a small "
            "cohort of 10-20 users, identify 2-3 champions within that group "
            "early, invest in making them successful, and then use their "
            "results and advocacy to pull in the next cohort. Champions should "
            "feel included in the strategy, not deployed as instruments of it "
            "— involve them in planning the next wave, ask for their input on "
            "what worked and what did not, and give them ownership of specific "
            "use cases. When champions feel invested in the rollout, they "
            "advocate naturally rather than performatively. Each wave of "
            "adoption should make the next wave easier because there are more "
            "internal proof points, more trained champions, and more visible "
            "momentum."
        ),
        "best_for": (
            "Any deployment above 50 users. The orchestrator should sequence "
            "champion identification and enablement in weeks 1-3, then begin "
            "expanding reach in weeks 4-6 using those champions as anchors "
            "for peer cohorts."
        ),
    },

    # ── GOAL ALIGNMENT ───────────────────────────────────────

    {
        "id": "field_goals_backward_planning",
        "framework": "Field-tested",
        "stage": "Strategy Design",
        "tactic": (
            "Start with the customer's business goals and work backward to "
            "the deployment strategy — not the other way around. A financial "
            "services firm whose goal is reducing compliance review cycle "
            "time needs different interventions than a tech company whose "
            "goal is accelerating feature velocity, even if both are "
            "deploying the same AI tool. Map each business goal to the "
            "persona most responsible for achieving it, then select "
            "interventions that directly connect the tool to that persona's "
            "workflow for that goal. Industry-specific interventions should "
            "be chosen based on which goals matter most in that vertical, "
            "not based on generic best practices."
        ),
        "best_for": (
            "Initial rollout planning. The orchestrator should read the "
            "org profile's industry and ai_tool_type fields and align its "
            "intervention strategy to the implicit business goals for that "
            "vertical rather than applying a one-size-fits-all playbook."
        ),
    },

    # ── WORKFLOW INTEGRATION ─────────────────────────────────

    {
        "id": "field_tie_to_sprints",
        "framework": "Field-tested",
        "stage": "Workflow Integration",
        "tactic": (
            "Adoption sticks when the AI tool is tied to existing work "
            "cadences, not treated as a separate activity. Map interventions "
            "to sprint cycles, project milestones, or quarterly planning "
            "rhythms so that using the tool is part of the work people are "
            "already doing. For example, if a team runs 2-week sprints, "
            "schedule a quick-win session at the start of a sprint using "
            "the tool on a real sprint task — not a synthetic exercise. When "
            "people see the tool producing value on something they were going "
            "to do anyway, adoption becomes a natural extension of their "
            "workflow rather than an additional obligation. Make this visible: "
            "track which sprint tasks or project deliverables used the AI "
            "tool and surface those wins in team standups and retros."
        ),
        "best_for": (
            "Any deployment targeting engineering, product, or project-based "
            "teams with existing sprint or milestone cadences. The "
            "orchestrator should time interventions to coincide with the "
            "start of work cycles, not arbitrary calendar weeks."
        ),
    },

    {
        "id": "field_centralize_communications",
        "framework": "Field-tested",
        "stage": "Visibility",
        "tactic": (
            "Centralize all deployment communications in one visible channel "
            "— a dedicated Slack channel, Teams channel, or shared dashboard "
            "— so that progress, wins, and resources are discoverable by "
            "anyone in the rollout population. Scattered communications "
            "(some in email, some in meetings, some in docs) mean that "
            "stakeholders only see the pieces directed at them and miss the "
            "broader momentum. A centralized channel creates ambient "
            "awareness: even people who are not actively using the tool see "
            "others posting wins, asking questions, and getting support. "
            "That ambient signal is one of the strongest drivers of organic "
            "adoption because it normalizes usage without requiring a formal "
            "intervention."
        ),
        "best_for": (
            "Week 1 setup action. The orchestrator should recommend "
            "establishing a centralized communications channel as one of "
            "its first async interventions, before any workshops or demos."
        ),
    },

    # ── TIMING AND URGENCY ───────────────────────────────────

    {
        "id": "field_intervention_timeliness",
        "framework": "Field-tested",
        "stage": "Execution Discipline",
        "tactic": (
            "The timing of an intervention matters as much as the "
            "intervention itself. A perfectly designed workshop delivered "
            "two weeks after the moment of need is wasted effort — the "
            "persona has already formed an opinion or found a workaround. "
            "When metrics signal a problem (engagement dip, VP silence, IT "
            "delay), respond within that same week. When a positive event "
            "happens (a champion posts a win, a team hits a milestone), "
            "amplify it immediately — not in next week's update. Deployment "
            "strategy is a real-time discipline. The orchestrator that waits "
            "for the next scheduled check-in to address a problem is already "
            "behind."
        ),
        "best_for": (
            "Every turn of the simulation. The orchestrator should treat "
            "risk flags as same-turn priorities, not items to address in the "
            "next planning cycle. Delayed response to stall signals is one "
            "of the most common orchestrator failure modes."
        ),
    },

    # ── RECOGNITION AND ORGANIC GROWTH ───────────────────────

    {
        "id": "field_recognition_gamification",
        "framework": "Field-tested",
        "stage": "Reinforcement",
        "tactic": (
            "Build a recognition layer into the deployment from week 2 "
            "onward: points for completing use cases, badges for milestones "
            "like first workflow automated or first team demo delivered, "
            "visible leaderboards in the centralized communication channel, "
            "and shout-outs in team standups or all-hands. Gamification works "
            "not because people care about points but because it makes "
            "progress visible and creates social proof. When someone sees a "
            "peer earn a badge for automating a report, they think 'I could "
            "do that too' — and now adoption is spreading through curiosity "
            "rather than mandate. Keep the system lightweight: a Slack emoji "
            "reaction workflow or a simple shared tracker is enough. "
            "Overengineered gamification platforms create their own adoption "
            "problem."
        ),
        "best_for": (
            "Weeks 2-8 of any deployment, especially when initial adoption "
            "is established but organic growth has stalled. The orchestrator "
            "should introduce recognition elements after the first quick win, "
            "not before — you need something real to recognize first."
        ),
    },

    {
        "id": "field_art_of_the_possible",
        "framework": "Field-tested",
        "stage": "Inspiration",
        "tactic": (
            "Showcase the art of the possible: curated demos, internal use "
            "case galleries, and live sessions where adopters show what they "
            "built with the tool in their own workflows. This is the single "
            "most effective way to get people to tell the adoption story for "
            "you. When a skeptical IC sees a peer — not a vendor, not a "
            "manager, but someone who does the same job — demo a workflow "
            "that saves them 2 hours a week, the credibility is instant. "
            "The deployment team's job shifts from pushing adoption to "
            "curating and amplifying what early adopters create. Run an "
            "internal showcase every 2-3 weeks where 2-3 users present "
            "their use cases in 5 minutes each. Record them. Post them in "
            "the centralized channel. Let people see what is possible and "
            "imagine their own version of it."
        ),
        "best_for": (
            "Mid-deployment (weeks 4-12) when a core group of adopters "
            "exists but the majority has not yet engaged. The orchestrator "
            "should transition from direct intervention to curation and "
            "amplification once activation rate exceeds 25%."
        ),
    },

    {
        "id": "field_user_driven_flywheel",
        "framework": "Field-tested",
        "stage": "Organic Growth",
        "tactic": (
            "The ultimate goal of a deployment is to make itself unnecessary. "
            "When users start creating their own use cases, sharing them "
            "unprompted, and onboarding peers without being asked, adoption "
            "has become self-sustaining. The deployment team's role shifts "
            "from driving adoption to feeding the flywheel: surfacing the "
            "best user-generated use cases, connecting people who are solving "
            "similar problems, removing friction when someone wants to try "
            "something new, and making sure leadership sees the organic "
            "momentum. Social selling within the org — users selling other "
            "users on the tool through their own results — is more durable "
            "than any top-down mandate. Design every intervention with this "
            "end state in mind: am I creating a dependent relationship or "
            "am I enabling the user to become an advocate?"
        ),
        "best_for": (
            "Late-stage deployment (weeks 8+) when adoption is above 40%. "
            "The orchestrator should recognize when user-driven signals "
            "emerge (champion advocating without being asked, new use cases "
            "appearing organically) and shift from active intervention to "
            "amplification and friction removal."
        ),
    },

    # ── ADKAR REFRAME: DESIRE IS THE BOTTLENECK ──────────────

    {
        "id": "field_adkar_desire_first",
        "framework": "Field-tested (ADKAR reframe)",
        "stage": "Strategy Design",
        "tactic": (
            "Most ADKAR implementations front-load Awareness and Knowledge: "
            "send announcement emails, run training workshops, build "
            "documentation. This gets the sequence wrong. Awareness and "
            "Knowledge mean nothing if people do not want to use the tool. "
            "Desire is the bottleneck — it is the stage where most "
            "deployments silently stall because teams assume that if people "
            "know about the tool and know how to use it, they will use it. "
            "They will not. Desire requires emotional investment, not "
            "information transfer. The orchestrator should diagnose every "
            "stall as a Desire problem first and only move to Knowledge or "
            "Ability once Desire is confirmed. If a persona is not engaging, "
            "the question is not 'do they know how to use it' — it is 'do "
            "they want to.'"
        ),
        "best_for": (
            "Every phase of the deployment. When the orchestrator detects "
            "low adoption despite completed training or high awareness, it "
            "should diagnose a Desire gap rather than scheduling more "
            "training. The default ADKAR diagnostic in the system prompt "
            "should weight Desire as the most likely root cause."
        ),
    },

    {
        "id": "field_desire_through_champions",
        "framework": "Field-tested (ADKAR reframe)",
        "stage": "Desire Building",
        "tactic": (
            "Champions are the primary vehicle for building Desire. A "
            "training session tells people what the tool does. A champion "
            "showing their own workflow tells people why they should care. "
            "The mechanism is social proof and relatability — when someone "
            "in the same role, with the same pressures, says 'this saves "
            "me 3 hours a week on report generation,' that registers as "
            "evidence in a way that a vendor demo never will. Identify "
            "champions early (week 1-2), invest in making them successful "
            "with a concrete use case by week 3, then deploy them as the "
            "primary Desire-building intervention from week 4 onward. The "
            "champion's use case becomes the proof that makes other people "
            "want in."
        ),
        "best_for": (
            "Building Desire in skeptical ICs and neutral mid-level "
            "personas. The orchestrator should pair champion showcase "
            "interventions with specific personas who share the champion's "
            "role or workflow."
        ),
    },

    {
        "id": "field_desire_through_incentives",
        "framework": "Field-tested (ADKAR reframe)",
        "stage": "Desire Building",
        "tactic": (
            "Recognition and tangible incentives lower the activation "
            "energy for Desire. A well-timed raffle — complete one use case "
            "this sprint and enter to win — can produce more first-time "
            "usage in a week than a month of training sessions. The ROI on "
            "a modest prize budget is enormous compared to the cost of a "
            "stalled deployment. The key is timing and specificity: tie the "
            "incentive to a concrete action (not just logging in), run it "
            "during a period when engagement is naturally dipping (week 6-8), "
            "and make the winner visible so it creates a story. Raffles, "
            "team challenges with prizes, and public leaderboards all work "
            "because they create a moment where using the tool feels "
            "rewarding rather than obligatory."
        ),
        "best_for": (
            "Re-engaging a population where Awareness and Knowledge are "
            "established but activation is low. Especially effective at the "
            "week 6-8 engagement dip. The orchestrator should consider "
            "incentive-based interventions when activation rate is below 30% "
            "despite completed workshops."
        ),
    },

    {
        "id": "field_desire_through_use_cases",
        "framework": "Field-tested (ADKAR reframe)",
        "stage": "Desire Building",
        "tactic": (
            "Use cases are the bridge between Awareness and Desire. A user "
            "who has seen the tool but not imagined how it fits their "
            "specific workflow is stuck between knowing and wanting. The "
            "fix is to show them a use case that maps to something they "
            "already do: not a generic demo but a real example from someone "
            "in their role, on their kind of data, solving their kind of "
            "problem. Curate a library of 5-10 role-specific use cases "
            "from early adopters and make them easily discoverable — pinned "
            "in the centralized channel, linked in onboarding materials, "
            "referenced in 1:1s. When someone says 'I do not see how this "
            "applies to me,' the answer should be a 2-minute use case "
            "walkthrough from their peer, not another feature overview."
        ),
        "best_for": (
            "Any persona expressing awareness without engagement — they "
            "know the tool exists but have not tried it. The orchestrator "
            "should match use case examples to the target persona's role "
            "and industry context."
        ),
    },
]
