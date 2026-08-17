"""Guards the startup-performance work.

Importing the app used to pull in spaCy, torch and sentence-transformers,
costing ~23s before the first request could be served. These tests fail if a
future change reintroduces an eager load at import time.

They run in a subprocess so the assertions see a clean module table rather than
whatever the rest of the suite has already imported.
"""
import os
import subprocess
import sys

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable

# Anything here at import time makes startup slow.
HEAVY_MODULES = ["torch", "sentence_transformers", "spacy", "transformers", "faiss"]


def run(code: str) -> str:
    result = subprocess.run(
        [PYTHON, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return result.stdout.strip()


def test_importing_the_app_loads_no_heavy_modules():
    out = run(
        "import sys, main;"
        f"print([m for m in {HEAVY_MODULES!r} if m in sys.modules])"
    )
    assert out == "[]", f"eagerly imported at startup: {out}"


def test_embedding_model_is_not_instantiated_at_import():
    out = run(
        "import main;"
        "from app.services import skill_gap_engine as s;"
        "print(s._model is None)"
    )
    assert out == "True"


@pytest.mark.slow
def test_model_is_cached_after_first_load():
    """Loaded once and reused — never rebuilt per request.

    Marked slow: this is the one test that actually pays the model load.
    Skip it with `pytest -m "not slow"`.
    """
    out = run(
        "from app.services import skill_gap_engine as s;"
        "a = s.get_model(); b = s.get_model();"
        "print(a is b and s._model is a)"
    )
    assert out == "True"


def test_skill_matching_works_without_touching_the_model():
    """Exact matches must not trigger a 20s model load."""
    out = run(
        "import sys;"
        "from app.services.skill_gap_engine import compute_skill_gap;"
        "r = compute_skill_gap(['python','docker'], ['python','docker']);"
        "print(r['match_score'], 'sentence_transformers' in sys.modules)"
    )
    assert out == "100.0 False"


def test_groq_client_is_not_built_at_import():
    """The client now lives in app.services.llm and is built on first call."""
    out = run(
        "import main;"
        "from app.services import llm;"
        "print(llm._client is None)"
    )
    assert out == "True"
