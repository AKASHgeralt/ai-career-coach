"""Next Best Action engine.

Decides the single highest-value thing a user should do next. Fully
deterministic — no LLM — so the recommendation is reproducible and the stated
reason is always literally true of the user's data.

Two tiers, checked in order:

  1. SETUP   — a signal has no data at all. Collecting it beats optimising
               anything else, because it also unlocks a chunk of the readiness
               score that currently isn't being measured.
  2. IMPROVE — everything is measured, so target the weakest signal.
"""
from app.services.readiness import weakest_component

# Dashboard section each action links to.
SECTION_RESUMES = "Resumes"
SECTION_SKILLS = "Skill Gap"
SECTION_ROADMAP = "Roadmap"
SECTION_INTERVIEW = "Interview"
SECTION_GITHUB = "GitHub"
SECTION_SETTINGS = "Settings"


def _action(action, why, cta_label, section, priority, based_on):
    return {
        "action": action,
        "why": why,
        "cta_label": cta_label,
        "target_section": section,
        "priority": priority,
        "based_on": based_on,
    }


def determine_next_action(
    *,
    readiness: dict,
    target_role_label: str | None = None,
    top_missing_skill: tuple[str, int] | None = None,
    gap_count: int = 0,
    role_scoped_gap: bool = False,
) -> dict:
    """Pick the highest-value next action.

    readiness          -- output of compute_readiness()
    target_role_label  -- e.g. "AI Engineer", or None if unset
    top_missing_skill  -- (skill, times_missing) most frequently missing skill
    gap_count          -- how many skill gap analyses the user has run
    role_scoped_gap    -- whether any analysis targets their chosen role
    """
    by_key = {c["key"]: c for c in readiness["components"]}
    role = target_role_label or "your target role"

    # --- Tier 1: setup ------------------------------------------------------
    if not target_role_label:
        return _action(
            "Choose your target role",
            "Every other measurement — skill gaps, roadmap, interview questions "
            "and your readiness score — is calibrated against a target role. "
            "Nothing can be personalised until you pick one.",
            "Choose target role", SECTION_SETTINGS, "setup", "target_role",
        )

    if not by_key["resume"]["available"]:
        return _action(
            "Upload your resume",
            f"Your resume is the starting point for everything else: it supplies "
            f"your ATS score and the skills compared against {role}. "
            f"It's worth {by_key['resume']['base_weight']}% of your readiness score.",
            "Upload resume", SECTION_RESUMES, "setup", "resume",
        )

    if not by_key["skills"]["available"]:
        return _action(
            f"Run a skill gap analysis for {role}",
            f"Skill match is the single largest part of your readiness score "
            f"({by_key['skills']['base_weight']}%), and it's not being measured yet. "
            f"This is also what generates your learning roadmap.",
            "Analyse skill gap", SECTION_SKILLS, "setup", "skills",
        )

    if not by_key["interview"]["available"]:
        return _action(
            f"Complete a mock interview for {role}",
            f"You have no interview data yet, so "
            f"{by_key['interview']['base_weight']}% of your readiness score isn't "
            f"being measured. One session is enough to start scoring it.",
            "Start interview", SECTION_INTERVIEW, "setup", "interview",
        )

    if not by_key["github"]["available"]:
        return _action(
            "Connect your GitHub profile",
            f"GitHub is worth {by_key['github']['base_weight']}% of your readiness "
            f"score and is currently unmeasured. Connecting it takes one step and "
            f"shows employers your practical work.",
            "Connect GitHub", SECTION_GITHUB, "setup", "github",
        )

    # A skill gap exists but none of them target the chosen role — the skill
    # number is real, but it isn't measuring what the user actually wants.
    if not role_scoped_gap:
        return _action(
            f"Re-run your skill gap analysis against {role}",
            f"Your skill match is currently based on a different role, so it isn't "
            f"telling you how ready you are for {role}. Re-running it against your "
            f"target role makes the largest part of your score meaningful.",
            "Analyse skill gap", SECTION_SKILLS, "setup", "skills",
        )

    # --- Tier 2: improve the weakest measured signal ------------------------
    weakest = weakest_component(readiness)
    if weakest is None:
        return _action(
            "Upload your resume",
            "Nothing has been measured yet.",
            "Upload resume", SECTION_RESUMES, "setup", "resume",
        )

    key, score = weakest["key"], weakest["score"]

    if key == "skills":
        if top_missing_skill:
            skill, times = top_missing_skill
            analyses = f"{times} of your {gap_count} analyses" if gap_count > 1 else "your analysis"
            return _action(
                f"Close your biggest skill gap: {skill}",
                f"Skill match is your weakest signal at {score:.0f}/100, and {skill} "
                f"is missing from {analyses} for {role}. It carries the most weight "
                f"of any component ({weakest['base_weight']}%), so closing this gap "
                f"moves your score more than anything else.",
                "Open roadmap", SECTION_ROADMAP, "improve", "skills",
            )
        return _action(
            f"Build the skills {role} requires",
            f"Skill match is your weakest signal at {score:.0f}/100 and carries the "
            f"most weight ({weakest['base_weight']}%).",
            "Open roadmap", SECTION_ROADMAP, "improve", "skills",
        )

    if key == "resume":
        return _action(
            "Improve your resume's ATS score",
            f"Your resume scores {score:.0f}/100, the weakest of your measured "
            f"signals. Re-analysing it shows exactly which sections are costing "
            f"you points, and a stronger resume lifts "
            f"{weakest['base_weight']}% of your readiness score.",
            "Open resumes", SECTION_RESUMES, "improve", "resume",
        )

    if key == "interview":
        return _action(
            f"Practise more {role} interviews",
            f"Your average answer scores {score:.0f}/100, the weakest of your "
            f"measured signals. Each session gives scored feedback on where your "
            f"answers fall short.",
            "Start interview", SECTION_INTERVIEW, "improve", "interview",
        )

    return _action(
        "Strengthen your GitHub profile",
        f"Your developer score is {score:.0f}/100, the weakest of your measured "
        f"signals. It's driven by repository count, stars, language spread and "
        f"followers — a well-documented portfolio project moves it most.",
        "Open GitHub", SECTION_GITHUB, "improve", "github",
    )
