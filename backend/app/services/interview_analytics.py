"""Aggregates per-answer interview scores into session-level analytics.

On which dimensions exist
-------------------------
Three are graded, because a written answer genuinely evidences them:

  technical        — accuracy and depth of the concepts used
  problem_solving  — the reasoning and approach shown
  communication    — clarity and structure of the explanation

"Confidence" is deliberately **not** graded. It is a delivery trait — tone,
hesitation, pacing — and this interview is typed. Scoring it from text would
mean inferring a quality the medium cannot show, so the platform would be
asserting something it hasn't measured. If voice interviews are added later,
it becomes measurable and can be introduced then.
"""
DIMENSIONS = [
    {
        "key": "technical",
        "label": "Technical knowledge",
        "description": "Accuracy and depth of the concepts used in your answers.",
    },
    {
        "key": "problem_solving",
        "label": "Problem solving",
        "description": "The reasoning and approach you showed, not just the conclusion.",
    },
    {
        "key": "communication",
        "label": "Communication",
        "description": "How clearly and coherently the answer was structured.",
    },
]

DIMENSION_KEYS = tuple(d["key"] for d in DIMENSIONS)

# Practice suggestions keyed to the weakest dimension. Deterministic — the
# recommendation follows from the score, not from another LLM call.
PRACTICE_FOR = {
    "technical": [
        "Re-study the fundamentals behind the questions you scored lowest on",
        "Practise explaining core concepts from memory, without notes",
        "Work through the missing skills in your roadmap before the next session",
    ],
    "problem_solving": [
        "Talk through your approach step by step before giving an answer",
        "Practise system design questions, where reasoning matters more than recall",
        "State your assumptions and trade-offs explicitly",
    ],
    "communication": [
        "Structure answers as situation, approach, result",
        "Lead with a one-sentence summary, then add detail",
        "Practise explaining a past project to a non-specialist",
    ],
}


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def aggregate_dimensions(answers: list) -> list[dict]:
    """Mean score per dimension across every answer that recorded one."""
    result = []
    for dimension in DIMENSIONS:
        key = dimension["key"]
        scores = []
        for a in answers:
            dims = getattr(a, "dimensions", None) or {}
            value = dims.get(key)
            if isinstance(value, (int, float)):
                scores.append(max(0.0, min(10.0, float(value))))
        result.append({
            **dimension,
            "score": _mean(scores),
            "answers_scored": len(scores),
        })
    return result


def _collect(answers: list, field: str, limit: int = 4) -> list[str]:
    """De-duplicated non-empty notes from per-answer feedback, newest first."""
    seen, out = set(), []
    for a in reversed(answers):
        text = (getattr(a, field, None) or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def build_session_analytics(session, answers: list) -> dict:
    """Session-level analytics: dimensions, overall, and what to work on."""
    dimensions = aggregate_dimensions(answers)
    scored = [d for d in dimensions if d["score"] is not None]

    # Overall is the mean of the raw answer scores, not of the dimensions, so
    # it always agrees with the session total the user already saw.
    answer_scores = [a.score for a in answers if a.score is not None]
    overall = _mean([float(s) for s in answer_scores])

    weakest = min(scored, key=lambda d: d["score"]) if scored else None
    strongest = max(scored, key=lambda d: d["score"]) if scored else None

    practice = PRACTICE_FOR.get(weakest["key"], []) if weakest else []

    if not scored:
        summary = (
            "This session was graded before dimension scoring was available, so "
            "only the overall score is shown."
        )
    elif weakest and strongest and weakest["key"] != strongest["key"]:
        summary = (
            f"{strongest['label']} is your strongest area at "
            f"{strongest['score']}/10, and {weakest['label']} is weakest at "
            f"{weakest['score']}/10."
        )
    else:
        summary = f"Scored consistently across all {len(scored)} dimensions."

    return {
        "session_id": session.id,
        "job_role": session.job_role,
        "difficulty": session.difficulty,
        "status": session.status,
        "questions_answered": len(answers),
        "overall": overall,
        "dimensions": dimensions,
        "weakest_dimension": weakest["key"] if weakest else None,
        "strongest_dimension": strongest["key"] if strongest else None,
        "summary": summary,
        "strengths": _collect(answers, "strengths"),
        "weaknesses": _collect(answers, "improvements"),
        "recommended_practice": practice,
    }
