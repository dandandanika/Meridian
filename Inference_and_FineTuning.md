# Meridian — Inference Options, Deployment & Prompt Fine-Tuning

Addendum to the web-app plan, covering two asks: (1) replacing Ollama with a free, low-cost, *deployable* inference backend, and (2) a user-facing "fine-tune the model with prompts" feature.

---

## 1. Bypassing Ollama — free, low-cost, deployable

Ollama is local-only: great for unlimited free trials, but it can't be deployed (no GPU on a web host) and is slow on CPU. To deploy the app, swap to a **hosted, OpenAI-compatible API**. Your code now supports this — `--backend groq` / `openrouter` / `huggingface` are wired into the same screener the ranker uses, so it's an env-var change, not a rewrite.

### Recommendation

| Provider | Free tier (Jun 2026) | Why / best for | Deployable? |
|---|---|---|---|
| **Groq** ⭐ | 30 req/min, 1,000 req/day, Llama 3.3 70B / Llama 3.1 8B / Qwen / DeepSeek | **Fastest** (LPU), OpenAI-compatible, dead-simple. Best default for this app. | ✅ |
| **Google Gemini** | ~1,500 req/day on Gemini Flash, no card | Highest daily request cap; good for batch audits | ✅ |
| **OpenRouter** | ~50 req/day, ~30 models incl. Llama/DeepSeek/Qwen/Gemma | **Model variety** in one key — ideal for cross-model comparison | ✅ |
| **Cerebras** | ~1M tokens/day on Llama 3.1 70B | Highest token volume | ✅ |
| **Cloudflare Workers AI** | 10k "neurons"/day | **Edge deploy** — inference co-located with the app | ✅ |
| Ollama (keep) | unlimited local | unlimited trials during development | ❌ local only |

**Pick Groq as the new default.** A bias audit at 30 trials × 4 dimensions ≈ 120 calls per model — comfortably inside Groq's 1,000/day, and *much* faster than local Llama. Because providers have independent free limits, you can **rotate across Groq + Gemini + OpenRouter** to multiply free capacity.

### How to use Groq (already wired)
```bash
# free key, no card: https://console.groq.com  →  create API key
export GROQ_API_KEY="gsk_..."
python run_pipeline.py --ranking --skip-rating --skip-generate \
    --backend groq --judges llama-3.3-70b-versatile llama-3.1-8b-instant --trials 40
```
`GROQ_API_KEY` is read by the new `_call_groq` adapter in `model_c_llm_judge.py` (OpenAI-compatible Chat Completions; reused by the ranker).

### Deployment architecture (when ready)
```
Vercel (Next.js frontend)
        │ HTTPS
Render / Railway / Fly.io  (FastAPI backend, no GPU needed)
        │
   Groq / Gemini / OpenRouter API  ◄── hosted inference (the Ollama replacement)
        │
   Postgres (managed)              ◄── registry, jobs, results
```
Nothing here needs a GPU, because inference is hosted. Frontend → Vercel free tier; backend → Render/Railway free tier; DB → Supabase/Neon free Postgres. **The whole app can run on free tiers.**

---

## 2. Prompt "fine-tuning" feature — steer the model, measure the effect

> Not weight fine-tuning — **prompt-level steering**: system prompt, fairness instructions, guardrails, examples. The question: *can you reduce a model's measured bias without retraining it?* This is cheap, reversible, and exactly what an HR team could realistically do.

### What the user can change (the "tuning knobs")
- **System prompt / persona** — replace "experienced IB recruiter" with e.g. a "bias-aware, merit-only assessor."
- **Fairness instruction** — explicit "ignore name, gender, background, postcode, institution prestige."
- **Guardrails** — hard rules ("judge only on skills, experience, degree class").
- **Examples** — reuse the P3 "past hires" mechanism to demonstrate fair decisions.
- **Free-text instructions** — any extra steering.

### How it works (already wired into the pipeline)
A `tuning` config flows `RankingScreener → build_rank_prompt` (in `model_d_ranking.py`) and injects the chosen blocks into the ranking prompt. The **same audit + significance stats** then run on the tuned prompt, so every condition gets a rigorous verdict. Run several conditions and compare:

```bash
# CLI (Phase P5): baseline vs fairness-instruction vs guardrail
python "CV Screening/run_tuning.py" --backend groq \
    --judges llama-3.3-70b-versatile --conditions baseline fairness guardrail \
    --dims name education --trials 40
python "Bias Scoring/ranking_stats.py" --results outputs/tuning_results.csv
```
Each condition appears as its own row (`D:...|tune=baseline`, `…|tune=fairness`, …) with its own 🔴/🟢 verdict and effect sizes — so you can see, with significance, whether the fairness instruction actually shrank the education or name bias or just moved it around.

Custom prompts via a JSON file:
```json
{ "my_strict": {"system_prompt": "You are a blind-screening assessor.",
                "guardrails": "Never consider name, address or university brand."} }
```
```bash
python "CV Screening/run_tuning.py" --conditions-file my_prompts.json --backend groq
```

### Web-app UX (Mode 1b: "Tune a Model")
1. User picks an audited model → sees its baseline Bias Profile.
2. **Tuning panel:** toggles for fairness instruction & guardrails, a textarea for a custom system prompt, optional example CVs.
3. "Run tuned audit" → backend runs the tuned condition → **side-by-side diff**: baseline vs tuned, per dimension (effect size + verdict change), e.g. *"Fairness instruction cut the education gap from Δ +1.1 (🔴) to Δ +0.3 (🟢), but introduced a new name effect."*
4. **Implication surfaced by the agent:** whether prompt-steering is a sufficient mitigation, or whether bias just relocates — a genuinely useful, honest finding for the programme.

### Why this is a strong feature
- It's the **cheapest mitigation a real HR team could deploy**, so testing whether it works is directly actionable.
- The literature warns fairness instructions are unreliable and can *backfire* (move bias rather than remove it) — your tool can demonstrate that empirically, with significance.
- It teaches the user prompt-engineering's limits as a fairness tool — exactly the kind of evidence-based caution the Tomorrow's Talent programme needs.

> Backend note: the `tuning` knobs are also natural fields on the web API's `AuditConfig`, so the frontend "Tune a Model" panel maps 1:1 onto the same job runner used for a normal audit.

Sources: [Best free LLM APIs 2026](https://costbench.com/best/best-llm-api-with-free-tier/), [Groq free tier 2026](https://tokenmix.ai/blog/groq-free-tier-limits-2026), [Free LLM API comparison](https://klymentiev.com/blog/free-llm-api).
