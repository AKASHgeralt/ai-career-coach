from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_question(job_role: str, difficulty: str, previous_questions: list[str] = []) -> str:
    prev = "\n".join(previous_questions) if previous_questions else "None"

    prompt = f"""You are a senior technical interviewer conducting a {difficulty} level interview for a {job_role} position.

Previous questions asked:
{prev}

Generate ONE new interview question that:
- Is different from all previous questions
- Is appropriate for {difficulty} difficulty
- Tests real technical knowledge for a {job_role}
- Is clear and concise

Return ONLY the question, nothing else. No numbering, no explanation."""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()

def evaluate_answer(question: str, answer: str, job_role: str) -> dict:
    prompt = f"""You are a senior technical interviewer evaluating a candidate's answer for a {job_role} position.

Question: {question}

Candidate's Answer: {answer}

Evaluate the answer and respond in this JSON format only, no extra text:
{{
  "score": <integer from 0 to 10>,
  "feedback": "<2-3 sentences of specific, constructive feedback>",
  "strengths": "<what the candidate did well>",
  "improvements": "<what could be better>"
}}

Scoring guide:
0-3: Poor - missing key concepts
4-6: Average - basic understanding shown
7-8: Good - solid understanding with minor gaps
9-10: Excellent - comprehensive and accurate

Return ONLY the JSON."""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        max_tokens=400,
        temperature=0.3,
    )

    response_text = response.choices[0].message.content.strip()

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {
            "score": 5,
            "feedback": "Answer received and noted.",
            "strengths": "Attempt made",
            "improvements": "Be more specific"
        }