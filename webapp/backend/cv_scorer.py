"""
webapp/backend/cv_scorer.py
────────────────────────────
Mode 2 — Test a CV.

Two things for an uploaded CV:
  1. Base scores — keyword (TF-IDF) and the LLM judge, for context.
  2. The flagship counterfactual — take the SAME CV, swap only the candidate's
     name across every demographic name-group, and have the model RANK those
     identical-but-renamed versions against each other. The resulting rank order
     shows which version of *this person's* CV the model prefers — bias made
     personal. (Ranking is the method that actually surfaces bias; see P0.)

Reuses the validated pipeline modules directly (no reimplementation).
"""

import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCREEN_DIR = REPO_ROOT / "CV Screening"
DATA = REPO_ROOT / "data"
sys.path.insert(0, str(SCREEN_DIR))

import json

from model_d_ranking import RankingScreener   # noqa: E402
from bias_signals import NAMES                  # noqa: E402

try:
    from model_a_keyword import KeywordScreener  # needs scikit-learn
except Exception:                                # noqa: BLE001
    KeywordScreener = None
from model_c_llm_judge import LLMJudgeScreener   # noqa: E402


def _jd() -> dict:
    return json.loads((DATA / "job_description.json").read_text())


def base_scores(cv_text: str, backend: str, model: str | None) -> dict:
    jd = _jd()
    out = {"keyword": None, "judge": None}
    if KeywordScreener:
        try:
            out["keyword"] = KeywordScreener(jd).score(cv_text)
        except Exception:  # noqa: BLE001
            pass
    try:
        out["judge"] = LLMJudgeScreener(jd, backend=backend, model=model).score(cv_text)
    except Exception as e:  # noqa: BLE001
        out["judge_error"] = str(e)
    return out


def name_counterfactual(cv_text: str, base_name: str, backend: str,
                        model: str | None, trials: int = 20) -> dict:
    """
    Build a slate = the CV re-named to each demographic name-group, rank it over
    `trials` shuffled passes, and return each version's mean rank + selection rate.
    Also returns the keyword score per variant (should be flat → name-blind).
    """
    jd = _jd()
    variants = []
    for entry in NAMES:
        swapped = _swap_name(cv_text, base_name, entry["value"])
        variants.append({"group": entry["group"], "name": entry["value"],
                         "cv_text": swapped})

    n = len(variants)
    k = max(1, n // 2)
    screener = RankingScreener(jd, backend=backend, model=model)
    rng = random.Random(13)
    ranks = {v["group"]: [] for v in variants}

    for t in range(trials):
        perm = variants[:]
        rng.shuffle(perm)
        slate = [{"local_id": f"c{i}", "group": v["group"], "cv_text": v["cv_text"]}
                 for i, v in enumerate(perm)]
        res = screener.rank_slate(slate, hash((t, base_name)) & 0xFFFFFFFF)
        for item in slate:
            ranks[item["group"]].append(res["ranks"][item["local_id"]])

    kw = KeywordScreener(jd) if KeywordScreener else None
    rows = []
    for v in variants:
        rk = ranks[v["group"]]
        rows.append({
            "group": v["group"],
            "name": v["name"],
            "mean_rank": round(sum(rk) / len(rk), 2),
            "selection_rate": round(sum(1 for r in rk if r <= k) / len(rk), 2),
            "keyword_score": round(kw.score(v["cv_text"]), 2) if kw else None,
        })
    rows.sort(key=lambda r: r["mean_rank"])
    return {"variants": rows, "n": n, "k": k, "trials": trials,
            "chance_rank": (n + 1) / 2}


def _swap_name(text: str, old: str, new: str) -> str:
    """Replace the candidate name (and its UPPERCASE form) throughout the CV."""
    if not old:
        return text
    out = text.replace(old, new).replace(old.upper(), new.upper())
    # also handle first-line-only case where name wasn't matched verbatim
    return out
