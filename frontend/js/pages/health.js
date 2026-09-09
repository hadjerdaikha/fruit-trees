// Crop health + AI diagnosis entry

import { api } from "../api.js";
import { esc, fmtDate, pill, getStore, toast } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let zones = [], issues = [];
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zones.push({ ...z, block: b.name })))); } catch {}
  issues = [];

  return `
  <h2 style="margin:0 0 4px">Crop health & AI diagnosis</h2>
  <div class="grid grid-2 mb">
    <section class="card">
      <h3>Recent diagnoses</h3>
      ${issues.length ? `<ul class="vstack">${issues.map((d) => `
        <li class="card mb"><div class="row space-between"><b>${esc(d.title)}</b> ${pill(d.severity || "medium", d.severity || "medium")}</div>
        <div class="small">${esc(d.summary || "")}</div>
        <div class="small muted mt">${fmtDate(d.created_at)} · ${esc(d.image_url || "")}</div></li>`).join("")}</ul>` : '<div class="empty">No diagnoses yet</div>'}
      <div class="mt"><a class="btn secondary" href="#/diagnosis/run">New diagnosis →</a></div>
    </section>
    <section class="card">
      <h3>Quick diagnostic</h3>
      <p class="small muted">Upload a canopy photo or describe symptoms to receive a ranked differential diagnosis.</p>
      <label class="fld"><div class="fld-k">Image</div><input type="file" id="diag-image" accept="image/*" /></label>
      <label class="fld"><div class="fld-k">Zone</div><select class="input" id="diag-zone">${zones.map((z) => `<option value="${z.id}">${esc(z.name)}</option>`).join("")}</select></label>
      <button class="btn mt" id="diag-run">Analyze</button>
      <div id="diag-result" class="mt"></div>
    </section>
  </div>
  <section class="card">
    <h3>Health notes</h3>
    <div class="banner"><b>Tip:</b> Inspect canopy for chlorosis, necrosis, and pest signs early in the morning. Record the zone and severity to feed the AI model.</div>
  </section>`;
};

export const mount = () => {
  document.getElementById("diag-run")?.addEventListener("click", async () => {
    const file = document.getElementById("diag-image").files[0];
    const zid = document.getElementById("diag-zone").value;
    const el = document.getElementById("diag-result");
    el.innerHTML = '<div class="loading">Uploading…</div>';
    try {
      const form = new FormData();
      form.append("uploader", "demo");
      form.append("zone_id", zid);
      if (file) form.append("file", file);
      else form.append("file", new Blob([""], { type: "image/png" }));
      const up = await api.upload("/images/upload", form);
      const imgId = up.id;
      const r = await api.post(`/images/${imgId}/analyze`);
      el.innerHTML = `<div class="card"><h4>Diagnosis</h4><p class="small">${esc(r.summary || r.diagnosis || "—")}</p>
        ${r.top_diagnoses ? r.top_diagnoses.map((d) => `<div class="row space-between small mt"><span>${esc(d.name)}</span><span>${fmtNum(d.confidence, 2)}</span></div>`).join("") : ""}</div>`;
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
};

export const runPage = async ({ params }) => {
  // standalone diagnostic page
  const zones = [];
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zones.push({ id: z.id, name: z.name })))); } catch {}
  return `
  <h2>AI diagnosis</h2>
  <section class="card">
    <label class="fld"><div class="fld-k">Upload image</div><input type="file" id="run-image" accept="image/*" /></label>
    <label class="fld"><div class="fld-k">Zone</div><select class="input" id="run-zone">${zones.map((z) => `<option value="${z.id}">${esc(z.name)}</option>`).join("")}</select></label>
    <button class="btn mt" id="run-now">Run diagnosis</button>
    <div id="run-result" class="mt"></div>
  </section>`;
};

export const mountRun = () => {
  document.getElementById("run-now")?.addEventListener("click", async () => {
    const file = document.getElementById("run-image").files[0];
    const zid = document.getElementById("run-zone").value;
    const el = document.getElementById("run-result");
    el.innerHTML = '<div class="loading">Running…</div>';
    try {
      const form = new FormData();
      if (file) form.append("image", file);
      else form.append("image", new Blob([""], { type: "image/png" }));
      const r = await api.upload(`/images/analyze?zone_id=${zid}`, form);
      el.innerHTML = `<div class="card"><h4>Diagnosis</h4><p class="small">${esc(r.summary || r.diagnosis || "—")}</p>
        ${r.top_diagnoses ? r.top_diagnoses.map((d) => `<div class="row space-between small mt"><span>${esc(d.name)}</span><span>${fmtNum(d.confidence, 2)}</span></div>`).join("") : ""}</div>`;
    } catch (e) { el.innerHTML = `<div class="banner crit">${esc(e.message)}</div>`; }
  });
};