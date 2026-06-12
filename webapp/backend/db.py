"""
webapp/backend/db.py
─────────────────────
Tiny SQLite layer for the Meridian web app (local-first; swap for Postgres later).

Two tables:
  jobs      — one audit run, its config, status, progress, and (when done) its
              raw result JSON.
  profiles  — the saved "Bias Profile" for a model+config (the Model Bias Registry
              that powers model comparison and CV interpretation).

Pure stdlib sqlite3 so there are no ORM dependencies to learn yet.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "meridian.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL,         -- queued|running|done|error
                progress    TEXT DEFAULT '',
                params      TEXT NOT NULL,          -- JSON config
                result      TEXT,                   -- JSON ranking_bias.json
                error       TEXT,
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profiles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      TEXT NOT NULL,
                model_label TEXT NOT NULL,          -- e.g. D:llama3.1:8b
                backend     TEXT,
                params      TEXT NOT NULL,          -- JSON config
                verdicts    TEXT NOT NULL,          -- JSON {dimension: bias?/effect}
                created_at  REAL NOT NULL
            );
            """
        )


# ── jobs ─────────────────────────────────────────────────────────────────────
def create_job(job_id: str, params: dict):
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO jobs (id,status,params,created_at,updated_at) VALUES (?,?,?,?,?)",
            (job_id, "queued", json.dumps(params), now, now),
        )


def update_job(job_id: str, **fields):
    fields["updated_at"] = time.time()
    cols = ", ".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))


def get_job(job_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def list_jobs(limit: int = 50) -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT id,status,progress,created_at FROM jobs "
            "ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── profiles (the registry) ──────────────────────────────────────────────────
def save_profile(job_id: str, model_label: str, backend: str,
                 params: dict, verdicts: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO profiles (job_id,model_label,backend,params,verdicts,created_at) "
            "VALUES (?,?,?,?,?,?)",
            (job_id, model_label, backend, json.dumps(params),
             json.dumps(verdicts), time.time()),
        )


def list_profiles() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT id,job_id,model_label,backend,params,verdicts,created_at "
            "FROM profiles ORDER BY created_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["params"] = json.loads(d["params"])
        d["verdicts"] = json.loads(d["verdicts"])
        out.append(d)
    return out


if __name__ == "__main__":
    init_db()
    print(f"Initialised {DB_PATH}")
