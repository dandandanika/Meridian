"use client";
import { DIMENSIONS } from "../lib/api";

export default function VerdictMatrix({ result, selected, onSelect }) {
  if (!result || !result._models) return null;
  const models = result._models;
  const cols = `1.6fr repeat(${DIMENSIONS.length}, 1fr)`;

  return (
    <div className="matrix" style={{ gridTemplateColumns: cols }}>
      <div />
      {DIMENSIONS.map((d) => (
        <div key={d} className="hint" style={{ fontSize: 12 }}>
          {d.replace("_", " ")}
        </div>
      ))}

      {models.map((m) => (
        <Row key={m} model={m} result={result} selected={selected} onSelect={onSelect} />
      ))}
    </div>
  );
}

function Row({ model, result, selected, onSelect }) {
  const label = (result._model_full && result._model_full[model]) || model;
  const short = label.replace("D_llm_rank_", "").replace(/_default$/, "");
  return (
    <>
      <div style={{ fontSize: 13, fontWeight: 500 }} title={label}>{short}</div>
      {DIMENSIONS.map((d) => {
        const cell = result[model] && result[model][d];
        if (!cell) return <div key={d} className="hint" style={{ fontSize: 11 }}>—</div>;
        const bias = cell.any_significant;
        const isSel = selected && selected.model === model && selected.dim === d;
        return (
          <span
            key={d}
            onClick={() => onSelect({ model, dim: d, cell })}
            className={"pill " + (bias ? "bad" : "ok")}
            style={{ cursor: "pointer", outline: isSel ? "2px solid var(--info)" : "none" }}
          >
            {bias ? "bias" : "clear"}
          </span>
        );
      })}
    </>
  );
}
