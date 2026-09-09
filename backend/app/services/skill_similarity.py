"""Precomputed semantic similarity between skills in the fixed vocabulary.

Generated once, offline, from sentence-transformers `all-MiniLM-L6-v2` — the
same model and thresholds the engine used at runtime. Every pair in SKILLS_DB
scoring at or above PARTIAL_THRESHOLD is listed, so classification is identical
to the previous behaviour.

Why this is a table and not a model: SKILLS_DB is a *closed* vocabulary of ~90
entries. Across all 3,081 possible pairs the model rates exactly 26 as related,
so the entire useful output fits here. Embeddings earn their keep on
open-ended text, not on a list you can enumerate — carrying torch (494MB,
~1GB RAM, ~30s startup) to reproduce this table was a bad trade.

Regenerate with scripts/regenerate_skill_similarity.py if SKILLS_DB changes.
"""

# (skill_a, skill_b) -> cosine similarity. Keys are alphabetically ordered.
SKILL_SIMILARITY: dict[tuple[str, str], float] = {
    ('git', 'github'): 0.759,
    ('github', 'github actions'): 0.741,
    ('deep learning', 'machine learning'): 0.689,
    ('agile', 'scrum'): 0.689,
    ('mysql', 'sql'): 0.687,
    ('css', 'html'): 0.605,
    ('javascript', 'nodejs'): 0.603,
    ('git', 'github actions'): 0.586,
    ('excel', 'matlab'): 0.568,
    ('numpy', 'python'): 0.554,
    ('mysql', 'postgresql'): 0.547,
    ('matplotlib', 'numpy'): 0.544,
    ('html', 'javascript'): 0.54,
    ('deep learning', 'tensorflow'): 0.537,
    ('c#', 'c++'): 0.536,
    ('sql', 'sqlite'): 0.534,
    ('nextjs', 'nodejs'): 0.524,
    ('html', 'php'): 0.522,
    ('keras', 'tensorflow'): 0.519,
    ('computer vision', 'machine learning'): 0.518,
    ('dynamodb', 'mongodb'): 0.517,
    ('matlab', 'matplotlib'): 0.515,
    ('postgresql', 'sql'): 0.509,
    ('c++', 'java'): 0.507,
    ('mysql', 'php'): 0.502,
    ('graphql', 'mysql'): 0.502,
}


def similarity(a: str, b: str) -> float:
    """Cosine similarity between two known skills. 1.0 if identical."""
    if a == b:
        return 1.0
    return SKILL_SIMILARITY.get(tuple(sorted((a, b))), 0.0)
