// Zone detail page

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async ({ params }) => {
  const zid = Number(params.id);
  if (!zid) return `<div class="card"><div class="banner warn">Select a zone</div></div>`;
  let z = null, sal = null, recs = [], tasks = [], irr = null;
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((zz) => { if (zz.id === zid) z = { ...zz, block: b.name, field: f.name }; }))); } catch {}
  try { sal = await api.get(`/zones/${zid}/salinity`); } catch {}
  try { recs = await api.get(`/irrigation/zones/${zid}/recommendations`); } catch {}
  try { tasks = await api.get(`/tasks?zone_id=${zid}`); } catch {}
  try { irr = await api.get(`/farms/${farmId}/water-balance`); } catch {}

  if (!z) return `<div class="card"><div class="banner crit">Zone not found</div></div>`;

  return `
  <h2 style="margin:0 0 4px">Zone ${esc(z.name)}</h2>
  <div class="muted small mb">${esc(z.block)} · ${esc(z.field)}</div>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Profile</h3>
      <div class="vstack small">
        <div><b>Crop:</b> ${esc(z.crop_name || z.crop_species_id || "—")}</div>
        <div><b>Soil texture:</b> ${esc(z.soil_texture || "—")}</div>
        <div><b>Soil EC:</b> ${fmtNum(z.soil_ec_ds_m, 2)} dS/m</div>
        <div><b>Water EC:</b> ${fmtNum(z.water_ec_ds_m, 2)} dS/m</div>
        <div><b>Trees:</b> ${fmtNum(z.trees ? z.trees.length : 0, 0)}</div>
        <div><b>Area:</b> ${fmtNum(z.area_m2, 0)} m²</div>
      </div>
    </section>
    <section class="card">
      <h3>Salinity assessment</h3>
      ${sal ? `
        <div class="row space-between"><b>Level:</b> ${pill(sal.level, sal.level)}</div>
        <div class="small">${esc(sal.message)}</div>
        <div class="small muted mt">Leaching requirement: ${fmtNum(z.leaching_req_mm, 1)} mm</div>
        ${sal.recommendations ? `<div class="small mt">${esc(sal.recommendations)}</div>` : ""}` : '<div class="muted">No data</div>'}
    </section>
  </div>
  <section class="card mb">
    <h3>Irrigation recommendations</h3>
    ${recs && recs.length ? recs.map((r) => `
      <div class="card mb explain-card">
        <div class="row space-between"><b>${esc(r.status || "ok")}</b> <span class="small muted">${fmtDate(r.created_at)}</span></div>
        <div class="small">${esc((r.rationale || "").slice(0, 200))}</div>
        <div class="small muted mt">${fmtNum(r.total_liters || 0, 0)} L · ${fmtNum((r.duration_min || 0) / 60, 1)} h</div>
      </div>`).join("") : '<div class="empty">No recommendations</div>'}
  </section>
  <section class="card mb">
    <h3>Open tasks</h3>
    ${tasks.length ? tasks.map((t) => `<div class="row space-between"><span class="small">${esc(t.title)}</span>${pill(t.priority || "medium", t.priority || "medium")}</div>`).join("") : '<div class="empty">No tasks</div>'}
  </section>
  <div class="hstack mt">
    <a class="btn secondary" href="#/irrigation">Irrigate zone →</a>
    <a class="btn secondary" href="#/diagnosis">Diagnose →</a>
    <a class="btn secondary" href="#/map">Back to map →</a>
  </div>`;
};

export const mount = () => {};