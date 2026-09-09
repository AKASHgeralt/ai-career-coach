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

# Configurable because model availability changes: llama-3.3-70b-versatile was
# hardcoded here and later became unavailable on this account, which broke every
# AI feature with a 404. Override with GROQ_MODEL without touching code.
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# gpt-oss models are *reasoning* models: they emit a private reasoning trace that
# is billed against the same completion budget as the answer. Measured on the
# roadmap prompt, that trace ran 600-1000 tokens at the default effort and pushed
# the JSON past max_tokens, so two runs in three arrived truncated. "low" cuts it
# to ~10-40 tokens and roadmap latency from ~18s to ~4s, with identical grades on
# the evaluation prompt (strong answer 8, weak answer 2 at both settings).
# Set to "none" to omit the parameter for a model that doesn't accept it.
REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "low")

T = TypeVar("T", bound=BaseModel)

_client = None
# Flipped off if the configured model rejects reasoning_effort, since GROQ_MODEL
# can point at a non-reasoning model.
_send_reasoning_effort = REASONING_EFFORT not in ("", "none")


class LLMError(RuntimeError):
    """The model could not produce a usable, schema-valid response."""


class LLMTruncated(LLMError):
    """The model hit the token ceiling mid-answer.

    Distinct from a malformed reply: the text was well-formed, it just stopped.
    Re-prompting at the same ceiling cannot fix it, so complete_json raises the
    budget instead of just asking again.
    """


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
    global _send_reasoning_effort

    def _call(with_effort: bool):
        extra = {"reasoning_effort": REASONING_EFFORT} if with_effort else {}
        return get_client().chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )

    try:
        try:
            response = _call(_send_reasoning_effort)
        except Exception as exc:
            # A non-reasoning model rejects the parameter outright. Fall back once
            # and stop sending it, rather than failing every later call too.
            if not _send_reasoning_effort or "reasoning_effort" not in str(exc):
                raise
            logger.info("Model %s rejected reasoning_effort; disabling it", model)
            _send_reasoning_effort = False
            response = _call(False)
    except LLMError:
        raise
    except Exception as exc:
        logger.warning("LLM text call failed: %s", exc)
        raise LLMError("The AI service is unavailable right now") from exc

    choice = response.choices[0]
    content = (choice.message.content or "").strip()

    # Checked before the empty test: a reasoning model that spends its whole
    # budget thinking returns empty content with finish_reason "length", and
    # "returned an empty response" would send the caller looking in the wrong
    # place. Truncation is a budget problem, and it says so.
    if choice.finish_reason == "length":
        raise LLMTruncated(
            f"The AI service's reply was cut off at the {max_tokens}-token limit"
        )
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
    budget = max_tokens

    for attempt in range(retries + 1):
        try:
            raw = complete_text(
                attempt_prompt, model=model, temperature=temperature, max_tokens=budget
            )
        except LLMTruncated as exc:
            # Asking again at the same ceiling would truncate again. Give the
            # retry room to finish instead of spending it on an identical failure.
            last_error = str(exc)
            logger.warning(
                "LLM response truncated at %d tokens (attempt %d/%d)",
                budget, attempt + 1, retries + 1,
            )
            budget *= 2
            continue

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
