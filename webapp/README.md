# Meridian Web App

Full-stack front end for the Meridian bias-audit pipeline. The existing Python pipeline is the engine; the backend wraps it.

Live:
- **Test a model** — configure model + prompt-tuning, run the ranking audit, view per-dimension verdicts with significance.
- **Test a CV** — score one CV, then rank the same CV under every demographic name to show which version the model prefers (bias made personal).
- **Insight assistant** — a LangGraph agent that interprets the registry, grounded (no invented stats).
- **Registry** — every saved bias profile.

```
webapp/
  backend/     FastAPI — wraps run_ranking.py + ranking_stats.py + CV scoring, SQLite registry
  frontend/    Next.js — Test a model / Test a CV / Assistant / Registry
  agent/       LangGraph Insight Assistant (tools over the registry)
```

## Run it locally (two terminals)

### 1. Backend (port 8000)
```bash
cd webapp/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
The backend shells out to the pipeline, so the Python deps for the pipeline must be importable from the repo root (`scikit-learn`, etc. — see the main README). For real models, set the relevant key first, e.g. `export GROQ_API_KEY=...` or have Ollama running.

### 2. Frontend (port 3000)
```bash
cd webapp/frontend
npm install
npm run dev
```
Open http://localhost:3000/test-model. (Override the API URL with `NEXT_PUBLIC_API_URL` if the backend isn't on :8000.)

## First run

Start with **backend = mock** — it runs offline in seconds and exercises the whole flow (config → progress → verdict matrix → per-dimension chart), including the prompt-tuning toggles (the mock dampens its planted bias when you add a fairness instruction/guardrail, so you can see the feature work). Then switch to `groq` (hosted, free, fast) or `ollama` (local) for real results.

## How it maps to the pipeline
- `POST /api/audits` → `run_ranking.py … && ranking_stats.py` (serialised; one audit at a time).
- The verdict matrix + chart read `outputs/ranking_bias.json` (ingested into SQLite).
- Tuning toggles → `--fairness / --guardrails / --system-prompt` on `run_ranking.py`.

## Endpoints
`GET /api/health` · `GET /api/models` · `POST /api/audits` · `GET /api/audits/{id}` · `GET /api/registry`

## Assistant (LangGraph) — extra setup
The chatbot needs its own deps and a tool-calling LLM:
```bash
pip install -r webapp/agent/requirements.txt
ollama pull llama3.1:8b          # default; or: export MERIDIAN_ASSISTANT_BACKEND=groq GROQ_API_KEY=...
```
Then use the Assistant page (run an audit first so it has data to discuss). See `agent/README.md` for the LangGraph walkthrough.

## Notes / next
- v0 serialises jobs and uses fixed output filenames — fine locally; use per-job output dirs + a real queue before deploy.
- Test a CV swaps the candidate name across groups and ranks; extending counterfactuals to address/education/gap is the next enhancement.
- Deploy: Vercel (frontend) + Render/Railway (backend) + Postgres, inference via Groq — no GPU.
