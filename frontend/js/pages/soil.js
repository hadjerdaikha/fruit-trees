// Soil & salinity dashboard

import { api } from "../api.js";
import { esc, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let zones = [], overview = [];
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zones.push({ ...z, block: b.name })))); } catch {}
  try { overview = await api.get(`/farms/${farmId}/salinity-overview`); } catch {}

  return `
  <h2 style="margin:0 0 4px">Soil & salinity</h2>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Salinity overview</h3>
      ${overview.length ? overview.map((o) => `<div class="row space-between"><span>${esc(o.name || "")}</span>${pill(o.status || "normal", o.status || "")}<span class="small">EC ${fmtNum(o.ec, 2)} dS/m</span></div>`).join("") : '<div class="empty">No overview data</div>'}
      <div class="mt"><a class="btn secondary" href="#/map">Open map →</a></div>
    </section>
    <section class="card">
      <h3>Zone detail</h3>
      ${zones.length ? `<table class="data"><thead><tr><th>Zone</th><th>Soil EC</th><th>Leaching req.</th><th>Status</th></tr></thead>
      <tbody>${zones.map((z) => `<tr><td>${esc(z.name)} <span class="small muted">(${esc(z.block)})</span></td><td>${fmtNum(z.soil_ec_ds_m, 2)}</td><td>${fmtNum(z.leaching_req_mm, 1)} mm</td><td>${pill(z.salinity_level, z.salinity_level)}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No zones</div>'}
    </section>
  </div>
  <section class="card">
    <h3>Salinity risk note</h3>
    <div class="banner warn">High EC in zones increases root stress and reduces infiltration. Maintain leaching fractions per crop and monitor EC after each irrigation event.</div>
    <div class="small muted mt">Reference thresholds vary by crop; see crop-specific guidelines under Variety selector.</div>
  </section>`;
};

export const mount = () => {};