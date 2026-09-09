// Irrigation planner + zone schedule/events

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async (paramsOrOpts) => {
  const params = typeof paramsOrOpts === "object" && paramsOrOpts !== null ? (paramsOrOpts.params || paramsOrOpts) : {};
  const sub = params.sub || "";
  if (sub === "schedule") return schedulePage();
  if (sub === "events") return eventsPage();
  return mainIrrigationPage();
};

export const mount = () => {
  document.getElementById("gen-rec-btn")?.addEventListener("click", async () => {
    const zid = document.getElementById("irr-zone-select").value;
    const el = document.getElementById("rec-result");
    el.innerHTML = '<div class="loading">Computing…</div>';
    try {
      const r = await api.post("/irrigation/recommendation", { zone_id: Number(zid), level: "zone" });
      el.innerHTML = `<div class="card explain-card"><div class="row space-between"><b>${esc(r.zone_name || "")}</b> ${pill(r.status || "draft", r.status || "draft")}</div>
        <div class="small">${esc((r.recommendation && r.recommendation.text) || (r.why || r.rationale || "")).slice(0, 160)}…</div>
        <div class="small muted mt">${fmtNum(r.volume_m3 || 0, 2)} m³ · ${fmtNum(r.duration_min || 0, 0)} min · ETo ${fmtNum(r.eto_mm, 1)} mm</div>
        ${r.assumptions ? `<div class="small muted mt">${esc(r.assumptions.slice(0, 140))}…</div>` : ""}</div>`;
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
  document.getElementById("sch-btn")?.addEventListener("click", async () => {
    const zid = document.getElementById("sch-zone").value;
    const el = document.getElementById("sch-detail");
    el.innerHTML = '<div class="loading">Loading…</div>';
    try {
      const [recs, events] = await Promise.all([
        api.get(`/irrigation/zones/${zid}/recommendations`).catch(() => []),
        api.get(`/irrigation/zones/${zid}/events`).catch(() => []),
      ]);
      const latest = recs && recs[0];
      el.innerHTML = latest ? `
        <div class="card"><b>Latest rec (${fmtDate(latest.generated_at)})</b><div class="small">${esc((latest.rationale || latest.text || "").slice(0, 160))}…</div>
        <div class="small muted mt">${fmtNum(latest.irrigation_volume_m3 || 0, 2)} m³ · ${fmtNum(latest.duration_min || 0, 0)} min · ${fmtNum(latest.frequency_days, 1)} days</div>
        <div class="hstack mt"><a class="btn secondary" href="#/irrigation/schedule">Approved schedule →</a></div></div>
        <div class="card mt"><h4>Events</h4>${events.length ? events.map((e) => `<div class="row space-between small"><span>${esc(e.type)}</span><span class="small muted">${fmtDate(e.irrigated_at || e.created_at)}</span></div>`).join("") : '<div class="empty">No events</div>'}</div>`
        : '<div class="empty">No recommendation for this zone yet.</div>';
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
};

async function mainIrrigationPage() {
  const mapData = await api.get(`/farms/${farmId}/map`).catch(() => null);
  const zoneList = [];
  if (mapData) mapData.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zoneList.push({ id: z.id, name: z.name, block: b.name }))));
  let schedule = [];
  try { schedule = await api.get("/irrigation/schedule"); } catch {}
  return `
  <h2 style="margin:0 0 4px">Irrigation planner</h2>
  <div class="muted small mb">ET₀-driven scheduling · farm ${farmId}</div>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Approved schedule</h3>
      ${schedule.length ? `<table class="data"><thead><tr><th>Zone</th><th>Volume (m³)</th><th>Duration (min)</th><th>Freq (days)</th><th>Generated</th></tr></thead>
      <tbody>${schedule.map((s) => `<tr><td>${esc(s.zone_name)}</td><td>${fmtNum(s.volume_m3, 2)}</td><td>${fmtNum(s.duration_min, 0)}</td><td>${s.frequency_days}</td><td class="small muted">${fmtDate(s.generated_at)}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No approved schedule yet. Generate a recommendation per zone.</div>'}
    </section>
    <section class="card">
      <h3>Quick apply</h3>
      <p class="small muted">Select a zone to generate an irrigation recommendation.</p>
      <select id="irr-zone-select" class="input">
        ${zoneList.map((z) => `<option value="${z.id}">${esc(z.name)} (${esc(z.block)})</option>`).join("")}
      </select>
      <button class="btn mt" id="gen-rec-btn">Generate recommendation</button>
      <div id="rec-result" class="mt"></div>
    </section>
  </div>
  ${zoneList.length ? `<div class="card"><h3>Zone detail</h3>
    <div class="hstack"><select id="sch-zone" class="input">${zoneList.map((z) => `<option value="${z.id}">${esc(z.name)}</option>`).join("")}</select>
    <button class="btn secondary" id="sch-btn">Load zone</button></div>
    <div id="sch-detail" class="mt"></div></div>` : ""}
  <div class="card mt"><h3>Upcoming events</h3><a class="btn secondary" href="#/irrigation/events">View all →</a></div>`;
}

async function schedulePage() {
  let schedule = [];
  try { schedule = await api.get("/irrigation/schedule"); } catch {}
  return `
  <h2 style="margin:0 0 4px">Approved schedule</h2>
  <div class="card">
    ${schedule.length ? `<table class="data"><thead><tr><th>Zone</th><th>Volume (m³)</th><th>Duration (min)</th><th>Freq (days)</th><th>Generated</th></tr></thead>
    <tbody>${schedule.map((s) => `<tr><td>${esc(s.zone_name)}</td><td>${fmtNum(s.volume_m3, 2)}</td><td>${fmtNum(s.duration_min, 0)}</td><td>${s.frequency_days}</td><td class="small muted">${fmtDate(s.generated_at)}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No approved schedule.</div>'}
  </div>`;
}

async function eventsPage() {
  const mapData = await api.get(`/farms/${farmId}/map`).catch(() => null);
  const zoneList = [];
  if (mapData) mapData.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zoneList.push({ id: z.id, name: z.name }))));
  let events = [];
  for (const z of zoneList.slice(0, 5)) {
    try { const e = await api.get(`/irrigation/zones/${z.id}/events`); if (e && e.length) events = events.concat(e); } catch {}
  }
  events.sort((a, b) => new Date(b.irrigated_at || b.created_at) - new Date(a.irrigated_at || a.created_at));
  return `
  <h2 style="margin:0 0 4px">Irrigation events</h2>
  <div class="card"><table class="data"><thead><tr><th>Zone</th><th>Event</th><th>Time</th><th>Details</th></tr></thead>
  <tbody>${events.slice(0, 30).map((e) => `<tr><td>${esc(e.zone_name || zoneList.find((z) => z.id === e.zone_id)?.name || "")}</td><td>${esc(e.type || "")}</td><td class="small muted">${fmtDate(e.irrigated_at || e.created_at)}</td><td class="small">${esc(e.note || "")}</td></tr>`).join("")}</tbody></table></div>`;
}