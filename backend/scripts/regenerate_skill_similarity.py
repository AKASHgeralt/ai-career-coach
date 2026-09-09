"""Regenerate app/services/skill_similarity.py from the embedding model.

Run this only when SKILLS_DB changes. It needs sentence-transformers and faiss
installed, which the application deliberately no longer depends on:

    pip install sentence-transformers faiss-cpu
    python scripts/regenerate_skill_similarity.py

The runtime uses the generated table, so these packages are a development-only
tool rather than a deployment dependency.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.nlp import SKILLS_DB
from app.services.skill_gap_engine import PARTIAL_THRESHOLD

OUT = os.path.join("app", "services", "skill_similarity.py")


def main() -> None:
    from sentence_transformers import SentenceTransformer
    import faiss

    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = model.encode(SKILLS_DB, convert_to_numpy=True)
    faiss.normalize_L2(emb)
    sim = emb @ emb.T

    pairs = []
    for i, a in enumerate(SKILLS_DB):
        for j, b in enumerate(SKILLS_DB):
            if i >= j:
                continue
            score = float(sim[i][j])
            if score >= PARTIAL_THRESHOLD:
                lo, hi = sorted((a, b))
                pairs.append((lo, hi, round(score, 3)))
    pairs.sort(key=lambda p: -p[2])

    existing = open(OUT, encoding="utf-8").read()
    header = existing.split("SKILL_SIMILARITY")[0]
    footer = existing.split("}\n", 1)[1]

    body = header + "SKILL_SIMILARITY: dict[tuple[str, str], float] = {\n"
    body += "\n".join(f"    ({a!r}, {b!r}): {s}," for a, b, s in pairs)
    body += "\n}\n" + footer

    open(OUT, "w", encoding="utf-8", newline="\n").write(body)
    print(f"wrote {len(pairs)} pairs to {OUT}")


if __name__ == "__main__":
    main()
