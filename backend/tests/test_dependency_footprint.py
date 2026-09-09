"""Guards the deployment footprint.

The skill engine used sentence-transformers, torch and faiss to compare skills.
Measured against the real vocabulary, that stack changed the result for exactly
one pair out of 3,081 (`git` <-> `github`) — because SKILLS_DB is a *closed*
vocabulary, so everything the model knew could simply be enumerated. It was
replaced by a generated lookup table, cutting installed size from 1,331MB to
152MB and startup from ~23s to ~1.2s.

These tests fail if any of it creeps back in, since re-adding it would quietly
put the project back outside free hosting tiers.
"""
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable

# Importing any of these would restore the ~1.2GB dependency footprint.
BANNED = ["torch", "sentence_transformers", "transformers", "faiss", "spacy",
          "sklearn", "scipy", "numpy"]


def run(code: str) -> str:
    result = subprocess.run(
        [PYTHON, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=300
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return result.stdout.strip()


def test_app_imports_no_heavy_modules():
    out = run(f"import sys, main;print([m for m in {BANNED!r} if m in sys.modules])")
    assert out == "[]", f"heavy dependency reintroduced at import: {out}"


def test_heavy_packages_are_not_installable_dependencies():
    """They must be absent from requirements.txt, not merely unimported."""
    reqs = open(os.path.join(BACKEND, "requirements.txt"), encoding="utf-8").read().lower()
    for pkg in ("torch", "sentence-transformers", "faiss-cpu", "transformers", "spacy"):
        assert pkg not in reqs, f"{pkg} is back in requirements.txt"


def test_skill_matching_works_without_them():
    out = run(
        "import sys;"
        "from app.services.skill_gap_engine import compute_skill_gap;"
        "r = compute_skill_gap(['python','github'], ['python','git','docker']);"
        f"print(r['match_score'], [m for m in {BANNED!r} if m in sys.modules])"
    )
    # github -> git is the one pair the embedding model used to rescue; the
    # lookup table must still make it, with no heavy import.
    assert out == "66.67 []", out


def test_groq_client_is_not_built_at_import():
    out = run("import main;from app.services import llm;print(llm._client is None)")
    assert out == "True"
