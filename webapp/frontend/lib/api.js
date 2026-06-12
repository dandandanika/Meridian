// Thin client for the FastAPI backend (default http://localhost:8000).
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getModels() {
  const r = await fetch(`${BASE}/api/models`);
  if (!r.ok) throw new Error("could not reach backend");
  return r.json();
}

export async function startAudit(config) {
  const r = await fetch(`${BASE}/api/audits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!r.ok) throw new Error("failed to start audit");
  return r.json(); // { job_id, status }
}

export async function getAudit(jobId) {
  const r = await fetch(`${BASE}/api/audits/${jobId}`);
  if (!r.ok) throw new Error("job not found");
  return r.json(); // { status, progress, error, result? }
}

export async function getRegistry() {
  const r = await fetch(`${BASE}/api/registry`);
  if (!r.ok) throw new Error("could not reach backend");
  return r.json(); // { profiles: [...] }
}

export const DIMENSIONS = ["name", "address", "education", "career_gap"];
