"""
meridian/src/model_c_llm_judge.py
──────────────────────────────────
MODEL C — LLM-as-judge screening model.

Implements the AutoScreen-FW (2026) prompt architecture, which structures the
screening prompt into four components:

  1. PERSONA   — instruct the model to act as an experienced recruiter / career advisor
  2. RUBRIC    — explicit, weighted evaluation criteria
  3. FEW-SHOT  — one worked example (high-merit CV → score) for in-context calibration
  4. STRUCTURED OUTPUT — force a JSON response so the score is machine-readable

The "sampling" step from the paper (multiple stochastic passes, then aggregate)
is OMITTED for simplicity — we take a single deterministic pass (temperature 0).

────────────────────────────────────────────────────────────────────────────
FREE INFERENCE OPTIONS  (pick one via the `backend` argument)
────────────────────────────────────────────────────────────────────────────

  backend="ollama"      → FULLY LOCAL, FREE, UNLIMITED.  Recommended for a student.
                          Install:  https://ollama.com/download
                          Then:     ollama pull llama3.1:8b   (or mistral:7b)
                          Runs on your own machine, no API key, no rate limit.

  backend="openrouter"  → FREE TIER via OpenRouter. Needs a free API key.
                          Set env var OPENROUTER_API_KEY.
                          Use a model with the ":free" suffix, e.g.
                          "meta-llama/llama-3.1-8b-instruct:free"
                          Rate-limited but $0 cost.

  backend="huggingface" → FREE TIER via HF Inference API. Needs HF token.
                          Set env var HF_TOKEN. ~unlimited small requests/day.

Returns a score in [0, 100] plus the model's reasoning.
"""

import os
import json
import re
import time
from typing import Optional


# ──────────────────────────────────────────────────────────────
# THE FOUR-COMPONENT PROMPT (AutoScreen-FW architecture)
# ──────────────────────────────────────────────────────────────

PERSONA = """\
You are an experienced investment banking recruiter with 15 years of experience \
screening graduate analyst applications at a top-tier London bank. You evaluate \
candidates fairly and consistently against the role requirements."""

RUBRIC = """\
Score each CV from 0 to 100 against these weighted criteria:
  - Education fit (25%): relevant degree, classification, institution quality
  - Technical skills (25%): financial modelling, Excel, Bloomberg, Python/SQL
  - Relevant experience (30%): internships, deal exposure, financial services work
  - Communication & overall fit (20%): clarity, structure, evidence of competence

A score of 70+ means strong shortlist candidate; 50-69 means borderline; \
below 50 means reject."""

FEWSHOT_CV = """\
JOHN SMITH
Education: 2:1 BSc Economics, University of Manchester (full-time)
Experience: 3-month Summer Analyst internship at a bulge-bracket bank; built DCF \
and LBO models, prepared pitch books.
Skills: Excel, Bloomberg Terminal, Python, financial modelling."""

FEWSHOT_OUTPUT = """\
{"score": 78, "reasoning": "Strong technical skills and directly relevant IB \
internship with deal exposure. Solid 2:1 from a Russell Group university. \
Clear shortlist candidate."}"""


def build_prompt(jd: dict, cv_text: str) -> str:
    """Assemble the full four-component prompt."""
    jd_summary = (
        f"ROLE: {jd['role']} ({jd['location']})\n"
        f"REQUIREMENTS:\n" + "\n".join(f"  - {r}" for r in jd["requirements"])
    )

    prompt = f"""\
{PERSONA}

{RUBRIC}

Here is the job you are screening for:
{jd_summary}

EXAMPLE (for calibration):
CV:
{FEWSHOT_CV}
Your evaluation:
{FEWSHOT_OUTPUT}

Now evaluate the following candidate. Respond with ONLY a JSON object in the same \
format: {{"score": <int 0-100>, "reasoning": "<one or two sentences>"}}.
Do not include any text outside the JSON.

CV:
{cv_text}

Your evaluation:"""
    return prompt


# ──────────────────────────────────────────────────────────────
# BACKEND ADAPTERS
# ──────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, model: str = "llama3.1:8b") -> str:
    """Call a locally running Ollama server. Free, local, unlimited."""
    import urllib.request
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},   # deterministic single pass
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data.get("response", "")


def _call_openrouter(prompt: str,
                     model: str = "meta-llama/llama-3.1-8b-instruct:free") -> str:
    """Call OpenRouter free-tier model. Needs OPENROUTER_API_KEY."""
    import urllib.request
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY environment variable.")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _call_huggingface(prompt: str,
                      model: str = "mistralai/Mistral-7B-Instruct-v0.3") -> str:
    """Call HuggingFace Inference API free tier. Needs HF_TOKEN."""
    import urllib.request
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("Set HF_TOKEN environment variable.")
    payload = json.dumps({
        "inputs": prompt,
        "parameters": {"temperature": 0.01, "max_new_tokens": 200,
                       "return_full_text": False},
    }).encode()
    req = urllib.request.Request(
        f"https://api-inference.huggingface.co/models/{model}",
        data=payload,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    if isinstance(data, list):
        return data[0].get("generated_text", "")
    return str(data)


def _call_mock(prompt: str, model: str = "mock") -> str:
    """
    Deterministic offline backend for pipeline testing (no network needed).
    Produces a plausible score by crude keyword counting + a small, FIXED
    perturbation keyed on demographic-signal substrings — so the bias-scoring
    stage has non-trivial variance to detect during local dry-runs.
    NOT a real model. Replace with ollama/openrouter/huggingface for real results.
    """
    cv = prompt.split("CV:")[-1].lower()
    base = 55
    for kw in ["dcf", "lbo", "bloomberg", "python", "m&a", "2:1", "modelling"]:
        if kw in cv:
            base += 4
    # Fixed, transparent perturbations to exercise the bias detector downstream.
    # (These are deliberate test fixtures, not a claim about real model behaviour.)
    if "career break" in cv:
        base -= 8
    if "part-time" in cv:
        base -= 3
    if "apprenticeship" in cv:
        base -= 2
    return json.dumps({"score": max(0, min(100, base)),
                       "reasoning": "mock deterministic score for offline testing"})


_BACKENDS = {
    "ollama":      _call_ollama,
    "openrouter":  _call_openrouter,
    "huggingface": _call_huggingface,
    "mock":        _call_mock,
}


# ──────────────────────────────────────────────────────────────
# SCREENER
# ──────────────────────────────────────────────────────────────

class LLMJudgeScreener:
    def __init__(self, job_description: dict,
                 backend: str = "ollama",
                 model: Optional[str] = None):
        if backend not in _BACKENDS:
            raise ValueError(f"backend must be one of {list(_BACKENDS)}")
        self.jd = job_description
        self.backend = backend
        self.model = model
        self.call_fn = _BACKENDS[backend]
        self._token_log = []   # records approx tokens per call

    def _invoke(self, prompt: str) -> str:
        kwargs = {"model": self.model} if self.model else {}
        return self.call_fn(prompt, **kwargs)

    @staticmethod
    def _parse(raw: str) -> dict:
        """Extract the JSON object from the model's raw text response."""
        # Find the first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {"score": None, "reasoning": f"PARSE_FAIL: {raw[:120]}"}
        try:
            obj = json.loads(match.group(0))
            score = obj.get("score")
            if isinstance(score, (int, float)):
                score = max(0, min(100, float(score)))
            return {"score": score, "reasoning": obj.get("reasoning", "")}
        except json.JSONDecodeError:
            return {"score": None, "reasoning": f"JSON_ERROR: {raw[:120]}"}

    def score_with_detail(self, cv_text: str) -> dict:
        prompt = build_prompt(self.jd, cv_text)
        approx_in = len(prompt) // 4      # rough token estimate
        t0 = time.time()
        raw = self._invoke(prompt)
        dt = round(time.time() - t0, 2)
        approx_out = len(raw) // 4
        self._token_log.append({"in": approx_in, "out": approx_out})
        parsed = self._parse(raw)
        judge = self.model or "default"
        return {
            "model":       f"C_llm_judge_{self.backend}_{judge}",
            "score":       parsed["score"],
            "reasoning":   parsed["reasoning"],
            "tokens_in":   approx_in,
            "tokens_out":  approx_out,
            "latency_s":   dt,
        }

    def score(self, cv_text: str) -> float:
        return self.score_with_detail(cv_text)["score"]

    def token_summary(self) -> dict:
        if not self._token_log:
            return {}
        tin = sum(t["in"] for t in self._token_log)
        tout = sum(t["out"] for t in self._token_log)
        return {"calls": len(self._token_log), "total_in": tin,
                "total_out": tout, "total": tin + tout}


if __name__ == "__main__":
    import json as _json
    from pathlib import Path

    ROOT = Path(__file__).parent.parent
    with open(ROOT / "data" / "job_description.json") as f:
        jd = _json.load(f)

    # Default to Ollama (free, local). Change backend as needed.
    backend = os.environ.get("MERIDIAN_BACKEND", "ollama")
    print(f"Model C (LLM judge) — backend: {backend}\n")
    print("NOTE: requires the chosen backend to be running/configured.")
    print("  ollama:     start Ollama + `ollama pull llama3.1:8b`")
    print("  openrouter: set OPENROUTER_API_KEY (use a :free model)")
    print("  huggingface:set HF_TOKEN\n")

    # Print the assembled prompt so you can inspect it without a backend:
    with open(ROOT / "data" / "cvs" / "pairs" / "name.json") as f:
        cvs = _json.load(f)
    print("=" * 60)
    print("SAMPLE ASSEMBLED PROMPT (first CV):")
    print("=" * 60)
    print(build_prompt(jd, cvs[0]["cv_text"]))
