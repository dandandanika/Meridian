"""
webapp/agent/tools.py
──────────────────────
Tools the LangGraph assistant can call. THIS is the important part: the agent
only *interprets* — every number it states comes from one of these tools reading
the real SQLite registry. The LLM is never asked to recall statistics from memory.

Each tool is a plain function decorated with @tool (LangChain). The docstring is
what the LLM sees to decide when to call it — so the docstrings are written for
the model, not just for humans.
"""

import json
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

DB = Path(__file__).resolve().parent.parent / "backend" / "meridian.db"


def _rows(q, args=()):
    if not DB.exists():
        return []
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in c.execute(q, args).fetchall()]
    finally:
        c.close()


@tool
def list_audited_models() -> str:
    """List every model that has a saved bias profile in the registry, with a
    one-line verdict summary (which dimensions showed bias). Call this first when
    the user asks what's been tested or which model is fairest."""
    rows = _rows("SELECT model_label, backend, params, verdicts FROM profiles ORDER BY created_at DESC")
    if not rows:
        return "The registry is empty — no audits have been run yet."
    out = []
    for r in rows:
        v = json.loads(r["verdicts"])
        biased = [d for d, x in v.items() if x.get("bias_detected")]
        params = json.loads(r["params"])
        out.append(f"- {r['model_label']} (backend={r['backend']}, trials={params.get('trials')}): "
                   + (f"bias in {', '.join(biased)}" if biased else "no detectable bias"))
    return "\n".join(out)


@tool
def get_model_profile(model_label: str) -> str:
    """Get the full per-dimension bias breakdown for ONE model. Use when the user
    asks about a specific model's bias. `model_label` should match a label from
    list_audited_models (partial match is allowed)."""
    rows = _rows("SELECT model_label, verdicts FROM profiles WHERE model_label LIKE ? ORDER BY created_at DESC LIMIT 1",
                 (f"%{model_label}%",))
    if not rows:
        return f"No profile found matching '{model_label}'. Call list_audited_models to see available models."
    v = json.loads(rows[0]["verdicts"])
    lines = [f"Profile for {rows[0]['model_label']}:"]
    for dim, x in v.items():
        verdict = "BIAS DETECTED" if x.get("bias_detected") else "no detectable bias"
        groups = x.get("groups", {})
        sig = [f"{g} (Δ={m['delta_vs_chance']:+}, Holm p={m['p_holm']})"
               for g, m in groups.items() if m.get("significant")]
        lines.append(f"  {dim}: {verdict}" + (f" — significant: {', '.join(sig)}" if sig else ""))
    return "\n".join(lines)


@tool
def compare_dimension(dimension: str) -> str:
    """Across all audited models, report which ones show bias on a given
    dimension (one of: name, address, education, career_gap). Use for questions
    like 'do any models show race bias?' (race → name) or 'which model is fairest
    on education?'."""
    rows = _rows("SELECT model_label, verdicts FROM profiles ORDER BY created_at DESC")
    if not rows:
        return "The registry is empty."
    out = [f"Dimension '{dimension}' across models:"]
    for r in rows:
        v = json.loads(r["verdicts"]).get(dimension)
        if not v:
            continue
        out.append(f"  {r['model_label']}: " + ("BIAS" if v.get("bias_detected") else "clear"))
    return "\n".join(out)


TOOLS = [list_audited_models, get_model_profile, compare_dimension]
