"""Structured LLM calls with validation, one retry, and explicit failure.

The previous behaviour was to swallow a malformed response and substitute a
default — an unparseable evaluation silently became "score 5". That turns a
model failure into misleading application data the user can't distinguish from
a real result. This module instead validates against a Pydantic model, retries
once, and raises LLMError if the response still doesn't conform, so the caller
can return an honest error.
"""
import json
import logging
import os
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"

T = TypeVar("T", bound=BaseModel)

_client = None


class LLMError(RuntimeError):
    """The model could not produce a usable, schema-valid response."""


def get_client():
    """Build the Groq client on first use; a missing key fails here with context."""
    global _client
    if _client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise LLMError("GROQ_API_KEY is not configured on the server")
        _client = Groq(api_key=api_key)
    return _client


def extract_json(text: str) -> str:
    """Pull the JSON payload out of a response that may be fenced or prefixed."""
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]

    cleaned = cleaned.strip()

    # Models sometimes prepend prose. Fall back to the outermost JSON object.
    if not cleaned.startswith(("{", "[")):
        start = min(
            (i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1),
            default=-1,
        )
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if start != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    return cleaned.strip()


def complete_text(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> str:
    """Plain text completion. Raises LLMError rather than leaking client errors."""
    try:
        response = get_client().chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except LLMError:
        raise
    except Exception as exc:
        logger.warning("LLM text call failed: %s", exc)
        raise LLMError("The AI service is unavailable right now") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise LLMError("The AI service returned an empty response")
    return content


def complete_json(
    prompt: str,
    schema: type[T],
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    retries: int = 1,
) -> T:
    """Call the model and validate its JSON against `schema`.

    Retries once on a parse or validation failure, nudging the model with the
    specific problem. Raises LLMError if it still can't comply — never returns
    a fabricated default.
    """
    attempt_prompt = prompt
    last_error = "unknown error"

    for attempt in range(retries + 1):
        raw = complete_text(
            attempt_prompt, model=model, temperature=temperature, max_tokens=max_tokens
        )

        try:
            payload = json.loads(extract_json(raw))
        except json.JSONDecodeError as exc:
            last_error = f"response was not valid JSON ({exc.msg})"
        else:
            try:
                return schema.model_validate(payload)
            except ValidationError as exc:
                first = exc.errors()[0]
                field = ".".join(str(p) for p in first.get("loc", ())) or "response"
                last_error = f"field '{field}' {first.get('msg', 'was invalid')}"

        logger.warning(
            "LLM JSON validation failed (attempt %d/%d): %s",
            attempt + 1, retries + 1, last_error,
        )

        if attempt < retries:
            attempt_prompt = (
                f"{prompt}\n\n"
                f"Your previous reply was rejected because {last_error}. "
                f"Reply with valid JSON matching the requested shape exactly. "
                f"No markdown, no commentary."
            )

    raise LLMError(
        f"The AI service returned an unusable response ({last_error}). Please try again."
    )
