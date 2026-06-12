# Meridian — Web App Phase: Design & Ideation

Turning the Meridian bias-audit pipeline into a full-stack app. Local-first, deployable later. The existing Python (`CV Generation/`, `CV Screening/`, `Bias Scoring/`) becomes the backend engine — we wrap it, we don't rewrite it.

---

## 0. The organising idea

Everything hangs off a **Model Bias Registry**: each model+config has a *precomputed bias profile* (the ranking + significance audit we already produce). That profile is the unit of reuse — it powers the model comparison, and it's the lens through which any individual CV's scores are interpreted ("this model scored you high, but it has proven education-pathway bias").

Three user journeys, one registry:

```
        ┌─────────────────────────────────────────────┐
        │              MODEL BIAS REGISTRY             │
        │  (precomputed audit per model + config)      │
        └───────▲──────────────▲───────────────▲───────┘
                │              │               │
        ┌───────┴──┐   ┌───────┴───┐   ┌───────┴────────┐
        │ 1 Test a │   │ 2 Test a  │   │ 3 HR Simulator │
        │  Model   │   │   CV      │   │  (batch, opt.) │
        └──────────┘   └───────────┘   └────────────────┘
```

---

## A. User journeys & site structure

### Navigation
1. **Dashboard** — registry leaderboard (models ranked by bias profile), shortcuts into the 3 modes.
2. **Test a Model** (Auditor)
3. **Test a CV** (Inspector)
4. **HR Simulator** (batch — optional / phase 4)
5. **Model Registry** — browse/compare saved bias profiles.
6. **Insight Assistant** — the agent/chatbot (contextual, see §B).
7. **Methodology & Caveats** — transparency: the design, the stats, the power limitations.

---

### Mode 1 — Test a Model (the Auditor)

| | |
|---|---|
| **Input** | Pick a model (Ollama / OpenRouter), set params: temperature, **trials**, dimensions to test, method (ranking / rating), and optional experiments (P3 history, P4 role). |
| **Process** | Kicks off an async audit job (reuses `run_ranking.py` + `ranking_stats.py`). Live progress bar + token/latency counter. |
| **Output** | A **Bias Profile card**: per-dimension verdict (🔴/🟢), effect sizes, 95% CIs, permutation p (Holm-corrected), rank/selection charts. Saved to the registry. |
| **Implication** | "Is this model+config safe to use, and where does it fail?" Side-by-side vs other audited models. Surfaces the education/class bias automatically. |
| **Screens** | Config form → live progress → results dashboard (verdict table + charts + an agent-written plain-English interpretation). |

> Design note: enforce a **minimum-trials guard** in the UI — if trials are too low to detect a moderate effect, the verdict card shows "underpowered, not 'no bias'." This bakes the honesty rule into the product.

### Mode 2 — Test a CV (the Inspector) — *the flagship feature*

| | |
|---|---|
| **Input** | Upload a real CV (PDF / .docx / text), optionally a JD. |
| **Process** | Parse the CV → score it across **all registered models** → attach each model's precomputed bias profile → **(killer feature)** auto-generate demographic *counterfactuals of this exact CV* (swap name, postcode, institution, gap) and re-score, to show how the score moves when only the demographic signal changes. |
| **Output** | (a) Per-model score table; (b) **consensus vs variance** view across models; (c) each score annotated with that model's bias profile; (d) **counterfactual panel**: "Changing your university to Oxford raised your score on 2 of 4 models by ~N." |
| **Implication** | The user sees whether models agree, and interprets any divergence through each model's known bias. The counterfactual makes bias *tangible and personal* for their CV. |
| **Screens** | Upload → parsed-fields confirm → results (model table + consensus chart + counterfactual explorer + agent explanation). |

> Build cost: needs a CV parser (extract name/education/etc.) and a counterfactual generator (extend the existing `bias_signals` perturbation logic to operate on an *uploaded* CV). Highest value, highest effort.

### Mode 3 — HR Simulator (batch) — *optional, phase 4*

| | |
|---|---|
| **Input** | A JD + a batch of CVs (upload many, or generate a synthetic applicant pool). |
| **Process** | Each model ranks/scores the pool → shortlist top-k → compute the **demographic composition of the shortlist vs the pool** (four-fifths / adverse-impact). |
| **Output** | "If you shortlisted with model M, your interview pool would be X% [group] vs Y% in applicants." Adverse-impact dashboard, models compared. |
| **Implication** | Shows **allocational harm at the hiring level** — the most visceral framing for an HR / UBS audience; ties directly to the EEOC four-fifths rule we already compute. |

---

## B. Agentic AI / LangGraph integration

**What LangGraph gives you:** stateful, multi-step workflows as a graph — nodes (steps or sub-agents), edges (control flow, including *conditional* routing), a shared state object, persistence (long runs survive), human-in-the-loop checkpoints, and tool-calling. Two strong fits here; start with the first.

### Option 1 — Insight Assistant (grounded interpretation chatbot) — *recommended first*

A conversational agent over the results. "Why did my CV score low on model C?" / "Which model is fairest for an analyst role?" / "Is the race result real or just underpowered?"

- **Graph shape:** `intake → planner → tool-loop → synthesize` (+ optional human clarify node).
- **Tools (this is the key — the agent interprets, it does *not* invent numbers):** `query_bias_registry`, `get_cv_scores`, `run_counterfactual`, `fetch_significance`, `summarize_report`.
- **State:** conversation history + retrieved data + which CV/model is in context.
- **Guardrails:** answers must cite the real stats the tools return; a system rule forbids calling an underpowered null "no bias." This is where agentic value is highest — it makes dense statistical output usable by non-technical HR users.
- **Why first:** clear value, contained scope, teaches the core LangGraph loop (tool-calling agent + state).

### Option 2 — Pipeline Orchestration agent — *the ambitious one*

Model the audit itself as a graph that **adapts based on intermediate results** — automating exactly the decisions we've been making by hand (flat rating → switch to ranking → underpowered → add trials → try P3/P4).

- **Graph shape:** `generate → screen(model) → stats → router`. The **router/supervisor node** inspects results and conditionally routes: if a dimension is near-significant but underpowered → loop back with more trials; if names are null but you want depth → trigger P3 history; etc. Stop when verdicts stabilise.
- **State:** accumulating results + a decision log (great for reproducibility/audit trail).
- **Extras:** human-in-the-loop checkpoint to approve an escalation; persistence so multi-hour Ollama runs survive restarts.
- **Why later:** more moving parts, but it directly encodes the methodology and is the strongest "agentic" story.

### Bonus agent ideas
- **Counterfactual red-teamer:** given a CV, autonomously searches for the perturbation that swings its score most ("your CV is most sensitive to *institution*").
- **Report-writer:** turns raw stats into the exec brief / Word doc, with the honest-null guardrail built in.

---

## C. Recommended architecture

```
Frontend (Mode 1/2/3 + chat)
        │  REST + WebSocket/SSE (live job progress)
        ▼
FastAPI backend  ──►  Job queue (async; Ollama is slow)
        │                   │
        │            wraps existing modules:
        │            run_ranking / ranking_stats / model_a..d
        ▼
   SQLite (local) ──► Postgres (deploy)
   tables: models+bias_profile · audits · cvs · cv_scores · jobs
        │
        ▼
LangGraph agent service (tools query the same DB + pipeline)
   LLMs: Ollama (local) + OpenRouter (hosted)
```

**Stack options (pick per goal):**
- **Fast internal MVP:** **Streamlit** front end + FastAPI. Python-native, days not weeks — but weaker for the polished multi-mode UX and embedded chat.
- **Real product / UBS demo:** **Next.js (React) + Tailwind + Recharts/Plotly** front end on FastAPI. More work, far better UX, proper chatbot panel.
- Backend is **FastAPI either way** so the front end is swappable. Async jobs: start with FastAPI background tasks + SQLite job table; graduate to Celery+Redis if needed.

---

## D. Suggested build order (each phase shippable)

1. **Backend API + Registry** — FastAPI wrapping the pipeline; SQLite; **Mode 1 (Test a Model)** end-to-end with live progress. Reuses everything already built.
2. **Mode 2 (CV Inspector)** — CV parsing + counterfactual generator + multi-model scoring + consensus view.
3. **LangGraph Option 1** — grounded Insight Assistant chatbot over results.
4. **Mode 3 (HR Simulator)** + **LangGraph Option 2** (orchestration).
5. **Deploy** — Postgres, hosted models via OpenRouter, auth.

## E. Key risks / decisions to settle early
- **Long-running model calls** (Ollama is slow) → must be async jobs with progress streaming, not request/response.
- **Agent grounding** → tools return real numbers; the LLM only interprets. No hallucinated stats.
- **Honest nulls in the UI** → never render "no bias" without the power caveat.
- **CV parsing reliability** → start with a confirm-the-parsed-fields step before scoring.
- **Privacy** → real uploaded CVs contain personal data; local-first helps, but plan redaction/retention before any deploy.
