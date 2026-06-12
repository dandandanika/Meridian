"""
meridian/CV Screening/ranking_core.py
───────────────────────────────────────
Shared engine for every ranking-based experiment so they stay consistent and
all emit the SAME P6-compatible row schema (one row per CV per trial). Used by:

  run_ranking.py   — baseline P0 ranking audit
  run_history.py   — P3 historical-hire few-shot (seed prompt with past hires)
  run_roles.py     — P4 role contrast (rank the same slates under different JDs)

Each experiment encodes its condition into the `model` label (e.g.
"D:llama3.1:8b|hist=white_male" or "D:llama3.1:8b|role=social_worker"), so the
existing ranking_stats.py treats every condition as its own row and produces a
verdict + significance for it with no changes.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

DIM_SIGNAL = {"name": "name", "address": "address",
              "education": "education", "career_gap": "career_gap"}


def load_jd(role: Optional[str] = None) -> dict:
    """
    role=None -> data/job_description.json (default IB analyst).
    role="x"  -> data/roles/x.json (falls back to default if missing).
    """
    if role:
        p = DATA / "roles" / f"{role}.json"
        if p.exists():
            return json.load(open(p))
    return json.load(open(DATA / "job_description.json"))


def list_roles() -> List[str]:
    rdir = DATA / "roles"
    return sorted(p.stem for p in rdir.glob("*.json")) if rdir.exists() else []


def load_dimension_cvs(dim: str) -> List[Dict]:
    """Variant CV records for one dimension, tagged with that dimension's group."""
    records = json.load(open(DATA / "cvs" / "pairs" / f"{dim}.json"))
    return [{"cv_uid": r["id"],
             "group": r["signals"][DIM_SIGNAL[dim]]["group"],
             "cv_text": r["cv_text"]} for r in records]


def history_block_cvs(group: str, n: int = 3) -> List[str]:
    """
    Build N 'past successful hire' CV texts that all belong to one name-group,
    holding merit constant (same identical-merit CVs used everywhere). Returns
    the CV text repeated/sampled from that group's record in the name slate.
    """
    cvs = load_dimension_cvs("name")
    match = [c["cv_text"] for c in cvs if c["group"] == group]
    if not match:
        return []
    # all merit-identical; repeat the single group exemplar n times
    return (match * n)[:n]


def run_ranking_rows(jd: dict, backend: str, judges: Optional[List[str]],
                     trials: int, dims: Optional[List[str]] = None,
                     history_cvs: Optional[List[str]] = None,
                     history_group: Optional[str] = None,
                     tuning: Optional[dict] = None,
                     condition_tag: str = "", seed: int = 7) -> List[Dict]:
    """
    Run the ranking audit and return P6-compatible rows.
    condition_tag (e.g. "hist=white_male" / "role=social_worker") is appended to
    the model label so ranking_stats treats it as a distinct row.
    """
    from model_d_ranking import RankingScreener
    dims = dims or list(DIM_SIGNAL)
    judge_list = judges if judges else [None]
    rows = []

    for j in judge_list:
        screener = RankingScreener(jd, backend=backend, model=j,
                                   history_cvs=history_cvs,
                                   history_group=history_group,
                                   tuning=tuning)
        base = "D" if j is None else f"D:{j}"
        mkey = base + (f"|{condition_tag}" if condition_tag else "")
        mfull = screener.label + (f"|{condition_tag}" if condition_tag else "")
        print(f"\n[{mkey}] backend={backend}")

        for dim in dims:
            cvs = load_dimension_cvs(dim)
            n = len(cvs)
            k = max(1, n // 2)
            rng = random.Random(f"{seed}-{mkey}-{dim}")
            print(f"  {dim}: slate {n}, top-k {k}, {trials} trials")
            for t in range(trials):
                perm = cvs[:]
                rng.shuffle(perm)
                slate_meta = [{"local_id": f"c{i}", "group": c["group"],
                               "cv_text": c["cv_text"], "cv_uid": c["cv_uid"]}
                              for i, c in enumerate(perm)]
                trial_seed = hash((mkey, dim, t)) & 0xFFFFFFFF
                res = screener.rank_slate(slate_meta, trial_seed)
                for pos, item in enumerate(slate_meta):
                    rank = res["ranks"][item["local_id"]]
                    rows.append({
                        "dimension": dim, "model": mkey, "model_full": mfull,
                        "trial": t, "group": item["group"],
                        "cv_uid": item["cv_uid"], "presented_pos": pos,
                        "rank": rank, "slate_n": n, "k": k,
                        "top_k_selected": int(rank <= k),
                        "parse_ok": int(res["ok"]),
                    })
        ts = screener.token_summary()
        if ts:
            print(f"  {mkey} tokens: {ts}")
    return rows


FIELDS = ["dimension", "model", "model_full", "trial", "group", "cv_uid",
          "presented_pos", "rank", "slate_n", "k", "top_k_selected", "parse_ok"]


def save_rows(rows: List[Dict], stem: str):
    import csv
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    with open(out / f"{stem}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    json.dump(rows, open(out / f"{stem}.json", "w"), indent=2)
    print(f"\n✓ Wrote {len(rows)} rows → outputs/{stem}.csv / .json")
