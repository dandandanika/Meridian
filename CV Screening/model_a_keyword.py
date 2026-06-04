"""
meridian/src/model_a_keyword.py
────────────────────────────────
MODEL A — Keyword / TF-IDF screening model.

Simulates a traditional ATS keyword matcher (Workday, Greenhouse, Lever style).
Scores a CV by TF-IDF-weighted overlap with the job description keywords.

Fully local. No model downloads, no API calls. Free.

Returns a score in [0, 100].
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re


class KeywordScreener:
    """TF-IDF cosine similarity between CV text and the job description."""

    def __init__(self, job_description: dict):
        self.jd = job_description
        # Build the JD reference text from description + requirements + keywords.
        # Keywords are repeated to weight them more heavily — this mirrors how
        # real ATS systems boost required-skill keywords.
        jd_text = " ".join([
            self.jd.get("description", ""),
            " ".join(self.jd.get("requirements", [])),
            " ".join(self.jd.get("keywords", []) * 3),   # 3x keyword weighting
        ])
        self.jd_text = self._clean(jd_text)

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),     # unigrams + bigrams ("financial modelling")
            lowercase=True,
            max_features=2000,
        )
        # Fit on the JD so the vocabulary is JD-driven (like a real ATS keyword set)
        self.vectorizer.fit([self.jd_text])
        self.jd_vec = self.vectorizer.transform([self.jd_text])

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"[=\-─•|]+", " ", text)     # strip template decoration
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def score(self, cv_text: str) -> float:
        """Return a keyword-match score in [0, 100]."""
        cv_clean = self._clean(cv_text)
        cv_vec = self.vectorizer.transform([cv_clean])
        sim = cosine_similarity(self.jd_vec, cv_vec)[0][0]
        return round(float(sim) * 100, 2)

    def score_with_detail(self, cv_text: str) -> dict:
        """Return score plus which JD keywords were matched (for transparency)."""
        cv_clean = self._clean(cv_text).lower()
        matched = [kw for kw in self.jd.get("keywords", [])
                   if kw.lower() in cv_clean]
        return {
            "model":          "A_keyword_tfidf",
            "score":          self.score(cv_text),
            "matched_kw":     matched,
            "n_matched":      len(matched),
            "n_total_kw":     len(self.jd.get("keywords", [])),
        }


if __name__ == "__main__":
    import json
    from pathlib import Path

    ROOT = Path(__file__).parent.parent
    with open(ROOT / "data" / "job_description.json") as f:
        jd = json.load(f)

    screener = KeywordScreener(jd)

    # Test on a sample CV
    with open(ROOT / "data" / "cvs" / "pairs" / "name.json") as f:
        cvs = json.load(f)

    print("Model A (Keyword TF-IDF) — test on name dimension:\n")
    for rec in cvs:
        detail = screener.score_with_detail(rec["cv_text"])
        grp = rec["signals"]["name"]["group"]
        print(f"  {grp:25s}  score={detail['score']:6.2f}  "
              f"matched {detail['n_matched']}/{detail['n_total_kw']} kw")
