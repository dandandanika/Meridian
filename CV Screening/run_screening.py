"""
meridian/src/run_screening.py
──────────────────────────────
Unified runner. Loads the CV pairs + JD, scores every CV across the selected
screening models, and writes a tidy results table (the input for Phase C bias
scoring).

Models:
  A — keyword TF-IDF        (always on; fully local, free)
  B — semantic embeddings   (on if sentence-transformers installed)
  C — LLM-as-judge          (backend: ollama | openrouter | huggingface | mock)

Usage:
  # Local dry-run with mock LLM (no network needed):
  python src/run_screening.py --models A C --backend mock

  # Real run on your machine:
  python src/run_screening.py --models A B C --backend ollama
  python src/run_screening.py --models A B C --backend openrouter

Output:
  outputs/screening_results.csv   (one row per CV per model)
  outputs/screening_results.json
"""

import argparse
import json
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

import sys
sys.path.insert(0, str(Path(__file__).parent))


def load_jd() -> dict:
    with open(DATA / "job_description.json") as f:
        return json.load(f)


def load_all_cvs() -> list:
    """Load every paired CV across all four dimensions, tagged with dimension."""
    cvs = []
    pairs_dir = DATA / "cvs" / "pairs"
    for dim_file in sorted(pairs_dir.glob("*.json")):
        with open(dim_file) as f:
            records = json.load(f)
        cvs.extend(records)
    return cvs


def build_screeners(models: list, backend: str, jd: dict,
                    judges: list = None) -> dict:
    screeners = {}

    if "A" in models:
        from model_a_keyword import KeywordScreener
        screeners["A"] = KeywordScreener(jd)
        print("  [A] keyword TF-IDF       ready")

    if "B" in models:
        try:
            from model_b_semantic import SemanticScreener
            screeners["B"] = SemanticScreener(jd)
            print("  [B] semantic embeddings  ready")
        except Exception as e:
            print(f"  [B] SKIPPED — {type(e).__name__}: {e}")
            print("      (install sentence-transformers, needs one-time model download)")

    if "C" in models:
        # One judge per entry in `judges`; each becomes its own model column
        # ("C:<name>") so the bias report compares judges side by side.
        # judges=None / [None] -> single judge using the backend's default model.
        judge_list = judges if judges else [None]
        from model_c_llm_judge import LLMJudgeScreener
        for j in judge_list:
            key = "C" if j is None else f"C:{j}"
            try:
                screeners[key] = LLMJudgeScreener(jd, backend=backend, model=j)
                print(f"  [{key}] LLM judge ({backend}, model={j or 'default'})  ready")
            except Exception as e:
                print(f"  [{key}] SKIPPED — {type(e).__name__}: {e}")

    return screeners


def run(models: list, backend: str, judges: list = None) -> list:
    jd = load_jd()
    cvs = load_all_cvs()
    print(f"\nLoaded {len(cvs)} CVs, JD: {jd['role']}")
    print("Initialising screeners:")
    screeners = build_screeners(models, backend, jd, judges)

    rows = []
    print(f"\nScoring {len(cvs)} CVs across {len(screeners)} model(s)...")
    for i, rec in enumerate(cvs):
        sig = rec["signals"]
        for mkey, screener in screeners.items():
            detail = screener.score_with_detail(rec["cv_text"])
            rows.append({
                "cv_id":         rec["id"],
                "swapped_dim":   rec["swapped_dim"],
                "model":         mkey,
                "model_full":    detail["model"],
                "score":         detail["score"],
                "name_group":    sig["name"]["group"],
                "address_group": sig["address"]["group"],
                "edu_group":     sig["education"]["group"],
                "gap_group":     sig["career_gap"]["group"],
                "reasoning":     detail.get("reasoning", ""),
            })
        if (i + 1) % 5 == 0:
            print(f"  ...{i + 1}/{len(cvs)} CVs done")

    # Token summary for each Model C judge
    for key, screener in screeners.items():
        if key == "C" or key.startswith("C:"):
            ts = screener.token_summary()
            if ts:
                print(f"\n  {key} token usage: {ts}")

    return rows


def save(rows: list):
    # CSV
    csv_path = OUT / "screening_results.csv"
    fields = ["cv_id", "swapped_dim", "model", "model_full", "score",
              "name_group", "address_group", "edu_group", "gap_group", "reasoning"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # JSON
    json_path = OUT / "screening_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Wrote {len(rows)} rows:")
    print(f"    {csv_path}")
    print(f"    {json_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["A"],
                    choices=["A", "B", "C"],
                    help="which models to run")
    ap.add_argument("--backend", default="mock",
                    choices=["ollama", "openrouter", "huggingface", "mock"],
                    help="LLM backend for Model C")
    ap.add_argument("--judges", nargs="+", default=None,
                    help="one or more LLM model names for Model C (e.g. "
                         "llama3.1:8b gemma3:12b qwen2:latest). Each runs as its "
                         "own judge column so the bias report compares them. "
                         "Omit for the backend's default model.")
    args = ap.parse_args()

    print("── Meridian Screening Runner ──")
    print(f"  Models : {args.models}")
    print(f"  Backend: {args.backend}")
    print(f"  Judges : {args.judges or '[default]'}")

    rows = run(args.models, args.backend, args.judges)
    save(rows)

    # Quick preview
    print("\nPreview (first 12 rows):")
    print(f"  {'cv_id':40s} {'model':6s} {'score':>6s}")
    for r in rows[:12]:
        print(f"  {r['cv_id'][:38]:40s} {r['model']:6s} {str(r['score']):>6s}")
