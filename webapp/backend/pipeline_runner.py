"""
webapp/backend/pipeline_runner.py
──────────────────────────────────
Bridges the web API to the existing Meridian pipeline. It does NOT reimplement
any analysis — it shells out to the same scripts the CLI uses
(`CV Screening/run_ranking.py` → `Bias Scoring/ranking_stats.py`), then ingests
`outputs/ranking_bias.json` into the SQLite registry.

Jobs are serialised (one audit at a time) via a global lock, because the pipeline
writes to fixed output filenames — fine for a local-first v0; revisit with
per-job output dirs + a real queue (Celery/RQ) before deploy.
"""

import json
import subprocess
import threading
from pathlib import Path

import db

# webapp/backend → webapp → <project root>
REPO_ROOT = Path(__file__).resolve().parents[2]
SCREEN_DIR = REPO_ROOT / "CV Screening"
STATS_DIR = REPO_ROOT / "Bias Scoring"
OUT_DIR = REPO_ROOT / "outputs"

_run_lock = threading.Lock()   # serialise audits (shared output filenames)


def build_commands(params: dict):
    """Translate an API audit config into the two CLI invocations."""
    backend = params.get("backend", "mock")
    trials = int(params.get("trials", 30))
    judges = params.get("judges") or []
    role = params.get("role")

    rank = ["python3", "run_ranking.py", "--backend", backend, "--trials", str(trials)]
    if judges:
        rank += ["--judges", *judges]
    if role:
        rank += ["--role", role]
    # prompt fine-tuning knobs
    if params.get("fairness"):
        rank += ["--fairness"]
    if params.get("guardrails"):
        rank += ["--guardrails", params["guardrails"]]
    if params.get("system_prompt"):
        rank += ["--system-prompt", params["system_prompt"]]

    stats = ["python3", "ranking_stats.py"]   # reads outputs/ranking_results.csv
    return [(rank, SCREEN_DIR), (stats, STATS_DIR)]


def ingest_result(job_id: str, params: dict, result_path: Path = None) -> dict:
    """Read ranking_bias.json, persist a Bias Profile per model, return a summary."""
    result_path = result_path or (OUT_DIR / "ranking_bias.json")
    data = json.loads(result_path.read_text())
    summary = {}
    for model in data.get("_models", []):
        verdicts = {}
        for dim, cell in data.get(model, {}).items():
            groups = {
                g: {"delta_vs_chance": m["delta_vs_chance"],
                    "p_holm": m["p_holm"], "significant": m["significant"]}
                for g, m in cell["groups"].items()
            }
            verdicts[dim] = {
                "bias_detected": cell.get("any_significant", False),
                "baseline": cell.get("baseline"),
                "groups": groups,
            }
        db.save_profile(job_id, model, params.get("backend", "mock"), params, verdicts)
        summary[model] = {d: v["bias_detected"] for d, v in verdicts.items()}
    db.update_job(job_id, result=json.dumps(data))
    return summary


def _run(job_id: str):
    params = json.loads(db.get_job(job_id)["params"])
    try:
        db.update_job(job_id, status="running", progress="starting…")
        with _run_lock:
            for cmd, cwd in build_commands(params):
                db.update_job(job_id, progress=f"running: {' '.join(cmd)}")
                proc = subprocess.Popen(
                    cmd, cwd=str(cwd), stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in proc.stdout:               # stream progress
                    line = line.strip()
                    if line:
                        db.update_job(job_id, progress=line[:200])
                proc.wait()
                if proc.returncode != 0:
                    raise RuntimeError(f"{cmd[1]} exited {proc.returncode}")
            db.update_job(job_id, progress="scoring complete, ingesting…")
            summary = ingest_result(job_id, params)
        db.update_job(job_id, status="done", progress="done")
        return summary
    except Exception as e:                              # noqa: BLE001
        db.update_job(job_id, status="error", error=str(e), progress=f"error: {e}")


def enqueue(job_id: str):
    """Launch the audit in a background thread (non-blocking for the API)."""
    threading.Thread(target=_run, args=(job_id,), daemon=True).start()
