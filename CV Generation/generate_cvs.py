"""
meridian/src/generate_cvs.py
─────────────────────────────
Generates synthetic CV pairs for bias testing.

TWO MODES:
  1. Paired generation  – for each bias dimension, hold 3 dims at baseline,
                          swap only the target dim across all its variants.
                          Produces "clean" pairs ideal for causal attribution.

  2. Full batch         – cartesian product of all four dimensions.
                          Produces the complete candidate pool.

Output:
  data/cvs/pairs/    → one JSON per dimension, each containing N pair entries
  data/cvs/batch/    → batch_all.json (full pool) + individual .txt CV files
  data/cvs/          → manifest.json (token counts, metadata)

Run:
  python src/generate_cvs.py
"""

import json
import os
import itertools
from pathlib import Path
from typing import List, Dict, Any

# ── Path setup ───────────────────────────────────────────────
SRC_DIR  = Path(__file__).parent
ROOT_DIR = SRC_DIR.parent
DATA_DIR = ROOT_DIR / "data" / "cvs"
PAIRS_DIR = DATA_DIR / "pairs"
BATCH_DIR = DATA_DIR / "batch"

for d in [PAIRS_DIR, BATCH_DIR]:
    d.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(SRC_DIR))

from bias_signals import NAMES, ADDRESSES, EDUCATION, CAREER_GAPS
from cv_template  import render_cv

# ──────────────────────────────────────────────────────────────
# BASELINE VALUES  (used when a dimension is NOT being swapped)
# ──────────────────────────────────────────────────────────────
BASELINE = {
    "name":       NAMES[0],        # James Wilson  (white male)
    "address":    ADDRESSES[0],    # Belgravia SW1  (high SES)
    "education":  EDUCATION[1],    # University of Birmingham (mid-traditional)
    "career_gap": CAREER_GAPS[0],  # No gap (linear)
}

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────

def _cv_id(name_g: str, addr_g: str, edu_g: str, gap_g: str) -> str:
    return f"{name_g}__{addr_g}__{edu_g}__{gap_g}"


def _token_estimate(text: str) -> int:
    """Rough estimate: ~4 chars per token (GPT-style tokenisation)."""
    return max(1, len(text) // 4)


def _make_record(
    name_e: Dict, addr_e: Dict, edu_e: Dict, gap_e: Dict,
    swapped_dim: str = "all"
) -> Dict[str, Any]:
    cv_text = render_cv(name_e, addr_e, edu_e, gap_e)
    uid = _cv_id(name_e["group"], addr_e["group"], edu_e["group"], gap_e["group"])
    return {
        "id":          uid,
        "swapped_dim": swapped_dim,
        "signals": {
            "name":       {"value": name_e["value"], "group": name_e["group"]},
            "address":    {"value": addr_e["value"], "group": addr_e["group"]},
            "education":  {"value": edu_e["value"],  "group": edu_e["group"]},
            "career_gap": {"value": gap_e["value"],  "group": gap_e["group"]},
        },
        "cv_text":      cv_text,
        "token_est":    _token_estimate(cv_text),
    }


# ──────────────────────────────────────────────────────────────
# MODE 1: PAIRED GENERATION
# For each dimension, hold 3 at baseline, vary 1 across all variants.
# ──────────────────────────────────────────────────────────────

def generate_pairs() -> Dict[str, List[Dict]]:
    """
    Returns dict mapping dimension name → list of CV records,
    one record per variant of that dimension.
    Also writes pairs/<dim>.json.
    """
    dims = {
        "name":       (NAMES,       "address",   "education", "career_gap"),
        "address":    (ADDRESSES,   "name",      "education", "career_gap"),
        "education":  (EDUCATION,   "name",      "address",   "career_gap"),
        "career_gap": (CAREER_GAPS, "name",      "address",   "education"),
    }

    all_pairs = {}

    for swapped_dim, (variants, *_other_dims) in dims.items():
        records = []
        for variant in variants:
            # Compose kwargs: use baseline for all dims except the swapped one
            kwargs = {
                "name_e":  BASELINE["name"],
                "addr_e":  BASELINE["address"],
                "edu_e":   BASELINE["education"],
                "gap_e":   BASELINE["career_gap"],
            }
            # Override only the swapped dimension
            dim_to_kwarg = {
                "name":       "name_e",
                "address":    "addr_e",
                "education":  "edu_e",
                "career_gap": "gap_e",
            }
            kwargs[dim_to_kwarg[swapped_dim]] = variant

            record = _make_record(**kwargs, swapped_dim=swapped_dim)
            records.append(record)

        all_pairs[swapped_dim] = records

        # Write to file
        out_path = PAIRS_DIR / f"{swapped_dim}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=str)
        print(f"  [pairs] {swapped_dim}: {len(records)} CVs → {out_path.name}")

    return all_pairs


# ──────────────────────────────────────────────────────────────
# MODE 2: FULL BATCH (cartesian product)
# ──────────────────────────────────────────────────────────────

def generate_batch(max_cvs: int = 50) -> List[Dict]:
    """
    Generates a cartesian product of all four dimensions.
    Capped at max_cvs to keep the batch manageable for small-scale testing.
    Selects a representative stratified sample if total > max_cvs.
    """
    all_combos = list(itertools.product(NAMES, ADDRESSES, EDUCATION, CAREER_GAPS))
    total = len(all_combos)
    print(f"  [batch] Total cartesian product: {total} CVs")

    # Stratified sample: take every Nth combination
    if total > max_cvs:
        step = total // max_cvs
        combos = all_combos[::step][:max_cvs]
        print(f"  [batch] Sampling every {step}th → {len(combos)} CVs")
    else:
        combos = all_combos

    records = []
    for name_e, addr_e, edu_e, gap_e in combos:
        record = _make_record(name_e, addr_e, edu_e, gap_e, swapped_dim="all")
        records.append(record)

    # Write batch JSON
    out_path = BATCH_DIR / "batch_all.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False, default=str)
    print(f"  [batch] {len(records)} CVs → {out_path.name}")

    # Write individual .txt files (useful for manual inspection)
    txt_dir = BATCH_DIR / "txt"
    txt_dir.mkdir(exist_ok=True)
    for i, rec in enumerate(records):
        fname = txt_dir / f"cv_{i:03d}_{rec['signals']['name']['group']}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(rec["cv_text"])

    return records


# ──────────────────────────────────────────────────────────────
# MANIFEST
# ──────────────────────────────────────────────────────────────

def write_manifest(pairs: Dict, batch: List) -> None:
    all_records = batch + [r for recs in pairs.values() for r in recs]
    tokens = [r["token_est"] for r in all_records]

    manifest = {
        "total_cvs_generated": len(all_records),
        "pairs_per_dimension": {dim: len(recs) for dim, recs in pairs.items()},
        "batch_size":          len(batch),
        "token_estimates": {
            "min":     min(tokens),
            "max":     max(tokens),
            "mean":    round(sum(tokens) / len(tokens), 1),
            "total":   sum(tokens),
        },
        "baseline_signals": {
            "name":       BASELINE["name"]["group"],
            "address":    BASELINE["address"]["group"],
            "education":  BASELINE["education"]["group"],
            "career_gap": BASELINE["career_gap"]["group"],
        },
        "dimensions": {
            "name":       [e["group"] for e in NAMES],
            "address":    [e["group"] for e in ADDRESSES],
            "education":  [e["group"] for e in EDUCATION],
            "career_gap": [e["group"] for e in CAREER_GAPS],
        }
    }

    out_path = DATA_DIR / "manifest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  [manifest] → {out_path}")
    print(f"  Total CVs : {manifest['total_cvs_generated']}")
    print(f"  Token est : mean={manifest['token_estimates']['mean']}, "
          f"total={manifest['token_estimates']['total']}")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n── Meridian CV Generator ──\n")

    print("Generating paired CVs (one dimension swapped at a time):")
    pairs = generate_pairs()

    print("\nGenerating full batch (cartesian sample, max 50 CVs):")
    batch = generate_batch(max_cvs=50)

    print("\nWriting manifest:")
    write_manifest(pairs, batch)

    print("\n✓ Done. Files written to data/cvs/")
