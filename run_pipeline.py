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
    ap.add_argument("--skip-generate", action="store_true",
                    help="reuse existing data/cvs instead of regenerating")
    args = ap.parse_args()

    print("\n████ MERIDIAN — AI hiring bias audit pipeline ████")
    print(f"  Models : {args.models}")
    print(f"  Backend: {args.backend}")
    print(f"  Judges : {args.judges or '[default]'}")

    # Phase A — generation
    if args.skip_generate and (ROOT / "data" / "cvs" / "pairs").exists():
        print("\n[Phase A] skipped (--skip-generate, data/cvs/pairs exists)")
    else:
        step("PHASE A — CV Generation", [GEN.name], GEN.parent)

    # Phase B — screening
    screen_cmd = [SCREEN.name, "--models", *args.models, "--backend", args.backend]
    if args.judges:
        screen_cmd += ["--judges", *args.judges]
    step("PHASE B — ATS Screening", screen_cmd, SCREEN.parent)

    # Phase C — bias scoring
    step("PHASE C — Bias Scoring",
         [SCORE.name, "--threshold", str(args.threshold)],
         SCORE.parent)

    print("\n" + "═" * 70)
    print("  ✓ Pipeline complete. Key artefacts in outputs/:")
    print("      screening_results.csv / .json   (Phase B)")
    print("      bias_scores.csv / .json          (Phase C)")
    print("      bias_report.md                   (Phase C, human-readable)")
    print("═" * 70)


if __name__ == "__main__":
    main()
