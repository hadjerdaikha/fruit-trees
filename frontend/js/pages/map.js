// Interactive farm map: renders zones from WKT (or synthetic layout) as SVG with status layers.

import { api } from "../api.js";
import { esc, fmtNum, pill, setStore, getStore, toast } from "../ui.js";

const LAYERS = [
  { key: "default", label: "Default", get: () => "normal", color: () => "#8d9b98" },
  { key: "salinity", label: "Soil salinity", get: (z) => z.salinity_level, color: (l) => colorOf(normLevel(l)) },
  { key: "moisture", label: "Soil moisture", get: (z) => moistureLevel(z), color: (l) => colorOf(normLevel(l)) },
  { key: "crop", label: "Crop", get: () => "normal", color: () => "#1d7f63" },
];

function normLevel(l) {
  return { ok: "ok", normal: "ok", high: "high", high_risk: "high", critical: "critical",
    warning: "warning", insufficient_data: "gray", null: "gray" }[l] || "gray";
}
function colorOf(l) { return { ok: "#2e8b57", warning: "#d9a404", high: "#e8890c", critical: "#c62828", gray: "#9aa7a4" }[l] || "#9aa7a4"; }
function moistureLevel(z) {
  if (z.moisture_pct == null) return "insufficient_data";
  return z.moisture_pct < 12 ? "critical" : z.moisture_pct < 15 ? "warning" : "ok";
}

const VIEW = { w: 800, h: 520, pad: 26 };

function wktToPath(wkt) {
  if (!wkt) return null;
  const m = wkt.match(/\(\(([\d\.\-eE,\s]+)\)\)/);
  if (!m) return null;
  const pts = m[1].split(",").map((p) => p.trim().split(/\s+/).map(Number));
  if (pts.length < 3) return null;
  return pts;
}

function syntheticLayout(zone, i, total) {
  const cols = Math.ceil(Math.sqrt(total));
  const col = i % cols, row = Math.floor(i / cols);
  const x0 = col * 3 + Math.sin(i * 7.3) * 0.2;
  const y0 = row * 2.2 + Math.cos(i * 3.1) * 0.2;
  return [[x0, y0], [x0 + 2.4, y0], [x0 + 2.4, y0 + 1.7], [x0, y0 + 1.7]];
}

function project(pts) {
  // normalize + scale into view box, flipping Y (lat up)
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const minx = Math.min(...xs), maxx = Math.max(...xs);
  const miny = Math.min(...ys), maxy = Math.max(...ys);
  const sx = (VIEW.w - VIEW.pad * 2) / (maxx - minx || 1);
  const sy = (VIEW.h - VIEW.pad * 2) / (maxy - miny || 1);
  const s = Math.min(sx, sy);
  const ox = (VIEW.w - (maxx - minx) * s) / 2 - minx * s;
  const oy = (VIEW.h - (maxy - miny) * s) / 2 - miny * s;
  const out = pts.map(([x, y]) => [x * s + ox, VIEW.h - (y * s + oy)]);
  const proj = pts.map(([x, y]) => [x * s + ox, VIEW.h - (y * s + oy)]);
  const cx = proj.reduce((a, p) => a + p[0], 0) / proj.length;
  const cy = proj.reduce((a, p) => a + p[1], 0) / proj.length;
  return { pts: proj, cx, cy };
}

let zonesCache = [];
let curLayer = "default";

let farmId = null;

export const page = async () => {
  const farms = await api.get("/farms");
  const farm = farms.find((f) => f.id === Number(getStore("oasis_farm_id", 1))) || farms[0];
  if (!farm) return `<div class="card"><div class="banner warn">No farms yet. Create a farm from Settings or the API.</div></div>`;
  farmId = farm.id;
  setStore("oasis_farm_id", farm.id);

  const html = `
  <div class="mb row space-between">
    <div><h2 style="margin:0">${esc(farm.name)}</h2>
      <div class="muted small">${esc(farm.climate_zone || "arid")} · ${esc(farm.soil_type || "—")} soil · ${fmtNum(farm.area_m2 / 10000, 1)} ha</div></div>
    <button class="chip-btn" id="pick-farm">⇄ Switch farm</button>
  </div>
  <div class="map-wrap">
    <div class="map-toolbar" id="layer-bar">
      ${LAYERS.map((l) => `<button class="layer-pill ${l.key === "default" ? "active" : ""}" data-layer="${l.key}">${l.label}</button>`).join("")}
    </div>
    <svg id="farm-svg" class="map-canvas" viewBox="0 0 ${VIEW.w} ${VIEW.h}"></svg>
    <div class="map-legend">
      <span><span class="dot ok"></span>Normal</span><span><span class="dot warn"></span>Attention</span>
      <span><span class="dot high"></span>High risk</span><span><span class="dot crit"></span>Urgent</span><span><span class="dot gray"></span>No data</span>
    </div>
    <div class="map-detail hidden" id="zone-detail"></div>
  </div>
  <div id="zone-summary" class="mt"></div>`;
  return html;
};

export const mount = async () => {
  await drawZones();
  bindToolbar();
};

async function loadZones() {
  const data = await api.get(`/farms/${farmId}/map`);
  const zones = [];
  data.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => {
    zones.push({ ...z, blockName: b.name, fieldName: f.name, cropName: cropNameFor(b) });
  })));
  // enrich with dashboard zone_status (has salinity_level, moisture_pct)
  try {
    const dash = await api.get(`/farms/${farmId}/dashboard`);
    const statusMap = {};
    (dash.zone_status || []).forEach((z) => { statusMap[z.zone_id] = z; });
    zones.forEach((z) => { const s = statusMap[z.id]; if (s) { z.salinity_level = s.salinity_level; z.moisture_pct = s.moisture_pct; z.soil_ec = s.soil_ec; } });
  } catch {}
  zonesCache = zones;
  return zones;
}

function cropNameFor(b) {
  return (b.crop_species_id ? "crop#" + b.crop_species_id : "—");
}

async function drawZones() {
  const svg = document.getElementById("farm-svg");
  if (!svg) return;
  const zones = await loadZones();
  const layerConf = LAYERS.find((l) => l.key === curLayer);

  let html = "";
  zones.forEach((z, i) => {
    const pts = wktToPath(z.boundary_wkt) || syntheticLayout(z, i, zones.length);
    const pr = project(pts);
    const level = layerConf.get(z);
    const color = layerConf.color(level);
    const shape = pr.pts.map((p, k) => `${k === 0 ? "M" : "L"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ") + " Z";
    html += `
    <g class="zone-g" data-zone="${z.id}" style="cursor:pointer">
      <path d="${shape}" fill="${color}" fill-opacity="0.5" stroke="#2f4f44" stroke-width="1.6"/>
      <circle cx="${pr.ctx}" cy="${pr.cy}" r="0" fill="none"/>
    </g>`;
  });
  svg.innerHTML = html;

  // zone labels
  zones.forEach((z, i) => {
    const pts = wktToPath(z.boundary_wkt) || syntheticLayout(z, i, zones.length);
    const pr = project(pts);
    const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lbl.setAttribute("x", pr.cx); lbl.setAttribute("y", pr.cy);
    lbl.setAttribute("text-anchor", "middle"); lbl.setAttribute("font-size", "11");
    lbl.setAttribute("font-weight", "700"); lbl.setAttribute("paint-order", "stroke");
    lbl.setAttribute("stroke", "#fff"); lbl.setAttribute("stroke-width", "3");
    lbl.setAttribute("fill", "#22332e");
    lbl.textContent = z.name;
    svg.appendChild(lbl);
  });

  svg.querySelectorAll(".zone-g").forEach((g) => {
    g.addEventListener("click", () => openZoneDetail(Number(g.dataset.zone)));
    const p = g.querySelector("path");
    g.addEventListener("mouseenter", () => p.setAttribute("fill-opacity", "0.85"));
    g.addEventListener("mouseleave", () => p.setAttribute("fill-opacity", "0.5"));
  });

  renderSummary(zones);
}

function renderSummary(zones) {
  const el = document.getElementById("zone-summary");
  const rows = zones.map((z) => `
    <tr>
      <td>${esc(z.name)} <span class="muted small">· ${esc(z.blockName || "")}</span></td>
      <td>${pill(normLevel(z.salinity_level), z.salinity_level)}</td>
      <td>${z.moisture_pct != null ? `${fmtNum(z.moisture_pct, 1)}%` : "—"}</td>
      <td>${fmtNum(z.soil_ec_ds_m, 2)}</td>
      <td><a href="#/zone?id=${z.id}">Details →</a></td>
    </tr>`).join("");
  el.innerHTML = `
    <div class="card">
      <h3>Zones</h3>
      <table class="data"><thead><tr><th>Zone</th><th>Salinity status</th><th>Moisture</th><th>Soil EC (dS/m)</th><th></th></tr></thead>
      <tbody>${rows}</tbody></table>
    </div>`;
}

function bindToolbar() {
  const bar = document.getElementById("layer-bar");
  if (bar) bar.querySelectorAll(".layer-pill").forEach((b) => {
    b.addEventListener("click", async () => {
      curLayer = b.dataset.layer;
      bar.querySelectorAll(".layer-pill").forEach((x) => x.classList.toggle("active", x === b));
      await drawZones();
    });
  });
  const pick = document.getElementById("pick-farm");
  if (pick) pick.addEventListener("click", async () => {
    const farms = await api.get("/farms");
    const opts = farms.map((f) => `<option value="${f.id}">${esc(f.name)}</option>`).join("");
    const { openModal, closeModal } = await import("../ui.js");
    openModal(`<h3>Switch farm</h3><select id="farm-sel">${opts}</select>
      <div class="hstack mt"><button class="btn" id="farm-go">Go</button><button class="btn secondary" data-modal-close>Cancel</button></div>`);
    document.getElementById("farm-go").addEventListener("click", () => {
      setStore("oasis_farm_id", Number(document.getElementById("farm-sel").value));
      closeModal();
      location.hash = "#/map";
    });
  });
}

async function openZoneDetail(zoneId) {
  const detail = document.getElementById("zone-detail");
  detail.classList.remove("hidden");
  detail.innerHTML = `<div class="loading">Loading…</div>`;
  try {
    const z = zonesCache.find((x) => x.id === zoneId) || {};
    let sal = null, latestRec = null, zoneTasks = [];
    try { sal = (await api.get(`/zones/${zoneId}/salinity`)).assessment; } catch {}
    try { const recs = await api.get(`/irrigation/zones/${zoneId}/recommendations`); latestRec = recs[0]; } catch {}
    try { zoneTasks = (await api.get("/tasks")).filter((t) => t.zone_id === zoneId); } catch {}

    detail.innerHTML = `
    <div class="row space-between">
      <h3 style="margin:0">${esc(z.name)}</h3>
      <button class="icon-btn" id="detail-close">✕</button>
    </div>
    <div class="muted small">${esc(z.blockName || "")} · ${esc(z.soil_texture || "soil texture unknown")}</div>
    ${sal ? `<div class="hstack mt">${pill(normLevel(sal.level), sal.level)}<span class="small">${esc(sal.message)}</span></div>` : ""}
    <div class="vstack mt small">
      <div><b>Soil EC:</b> ${fmtNum(z.soil_ec_ds_m, 2)} dS/m</div>
      <div><b>Water EC:</b> ${fmtNum(z.water_ec_ds_m, 2)} dS/m</div>
      <div><b>Trees:</b> ${fmtNum(z.trees ? z.trees.length : 0, 0)}</div>
      ${latestRec ? `<div><b>Irrigation rec:</b> ${esc((latestRec.rationale || "").slice(0, 120))}…</div>` : ""}
    </div>
    <div class="hstack mt">
      <a class="btn secondary" href="#/zone?id=${zoneId}" style="font-size:12.5px">Open details</a>
      <a class="btn secondary" href="#/irrigation" style="font-size:12.5px">Irrigate</a>
    </div>
    ${zoneTasks.length ? `<div class="small muted mt"><b>Tasks:</b> ${zoneTasks.map((x) => esc(x.title)).join(" · ")}</div>` : ""}
    <div class="mt small">
      ${latestRec ? explainBlock(latestRec) : ""}
    </div>`;
    detail.querySelector("#detail-close").addEventListener("click", () => detail.classList.add("hidden"));
  } catch (e) {
    detail.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`;
  }
}

function explainBlock(rec) {
  return `<div style="border-top:1px solid var(--line);padding-top:8px">
    <b>Why this rec:</b><ul style="margin:6px 0;padding-inline-start:18px" class="small">
    ${(rec.rationale || "").split("\n").slice(0, 3).map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
  </div>`;
}