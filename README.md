# Meridian — AI Hiring Bias Audit Pipeline

A controlled, reproducible audit of demographic bias in automated CV screening.
Synthetic CVs are generated with merit held constant and one demographic signal
swapped at a time, scored by three classes of screening model, and the resulting
score gaps are attributed cleanly to the swapped signal.

The target role is a **Junior Analyst, Investment Banking (London)** — see
`data/job_description.json`.

## The three phases

| Phase | Folder | What it does | Output |
|-------|--------|--------------|--------|
| **A — Generation** | `CV Generation/` | Builds synthetic CV pairs. Four bias dimensions (name, address, education pathway, career gap); one swapped at a time, all merit fields constant. | `data/cvs/` + `manifest.json` |
| **B — Screening** | `CV Screening/` | Scores every CV with three ATS paradigms: A=keyword TF-IDF, B=semantic embeddings, C=LLM-as-judge. | `outputs/screening_results.csv` / `.json` |
| **C — Scoring** | `CV Scoring/` | Computes per-model, per-dimension score gaps vs the baseline group, shortlist rates, and EEOC four-fifths adverse-impact ratios. | `outputs/bias_scores.csv` / `.json`, `bias_report.md` |

## Quick start

```bash
pip install scikit-learn numpy            # Phase B Model A (required)
pip install sentence-transformers         # Phase B Model B (optional)

# Full local dry-run — no network, Model C uses a deterministic mock backend:
python run_pipeline.py --models A C --backend mock

# Real run on your machine (free, local LLM via Ollama, plus semantic Model B):
#   install Ollama from https://ollama.com/download, then: ollama pull llama3.1:8b
python run_pipeline.py --models A B C --backend ollama

# Compare several LLM judges side by side (each becomes its own column in the
# report, exposing cross-judge disagreement):
python run_pipeline.py --models A C --backend ollama \
    --judges llama3.1:8b gemma3:12b qwen2:latest
```

> **Note on a single judge / low temperature:** one `temperature 0` pass of a
> small model often assigns the same integer to near-identical CVs, masking
> sub-integer bias. Running multiple judges (`--judges ...`) and/or larger models
> gives the spread needed to actually detect demographic effects.

Run phases individually if you prefer:

```bash
python "CV Generation/generate_cvs.py"
python "CV Screening/run_screening.py" --models A C --backend mock
python "CV Scoring/bias_scoring.py" --threshold 70
```

## The four bias dimensions

| Dimension | Signal encoded | Baseline group |
|-----------|----------------|----------------|
| Name | perceived race + gender (+ religion for Arab/Muslim) | `white_male` |
| Address | socioeconomic status (London IMD deciles) | `high_ses` |
| Education pathway | class / first-gen / non-traditional route | `mid_traditional` |
| Career gap | gender (caregiving), SES (financial), travel | `linear_no_gap` |

All CVs hold the same merit: 2:1 BSc Economics, a 3-month Tier-1 IB internship,
and identical technical skills (Python, Excel, Bloomberg, SQL).

## How bias is attributed

Because each dimension is varied **one signal at a time** with every merit field
held constant, any difference in score between two groups within a dimension is
caused by the demographic signal alone — there is no merit confound. Phase C
reports each group's mean score, its gap versus the baseline group, the
shortlist rate at a score threshold (default 70), and the four-fifths impact
ratio. A model whose mean-absolute-gap is near zero is effectively blind to the
signal; a larger value indicates more demographically structured scoring.

## Reproducibility notes

- Phase A and Model A (TF-IDF) are fully deterministic.
- Model C is run at `temperature 0` (single deterministic pass). The paper's
  stochastic multi-sampling step is intentionally omitted for reproducibility.
- The `mock` Model-C backend produces fixed test scores so the pipeline can be
  exercised offline; those numbers are fixtures, **not** a claim about any real
  LLM. Use `--backend ollama / openrouter / huggingface` for real results.
