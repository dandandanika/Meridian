"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SAMPLE = `James Wilson
14 Eaton Square, London SW1W 9BH

EDUCATION
University of Birmingham — BSc Economics, 2:1

WORK EXPERIENCE
Investment Banking Summer Analyst, Global Investment Bank (London)
Built DCF/LBO models, prepared pitch books, Bloomberg research.

SKILLS
Python, Excel, Bloomberg Terminal, SQL, financial modelling.`;

export default function TestCV() {
  const [cv, setCv] = useState(SAMPLE);
  const [name, setName] = useState("");
  const [backend, setBackend] = useState("mock");
  const [trials, setTrials] = useState(20);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);
  const [backends, setBackends] = useState(["mock"]);

  useEffect(() => {
    fetch(`${API}/api/models`).then((r) => r.json())
      .then((d) => setBackends(d.backends || ["mock"]))
      .catch(() => setErr("Backend not reachable on :8000."));
  }, []);

  async function run() {
    setErr(null); setRes(null); setBusy(true);
    try {
      const r = await fetch(`${API}/api/cv/score`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_text: cv, name: name || null, backend, trials: Number(trials) }),
      });
      if (!r.ok) throw new Error((await r.json()).detail || "request failed");
      setRes(await r.json());
    } catch (e) { setErr(String(e.message || e)); }
    setBusy(false);
  }

  const cf = res?.counterfactual;
  const worst = cf ? Math.max(...cf.variants.map((v) => v.mean_rank)) : 1;

  return (
    <div>
      <h1>Test a CV</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        Score one CV, then see which demographic version of it the model prefers — same CV, only the name changes.
      </p>
      {err && <div className="card" style={{ color: "var(--danger)" }}>{err}</div>}

      <p className="step">1 · Your CV</p>
      <div className="card">
        <textarea rows={10} value={cv} onChange={(e) => setCv(e.target.value)} style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 13 }} />
        <div className="grid2" style={{ marginTop: 12 }}>
          <label className="field">Candidate name <span className="hint">(blank = first line)</span>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="James Wilson" />
          </label>
          <label className="field">Inference backend
            <select value={backend} onChange={(e) => setBackend(e.target.value)}>
              {backends.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </label>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "12px 0 0" }}>
          <label className="field" style={{ minWidth: 42 }}>Trials</label>
          <input type="range" min="10" max="40" step="5" value={trials} onChange={(e) => setTrials(e.target.value)} style={{ flex: 1 }} />
          <span style={{ fontSize: 14, fontWeight: 500 }}>{trials}</span>
        </div>
        <button className="primary" onClick={run} disabled={busy}>{busy ? "Scoring…" : "▶ Score & test"}</button>
      </div>

      {res && (
        <>
          <p className="step">2 · Base scores</p>
          <div className="card">
            <div style={{ display: "flex", gap: 24 }}>
              <Metric label="Keyword (TF-IDF)" value={res.base_scores.keyword} />
              <Metric label="LLM judge" value={res.base_scores.judge} />
            </div>
            <p className="hint" style={{ fontSize: 12, marginBottom: 0 }}>Scored as “{res.base_name}”. Base scores are context; the bias shows up in the ranking below.</p>
          </div>

          <p className="step">3 · Which version of your CV does the model prefer?</p>
          <div className="card">
            <p className="hint" style={{ fontSize: 12, marginTop: 0 }}>
              Same CV, name swapped across {cf.n} demographic groups, ranked over {cf.trials} shuffled trials. Lower mean rank = preferred. Chance = {cf.chance_rank}.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              {cf.variants.map((v, i) => (
                <div key={v.group} style={{ display: "grid", gridTemplateColumns: "150px 1fr 92px", alignItems: "center", gap: 10, fontSize: 12 }}>
                  <div><span style={{ fontWeight: 500 }}>{v.name}</span><br /><span className="hint">{v.group.replace(/_/g, " ")}</span></div>
                  <div style={{ position: "relative", height: 16, background: "var(--surface)", borderRadius: 3 }}>
                    <div style={{ position: "absolute", left: 0, top: 2, bottom: 2, width: `${Math.round((1 - (v.mean_rank - 1) / (worst - 1 || 1)) * 100)}%`, background: i === 0 ? "var(--info)" : "var(--border-strong)", borderRadius: 2 }} />
                  </div>
                  <div className="muted" style={{ textAlign: "right" }}>rank {v.mean_rank} · {Math.round(v.selection_rate * 100)}%</div>
                </div>
              ))}
            </div>
            <p className="hint" style={{ fontSize: 12, marginBottom: 0, marginTop: 10 }}>
              Keyword score is identical across names ({res.base_scores.keyword ?? "—"}) — TF-IDF is name-blind. Divergence here is the LLM ranker’s name preference for your CV.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div style={{ background: "var(--surface)", borderRadius: "var(--radius)", padding: "12px 16px", minWidth: 130 }}>
      <div className="muted" style={{ fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 500 }}>{value == null ? "—" : value}</div>
    </div>
  );
}
