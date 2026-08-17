from datetime import datetime

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    # One of: resume | skills | interview | github | task
    kind: str
    at: datetime
    title: str
    detail: str | None = None
    # Present only for events that recorded a measurable value.
    metric_label: str | None = None
    metric_value: float | None = None


class SeriesPoint(BaseModel):
    at: datetime
    value: float
    label: str | None = None


class TimelineOut(BaseModel):
    events: list[TimelineEvent]
    # Keyed by event kind. Only signals with 2+ points appear — a single
    # measurement is not a trend.
    series: dict[str, list[SeriesPoint]]
