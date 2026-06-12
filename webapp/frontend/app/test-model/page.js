"use client";
import { useEffect, useRef, useState } from "react";
import { getModels, startAudit, getAudit } from "../../lib/api";
import VerdictMatrix from "../../components/VerdictMatrix";
import DimensionChart from "../../components/DimensionChart";

export default function TestModel() {
  const [backends, setBackends] = useState(["mock"]);
  const [models, setModels] = useState([]);
  const [backend, setBackend] = useState("mock");
  const [judges, setJudges] = useState([]);
  const [trials, setTrials] = useState(30);
  const [role, setRole] = useState("");
  const [fairness, setFairness] = useState(false);
  const [guardrails, setGuardrails] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("");

  const [job, setJob] = useState(null);     // {status, progress, error, result}
  const [running, setRunning] = useState(false);
  const [selection, setSelection] = useState(null);
  const [err, setErr] = useState(null);
  const poll = useRef(null);

  useEffect(() => {
    getModels()
      .then((d) => { setBackends(d.backends || ["mock"]); setModels(d.models || []); })
      .catch(() => setErr("Backend not reachable. Start it with: uvicorn main:app --port 8000"));
    return () => clearInterval(poll.current);
  }, []);

  function toggleJudge(m) {
    setJudges((j) => (j.includes(m) ? j.filter((x) => x !== m) : [...j, m]));
  }

  async function run() {
    setErr(null); setSelection(null); setJob(null); setRunning(true);
    try {
      const cfg = {
        backend, judges, trials: Number(trials),
        role: role || null,
        guardrails: guardrails ? "Ignore the candidate's name, postcode and the prestige of their institution; judge only on skills, experience and degree class." : null,
        system_prompt: systemPrompt || null,
        fairness,
      };
      const { job_id } = await startAudit(cfg);
      poll.current = setInterval(async () => {
        const s = await getAudit(job_id);
        setJob(s);
        if (s.status === "done" || s.status === "error") {
          clearInterval(poll.current); setRunning(false);
        }
      }, 1500);
    } catch (e) {
      setErr(String(e.message || e)); setRunning(false);
    }
  }

  const result = job && job.status === "done" ? job.result : null;

  return (
    <div>
      <h1>Test a model</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        Audit a model for demographic bias on identical-merit CVs, with significance testing.
      </p>

      {err && <div className="card" style={{ color: "var(--danger)" }}>{err}</div>}

      <p className="step">1 · Configure</p>
      <div className="card">
        <div className="grid2">
          <label className="field">Inference backend
            <select value={backend} onChange={(e) => setBackend(e.target.value)}>
              {backends.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </label>
          <label className="field">Job role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="">Investment banking analyst (default)</option>
              <option value="social_worker">Social worker</option>
            </select>
          </label>
        </div>

        <p className="field" style={{ margin: "14px 0 6px" }}>Models to audit {judges.length === 0 && <span className="hint">(none = backend default)</span>}</p>
        <div className="chips">
          {models.length === 0 && <span className="hint" style={{ fontSize: 12 }}>no models listed — using backend default</span>}
          {models.map((m) => (
            <span key={m} className={"chip" + (judges.includes(m) ? " on" : "")} onClick={() => toggleJudge(m)}>{m}</span>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "16px 0 4px" }}>
          <label className="field" style={{ minWidth: 42 }}>Trials</label>
          <input type="range" min="10" max="50" step="5" value={trials} onChange={(e) => setTrials(e.target.value)} style={{ flex: 1 }} />
          <span style={{ fontSize: 14, fontWeight: 500, minWidth: 24 }}>{trials}</span>
        </div>
        {trials < 30 && <p className="hint" style={{ fontSize: 12, margin: 0 }}>Low trials → name/race effects may be underpowered (reported as "no detectable", not "fair").</p>}

        <details style={{ marginTop: 12 }}>
          <summary style={{ fontSize: 13, color: "var(--info)", cursor: "pointer" }}>Prompt fine-tuning (optional)</summary>
          <div className="card" style={{ marginTop: 8, marginBottom: 0 }}>
            <label style={{ display: "flex", gap: 8, fontSize: 13, marginBottom: 8 }}>
              <input type="checkbox" checked={fairness} onChange={(e) => setFairness(e.target.checked)} /> Add fairness instruction
            </label>
            <label style={{ display: "flex", gap: 8, fontSize: 13, marginBottom: 8 }}>
              <input type="checkbox" checked={guardrails} onChange={(e) => setGuardrails(e.target.checked)} /> Add guardrail (ignore name / postcode / institution)
            </label>
            <label className="field">Custom system prompt
              <textarea rows={2} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} placeholder="You are a bias-aware, merit-only assessor…" />
            </label>
          </div>
        </details>

        <button className="primary" onClick={run} disabled={running}>
          {running ? "Running…" : "▶ Run audit"}
        </button>
      </div>

      {job && (
        <>
          <p className="step">2 · {job.status === "done" ? "Results" : "Progress"}</p>
          <div className="card">
            {job.status !== "done" && (
              <div className="progress">
                {job.status !== "error" && <span className="spinner" />}
                <span>{job.status === "error" ? "Error: " + (job.error || "") : (job.progress || "starting…")}</span>
              </div>
            )}
            {result && (
              <>
                <div className="muted" style={{ fontSize: 13, marginBottom: 12 }}>
                  {result._models.length} model(s) · {result._perms?.toLocaleString?.() || "—"} permutations · α={result._alpha}
                </div>
                <VerdictMatrix result={result} selected={selection} onSelect={setSelection} />
                <div style={{ borderTop: "0.5px solid var(--border)", marginTop: 16, paddingTop: 14 }}>
                  <DimensionChart selection={selection} />
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
