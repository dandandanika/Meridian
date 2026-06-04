"""
meridian/src/sanity_check.py
─────────────────────────────
Loads generated CV pairs and runs automated + visual sanity checks.

Checks performed:
  1. Pair completeness  – expected number of variants per dimension
  2. Merit invariance   – merit fields are identical across all CVs in a pair
  3. Signal presence    – the swapped signal value appears in the CV text
  4. Isolation check    – non-swapped signals are identical to baseline in all pairs
  5. Token report       – prints estimated token count per CV

Run AFTER generate_cvs.py:
  python src/sanity_check.py
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "cvs"
PAIRS_DIR = DATA_DIR / "pairs"

sys.path.insert(0, str(Path(__file__).parent))
from bias_signals import NAMES, ADDRESSES, EDUCATION, CAREER_GAPS
from cv_template  import MERIT


# ── Expected counts ───────────────────────────────────────────
EXPECTED_COUNTS = {
    "name":       len(NAMES),
    "address":    len(ADDRESSES),
    "education":  len(EDUCATION),
    "career_gap": len(CAREER_GAPS),
}

# ── Merit strings that must appear in EVERY CV ────────────────
MERIT_ANCHORS = [
    MERIT["internship_title"],
    MERIT["internship_company"],
    "2:1",
    "Python",
    "Bloomberg Terminal",
]

# ── Baseline groups (non-swapped dims should match these) ─────
BASELINE_GROUPS = {
    "name":       "white_male",
    "address":    "high_ses",
    "education":  "mid_traditional",
    "career_gap": "linear_no_gap",
}

PASS = "✓"
FAIL = "✗"


def check_pairs() -> bool:
    all_passed = True

    for dim in ["name", "address", "education", "career_gap"]:
        path = PAIRS_DIR / f"{dim}.json"
        if not path.exists():
            print(f"{FAIL}  {dim}: file not found — run generate_cvs.py first")
            all_passed = False
            continue

        with open(path) as f:
            records = json.load(f)

        print(f"\n{'─'*50}")
        print(f"DIMENSION: {dim.upper()}  ({len(records)} variants)")
        print(f"{'─'*50}")

        dim_passed = True

        # ── Check 1: count ────────────────────────────────────
        expected = EXPECTED_COUNTS[dim]
        if len(records) == expected:
            print(f"  {PASS} Count: {len(records)} (expected {expected})")
        else:
            print(f"  {FAIL} Count: {len(records)} (expected {expected})")
            dim_passed = False

        # ── Per-record checks ─────────────────────────────────
        for rec in records:
            cv   = rec["cv_text"]
            sigs = rec["signals"]
            grp  = sigs[dim]["group"]

            issues = []

            # Check 2: merit invariance
            for anchor in MERIT_ANCHORS:
                if anchor not in cv:
                    issues.append(f"missing merit anchor: '{anchor}'")

            # Check 3: signal presence
            sig_val = sigs[dim]["value"]
            if isinstance(sig_val, dict):
                # Education: check institution name
                check_str = sig_val.get("institution", "")
            else:
                check_str = sig_val

            if check_str and check_str not in cv and check_str.upper() not in cv:
                issues.append(f"signal value not found in CV text: '{check_str[:40]}'")

            # Check 4: isolation — other dims should match baseline
            for other_dim, baseline_grp in BASELINE_GROUPS.items():
                if other_dim == dim:
                    continue
                actual_grp = sigs[other_dim]["group"]
                if actual_grp != baseline_grp:
                    issues.append(
                        f"non-swapped dim '{other_dim}' is '{actual_grp}' "
                        f"(expected baseline '{baseline_grp}')"
                    )

            # Report
            status = PASS if not issues else FAIL
            tok = rec["token_est"]
            print(f"  {status} [{grp:30s}]  ~{tok:4d} tokens", end="")
            if issues:
                dim_passed = False
                for iss in issues:
                    print(f"\n       ↳ {iss}", end="")
            print()

        if not dim_passed:
            all_passed = False

    return all_passed


def print_summary() -> None:
    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        print("\n[no manifest found]")
        return

    with open(manifest_path) as f:
        m = json.load(f)

    print(f"\n{'='*50}")
    print("MANIFEST SUMMARY")
    print(f"{'='*50}")
    print(f"  Total CVs generated : {m['total_cvs_generated']}")
    print(f"  Pair sets           : {list(m['pairs_per_dimension'].items())}")
    print(f"  Batch size          : {m['batch_size']}")
    print(f"  Token estimates     : mean={m['token_estimates']['mean']}, "
          f"total={m['token_estimates']['total']}")
    print(f"  Baseline signals    : {m['baseline_signals']}")


def print_sample_pair(dim: str = "name", index_a: int = 0, index_b: int = 1) -> None:
    """Print two CVs side by side (truncated) to visually confirm they differ only on the target dim."""
    path = PAIRS_DIR / f"{dim}.json"
    if not path.exists():
        return

    with open(path) as f:
        records = json.load(f)

    if len(records) < 2:
        return

    rec_a = records[index_a]
    rec_b = records[index_b]

    print(f"\n{'='*50}")
    print(f"SAMPLE PAIR — dimension: {dim.upper()}")
    print(f"  A: {rec_a['signals'][dim]['group']}")
    print(f"  B: {rec_b['signals'][dim]['group']}")
    print(f"{'='*50}")

    lines_a = rec_a["cv_text"].split("\n")
    lines_b = rec_b["cv_text"].split("\n")
    max_lines = max(len(lines_a), len(lines_b))

    print(f"{'CV A':<55} | {'CV B'}")
    print(f"{'-'*55}-+-{'-'*55}")
    for i in range(min(max_lines, 30)):  # show first 30 lines
        la = lines_a[i] if i < len(lines_a) else ""
        lb = lines_b[i] if i < len(lines_b) else ""
        marker = "◄" if la != lb else " "
        print(f"{la:<55} {marker}  {lb}")

    if max_lines > 30:
        print(f"  ... ({max_lines - 30} more lines)")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── Meridian Sanity Check ──\n")

    passed = check_pairs()
    print_summary()
    print_sample_pair(dim="name", index_a=0, index_b=1)
    print_sample_pair(dim="career_gap", index_a=0, index_b=2)

    print(f"\n{'='*50}")
    if passed:
        print(f"{PASS} All checks passed — CV generation is clean.")
    else:
        print(f"{FAIL} Some checks failed — review issues above.")
    print(f"{'='*50}\n")
