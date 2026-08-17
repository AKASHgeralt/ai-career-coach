from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.services.llm import complete_json

load_dotenv()


class Course(BaseModel):
    title: str
    platform: str = ""
    skill: str = ""
    duration: str = ""
    level: str = ""
    url: str = ""


class Project(BaseModel):
    title: str
    description: str = ""
    skills_covered: list[str] = Field(default_factory=list)
    difficulty: str = ""
    estimated_time: str = ""


class Book(BaseModel):
    title: str
    author: str = ""
    skill: str = ""
    why: str = ""


class RoadmapWeek(BaseModel):
    week: int = 1
    focus: str = ""
    goal: str = ""
    tasks: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class RecommendationBundle(BaseModel):
    """Validated shape of a generated roadmap.

    Only `title` is genuinely required on each item — everything else defaults
    to empty so a slightly sparse but structurally valid response is still
    usable, while a malformed one is rejected.
    """
    courses: list[Course] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    books: list[Book] = Field(default_factory=list)
    roadmap: list[RoadmapWeek] = Field(default_factory=list)


def recommendations_prompt(skills_str: str, target_role: str) -> str:
    return f"""You are an expert career coach and technical mentor.

A candidate wants to become a {target_role} but is missing these skills: {skills_str}

Generate personalized recommendations in the following JSON format only, no extra text:

{{
  "courses": [
    {{
      "title": "course name",
      "platform": "Udemy/Coursera/YouTube/etc",
      "skill": "which skill this covers",
      "duration": "estimated duration",
      "level": "Beginner/Intermediate/Advanced",
      "url": "https://example.com"
    }}
  ],
  "projects": [
    {{
      "title": "project name",
      "description": "what to build in one sentence",
      "skills_covered": ["skill1", "skill2"],
      "difficulty": "Easy/Medium/Hard",
      "estimated_time": "X weeks"
    }}
  ],
  "books": [
    {{
      "title": "book name",
      "author": "author name",
      "skill": "which skill this covers",
      "why": "one sentence reason to read this"
    }}
  ],
  "roadmap": [
    {{
      "week": 1,
      "focus": "skill to focus on",
      "goal": "what to achieve this week",
      "tasks": ["specific actionable task", "another specific task"],
      "resources": ["resource1", "resource2"]
    }}
  ]
}}

Generate 3 courses, 3 projects, 2 books, and a 6 week roadmap.
Each roadmap week must include 3-5 concrete tasks the candidate can tick off.
Tasks must be specific and verifiable ("Build a REST API with FastAPI"), not
vague ("learn backend").
Return ONLY the JSON, no markdown, no explanation."""


def get_recommendations(missing_skills: list[str], target_role: str) -> dict:
    """Generate a learning plan.

    Raises LLMError if the model can't return a valid bundle, rather than
    silently handing back empty lists that look like "nothing to learn".
    """
    if not missing_skills:
        return {"courses": [], "projects": [], "books": [], "roadmap": []}

    bundle = complete_json(
        recommendations_prompt(", ".join(missing_skills), target_role),
        RecommendationBundle,
        temperature=0.7,
        max_tokens=2000,
    )
    return bundle.model_dump()
