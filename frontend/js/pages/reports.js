// Reports page — exportable farm metrics

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, getStore } from "../ui.js";
import { barChart } from "../chart.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let kpis = [], summary = [];
  try { const d = await api.get(`/farms/${farmId}/dashboard`); kpis = d.kpis || {}; summary = d.zone_status || []; } catch {}

  const vals = Object.values(kpis).map((v) => Number(v));
  const labels = Object.keys(kpis);

  return `
  <h2 style="margin:0 0 4px">Reports</h2>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Farm KPIs</h3>
      ${labels.length ? barChart(labels.map((l) => l.replace(/_/g, " ")), vals.map((v) => Number(v).toFixed(1)), { width: 500, height: 180 }).replace(/<svg /, '<svg ') : '<div class="empty">No KPI data</div>'}
    </section>
    <section class="card">
      <h3>Export</h3>
      <div class="vstack">
        <button class="btn" id="export-kpis">Download KPIs (JSON)</button>
        <button class="btn secondary" id="export-logs">Download audit log (JSON)</button>
        <button class="btn secondary" id="export-farm">Download farm summary (JSON)</button>
      </div>
      <div id="export-result" class="mt"></div>
    </section>
  </div>
  <section class="card">
    <h3>Zone summary</h3>
    <table class="data"><thead><tr><th>Zone</th><th>Status</th><th>Details</th></tr></thead>
    <tbody>${summary.map((z) => `<tr><td>${esc(z.name)}</td><td>${pill(z.status || "normal", z.status || "")}</td><td class="small">${esc(z.message || "")}</td></tr>`).join("")}</tbody></table>
  </section>`;
};

export const mount = () => {
  document.getElementById("export-kpis")?.addEventListener("click", async () => download("kpis"));
  document.getElementById("export-logs")?.addEventListener("click", async () => download("audit-log"));
  document.getElementById("export-farm")?.addEventListener("click", async () => download("farm"));
};

async function download(name) {
  try {
    const url = name === "kpis" ? `/farms/${farmId}/reports/kpis` : name === "audit-log" ? `/audit/logs` : `/farms/${farmId}`;
    const data = await api.get(url);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name + "-" + new Date().toISOString().slice(0, 10) + ".json";
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (e) { toast(e.message, "error"); }
}