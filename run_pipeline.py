"""
meridian/run_pipeline.py
─────────────────────────
End-to-end orchestrator for the Meridian AI-hiring bias audit.

Runs the three phases in order:

  Phase A — CV Generation   (CV Generation/generate_cvs.py)
  Phase B — ATS Screening   (CV Screening/run_screening.py)
  Phase C — Bias Scoring    (CV Scoring/bias_scoring.py)

Each phase writes its artefacts to data/ and outputs/, and the next phase reads
them — so the phases are decoupled and can also be run individually.

Usage:
  # Full local dry-run (no network; Model C uses the deterministic mock backend):
  python run_pipeline.py --models A C --backend mock

  # Real run on your own machine (Ollama running llama3.1:8b, plus Model B):
  python run_pipeline.py --models A B C --backend ollama

  # Skip regeneration if data/cvs already exists:
  python run_pipeline.py --skip-generate --models A C --backend mock
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
GEN = ROOT / "CV Generation" / "generate_cvs.py"
SCREEN = ROOT / "CV Screening" / "run_screening.py"
SCORE = ROOT / "Bias Scoring" / "bias_scoring.py"
RANK = ROOT / "CV Screening" / "run_ranking.py"
RANKSTATS = ROOT / "Bias Scoring" / "ranking_stats.py"
HIST = ROOT / "CV Screening" / "run_history.py"
HISTSTATS = ROOT / "Bias Scoring" / "history_stats.py"
ROLES = ROOT / "CV Screening" / "run_roles.py"


def step(title: str, cmd: list, cwd: Path):
    print("\n" + "═" * 70)
    print(f"  {title}")
    print("═" * 70)
    print(f"  $ {' '.join(str(c) for c in cmd)}   (cwd: {cwd.name})")
    result = subprocess.run([sys.executable, *cmd], cwd=str(cwd))
    if result.returncode != 0:
        print(f"\n✗ Step failed: {title} (exit {result.returncode})")
        sys.exit(result.returncode)


def main():
    ap = argparse.ArgumentParser(description="Meridian end-to-end pipeline")
    ap.add_argument("--models", nargs="+", default=["A", "C"],
                    choices=["A", "B", "C"], help="screening models to run")
    ap.add_argument("--backend", default="mock",
                    choices=["ollama", "openrouter", "huggingface", "mock"],
                    help="LLM backend for Model C")
    ap.add_argument("--threshold", type=float, default=70,
                    help="shortlist score threshold for Phase C")
    ap.add_argument("--judges", nargs="+", default=None,
                    help="LLM model name(s) for Model C, e.g. "
                         "llama3.1:8b gemma3:12b qwen2:latest. Each runs as its "
                         "own judge column for side-by-side comparison.")
    ap.add_argument("--ranking", action="store_true",
                    help="run the P0 ranking-audit track (LLM ranks identical-"
                         "merit slates) + P6 significance stats. This is the "
                         "method that actually surfaces bias.")
    ap.add_argument("--trials", type=int, default=30,
                    help="randomized ranking trials per dimension per judge (P0)")
    ap.add_argument("--history", action="store_true",
                    help="run the P3 historical-hire (in-context bias) experiment")
    ap.add_argument("--roles", action="store_true",
                    help="run the P4 role-contrast experiment (IB vs social worker)")
    ap.add_argument("--skip-rating", action="store_true",
                    help="skip the pointwise rating track (Phases B & C)")
    ap.add_argument("--skip-generate", action="store_true",
                    help="reuse existing data/cvs instead of regenerating")
    args = ap.parse_args()

    print("\n████ MERIDIAN — AI hiring bias audit pipeline ████")
    print(f"  Models : {args.models}")
    print(f"  Backend: {args.backend}")
    print(f"  Judges : {args.judges or '[default]'}")
    print(f"  Track  : {'ranking ' if args.ranking else ''}"
          f"{'' if args.skip_rating else 'rating'}".strip() or "none")

    # Phase A — generation
    if args.skip_generate and (ROOT / "data" / "cvs" / "pairs").exists():
        print("\n[Phase A] skipped (--skip-generate, data/cvs/pairs exists)")
    else:
        step("PHASE A — CV Generation", [GEN.name], GEN.parent)

    # Rating track (pointwise) — Phases B & C
    if not args.skip_rating:
        screen_cmd = [SCREEN.name, "--models", *args.models, "--backend", args.backend]
        if args.judges:
            screen_cmd += ["--judges", *args.judges]
        step("PHASE B — ATS Screening (pointwise rating)", screen_cmd, SCREEN.parent)
        step("PHASE C — Bias Scoring",
             [SCORE.name, "--threshold", str(args.threshold)], SCORE.parent)

    # Ranking track (P0 + P6) — the bias-revealing method
    if args.ranking:
        rank_cmd = [RANK.name, "--backend", args.backend, "--trials", str(args.trials)]
        if args.judges:
            rank_cmd += ["--judges", *args.judges]
        step("PHASE P0 — Ranking Audit", rank_cmd, RANK.parent)
        step("PHASE P6 — Ranking Significance", [RANKSTATS.name], RANKSTATS.parent)

    # P3 — historical-hire in-context bias
    if args.history:
        hist_cmd = [HIST.name, "--backend", args.backend, "--trials", str(args.trials)]
        if args.judges:
            hist_cmd += ["--judges", *args.judges]
        step("PHASE P3 — Historical-Hire Bias", hist_cmd, HIST.parent)
        step("PHASE P3 — History Significance", [HISTSTATS.name], HISTSTATS.parent)

    # P4 — role / occupation contrast
    if args.roles:
        roles_cmd = [ROLES.name, "--backend", args.backend, "--trials", str(args.trials)]
        if args.judges:
            roles_cmd += ["--judges", *args.judges]
        step("PHASE P4 — Role Contrast", roles_cmd, ROLES.parent)
        step("PHASE P4 — Role Significance",
             [RANKSTATS.name, "--results", "../outputs/role_results.csv"],
             RANKSTATS.parent)

    print("\n" + "═" * 70)
    print("  ✓ Pipeline complete. Key artefacts in outputs/:")
    if not args.skip_rating:
        print("      screening_results.csv / bias_report.md   (rating track)")
    if args.ranking:
        print("      ranking_results.csv                      (P0)")
        print("      ranking_bias_report.md                   (P6 — verdicts + significance)")
    if args.history:
        print("      history_bias_report.md                   (P3 — in-context favouritism)")
    if args.roles:
        print("      role_results.csv + ranking_bias_report.md (P4 — per-role verdicts)")
    print("═" * 70)


if __name__ == "__main__":
    main()
