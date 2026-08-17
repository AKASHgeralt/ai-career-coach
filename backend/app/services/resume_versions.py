"""Resume version comparison.

Compares two versions of a user's resume: which skills were gained or dropped,
how each ATS category moved, and what the target role still requires. All of it
is derived from data already extracted from the two documents — nothing is
inferred about intent or quality beyond what the analyser measured.
"""
from app.services.nlp import ATS_MAX, calculate_ats_breakdown, extract_skills


def next_version_for(existing_versions: list[int]) -> int:
    """Next sequential version number for a user's resumes."""
    return (max(existing_versions) + 1) if existing_versions else 1


def _delta_label(delta: float) -> str:
    if delta > 0:
        return "improved"
    if delta < 0:
        return "declined"
    return "unchanged"


def compare_resumes(base, target, role_skills: list[str] | None = None) -> dict:
    """Compare two resume rows, oldest as `base`.

    `role_skills` is the target role's baseline, used to report what is still
    missing after the newer version.
    """
    base_skills = set(extract_skills(base.parsed_text or ""))
    target_skills = set(extract_skills(target.parsed_text or ""))

    base_breakdown = calculate_ats_breakdown(base.parsed_text or "", sorted(base_skills))
    target_breakdown = calculate_ats_breakdown(target.parsed_text or "", sorted(target_skills))

    base_by_key = {c["key"]: c for c in base_breakdown["components"]}

    categories = []
    for component in target_breakdown["components"]:
        key = component["key"]
        before = base_by_key.get(key, {}).get("earned", 0)
        after = component["earned"]
        categories.append({
            "key": key,
            "label": component["label"],
            "before": before,
            "after": after,
            "delta": after - before,
            "max": ATS_MAX[key],
            "status": _delta_label(after - before),
            # Only surfaced when the newer version still isn't maxed out.
            "suggestion": component["suggestion"],
        })

    gained = sorted(target_skills - base_skills)
    lost = sorted(base_skills - target_skills)
    kept = sorted(base_skills & target_skills)

    still_missing = []
    if role_skills:
        still_missing = sorted(set(role_skills) - target_skills)

    ats_delta = target_breakdown["total"] - base_breakdown["total"]

    return {
        "base": {
            "id": base.id, "version": base.version, "file_name": base.file_name,
            "ats_score": base_breakdown["total"], "uploaded_at": base.uploaded_at,
            "skill_count": len(base_skills),
        },
        "target": {
            "id": target.id, "version": target.version, "file_name": target.file_name,
            "ats_score": target_breakdown["total"], "uploaded_at": target.uploaded_at,
            "skill_count": len(target_skills),
        },
        "ats_delta": ats_delta,
        "ats_status": _delta_label(ats_delta),
        "skills_gained": gained,
        "skills_lost": lost,
        "skills_kept": kept,
        "still_missing": still_missing,
        "categories": categories,
        "summary": _summarise(ats_delta, gained, lost, still_missing),
    }


def _summarise(ats_delta, gained, lost, still_missing) -> str:
    """Plain-language description of what changed between the two versions."""
    parts = []

    if ats_delta > 0:
        parts.append(f"ATS score rose {ats_delta} points.")
    elif ats_delta < 0:
        parts.append(f"ATS score fell {abs(ats_delta)} points.")
    else:
        parts.append("ATS score is unchanged.")

    if gained:
        shown = ", ".join(gained[:4])
        more = f" and {len(gained) - 4} more" if len(gained) > 4 else ""
        parts.append(f"Added {shown}{more}.")

    if lost:
        shown = ", ".join(lost[:3])
        parts.append(
            f"No longer detected: {shown}"
            f"{f' and {len(lost) - 3} more' if len(lost) > 3 else ''}. "
            "Check these weren't removed by accident."
        )

    if still_missing:
        parts.append(
            f"{len(still_missing)} skill{'s' if len(still_missing) != 1 else ''} "
            "your target role expects are still absent."
        )

    return " ".join(parts)


def build_version_history(resumes: list) -> dict:
    """Version list plus an ATS series, for the improvement chart."""
    ordered = sorted(resumes, key=lambda r: (r.version, r.uploaded_at))
    versions = [
        {
            "id": r.id,
            "version": r.version,
            "file_name": r.file_name,
            "ats_score": r.ats_score,
            "uploaded_at": r.uploaded_at,
        }
        for r in ordered
    ]

    first, last = (ordered[0], ordered[-1]) if ordered else (None, None)
    return {
        "versions": versions,
        "count": len(versions),
        # A single version is a data point, not a trend.
        "improvement": (
            (last.ats_score - first.ats_score) if len(ordered) >= 2 else None
        ),
        "latest_version": last.version if last else None,
    }
