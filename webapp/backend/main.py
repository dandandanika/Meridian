"""
webapp/backend/main.py
───────────────────────
FastAPI backend for the Meridian web app — Mode 1 (Test a Model).

Endpoints
  GET  /api/health                 liveness
  GET  /api/models                 selectable models (config + live Ollama tags)
  POST /api/audits                 start an audit job  → {job_id}
  GET  /api/audits/{id}            job status + progress
  GET  /api/registry               saved Bias Profiles (the Model Bias Registry)

Run:
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
"""

import uuid
import urllib.request
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
import pipeline_runner

app = FastAPI(title="Meridian Bias Audit API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:3000"],
    allow_methods=["*"], allow_headers=["*"],
)

# Curated fallback list; we also try to read the user's actual Ollama models live.
KNOWN_MODELS = ["llama3.1:8b", "gemma3:12b", "qwen2:latest", "llama3.2:latest"]


@app.on_event("startup")
def _startup():
    db.init_db()


class AuditConfig(BaseModel):
    backend: str = "mock"            # mock | ollama | openrouter | groq | huggingface
    judges: list[str] = []           # model name(s); [] = backend default
    trials: int = 30
    role: str | None = None          # data/roles/<role>.json (P4); None = default JD
    # prompt "fine-tuning" knobs (optional)
    fairness: bool = False
    guardrails: str | None = None
    system_prompt: str | None = None


@app.get("/")
def root():
    return {"service": "Meridian Bias Audit API",
            "health": "/api/health",
            "frontend": "http://localhost:3000/test-model",
            "endpoints": ["/api/models", "/api/audits", "/api/registry"]}


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/models")
def models():
    """Curated list + whatever Ollama is actually serving locally (if reachable)."""
    found = set(KNOWN_MODELS)
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1) as r:
            for m in json.loads(r.read()).get("models", []):
                found.add(m["name"])
    except Exception:
        pass
    return {"backends": ["mock", "ollama", "openrouter", "huggingface"],
            "models": sorted(found)}


@app.post("/api/audits")
def start_audit(cfg: AuditConfig):
    job_id = uuid.uuid4().hex[:12]
    db.create_job(job_id, cfg.model_dump())
    pipeline_runner.enqueue(job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/audits/{job_id}")
def audit_status(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    out = {"job_id": job["id"], "status": job["status"],
           "progress": job["progress"], "error": job["error"]}
    if job["status"] == "done" and job["result"]:
        out["result"] = json.loads(job["result"])
    return out


@app.get("/api/registry")
def registry():
    return {"profiles": db.list_profiles()}


class CVRequest(BaseModel):
    cv_text: str
    name: str | None = None          # candidate name to swap; defaults to 1st line
    backend: str = "mock"
    model: str | None = None
    trials: int = 20


@app.post("/api/cv/score")
def score_cv(req: CVRequest):
    import cv_scorer
    text = req.cv_text.strip()
    if not text:
        raise HTTPException(400, "empty CV")
    name = req.name or text.splitlines()[0].strip()
    base = cv_scorer.base_scores(text, req.backend, req.model)
    cf = cv_scorer.name_counterfactual(text, name, req.backend, req.model, req.trials)
    return {"base_name": name, "base_scores": base, "counterfactual": cf}


class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []         # [{role: 'user'|'assistant', content: str}]


@app.post("/api/assistant")
def assistant(req: ChatMessage):
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "agent"))
    try:
        import assistant as agent
    except ImportError as e:
        raise HTTPException(
            503, f"Assistant deps not installed ({e}). Run: "
            "pip install -r ../agent/requirements.txt")
    try:
        return {"reply": agent.ask(req.message, req.history)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"agent error: {e}")
