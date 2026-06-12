"use client";
import {
  BarChart, Bar, XAxis, YAxis, ReferenceLine, Cell, Tooltip, ResponsiveContainer,
} from "recharts";

// Renders one model×dimension cell: each group's mean-rank delta vs chance.
// Negative = ranked better than chance (favoured); positive = penalised.
export default function DimensionChart({ selection }) {
  if (!selection) {
    return <p className="hint" style={{ fontSize: 13 }}>Select a cell above to see the per-group breakdown.</p>;
  }
  const { model, dim, cell } = selection;
  const data = Object.entries(cell.groups || {})
    .map(([group, m]) => ({
      group: group.replace(/_/g, " "),
      delta: m.delta_vs_chance,
      sig: m.significant,
      p: m.p_holm,
    }))
    .sort((a, b) => a.delta - b.delta);

  const danger = "var(--danger)";
  const info = "var(--info)";

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>
        {dim.replace("_", " ")} · {model}
        <span style={{ color: cell.any_significant ? danger : "var(--success)", fontSize: 12 }}>
          {cell.any_significant ? " · bias detected" : " · no detectable bias"}
        </span>
      </div>
      <div style={{ fontSize: 12, color: "var(--hint)", marginBottom: 10 }}>
        mean rank vs chance — identical merit, only this signal differs (baseline: {cell.baseline})
      </div>
      <div style={{ width: "100%", height: Math.max(120, data.length * 34) }}>
        <ResponsiveContainer>
          <BarChart layout="vertical" data={data} margin={{ left: 8, right: 24 }}>
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="group" width={120} tick={{ fontSize: 11 }} />
            <ReferenceLine x={0} stroke="var(--border-strong)" />
            <Tooltip formatter={(v, n, p) =>
              [`${v > 0 ? "+" : ""}${v}  (Holm p=${p.payload.p}${p.payload.sig ? ", significant" : ""})`, "Δ vs chance"]} />
            <Bar dataKey="delta">
              {data.map((d, i) => (
                <Cell key={i} fill={d.delta > 0 ? danger : info} fillOpacity={d.sig ? 1 : 0.45} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--hint)", marginTop: 6 }}>
        <span><Dot c={info} /> favoured</span>
        <span><Dot c={danger} /> penalised</span>
        <span>solid = significant (Holm)</span>
      </div>
    </div>
  );
}

function Dot({ c }) {
  return <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: c, verticalAlign: 1 }} />;
}
