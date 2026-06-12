"use client";
import { useState, useRef, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTIONS = [
  "Which model is fairest for an analyst role?",
  "Is the race/name bias real, or just underpowered?",
  "Explain the education bias in plain English.",
];

export default function Assistant() {
  const [msgs, setMsgs] = useState([
    { role: "assistant", content: "Ask me about the bias audit results — I read them from the registry and won't make numbers up." },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef(null);

  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    const history = msgs.filter((m) => m.role !== "system");
    const next = [...msgs, { role: "user", content: q }];
    setMsgs(next); setBusy(true);
    try {
      const r = await fetch(`${API}/api/assistant`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q, history }),
      });
      const d = await r.json();
      setMsgs([...next, { role: "assistant", content: r.ok ? d.reply : `⚠️ ${d.detail || "error"}` }]);
    } catch (e) {
      setMsgs([...next, { role: "assistant", content: "⚠️ Backend not reachable on :8000." }]);
    }
    setBusy(false);
  }

  return (
    <div>
      <h1>Insight assistant</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        A LangGraph agent that interprets the bias results, grounded in the registry.
      </p>

      <div className="card" style={{ minHeight: 320 }}>
        {msgs.map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", margin: "8px 0" }}>
            <div style={{
              maxWidth: "82%", padding: "9px 13px", borderRadius: "var(--radius-lg)", fontSize: 14, whiteSpace: "pre-wrap",
              background: m.role === "user" ? "var(--info-bg)" : "var(--surface)",
              color: m.role === "user" ? "var(--info)" : "var(--text)",
              border: "0.5px solid var(--border)",
            }}>{m.content}</div>
          </div>
        ))}
        {busy && <div className="progress" style={{ margin: "8px 0" }}><span className="spinner" /> thinking…</div>}
        <div ref={end} />
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, margin: "10px 0" }}>
        {SUGGESTIONS.map((s) => (
          <span key={s} className="chip" onClick={() => send(s)}>{s}</span>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask about the results…" style={{ flex: 1 }} />
        <button className="primary" style={{ marginTop: 0 }} onClick={() => send()} disabled={busy}>Send</button>
      </div>
    </div>
  );
}
