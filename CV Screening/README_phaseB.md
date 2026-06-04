# Meridian — Phase B: ATS Screening Simulation

Three screening models that simulate the main paradigms used by commercial ATS / AI hiring tools.
All run **locally** and use **free** inference. Output feeds directly into Phase C (bias scoring).

## The three models

| Model | Simulates | Tech | Cost | Network |
|-------|-----------|------|------|---------|
| **A** — Keyword | Legacy ATS (Workday, Greenhouse, Lever) | TF-IDF + cosine (scikit-learn) | Free | None |
| **B** — Semantic | Embedding matchers (Eightfold, HiredScore) | sentence-transformers `all-MiniLM-L6-v2` | Free | One-time model download |
| **C** — LLM judge | Modern LLM screeners (AutoScreen-FW style) | Llama 3.1 8B / Mistral 7B | Free | Depends on backend |

## Free inference options for Model C (pick one)

**1. Ollama — recommended (fully local, unlimited, no key)**
```bash
# install from https://ollama.com/download, then:
ollama pull llama3.1:8b      # or: ollama pull mistral:7b
# Ollama runs a server on localhost:11434 automatically
python src/run_screening.py --models A B C --backend ollama
```

**2. OpenRouter free tier (needs free API key)**
```bash
export OPENROUTER_API_KEY="sk-or-..."
# uses meta-llama/llama-3.1-8b-instruct:free by default ($0, rate-limited)
python src/run_screening.py --models A B C --backend openrouter
```

**3. HuggingFace Inference API free tier (needs HF token)**
```bash
export HF_TOKEN="hf_..."
python src/run_screening.py --models A B C --backend huggingface
```

## Setup

```bash
pip install scikit-learn numpy                 # Model A (required)
pip install sentence-transformers              # Model B (optional)
# Model C: install one of the backends above
```

## Run

```bash
# 1. Generate CVs (Phase A — run once)
python src/generate_cvs.py
python src/sanity_check.py

# 2. Offline dry-run (no network — uses mock LLM to test the pipeline)
python src/run_screening.py --models A C --backend mock

# 3. Real run on your machine
python src/run_screening.py --models A B C --backend ollama
```

Output: `outputs/screening_results.csv` and `.json` — one row per CV per model,
tagged with all four demographic signal groups. This is the input for bias scoring.

## Token economics (Model C)

The four-component prompt is ~770 tokens in, ~20 tokens out per CV.
For the 24-CV pair set: ~19k tokens total per model.

- **Ollama**: $0 (runs on your hardware)
- **OpenRouter `:free` models**: $0 (rate-limited)
- **HuggingFace free tier**: $0 (within daily request limit)

Even on a paid model (e.g. GPT-4o-mini at ~$0.15/1M input tokens), 24 CVs would cost
under £0.01 — so running across two different LLMs to demonstrate inter-judge
disagreement is trivially affordable.

## Notes on the AutoScreen-FW prompt (Model C)

Model C implements the paper's four-component architecture:
1. **Persona** — experienced IB recruiter
2. **Rubric** — weighted criteria (education 25%, skills 25%, experience 30%, fit 20%)
3. **Few-shot** — one worked example for score calibration
4. **Structured output** — forced JSON for machine-readable scores

The paper's "sampling" step (multiple stochastic passes) is **omitted** — we use a
single deterministic pass (temperature 0) for simplicity and reproducibility.

## Expected findings (for the sanity check in Phase C)

- **Model A** scores all name-variants identically — keyword matchers are blind to
  names (confirmed: all 10 name variants score 67.52). Bias only enters via fields
  that overlap with JD vocabulary.
- **Model B** may show subtle variance from demographic correlations in the
  embedding space.
- **Model C** is expected to show the largest, most demographically structured gaps —
  consistent with Wilson & Caliskan (2024).
