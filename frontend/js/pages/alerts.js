// Alert center — list, summary, acknowledge

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, toast, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async ({ params }) => {
  let list = [], summary = {};
  try { list = await api.get(`/alerts?farm_id=${farmId}&limit=50`); } catch {}
  try { summary = await api.get("/alerts/summary"); } catch {}

const sev = ["critical", "high", "medium", "warning", "low", "ok"];
  const counts = {};
  sev.forEach((s) => counts[s] = 0);
  list.forEach((a) => { if (counts[a.severity] !== undefined) counts[a.severity]++; });

  return `
  <h2 style="margin:0 0 4px">Alert center</h2>
  <div class="grid grid-5 mb">
    ${sev.map((s) => `<div class="card kpi"><div class="kpi-label">${s}</div><div class="kpi-value" style="color:${s === "critical" || s === "high" ? "#c62828" : s === "medium" || s === "warning" ? "#d9a404" : "#2e8b57"}">${counts[s]}</div></div>`).join("")}
  </div>
  <section class="card mb">
    <h3>All alerts <span class="small muted">(${list.length})</span></h3>
    ${list.length ? `<table class="data"><thead><tr><th>Severity</th><th>Type</th><th>Message</th><th>Zone</th><th>Time</th><th>Status</th></tr></thead>
    <tbody>${list.map((a) => `<tr>
      <td>${pill(a.severity, a.severity)}</td>
      <td class="small">${esc(a.alert_type || "")}</td>
      <td class="small">${esc(a.title || a.message || "")}</td>
      <td class="small">${esc(a.zone_id || "")}</td>
      <td class="small muted">${fmtDate(a.created_at)}</td>
      <td>${pill(a.status || "open", a.status || "open")}</td>
    </tr>`).join("")}</tbody></table>` : '<div class="empty">No alerts</div>'}
  </section>
  <div class="hstack mt">
    <button class="btn secondary" id="analyze-alerts">Analyze farm now</button>
    <button class="btn secondary" id="ack-done">Mark open as done</button>
  </div>
  <div id="alert-msg" class="mt"></div>`;
};

export const mount = () => {
  document.getElementById("analyze-alerts")?.addEventListener("click", async () => {
    const btn = document.getElementById("analyze-alerts");
    btn.disabled = true; btn.textContent = "Analyzing…";
    try {
      const r = await api.post(`/alerts/analyze?farm_id=${farmId}`);
      toast("Created " + (r.created || 0) + " alerts");
      location.reload();
    } catch (e) { toast(e.message, "error"); }
    btn.disabled = false; btn.textContent = "Analyze farm now";
  });
  document.getElementById("ack-done")?.addEventListener("click", async () => {
    try {
      await api.post(`/alerts/acknowledge?farm_id=${farmId}`, { status: "done" });
      toast("Acknowledged");
      location.reload();
    } catch (e) { toast(e.message, "error"); }
  });
};