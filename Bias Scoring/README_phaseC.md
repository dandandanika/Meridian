# Meridian — Phase C: Bias Scoring

Turns the Phase B screening table into an attributable bias measurement.

## Input
`outputs/screening_results.csv` — one row per CV per model, tagged with the
demographic group on each of the four dimensions (produced by Phase B).

## What it computes

For every **model × dimension × group** cell:

| Metric | Meaning |
|--------|---------|
| `mean_score` | mean screening score (0–100) for that group |
| `gap_vs_baseline` | `mean_score − baseline_group_mean` (negative = penalised) |
| `pct_of_baseline` | group mean as a % of the baseline group's mean |
| `shortlist_rate` | fraction scoring ≥ threshold (default 70) |
| `impact_ratio` | `shortlist_rate / baseline_shortlist_rate` — the EEOC four-fifths rule; `< 0.80` is flagged as adverse impact |

Per **model × dimension**: spread (max − min mean), most penalised / most
favoured group. Per **model**: mean & max absolute gap across all non-baseline
groups, and a count of adverse-impact flags — a single "how bias-sensitive is
this model" number.

## Why the gaps are clean
Phase A swaps one demographic signal at a time and holds every merit field
constant, so a score gap between two groups in a dimension is the *average
treatment effect of that signal* — no merit confound.

## Run

```bash
python bias_scoring.py                       # uses outputs/screening_results.csv, threshold 70
python bias_scoring.py --threshold 65        # different shortlist bar
python bias_scoring.py --results /path/to/screening_results.csv
```

## Output
- `outputs/bias_scores.csv` — flat table, one row per model/dimension/group
- `outputs/bias_scores.json` — full nested structure incl. per-model summary
- `outputs/bias_report.md` — human-readable report with ranked tables

## Reading the result
A model with `mean_abs_gap ≈ 0` is effectively blind to the signal. Keyword
TF-IDF (Model A) is name-invariant by construction — all name variants score
identically — so bias can only enter via fields that overlap the JD vocabulary.
LLM judges (Model C) are expected to show the largest, most demographically
structured gaps, consistent with Wilson & Caliskan (2024).

> Pure standard library — no pandas/numpy needed.
