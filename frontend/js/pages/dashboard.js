// Dashboard page — Today's priorities, alerts, farm KPIs

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, currentUser, getStore, toast } from "../ui.js";
import { barChart } from "../chart.js";

export const page = async () => {
  const farmId = Number(getStore("oasis_farm_id", 1));
  let dash = {}, alerts = [], tasks = [], weather = {};
  try { dash = await api.get(`/farms/${farmId}/dashboard`); } catch {}
  try { alerts = await api.get(`/alerts?farm_id=${farmId}&limit=8`); } catch {}
  try { tasks = await api.get(`/tasks?farm_id=${farmId}&limit=6`); } catch {}
  try { weather = await api.get(`/farms/${farmId}/weather/climate-risks`); } catch {}

  const p1 = alerts.filter((a) => a.severity === "critical" || a.severity === "high");
  const p2 = alerts.filter((a) => a.severity === "medium" || a.severity === "warning");
  const dueToday = tasks.filter((t) => t.status !== "done");

  const kpis = dash.kpis || {};
  const summary = dash.zone_status || [];
  const vals = Object.values(kpis).map((v) => Number(v).toFixed(1));
  const labels = Object.keys(kpis);

  return `
  <h2 style="margin:0 0 4px">${esc(dash.farm_name || "Dashboard")}</h2>
  <div class="muted small mb">Today · ${new Date().toLocaleDateString()}</div>
  <div class="grid grid-4 mb">
    <div class="card kpi"><div class="kpi-label">Critical alerts</div><div class="kpi-value" style="color:#c62828">${p1.length}</div></div>
    <div class="card kpi"><div class="kpi-label">Warnings</div><div class="kpi-value" style="color:#d9a404">${p2.length}</div></div>
    <div class="card kpi"><div class="kpi-label">Tasks open</div><div class="kpi-value">${dueToday.length}</div></div>
    <div class="card kpi"><div class="kpi-label">Zones</div><div class="kpi-value">${dash.total_zones ?? summary.length}</div></div>
  </div>
  ${labels.length ? `<section class="card mb"><h3>KPIs</h3>${barChart(labels.map((l) => l.replace(/_/g, " ")), vals, { width: 540, height: 160 })}</section>` : ""}
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Alerts queue <span class="small muted">(${alerts.length})</span></h3>
      ${alerts.length ? `<table class="data"><thead><tr><th>Severity</th><th>Alert</th><th>Time</th></tr></thead><tbody>
      ${alerts.map((a) => `<tr><td>${pill(a.severity, a.severity)}</td><td class="small">${esc(a.title)}</td><td class="small muted">${fmtDate(a.created_at)}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No alerts</div>'}
      <div class="mt"><a class="btn secondary" href="#/alerts">View all →</a></div>
    </section>
    <section class="card">
      <h3>Today's priorities</h3>
      ${dueToday.length ? `<ul class="vstack">${dueToday.map((t) => `<li class="row space-between"><span class="small">${esc(t.title)}</span><span class="pill ${t.priority || "medium"}">${t.priority || ""}</span></li>`).join("")}</ul>` : '<div class="empty">No tasks open</div>'}
      <div class="mt"><a class="btn secondary" href="#/tasks">All tasks →</a></div>
    </section>
  </div>
  <div class="grid grid-2">
    <section class="card">${weatherBlock(weather)}</section>
    <section class="card">${zonesBlock(summary)}</section>
  </div>`;
};

export const mount = () => {};

function weatherBlock(w) {
  const r = w.risks || w;
  return `
  <h3 style="margin-top:0">Climate risks</h3>
  ${r.length ? `<ul class="vstack small">${r.map((x) => `<li><b>${esc(x.type)}</b>: ${esc(x.description)} <span class="pill ${x.severity}">${x.severity}</span></li>`).join("")}</ul>` : '<div class="muted small">No active climate risks</div>'}
  <div class="small muted mt">Forecast updated: ${fmtDate(w.updated_at)}</div>`;
}

function zonesBlock(summary) {
  return `
  <h3 style="margin-top:0">Zone status</h3>
  ${summary.length ? `<ul class="vstack small">${summary.map((z) => `<li class="row space-between"><span>${esc(z.zone_name)}</span>${pill(z.salinity_level, z.salinity_level)}<span class="small muted">${z.moisture_pct != null ? z.moisture_pct + "%" : ""}</span></li>`).join("")}</ul>` : '<div class="muted small">No zones</div>'}
  <div class="mt"><a class="btn secondary" href="#/map">Open map →</a></div>`;
}