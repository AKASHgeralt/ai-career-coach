from pydantic import BaseModel


class ReadinessComponent(BaseModel):
    key: str
    label: str
    score: float | None
    available: bool
    base_weight: float
    # What this component is worth after renormalising over available data.
    effective_weight: float
    detail: str | None
    # Present only when the component has no data: what the user should do.
    action: str | None


class NextAction(BaseModel):
    action: str
    why: str
    cta_label: str
    # Dashboard section the CTA should open.
    target_section: str
    # "setup" = a signal has no data yet; "improve" = optimise the weakest one.
    priority: str
    based_on: str


class TopMissingSkill(BaseModel):
    skill: str
    count: int


class RoadmapProgressSummary(BaseModel):
    total: int
    completed: int
    percent: float
    has_roadmap: bool


class ReadinessOut(BaseModel):
    # None when no component has data yet — deliberately not 0, which would
    # read as "you scored zero" rather than "nothing measured yet".
    score: float | None
    components: list[ReadinessComponent]
    available_count: int
    total_components: int
    missing: list[str]
    explanation: str
    target_role: str | None
    target_role_label: str | None
    next_action: NextAction
    top_missing_skills: list[TopMissingSkill]
    roadmap_progress: RoadmapProgressSummary
