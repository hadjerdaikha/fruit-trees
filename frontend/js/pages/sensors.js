// Sensors page — live readings and quality flags

import { api } from "../api.js";
import { esc, fmtDate, fmtNum, pill, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let sensors = [], readings = [];
  try { sensors = await api.get("/sensors"); } catch {}
  try { readings = await api.get(`/sensors/readings?farm_id=${farmId}&limit=30`); } catch {}
  const farmSensors = sensors.filter((s) => s.farm_id === farmId || s.farmId === farmId);
  const recent = readings.filter((r) => r.sensor_id && farmSensors.some((s) => String(s.id) === String(r.sensor_id)));

  return `
  <h2 style="margin:0 0 4px">Sensors</h2>
  <section class="card mb">
    <h3>Registered sensors</h3>
    <table class="data"><thead><tr><th>Code</th><th>Type</th><th>Zone</th><th>Status</th><th>Last heartbeat</th></tr></thead>
    <tbody>${farmSensors.length ? farmSensors.map((s) => `<tr>
      <td><b>${esc(s.sensor_code || s.id)}</b></td><td class="small">${esc(s.sensor_type)}</td>
      <td class="small">${esc(s.zone_id || "—")}</td>
      <td>${pill(s.status || "ok", s.status || "ok")}</td><td class="small muted">${fmtDate(s.last_heartbeat)}</td>
    </tr>`).join("") : '<tr><td colspan="5"><div class="empty">No sensors</div></td></tr>'}</tbody></table>
  </section>
  <section class="card">
    <h3>Recent readings</h3>
    ${recent.length ? `<table class="data"><thead><tr><th>Sensor</th><th>Value</th><th>Unit</th><th>Time</th><th>Quality</th></tr></thead>
    <tbody>${recent.map((r) => `<tr><td class="small">${esc(r.sensor_id || r.sensor_code)}</td><td>${fmtNum(r.value, 2)}</td><td class="small">${esc(r.unit)}</td><td class="small muted">${fmtDate(r.timestamp)}</td><td>${pill(r.quality || "ok", r.quality || "ok")}</td></tr>`).join("")}</tbody></table>` : '<div class="empty">No readings</div>'}
  </section>`;
};

export const mount = () => {};