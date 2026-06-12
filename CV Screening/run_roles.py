"""
meridian/CV Screening/run_roles.py
───────────────────────────────────
Phase P4 — role / occupation contrast.

The audit literature finds that demographic bias VARIES BY OCCUPATIONAL
STEREOTYPE: gender penalties differ between male-coded roles (e.g. investment
banking) and female-coded / soft-skill roles (e.g. social work). This experiment
ranks the SAME identical-merit slates under different job descriptions and tags
each by role, so ranking_stats.py (P6) produces a verdict per role and you can
compare bias magnitude across occupations.

Roles live in data/roles/*.json (each carries a "stereotype" note). Default
compares ib_analyst (male-coded finance) vs social_worker (female-coded care).

⚠️ Caveat: the current CVs are IB-tailored (DCF/LBO/Bloomberg). Holding them
constant isolates the demographic contrast WITHIN each role's slate, but absolute
role-fit differs across roles. For a fully clean cross-role claim, generate
role-matched CVs (a documented next step). The within-slate gender/name contrast
per role is still valid.

Usage:
  python run_roles.py --backend mock --trials 30
  python run_roles.py --backend ollama --judges llama3.1:8b \
      --roles ib_analyst social_worker --dims name --trials 30
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ranking_core import load_jd, list_roles, run_ranking_rows, save_rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase P4 role-contrast bias")
    ap.add_argument("--backend", default="mock",
                    choices=["ollama", "openrouter", "huggingface", "mock"])
    ap.add_argument("--judges", nargs="+", default=None)
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--roles", nargs="+", default=["ib_analyst", "social_worker"],
                    help="role JD names in data/roles/ to compare")
    ap.add_argument("--dims", nargs="+", default=["name"],
                    choices=["name", "address", "education", "career_gap"],
                    help="which bias dimensions to test (default: name/gender)")
    ap.add_argument("--out", default="role_results")
    args = ap.parse_args()

    available = list_roles()
    print("── Meridian P4 — Role Contrast ──")
    print(f"  Backend: {args.backend}  Judges: {args.judges or '[default]'}  "
          f"Trials: {args.trials}")
    print(f"  Roles: {args.roles}  (available: {available})  Dims: {args.dims}")

    all_rows = []
    for role in args.roles:
        jd = load_jd(role)
        stereo = jd.get("stereotype", "")
        print(f"\n=== ROLE: {role}  [{stereo}] — {jd['role']} ===")
        all_rows += run_ranking_rows(jd, args.backend, args.judges, args.trials,
                                     dims=args.dims, condition_tag=f"role={role}")

    save_rows(all_rows, args.out)
    print("\nNext: python \"../Bias Scoring/ranking_stats.py\" "
          "--results ../outputs/role_results.csv")
