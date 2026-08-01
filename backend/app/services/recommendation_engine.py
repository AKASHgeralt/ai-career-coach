from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_recommendations(missing_skills: list[str], target_role: str) -> dict:
    if not missing_skills:
        return {
            "courses": [],
            "projects": [],
            "books": [],
            "roadmap": []
        }

    skills_str = ", ".join(missing_skills)

    prompt = f"""You are an expert career coach and technical mentor.

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
      "resources": ["resource1", "resource2"]
    }}
  ]
}}

Generate 3 courses, 3 projects, 2 books, and a 6 week roadmap.
Return ONLY the JSON, no markdown, no explanation."""

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=2000,
    )

    response_text = chat_completion.choices[0].message.content.strip()

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {
            "courses": [],
            "projects": [],
            "books": [],
            "roadmap": []
        }