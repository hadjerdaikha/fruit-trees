// Fertigation planner — program per zone with safety checks

import { api } from "../api.js";
import { esc, fmtNum, pill, getStore } from "../ui.js";
import { horizontalBars } from "../chart.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let zones = [], program = [];
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zones.push({ ...z, block: b.name })))); } catch {}
  try { program = await api.post("/fertigation/program", { zone_id: 2 }); } catch {}

  const progList = Array.isArray(program) ? program : [];
  return `
  <h2 style="margin:0 0 4px">Fertigation</h2>
  <div class="muted small mb">Per-tree rates with irrigation-coupled safety blocks</div>
  <section class="card mb">
    <h3>Program (latest)</h3>
    ${progList.length ? `<table class="data"><thead><tr><th>Zone</th><th>Crop</th><th>N (g/tree)</th><th>P (g/tree)</th><th>K (g/tree)</th><th>Timing</th><th>Safety</th></tr></thead>
    <tbody>${progList.map((p) => `<tr>
      <td>${esc(p.zone_name || "")}</td><td>${esc(p.crop || "")}</td>
      <td>${fmtNum(p.n_rate_per_tree, 1)}</td><td>${fmtNum(p.p_rate_per_tree, 1)}</td><td>${fmtNum(p.k_rate_per_tree, 1)}</td>
      <td class="small">${fmtDate(p.date)}</td><td>${pill(p.safety_status || "ok", p.safety_status || "ok")}</td>
    </tr>`).join("")}</tbody></table>` : '<div class="empty">No program. Run a fertigation plan.</div>'}
  </section>
  <section class="card">
    <h3>Quick run</h3>
    <select class="input" id="fert-zone">${zones.map((z) => `<option value="${z.id}">${esc(z.name)}</option>`).join("")}</select>
    <div class="hstack mt"><button class="btn" id="fert-run">Generate</button></div>
    <div id="fert-result" class="mt"></div>
  </section>`;
};

export const mount = () => {
  document.getElementById("fert-run")?.addEventListener("click", async () => {
    const zid = document.getElementById("fert-zone").value;
    const el = document.getElementById("fert-result");
    el.innerHTML = '<div class="loading">Computing…</div>';
    try {
      const r = await api.post("/fertigation/program", { zone_id: Number(zid) });
      const items = Array.isArray(r) ? r : (r && r.programs) ? r.programs : [];
      el.innerHTML = items.length ? items.map((p) => `
        <div class="card"><div class="row space-between"><b>${esc(p.zone_name)}</b><span class="pill ${p.safety_status || "ok"}">${p.safety_status || "ok"}</span></div>
        <div class="small muted mt">${(p.note || p.rationale || "").slice(0, 180)}</div></div>`).join("") : '<div class="empty">No recommendations</div>';
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
};