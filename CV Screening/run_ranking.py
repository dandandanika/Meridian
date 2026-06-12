"""
meridian/CV Screening/run_ranking.py
─────────────────────────────────────
Phase P0 orchestrator — baseline LLM RANKING audit.

For each bias dimension we build a SLATE of identical-merit CVs that differ only
on that dimension (one CV per variant), then ask each judge to rank the whole
slate, repeated over many trials with the presentation order SHUFFLED each time
to cancel position bias.

Output: outputs/ranking_results.csv / .json — input to ranking_stats.py (P6).

Usage:
  python run_ranking.py --backend mock --trials 30
  python run_ranking.py --backend ollama --judges llama3.1:8b gemma3:12b --trials 20
  python run_ranking.py --backend ollama --role social_worker   # P4 single role
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ranking_core import load_jd, run_ranking_rows, save_rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase P0 LLM ranking audit")
    ap.add_argument("--backend", default="mock",
                    choices=["ollama", "openrouter", "groq", "huggingface", "mock"])
    ap.add_argument("--judges", nargs="+", default=None,
                    help="LLM model name(s); each ranks independently")
    ap.add_argument("--trials", type=int, default=30,
                    help="randomized ranking trials per dimension per judge")
    ap.add_argument("--role", default=None,
                    help="job role to screen for (data/roles/<role>.json); "
                         "default = the IB analyst JD")
    # prompt "fine-tuning" knobs (optional)
    ap.add_argument("--fairness", action="store_true",
                    help="add an explicit fairness instruction to the prompt")
    ap.add_argument("--guardrails", default=None,
                    help="hard rule(s) appended to the prompt")
    ap.add_argument("--system-prompt", dest="system_prompt", default=None,
                    help="override the recruiter persona")
    ap.add_argument("--out", default="ranking_results",
                    help="output filename stem in outputs/")
    args = ap.parse_args()

    tuning = {}
    if args.fairness:
        tuning["fairness"] = True
    if args.guardrails:
        tuning["guardrails"] = args.guardrails
    if args.system_prompt:
        tuning["system_prompt"] = args.system_prompt

    print("── Meridian P0 — Ranking Audit ──")
    print(f"  Backend: {args.backend}  Judges: {args.judges or '[default]'}  "
          f"Trials: {args.trials}  Role: {args.role or 'ib_analyst(default)'}"
          f"{'  Tuning: ' + ','.join(tuning) if tuning else ''}")

    jd = load_jd(args.role)
    tag = f"role={args.role}" if args.role else ""
    rows = run_ranking_rows(jd, args.backend, args.judges, args.trials,
                            tuning=tuning or None, condition_tag=tag)
    save_rows(rows, args.out)
