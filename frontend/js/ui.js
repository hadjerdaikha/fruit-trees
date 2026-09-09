// Shared UI helpers: status pills, cards, modals, toasts, formatting

export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function pill(level, label) {
  return `<span class="pill ${esc(level)}">${esc(label ?? level)}</span>`;
}

export function dot(level) {
  const cls = { ok: "ok", normal: "ok", green: "ok", warning: "warn", yellow: "warn",
    high: "high", high_risk: "high", orange: "high", critical: "crit", red: "crit",
    insufficient_data: "gray", gray: "gray" }[level] || "gray";
  return `<span class="dot ${cls}"></span>`;
}

export function severityPill(sev) {
  const map = { critical: "critical", high: "high", high_risk: "high", medium: "medium", warning: "warning", low: "ok", ok: "ok", normal: "ok" };
  return pill(map[sev] || "info", sev);
}

export function cards(items) {
  // items: [{label, value, sub, tone}]
  return `<div class="grid grid-4 mb">` + items.map((i) => `
    <div class="card kpi">
      <div class="kpi-label">${esc(i.label)}</div>
      <div class="kpi-value" style="color:${i.color || "inherit"}">${esc(i.value ?? "—")}</div>
      ${i.sub ? `<div class="kpi-sub">${esc(i.sub)}</div>` : ""}
    </div>`).join("") + `</div>`;
}

export function card(title, bodyHtml, extraClass = "") {
  return `<section class="card ${extraClass} mb"><h3>${esc(title)}</h3>${bodyHtml}</section>`;
}

export function explainCard(data) {
  // data: {what, why, dataused, action, urgency, confidence, verify}
  const f = (k, v) => `<div class="fld"><div class="fld-k">${esc(k)}</div><div class="fld-v">${v}</div></div>`;
  return `
  <div class="card explain-card mb">
    <h3>Recommendation — explainability</h3>
    <div class="explain-grid">
      ${f("What was detected", esc(data.what ?? ""))}
      ${f("Why it matters", esc(data.why ?? ""))}
      ${f("Data used", esc(data.dataused ?? ""))}
      ${f("Recommended action", esc(data.action ?? ""))}
      ${f("Urgency", severityPill(data.urgency))}
      ${f("Confidence", confidencePill(data.confidence))}
    </div>
    ${data.verify ? `<div class="banner warn mt"><strong>Verify before acting:</strong> ${esc(data.verify)}</div>` : ""}
    ${data.assumptions && data.assumptions.length ? `<div class="small muted mt"><strong>Assumptions:</strong><ul>${data.assumptions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>` : ""}
  </div>`;
}

export function confidencePill(level) {
  const map = { high: "ok", medium: "warning", low: "high" };
  return pill(map[level] || "info", level);
}

export function table(headers, rows) {
  if (!rows || !rows.length) return '<div class="empty">No data yet</div>';
  return `<table class="data"><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
  <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

export function toast(message, type = "info", ms = 4200) {
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.textContent = message;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), ms);
}

export function openModal(html) {
  const root = document.getElementById("modal-root");
  root.innerHTML = `<div class="modal-overlay" data-close><div class="modal">${html}</div></div>`;
  root.querySelector("[data-close]").addEventListener("click", (e) => {
    if (e.target === e.currentTarget || e.target.closest("[data-modal-close]")) closeModal();
  });
}

export function closeModal() {
  document.getElementById("modal-root").innerHTML = "";
}

export function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d) ? "—" : d.toLocaleString();
}

export function fmtNum(n, digits = 1) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function getStore(key, fallback) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : (fallback !== undefined ? fallback : null);
  } catch { return fallback !== undefined ? fallback : null; }
}

export function setStore(key, val) {
  localStorage.setItem(key, JSON.stringify(val));
}

export function currentUser() {
  return getStore("oasis_user", null);
}

export function roleLabel(role) {
  return (role || "").replace(/^./, (c) => c.toUpperCase());
}

export function can(role, min) {
  const levels = { worker: 1, technician: 2, manager: 3, agronomist: 3, owner: 4, admin: 5 };
  return (levels[role] || 0) >= (levels[min] || 0);
}

export function statusColorFor(level) {
  return { ok: "#2e8b57", normal: "#2e8b57", warning: "#d9a404", high: "#e8890c", high_risk: "#e8890c", critical: "#c62828" }[level] || "#8d9b98";
}