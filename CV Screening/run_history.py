"""
meridian/CV Screening/run_history.py
─────────────────────────────────────
Phase P3 — historical-hiring / in-context bias.

Mechanism under test: a firm's past hires are demographically skewed, and an LLM
shown those "successful hires" as in-context examples may transfer the skew onto
new candidates — even when every new candidate has identical merit. This is a
distinct channel from the model's baseline prior (P0): bias injected by the
hiring *history* itself.

Design: hold the slate fixed (the name dimension — 10 identical-merit CVs) and
vary only the HISTORY CONDITION:
    none                      (control — no past hires shown)
    hist=white_male           (past hires all white male)
    hist=arab_muslim_female   (past hires all arab/muslim female)
    ... any group you pass via --history-groups
Each condition is ranked over many shuffled trials, exactly like P0, and tagged
into the model label so ranking_stats.py (P6) gives each its own verdict.

The key read-out (run history_stats.py afterwards): does seeding the history with
group X lift X's own ranking vs the no-history control? That "representational
favouritism" is the in-context bias effect.

Usage:
  python run_history.py --backend mock --trials 40
  python run_history.py --backend ollama --judges llama3.1:8b \
      --history-groups white_male arab_muslim_female --trials 30
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ranking_core import load_jd, history_block_cvs, run_ranking_rows, save_rows

DEFAULT_HISTORY = ["white_male", "arab_muslim_female"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase P3 historical-hire bias")
    ap.add_argument("--backend", default="mock",
                    choices=["ollama", "openrouter", "huggingface", "mock"])
    ap.add_argument("--judges", nargs="+", default=None)
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--history-groups", nargs="+", default=DEFAULT_HISTORY,
                    help="name-groups to seed the 'past hires' block with; "
                         "a 'none' control is always included")
    ap.add_argument("--history-n", type=int, default=3,
                    help="number of past-hire exemplars in the prompt")
    ap.add_argument("--role", default=None)
    ap.add_argument("--out", default="history_results")
    args = ap.parse_args()

    print("── Meridian P3 — Historical-Hire Bias ──")
    print(f"  Backend: {args.backend}  Judges: {args.judges or '[default]'}  "
          f"Trials: {args.trials}")
    print(f"  History conditions: none + {args.history_groups}")

    jd = load_jd(args.role)
    all_rows = []

    # control: no history
    all_rows += run_ranking_rows(jd, args.backend, args.judges, args.trials,
                                 dims=["name"], condition_tag="hist=none")

    # one block of past-hires per chosen group
    for grp in args.history_groups:
        hist = history_block_cvs(grp, n=args.history_n)
        if not hist:
            print(f"  ! skipping {grp}: no exemplar CV found")
            continue
        all_rows += run_ranking_rows(
            jd, args.backend, args.judges, args.trials, dims=["name"],
            history_cvs=hist, history_group=grp, condition_tag=f"hist={grp}")

    save_rows(all_rows, args.out)
    print("\nNext: python \"../Bias Scoring/history_stats.py\"")
