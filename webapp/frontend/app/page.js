"use client";
import { useEffect, useState } from "react";
import { getRegistry, DIMENSIONS } from "../lib/api";

export default function Registry() {
  const [profiles, setProfiles] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    getRegistry()
      .then((d) => setProfiles(d.profiles || []))
      .catch(() => setErr("Backend not reachable. Start it with: uvicorn main:app --port 8000"));
  }, []);

  return (
    <div>
      <h1>Model bias registry</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        Every audited model + config and its bias profile. <a href="/test-model">Run a new audit →</a>
      </p>

      {err && <div className="card" style={{ color: "var(--danger)" }}>{err}</div>}
      {!err && profiles.length === 0 && (
        <div className="card hint">No audits yet. Head to “Test a model” to create the first bias profile.</div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 14 }}>
        {profiles.map((p) => (
          <div key={p.id} className="profile-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h3 title={p.model_label}>{p.model_label.replace("D_llm_rank_", "")}</h3>
              <span className="hint" style={{ fontSize: 11 }}>{p.backend}</span>
            </div>
            <div className="hint" style={{ fontSize: 12, margin: "2px 0 10px" }}>
              {p.params?.trials} trials
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {DIMENSIONS.map((d) => {
                const v = p.verdicts?.[d];
                if (!v) return null;
                return (
                  <span key={d} className={"pill " + (v.bias_detected ? "bad" : "ok")}>
                    {d.replace("_", " ")}
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
