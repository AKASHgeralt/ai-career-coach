"""Tests for structured LLM output handling.

The behaviour that matters: a malformed model response must never become
plausible-looking application data. It retries once, then fails loudly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import BaseModel

from app.services import llm
from app.services.llm import LLMError, complete_json, extract_json


class Demo(BaseModel):
    score: int
    label: str


class FakeLLM:
    """Stands in for complete_text, returning canned replies in order."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else "{}"


@pytest.fixture
def fake(monkeypatch):
    def install(*replies):
        f = FakeLLM(*replies)
        monkeypatch.setattr(llm, "complete_text", f)
        return f
    return install


class TestExtractJson:
    def test_plain_json(self):
        assert extract_json('{"a": 1}') == '{"a": 1}'

    def test_json_fence(self):
        assert extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'

    def test_bare_fence(self):
        assert extract_json('```\n{"a": 1}\n```') == '{"a": 1}'

    def test_prose_before_and_after(self):
        assert extract_json('Sure! {"a": 1} Hope that helps.') == '{"a": 1}'

    def test_array_payload(self):
        assert extract_json('Here: [1, 2]') == '[1, 2]'


class TestValidation:
    def test_valid_response_passes_through(self, fake):
        fake('{"score": 8, "label": "good"}')
        result = complete_json("p", Demo)
        assert result.score == 8 and result.label == "good"

    def test_fenced_response_is_accepted(self, fake):
        fake('```json\n{"score": 3, "label": "weak"}\n```')
        assert complete_json("p", Demo).score == 3

    def test_retries_once_then_succeeds(self, fake):
        f = fake("not json at all", '{"score": 5, "label": "ok"}')
        assert complete_json("p", Demo).score == 5
        assert len(f.prompts) == 2

    def test_retry_prompt_names_the_problem(self, fake):
        f = fake("garbage", '{"score": 1, "label": "x"}')
        complete_json("p", Demo)
        assert "was rejected because" in f.prompts[1]
        assert "not valid JSON" in f.prompts[1]

    def test_raises_after_exhausting_retries(self, fake):
        f = fake("garbage", "still garbage")
        with pytest.raises(LLMError) as exc:
            complete_json("p", Demo)
        assert "unusable response" in str(exc.value)
        assert len(f.prompts) == 2

    def test_schema_violation_is_rejected_not_coerced(self, fake):
        """Missing required field must fail, not silently default."""
        fake('{"score": 7}', '{"score": 7}')
        with pytest.raises(LLMError):
            complete_json("p", Demo)

    def test_never_returns_a_fabricated_default(self, fake):
        """The old code turned this exact case into score 5."""
        fake("The candidate did well.", "I cannot produce JSON.")
        with pytest.raises(LLMError):
            complete_json("p", Demo)


class TestAnswerEvaluation:
    def _evaluate(self, monkeypatch, *replies):
        from app.services import interview_engine
        monkeypatch.setattr(llm, "complete_text", FakeLLM(*replies))
        return interview_engine.evaluate_answer("q", "a", "Backend Developer")

    def test_valid_evaluation(self, monkeypatch):
        out = self._evaluate(
            monkeypatch,
            '{"score": 9, "feedback": "Strong.", "strengths": "s", "improvements": "i"}',
        )
        assert out["score"] == 9 and out["feedback"] == "Strong."

    def test_string_score_is_coerced(self, monkeypatch):
        out = self._evaluate(monkeypatch, '{"score": "7", "feedback": "ok"}')
        assert out["score"] == 7

    def test_out_of_range_score_is_rejected(self, monkeypatch):
        with pytest.raises(LLMError):
            self._evaluate(
                monkeypatch,
                '{"score": 50, "feedback": "ok"}',
                '{"score": 50, "feedback": "ok"}',
            )

    def test_unparseable_evaluation_raises_instead_of_scoring_5(self, monkeypatch):
        with pytest.raises(LLMError):
            self._evaluate(monkeypatch, "no json here", "still none")


class TestDimensionsAreOptional:
    """A missing breakdown must not fail an otherwise usable evaluation."""

    def _evaluate(self, monkeypatch, *replies):
        from app.services import interview_engine
        monkeypatch.setattr(llm, "complete_text", FakeLLM(*replies))
        return interview_engine.evaluate_answer("q", "a", "Backend Developer")

    def test_evaluation_without_dimensions_still_succeeds(self, monkeypatch):
        out = self._evaluate(monkeypatch, '{"score": 7, "feedback": "Solid."}')
        assert out["score"] == 7
        assert out["dimensions"] is None

    def test_dimensions_are_parsed_when_present(self, monkeypatch):
        out = self._evaluate(monkeypatch, (
            '{"score": 7, "feedback": "ok", "dimensions": '
            '{"technical": 8, "problem_solving": 6, "communication": "7"}}'
        ))
        assert out["dimensions"] == {
            "technical": 8, "problem_solving": 6, "communication": 7
        }

    def test_out_of_range_dimension_is_rejected(self, monkeypatch):
        bad = ('{"score": 7, "feedback": "ok", "dimensions": '
               '{"technical": 99, "problem_solving": 6, "communication": 7}}')
        with pytest.raises(LLMError):
            self._evaluate(monkeypatch, bad, bad)


class TestTruncationIsReportedHonestly:
    """A reply cut off at the token ceiling is a budget problem, not bad JSON.

    gpt-oss models spend part of the completion budget on a private reasoning
    trace, so a ceiling sized for a non-reasoning model truncates the answer
    mid-string. That surfaced as "response was not valid JSON", which points
    the reader at the model's formatting instead of at the token limit.
    """

    class _Choice:
        def __init__(self, content, finish_reason):
            self.message = type("M", (), {"content": content})()
            self.finish_reason = finish_reason

    def _client_returning(self, monkeypatch, content, finish_reason):
        choice = self._Choice(content, finish_reason)
        response = type("R", (), {"choices": [choice]})()
        create = lambda **kwargs: response
        client = type("C", (), {
            "chat": type("Ch", (), {"completions": type("Co", (), {"create": staticmethod(create)})()})()
        })()
        monkeypatch.setattr(llm, "get_client", lambda: client)

    def test_truncated_reply_names_the_token_limit(self, monkeypatch):
        self._client_returning(monkeypatch, '{"score": 9, "lab', "length")
        with pytest.raises(llm.LLMTruncated) as exc:
            llm.complete_text("p", max_tokens=400)
        assert "cut off" in str(exc.value) and "400" in str(exc.value)

    def test_truncation_is_an_llm_error_for_existing_handlers(self):
        # main.py maps LLMError to a 503; truncation must keep taking that path.
        assert issubclass(llm.LLMTruncated, LLMError)

    def test_empty_content_at_the_ceiling_is_not_called_empty(self, monkeypatch):
        # All budget spent reasoning: content is empty, but the cause is the limit.
        self._client_returning(monkeypatch, "", "length")
        with pytest.raises(llm.LLMTruncated):
            llm.complete_text("p", max_tokens=200)

    def test_retry_raises_the_budget_instead_of_repeating_it(self, monkeypatch):
        budgets = []

        def fake_complete_text(prompt, **kwargs):
            budgets.append(kwargs["max_tokens"])
            if len(budgets) == 1:
                raise llm.LLMTruncated("cut off at 1000")
            return '{"score": 9, "label": "ok"}'

        monkeypatch.setattr(llm, "complete_text", fake_complete_text)
        out = complete_json("p", Demo, max_tokens=1000)
        assert out.score == 9
        assert budgets == [1000, 2000], "retry must get more room, not the same ceiling"
