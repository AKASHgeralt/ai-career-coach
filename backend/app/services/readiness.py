"""Career Readiness Score.

A single 0-100 number summarising how ready a user is for their target role,
built from the four signals the platform already measures. Deliberately
deterministic: no LLM is involved, so the number is reproducible and every
point of it can be traced back to a component the user can see.

Missing components are excluded rather than counted as zero, and the remaining
weights are renormalised. Someone who hasn't connected GitHub yet is not
"20% worse" — GitHub simply doesn't participate in their score, and the API
says so explicitly.
"""

# Skills carry the most weight: the gap against the target role is the most
# direct measure of readiness. Resume is next (it's the artefact that actually
# gets screened). Interview and GitHub are corroborating evidence.
COMPONENT_WEIGHTS = {
    "resume": 25,
    "skills": 35,
    "interview": 20,
    "github": 20,
}

COMPONENT_LABELS = {
    "resume": "Resume / ATS",
    "skills": "Skill Match",
    "interview": "Interview",
    "github": "GitHub",
}

# Shown when a component has no data, so the UI never has to invent copy.
MISSING_REASONS = {
    "resume": ("No resume uploaded yet.", "Upload a resume to score this."),
    "skills": ("No skill gap analysis yet.", "Run a skill gap analysis to score this."),
    "interview": ("No interview answers yet.", "Complete a mock interview to score this."),
    "github": ("No GitHub profile connected.", "Connect GitHub to score this."),
}

COMPONENT_ORDER = ("resume", "skills", "interview", "github")


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def compute_readiness(
    resume: float | None = None,
    skills: float | None = None,
    interview: float | None = None,
    github: float | None = None,
    details: dict[str, str] | None = None,
) -> dict:
    """Combine 0-100 component scores into an overall readiness score.

    Each argument is a 0-100 score, or None when that signal has no data yet.
    `details` optionally maps a component key to a short human explanation of
    where its number came from.

    Returns a dict carrying the overall score, every component (present or
    not), and a plain-language explanation of what drove the result.
    """
    details = details or {}
    raw = {"resume": resume, "skills": skills, "interview": interview, "github": github}

    available = {k: _clamp(v) for k, v in raw.items() if v is not None}
    total_weight = sum(COMPONENT_WEIGHTS[k] for k in available)

    score = None
    if total_weight > 0:
        weighted = sum(available[k] * COMPONENT_WEIGHTS[k] for k in available)
        score = round(weighted / total_weight, 1)

    components = []
    for key in COMPONENT_ORDER:
        present = key in available
        # Effective weight is what this component is actually worth right now,
        # after renormalising over whatever data exists.
        effective = (
            round(COMPONENT_WEIGHTS[key] / total_weight * 100, 1)
            if present and total_weight else 0.0
        )
        reason, action = MISSING_REASONS[key]
        components.append({
            "key": key,
            "label": COMPONENT_LABELS[key],
            "score": available.get(key),
            "available": present,
            "base_weight": COMPONENT_WEIGHTS[key],
            "effective_weight": effective,
            "detail": details.get(key) if present else reason,
            "action": None if present else action,
        })

    return {
        "score": score,
        "components": components,
        "available_count": len(available),
        "total_components": len(COMPONENT_ORDER),
        "missing": [c["key"] for c in components if not c["available"]],
        "explanation": _explain(score, components, available),
    }


def _explain(score, components, available: dict[str, float]) -> str:
    """Deterministic prose describing why the score is what it is."""
    if score is None:
        return (
            "No readiness score yet. Upload a resume, run a skill gap analysis, "
            "complete a mock interview or connect GitHub to start measuring."
        )

    by_key = {c["key"]: c for c in components}
    ranked = sorted(available.items(), key=lambda kv: kv[1])
    weakest_key, weakest_val = ranked[0]
    strongest_key, strongest_val = ranked[-1]

    missing = [by_key[k]["label"] for k in by_key if not by_key[k]["available"]]

    if len(available) == 1:
        only = by_key[strongest_key]["label"]
        parts = [
            f"Your score of {score} comes entirely from {only} ({strongest_val:.0f}), "
            f"the only signal with data so far."
        ]
    else:
        parts = [
            f"Your score of {score} is a weighted blend of "
            f"{len(available)} of {len(COMPONENT_ORDER)} signals. "
            f"{by_key[strongest_key]['label']} is your strongest at "
            f"{strongest_val:.0f}, and {by_key[weakest_key]['label']} is holding "
            f"you back most at {weakest_val:.0f}."
        ]

    if missing:
        parts.append(
            f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} not "
            f"counted yet, so the remaining weights were rebalanced to total 100%."
        )

    return " ".join(parts)


def weakest_component(readiness: dict) -> dict | None:
    """Lowest-scoring component that actually has data. Drives next-best-action."""
    scored = [c for c in readiness["components"] if c["available"]]
    return min(scored, key=lambda c: c["score"]) if scored else None
