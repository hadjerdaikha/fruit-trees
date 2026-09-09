// Variety selector — recommendations per block

import { api } from "../api.js";
import { esc, fmtNum, pill, currentUser, getStore, toast } from "../ui.js";
import { horizontalBars } from "../chart.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let blocks = [], recs = [];
  try {
    const m = await api.get(`/farms/${farmId}/map`);
    m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => blocks.push({ id: z.id, name: z.name, field: f.name }))));
  } catch {}
  try {
    recs = await api.post("/variety/suitability", {
      max_summer_temp_c: 46, min_winter_temp_c: 12, soil_ec_ds_m: 4.0,
      water_ec_ds_m: 1.2, soil_type: "sandy", market_objective: "dates",
    });
  } catch {}
  const results = recs && recs.results ? recs.results : [];

  return `
  <h2 style="margin:0 0 4px">Variety suitability</h2>
  <div class="muted small mb">Crop–climate–soil match analysis</div>
  <section class="card mb">
    <h3>Suitability scores</h3>
    ${results.length ? results.map((r) => `
      <div class="card mb"><div class="row space-between"><b>${esc(r.variety_name)}</b> <span class="small">${esc(r.species)}</span> <span class="pill ${r.suitability_score > 0.7 ? "ok" : r.suitability_score > 0.4 ? "warning" : "high"}">${fmtNum(r.suitability_score, 2)}</span></div>
      <div class="small muted mt"><b>Strengths:</b> ${esc((r.strengths || []).join(", "))}</div>
      <div class="small muted"><b>Limitations:</b> ${esc((r.limitations || []).join(", "))}</div></div>`).join("") : '<div class="empty">Run variety analysis with conditions.</div>'}
  </section>
  <section class="card">
    <h3>Quick check</h3>
    <p class="small muted">Demo uses arid-summer conditions (max 46 °C, sandy soil, EC 4.0 dS/m).</p>
    <div class="hstack mt"><button class="btn" id="var-refresh">Refresh ranking</button></div>
    <div id="var-refresh-result" class="mt"></div>
  </div>`;
};

export const mount = () => {
  document.getElementById("var-refresh")?.addEventListener("click", async () => {
    const el = document.getElementById("var-refresh-result");
    el.innerHTML = '<div class="loading">Computing…</div>';
    try {
      const r = await api.post("/variety/suitability", {
        max_summer_temp_c: 46, min_winter_temp_c: 12, soil_ec_ds_m: 4.0,
        water_ec_ds_m: 1.2, soil_type: "sandy", market_objective: "dates",
      });
      const res = r && r.results ? r.results.slice(0, 5) : [];
      el.innerHTML = res.length ? horizontalBars(res.map((x) => ({ label: x.variety_name, value: fmtNum(x.suitability_score, 2), color: x.suitability_score > 0.7 ? "#2e8b57" : x.suitability_score > 0.4 ? "#d9a404" : "#c62828" }))) : '<div class="empty">No results</div>';
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
};