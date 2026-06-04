"""
meridian/src/model_b_semantic.py
─────────────────────────────────
MODEL B — Semantic embedding screening model.

Simulates a modern embedding-based matcher (Eightfold, HiredScore, Beamery style).
Encodes the CV and JD into dense vectors and scores by cosine similarity.

Uses sentence-transformers `all-MiniLM-L6-v2` (~80 MB, downloaded once from
HuggingFace Hub on first run, then cached locally). After the first run it is
fully local and free — no API calls, no per-query cost.

  pip install sentence-transformers

NOTE: the model download requires internet on first run. If you are offline or
behind a restricted network, pre-download on a connected machine — the cache
lives in ~/.cache/huggingface and can be copied across.

Returns a score in [0, 100].
"""

import re

# Lazy import so the file can be inspected without the dependency installed.
_MODEL = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(model_name)
    return _MODEL


class SemanticScreener:
    """Dense-embedding cosine similarity between CV and JD."""

    def __init__(self, job_description: dict, model_name: str = "all-MiniLM-L6-v2"):
        self.jd = job_description
        self.model_name = model_name
        jd_text = " ".join([
            self.jd.get("description", ""),
            " ".join(self.jd.get("requirements", [])),
        ])
        self.jd_text = self._clean(jd_text)
        self.model = _get_model(model_name)
        self.jd_emb = self.model.encode(self.jd_text, normalize_embeddings=True)

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"[=\-─•|]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def score(self, cv_text: str) -> float:
        cv_emb = self.model.encode(self._clean(cv_text), normalize_embeddings=True)
        # normalized embeddings → dot product == cosine similarity
        sim = float((self.jd_emb * cv_emb).sum())
        # cosine sim is roughly [0.0, 1.0] for related text; scale to [0, 100]
        return round(max(0.0, sim) * 100, 2)

    def score_with_detail(self, cv_text: str) -> dict:
        return {
            "model": "B_semantic_minilm",
            "score": self.score(cv_text),
            "embedding_model": self.model_name,
        }


if __name__ == "__main__":
    import json
    from pathlib import Path

    ROOT = Path(__file__).parent.parent
    with open(ROOT / "data" / "job_description.json") as f:
        jd = json.load(f)

    print("Loading embedding model (first run downloads ~80 MB)...")
    screener = SemanticScreener(jd)

    with open(ROOT / "data" / "cvs" / "pairs" / "name.json") as f:
        cvs = json.load(f)

    print("\nModel B (Semantic MiniLM) — test on name dimension:\n")
    for rec in cvs:
        d = screener.score_with_detail(rec["cv_text"])
        grp = rec["signals"]["name"]["group"]
        print(f"  {grp:25s}  score={d['score']:6.2f}")
