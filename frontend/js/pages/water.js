// Water balance & quality

import { api } from "../api.js";
import { esc, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let balance = [], quality = [];
  try { balance = await api.get(`/farms/${farmId}/water-balance`); } catch {}
  try { quality = await api.get(`/farms/${farmId}/water-quality`); } catch {}

  return `
  <h2 style="margin:0 0 4px">Water balance & quality</h2>
  <section class="card mb">
    <h3>Farm water balance</h3>
    ${balance.length ? balance.map((b) => `
      <div class="card mb"><div class="row space-between"><b>${esc(b.zone_name || b.zone || "")}</b> <span class="small muted">${fmtDate(b.date)}</span></div>
      <div class="grid grid-3">
        <div class="kpi"><div class="kpi-label">Input</div><div class="kpi-value">${fmtNum(b.input_mm, 1)} mm</div></div>
        <div class="kpi"><div class="kpi-label">ETc</div><div class="kpi-value">${fmtNum(b.etc_mm, 1)} mm</div></div>
        <div class="kpi"><div class="kpi-label">Drainage</div><div class="kpi-value">${fmtNum(b.drainage_mm, 1)} mm</div></div>
      </div>
      <div class="small muted mt">Status: ${pill(b.status || "normal", b.status || "")} · Balance: ${fmtNum(b.balance_mm, 1)} mm</div></div>`).join("") : '<div class="empty">No balance data</div>'}
  </section>
  <section class="card">
    <h3>Water quality</h3>
    ${quality.length ? `<table class="data"><thead><tr><th>Source</th><th>EC (dS/m)</th><th>SAR</th><th>pH</th><th>Status</th></tr></thead>
    <tbody>${quality.map((q) => `<tr><td>${esc(q.source || "")}</td><td>${fmtNum(q.ec, 2)}</td><td>${fmtNum(q.sar, 2)}</td><td>${fmtNum(q.ph, 1)}</td><td>${pill(q.status || "ok", q.status || "")}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No quality data</div>'}
  </section>`;
};

export const mount = () => {};