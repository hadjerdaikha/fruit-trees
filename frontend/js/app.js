// Oasis SPA — router and layout shell

import { api } from "./api.js";
import { initLang, setLang, t } from "./i18n.js";
import { currentUser, getStore, roleLabel, toast } from "./ui.js";

import * as loginMod from "./pages/login.js";
import * as dashboardPage from "./pages/dashboard.js";
import * as farmMapPage from "./pages/map.js";
import * as irrigationMod from "./pages/irrigation.js";
import * as soilPage from "./pages/soil.js";
import * as waterPage from "./pages/water.js";
import * as healthPage from "./pages/health.js";
import * as fertilityPage from "./pages/fertigation.js";
import * as climatePage from "./pages/climate.js";
import * as tasksPage from "./pages/tasks.js";
import * as sensorsPage from "./pages/sensors.js";
import * as reportsPage from "./pages/reports.js";
import * as varietyPage from "./pages/variety.js";
import * as alertsPage from "./pages/alerts.js";
import * as zoneDetailPage from "./pages/zone.js";

const NAV = [
  { key: "dashboard", icon: "📊", labelKey: "nav_dashboard" },
  { key: "map", icon: "🗺️", labelKey: "nav_map" },
  { key: "irrigation", icon: "💧", labelKey: "nav_irrigation" },
  { key: "soil", icon: "🟫", labelKey: "nav_soil" },
  { key: "water", icon: "🌊", labelKey: "nav_water" },
  { key: "health", icon: "🌱", labelKey: "nav_health" },
  { key: "diagnosis", icon: "🔬", labelKey: "nav_diagnosis" },
  { key: "fertigation", icon: "🧪", labelKey: "nav_fertigation" },
  { key: "climate", icon: "🌡️", labelKey: "nav_climate" },
  { key: "tasks", icon: "✅", labelKey: "nav_tasks" },
  { key: "alerts", icon: "🚨", labelKey: "nav_alerts" },
  { key: "sensors", icon: "📡", labelKey: "nav_sensors" },
  { key: "variety", icon: "🌿", labelKey: "nav_variety" },
  { key: "reports", icon: "📈", labelKey: "nav_reports" },
];

// Pages export { page(params) -> HTML|Promise<HTML>, mount?(params) -> void }
const ROUTES = {
  dashboard: dashboardPage,
  map: farmMapPage,
  irrigation: irrigationMod,
  "irrigation/schedule": irrigationMod,
  "irrigation/events": irrigationMod,
  soil: soilPage,
  water: waterPage,
  health: healthPage,
  diagnosis: healthPage,
  fertigation: fertilityPage,
  climate: climatePage,
  tasks: tasksPage,
  alerts: alertsPage,
  sensors: sensorsPage,
  variety: varietyPage,
  reports: reportsPage,
  zone: zoneDetailPage,
};

function parseHash() {
  const raw = location.hash.slice(1) || "/dashboard";
  const [path, qs] = raw.split("?");
  const params = {};
  if (qs) for (const kv of qs.split("&")) {
    const [k, v] = kv.split("=");
    params[decodeURIComponent(k)] = decodeURIComponent(v || "");
  }
  const seg = path.split("/").filter(Boolean);
  if (seg.length >= 2) {
    params.sub = seg[1];
    if (seg.length >= 3) params.id = seg.slice(2).join("/");
  }
  return { seg, params, name: seg[0] || "dashboard" };
}

function currentFarmId() {
  return getStore("oasis_farm_id", null);
}

async function buildNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = NAV.map((n) => `
    <a href="#/${n.key}" data-key="${n.key}">
      <span class="nav-icon">${n.icon}</span><span>${t(n.labelKey)}</span>
    </a>`).join("");
}

function setActiveNav(key) {
  document.querySelectorAll("#nav a").forEach((a) => {
    a.classList.toggle("active", a.dataset.key === key);
  });
}

async function listen() {
  window.addEventListener("hashchange", render);
  window.addEventListener("auth:logout", () => showLogin());
  document.getElementById("lang-btn").addEventListener("click", () => {
    const langs = ["en", "ar", "fr"];
    const next = langs[(langs.indexOf(localStorage.getItem("oasis_lang") || "en") + 1) % 3];
    setLang(next);
    render();
  });
  document.getElementById("nav-toggle").addEventListener("click", () => {
    const sb = document.getElementById("sidebar");
    sb.classList.toggle("hidden");
  });
  document.getElementById("alert-bell").addEventListener("click", () => { location.hash = "#/alerts"; });
}

async function refreshBadge() {
  try {
    const s = await api.get("/alerts/summary");
    const badgeEl = document.getElementById("bell-badge");
    const urgent = (s.high || 0) + (s.critical || 0);
    badgeEl.classList.toggle("hidden", !urgent);
    badgeEl.textContent = urgent;
  } catch { /* ignore */ }
}

async function render() {
  const user = currentUser();
  if (!user || !api.token()) { showLogin(); return; }

  if (!getStore("oasis_farm_id")) {
    await setDefaultFarm();
  }

  const { seg, params, name } = parseHash();

  document.getElementById("main-shell").classList.remove("hidden");
  document.getElementById("login-shell").classList.add("hidden");
  document.getElementById("sidebar").classList.remove("hidden");

  const mod = ROUTES[name] || ROUTES.dashboard;
  const content = document.getElementById("content");

  const title = document.querySelector(`#nav a[data-key="${name}"]`);
  document.getElementById("topbar-title").textContent =
    (title ? title.querySelector("span:last-child").textContent : t("nav_dashboard"));

  buildNav(); // re-render for i18n
  setActiveNav(name === "zone" || name === "irrigation/schedule" || name === "irrigation/events" ? name.split("/")[0] : name);

  document.getElementById("user-chip").textContent = user.full_name + " · " + roleLabel(user.role);

  content.innerHTML = `<div class="loading">${t("loading")}</div>`;
    try {
      const html = await mod.page(params || {});
    if (html !== undefined) content.innerHTML = html;
    if (mod.mount) await mod.mount(params);
  } catch (e) {
    console.error(e);
    content.innerHTML = `<div class="card"><div class="banner crit">Error: ${e.message}</div></div>`;
  }
  content.querySelectorAll("[data-nav]").forEach((el) => {
    el.addEventListener("click", (e) => { e.preventDefault(); location.hash = "#/" + el.dataset.nav; });
  });
  refreshBadge();
}

async function setDefaultFarm() {
  try {
    const farms = await api.get("/farms");
    if (farms && farms.length) {
      setStore("oasis_farm_id", farms[0].id);
    }
  } catch {}
}

function showLogin() {
  document.getElementById("main-shell").classList.add("hidden");
  const ls = document.getElementById("login-shell");
  ls.classList.remove("hidden");
  ls.innerHTML = loginMod.page();
  const doLogin = async (email, password) => {
    try {
      const res = await api.post("/auth/login", { email, password });
      api.setToken(res.access_token);
      localStorage.setItem("oasis_user", JSON.stringify(res.user));
      await setDefaultFarm();
      location.hash = "#/dashboard";
      render();
    } catch (err) {
      toast(err.message, "error");
    }
  };
  ls.querySelector("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await doLogin(e.target.email.value, e.target.password.value);
  });
  ls.querySelector("#demo-btn").addEventListener("click", async () => {
    await doLogin("demo@oasis.farm", "demo1234");
  });
  const logoutEl = document.getElementById("sidebar-footer");
  if (logoutEl && !logoutEl.querySelector("#logout-btn")) {
    logoutEl.innerHTML = `<button class="btn secondary" id="logout-btn" style="width:100%">${t("logout")}</button>`;
    logoutEl.querySelector("#logout-btn").addEventListener("click", () => {
      api.clearToken();
      showLogin();
    });
  }
}

initLang();
listen();

const loggedIn = currentUser() && api.token();
if (loggedIn) {
  render();
} else {
  showLogin();
}