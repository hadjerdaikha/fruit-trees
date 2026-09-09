// Climate risks page

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let risks = [], hist = [];
  try { risks = await api.get(`/farms/${farmId}/weather/climate-risks`); } catch {}
  try { hist = await api.get(`/farms/${farmId}/weather/history`); } catch {}
  const riskList = risks.risks || risks || [];

  return `
  <h2 style="margin:0 0 4px">Climate risks</h2>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Active risks</h3>
      ${riskList.length ? `<ul class="vstack">${riskList.map((r) => `
        <li class="card mb"><div class="row space-between"><b>${esc(r.type)}</b> ${pill(r.level, r.level)}</div>
        <div class="small">${esc(r.detail)}</div>
        <div class="small muted mt">Timing: ${fmtDate(r.timing)}</div>
        ${r.actions ? `<div class="small mt"><b>Actions:</b> ${esc(r.actions)}</div>` : ""}</li>`).join("")}</ul>` : '<div class="empty">No active climate risks</div>'}
    </section>
    <section class="card">
      <h3>Farm weather summary</h3>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">Max temp</div><div class="kpi-value" style="color:#e8890c">—</div></div>
        <div class="kpi"><div class="kpi-label">Min temp</div><div class="kpi-value">—</div></div>
        <div class="kpi"><div class="kpi-label">Humidity</div><div class="kpi-value">—</div></div>
        <div class="kpi"><div class="kpi-label">Wind</div><div class="kpi-value">—</div></div>
      </div>
      <div class="small muted mt">Forecast source: Open-Meteo (auto-synced)</div>
    </section>
  </div>
  ${hist.length ? `<section class="card"><h3>Recent history</h3><table class="data"><thead><tr><th>Date</th><th>Temp max</th><th>Temp min</th><th>Precip</th><th>Notes</th></tr></thead>
  <tbody>${hist.slice(0, 14).map((h) => `<tr><td>${fmtDate(h.date)}</td><td>${fmtNum(h.temp_max)} °C</td><td>${fmtNum(h.temp_min)} °C</td><td>${fmtNum(h.precip_mm, 1)} mm</td><td class="small">${esc(h.note || "")}</td></tr>`).join("")}</tbody></table></section>` : ""}`;
};

export const mount = () => {};