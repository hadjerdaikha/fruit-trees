// Algeria planting & tracking guide — regional map + desert crop playbooks (pistachio, mango, saffron).

import { esc, pill } from "../ui.js";
import { OUTLINE, CITIES, svg, W, H } from "../data/algeria.js";

// Longitude/latitude of representative growing provinces per crop.
const ZONES = [
  { name: "High Plateaus (chill confirmed)", lon: 3.26, lat: 34.67, crop: "pistachio", r: 88, color: "#7a9c6d" },
  { name: "Tell Atlas fringe", lon: 1.32, lat: 35.37, crop: "pistachio", r: 45, color: "#7a9c6d" },
  { name: "Constantinois shelf", lon: 6.17, lat: 35.56, crop: "pistachio", r: 55, color: "#7a9c6d" },
  { name: "Sahara oases (irrigated)", lon: 5.32, lat: 31.95, crop: "mango", r: 130, color: "#c98a3d" },
  { name: "Extreme-south oases", lon: -0.29, lat: 27.87, crop: "mango", r: 120, color: "#c98a3d" },
  { name: "Oued Righ basin", lon: 6.87, lat: 33.37, crop: "mango", r: 70, color: "#c98a3d" },
  { name: "Saharian Atlas piedmont", lon: 3.26, lat: 34.67, crop: "saffron", r: 60, color: "#a9746b" },
  { name: "High plateau west", lon: 0.15, lat: 34.83, crop: "saffron", r: 80, color: "#a9746b" },
  { name: "Hoggar highlands", lon: 5.52, lat: 22.79, crop: "saffron", r: 70, color: "#a9746b" },
];

const CROPS = [
  {
    key: "pistachio",
    icon: "🥜",
    name: "Pistachio",
    species: "Pistacia vera",
    ar: "الفستق",
    fr: "Pistachier",
    summary: "High-value nut tree for semi-arid steppes. Long-term investment: enters production in years 4–7, full yield ~10. Tolerates saline soil and water better than most nut crops.",
    regions: "High Plateaus and Saharian Atlas piedmont — Sétif, Batna, Tiaret, M’sila, Djelfa, Tlemcen.",
    climate: ["Chill: 900–1,200 h below 7 °C for steady budbreak", "Heat: 40–46 °C tolerated if irrigated", "Frost: -10 °C dormant; avoid late-spring frost", "Dry hot summers required; humidity risks disease"],
    soil: ["Deep, well-drained sandy–loam or calcareous", "pH 7.0–8.2 (tolerates calcareous)", "Soil EC up to ~4 dS/m acceptable; water EC <2.5 dS/m"],
    water: ["Low water user: ~350–450 L/tree/season", "Deficit irrigation after shell-fill improves split ratio", "Apply 25% in spring, 50% in kernel-fill, 25% pre-harvest"],
    planting: ["Nov–Mar while dormant; grafted saplings", "Spacing 5–7 m; ~200–280 trees/ha", "Need males: 1 pollinator per 8–10 females", "Rootstock: P. atlantica or P. vera"],
    nutrition: ["Moderate N; excess N = vegetative sink", "K supports nut fill and split", "Zn foliar on young leaves", "60% N split pre-flush + post-set"],
    pests: ["Stink bugs, pistachio psylla", "Verticillium, Alternaria in humid pockets", "Stem/root borers near old groves"],
    harvest: ["Sep–Oct when hull splits and kernel crack reveals color", "Shake onto nets; dry thin layer 24–48 h", "Yield: 1.5–3 t/ha mature"],
    timeline: [
      ["Y1–3", "Establishment: form central leader, trunk irrigation, replace casualties"],
      ["Y4–7", "First cropping; alternate-bearing control with pruning + nutrition"],
      ["Y8–12", "Full canopy; manage fruit load, watch boron/zinc"],
      ["12+", "Mature yield; crown renewal pruning in 3-year cycles"],
    ],
    track: ["Soil moisture at 60–90 cm (drip roots)", "EC: soil + irrigation water monthly", "Chill-hour log vs. split rate", "Pest trap counts near harvest", "Task alerts: pruning, foliar, harvest"],
  },
  {
    key: "mango",
    icon: "🥭",
    name: "Mango",
    species: "Mangifera indica",
    ar: "المانجو",
    fr: "Manguier",
    summary: "Tropical fruit that only produces in Algeria in frost-free hot oases (south) with drip irrigation, shade and winter protection. High yield, high water demand, low salt tolerance — site-limited.",
    regions: "Sahara oases with irrigated horticulture: Ouargla, El Oued (Oued Righ), Adrar, Biskra (Ziban).",
    climate: ["No frost ever: damage below 4 °C, kill below -1 °C", "Grows 25–40 °C; flowering after 3–4 dry months", "Requires dry season for flowering, heat for fruit set", "Winter protection needed in marginal winters"],
    soil: ["Deep, loose, well-drained; waterlogging fatal", "pH 5.5–7.0; alkaline/lime causes micronutrient lockup", "Soil EC <1.5 dS/m; water EC <1.0 dS/m — least salt-tolerant here"],
    water: ["High: 1,500–2,000 mm or 20–25 k m³/ha in desert", "Drip with 60–80% canopy wetting", "Critical: flowering panicle stress + fruit-fill weeks", "Cut back 10–15% before flowering to induce bloom"],
    planting: ["Feb–Apr in oasis (after last cold)", "Spacing 8–10 m standard, 5 m dwarfs; ~100–160 trees/ha", "Grafted on polyembryonic rootstock (e.g. Kensington)", "Mulch + wind/shade nets first 2 years"],
    nutrition: ["N+K foundation; K at fruit fill", "Zn, B = routine foliar (alkaline soils deficient)", "No N flush 30 d before flower induction", "Annual leaf analysis at 6–8 months"],
    pests: ["Fruit fly (Bactrocera) — bait + netting", "Anthracnose, powdery mildew during humid spells", "Mango scale, mealybug in dry heat"],
    harvest: ["Jun–Sep depending on variety", "Harvest with stem when Brix ≥ 14 and blush develops", "Hot-water treatment 46–48 °C/60–90 min for fly disinfestation"],
    timeline: [
      ["Y1–3", "Canopy build, structural pruning, no fruit allowed"],
      ["Y4–6", "Light crops; train for balance, monitor Zn/B"],
      ["Y7–10", "Full commercial yield; regulate alternate bearing"],
      ["10+", "Mature grove; canopy management + fruit-grade sorting"],
    ],
    track: ["Air temp min/max — freeze alarm (critical)", "Soil moisture & root-zone EC daily", "Fruit-fly trap thresholds at set-flush", "Leaf nutrient panel yearly", "Brix / heat-unit log for harvest timing"],
  },
  {
    key: "saffron",
    icon: "🌼",
    name: "Saffron",
    species: "Crocus sativus",
    ar: "الزعفران",
    fr: "Safran",
    summary: "The world’s most valuable spice, not a tree — a high-work-input crocus for cold, dry, well-drained highlands. Excellent fit for small plots, high margins, and staggered cash-flow with orchards.",
    regions: "Saharian Atlas piedmont and High Plateaus: Tazoughit (Constantine), Sétif, Saïda, Tiaret, Djelfa, Laghouat.",
    climate: ["Cold winters + hot dry summers required", "Dormant corms tolerate -10 °C in dry soil", "Flowering Oct–Nov stimulated by onset of rain + cool nights", "Too much rain at flowering spikes rot"],
    soil: ["Light, calcareous, free-draining (pH 6.5–8)", "Root-zone EC <4 dS/m", "Sandy-loam that does not waterlog", "New land each cycle (5–7 yr), rotate with legumes"],
    water: ["Low: 4–6 irrigations/cycle, ~3,000–4,000 m³/ha", "Irrigate at planting + after flowering for leaf growth", "Dry period Aug–Sep essential before flowering", "Avoid overhead at bloom"],
    planting: ["Jul–Sep; corms 8–10 cm deep, 10–15 cm spacing", "Plant 1–2 t/ha of corms (30–50/m²)", "Fresh corms from certified multiplier plots", "Lift + grade corms every 4–6 years"],
    nutrition: ["Light organic matter at planting", "Low N; K + P for corm reserves", "Avoid fresh manure near bloom", "Micro-nutrients marginal on calcareous"],
    pests: ["Corm rots (Fusarium), grubs, field mice", "Damping-off in wet cool spell", "Rodents in store"],
    harvest: ["Oct–Nov: pick flowers at dawn daily, 3–4 week window", "150–200 flowers ≈ 100 g fresh → ~20 g dry", "De-stigma same day; dry 50–55 °C 12–15 min", "Yield 1.5–3 kg/ha dried; premium grade market"],
    timeline: [
      ["Aug–Sep", "Corm planting, bed preparation, first irrigations"],
      ["Oct–Nov", "Bloom: daily harvest, stigma extraction, drying"],
      ["Dec–Apr", "Leaf growth, fertilization, weed control"],
      ["May–Jul", "Senescence, corm multiplication, lifting on cycle end"],
    ],
    track: ["Harvest-rate log (kg/ha daily) — bloom forecast", "Rain/irrigation at flowering = rot risk alert", "Corm health & replacement cycle reminders", "Labor scheduling around 3–4 h dawn window", "Moisture at 10–15 cm during bloom window"],
  },
];

function cropChip(cl) {
  const cls = { pistachio: "ok", mango: "warning", saffron: "info" }[cl] || "info";
  return pill(cls, cl);
}

function sectionsHtml(c) {
  const rows = (k, label) => `
    <tr><th class="playbook-th">${esc(label)}</th>
    <td><ul class="playbook-ul">${c[k].map((x) => `<li>${esc(x)}</li>`).join("")}</ul></td></tr>`;
  return `
    <section class="card mb"><h3>${c.icon} ${esc(c.species)} — playbook</h3>
      <p class="small">${esc(c.summary)}</p>
      <div class="muted small mb"><b>Priority regions:</b> ${esc(c.regions)}</div>
      <table class="data playbook-table">
        ${rows("climate", "Climate requirements")}
        ${rows("soil", "Soil & salt")}
        ${rows("water", "Water strategy")}
        ${rows("planting", "Planting")}
        ${rows("nutrition", "Nutrition")}
        ${rows("pests", "Pests & risks")}
        ${rows("harvest", "Harvest")}
      </table>
    </section>
    <section class="card mb"><h3>Timeline & tracking</h3>
      <table class="data"><thead><tr><th>Stage</th><th>Focus</th></tr></thead>
      <tbody>${c.timeline.map(([a, b]) => `<tr><td><b>${esc(a)}</b></td><td>${esc(b)}</td></tr>`).join("")}</tbody></table>
    </section>
    <section class="card"><h3>Track in Oasis</h3>
      <ul class="playbook-ul">${c.track.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
      <a class="btn secondary mt" href="#/algeria">← Back to map</a>
    </section>`;
}

export const page = (paramsOrOpts = {}) => {
  const params = (paramsOrOpts && paramsOrOpts.params) || paramsOrOpts || {};
  const cropKey = params.sub || "all";
  const crop = CROPS.find((c) => c.key === cropKey);
  if (crop) {
    return `
      <h2 style="margin:0 0 4px">${crop.icon} ${esc(crop.name)} · ${esc(crop.fr)}</h2>
      <div class="muted small mb">${esc(crop.ar)} — desert crop playbook for Algerian regions</div>
      ${sectionsHtml(crop)}
    `;
  }
  return `
  <h2 style="margin:0 0 4px">Algeria planting guide</h2>
  <div class="muted small mb">Desert crop playbooks for pistachio, mango and saffron, mapped to Algerian growing regions</div>

  <section class="card mb">
    <div class="row space-between" style="align-items:start">
      <div>
        <h3>Crop suitability map</h3>
        <div class="muted small">Toggle a crop to see its Algerian growing regions. Tap a province for context.</div>
      </div>
      <div class="hstack" id="algeria-layers">
        <button class="chip-btn" data-layer="all" data-map-pill active>All</button>
        <button class="chip-btn" data-layer="pistachio" data-map-pill><span class="dot ok"></span>Pistachio</button>
        <button class="chip-btn" data-layer="mango" data-map-pill><span class="dot warn"></span>Mango</button>
        <button class="chip-btn" data-layer="saffron" data-map-pill><span class="dot crit"></span>Saffron</button>
      </div>
    </div>
    <div class="map-wrap" style="margin-top:12px">
      <svg id="algeria-svg" class="map-canvas" viewBox="0 0 ${W} ${H}"></svg>
      <div class="map-detail hidden" id="algeria-detail"></div>
    </div>
  </section>

  <div class="grid grid-3" id="algeria-guides">
    ${CROPS.map((c) => `
    <section class="card crop-card" data-crop-card="${c.key}">
      <div class="row space-between" style="align-items:center">
        <h3 style="margin:0">${c.icon} ${esc(c.name)}</h3>${cropChip(c.key)}
      </div>
      <div class="muted small mt">${esc(c.species)} · <i>${esc(c.ar)}</i></div>
      <p class="small mt">${esc(c.summary)}</p>
      <div class="small muted"><b>Regions:</b> ${esc(c.regions)}</div>
      <div class="hstack mt"><a class="btn secondary" href="#/algeria/${c.key}" data-guide="${c.key}">Full playbook →</a></div>
    </section>`).join("")}
  </div>

  <section class="card mt">
    <h3>How Oasis supports these crops</h3>
    <div class="grid grid-3 small">
      <div><b>💧 Irrigation engine</b><br>Deficit schedules for pistachio, oasis drip maps for mango, bloom-window control for saffron.</div>
      <div><b>🌡️ Climate & freeze alerts</b><br>Mango freeze alarms, chill-hour tracking for pistachio, flowering-rain risk for saffron.</div>
      <div><b>⚗️ Salinity & fertigation</b><br>EC-limited programs — mango needs low salt water, pistachio tolerates more.</div>
    </div>
  </section>
`;
}

function zoneSvg(el) {
  const [x, y] = svg(el.lon, el.lat);
  return `<circle class="algeria-zone" data-crop="${el.crop}" cx="${x}" cy="${y}" r="${el.r}" fill="${el.color}" fill-opacity="0.28" stroke="${el.color}" stroke-opacity="0.55" stroke-dasharray="3 3" />
    <text class="algeria-zone" data-crop="${el.crop}" x="${x}" y="${y - el.r - 5}" text-anchor="middle" font-size="10" fill="${el.color}" font-weight="700">${esc(el.name)}</text>`;
}

function citySvg(c) {
  const [x, y] = svg(c[0], c[1]);
  const right = x < W * 0.62;
  const anchor = right ? "start" : "end";
  const tx = right ? x + 7 : x - 7;
  return `<g class="algeria-city" data-city="${esc(c[2])}" style="cursor:pointer">
    <circle cx="${x}" cy="${y}" r="4" fill="#0f3d33" stroke="#fff" stroke-width="1.5"/>
    <text x="${tx}" y="${y + 3}" text-anchor="${anchor}" font-size="10.5" font-weight="600" fill="#22332e" paint-order="stroke" stroke="#fff" stroke-width="3">${esc(c[2])}</text>
  </g>`;
}

export const mount = () => {
  const svgEl = document.getElementById("algeria-svg");
  if (svgEl) {
    svgEl.innerHTML = `
      <path d="${OUTLINE}" fill="#f2ead9" stroke="#0f3d33" stroke-width="1.6"/>
      ${ZONES.map(zoneSvg).join("")}
      ${CITIES.map(citySvg).join("")}
    `;
    bindLayers();
    bindCities();
  }
};

function bindLayers() {
  const btns = document.querySelectorAll("[data-map-pill]");
  const showAll = (dataCrop) => {
    document.querySelectorAll(".algeria-zone").forEach((el) => {
      el.classList.toggle("hidden", dataCrop !== "all" && el.dataset.crop !== dataCrop);
    });
  };
  btns.forEach((b) => b.addEventListener("click", () => {
    btns.forEach((x) => x.classList.toggle("active", x === b));
    showAll(b.dataset.layer);
  }));
  showAll("all");
}

function bindCities() {
  const detail = document.getElementById("algeria-detail");
  document.querySelectorAll(".algeria-city").forEach((g) => {
    g.addEventListener("click", () => {
      const name = g.dataset.city;
      const cropHits = ZONES.filter((z) => {
        const [x0, y0] = svg(z.lon, z.lat);
        const c = g.querySelector("circle");
        const cx = Number(c.getAttribute("cx")), cy = Number(c.getAttribute("cy"));
        return Math.hypot(x0 - cx, y0 - cy) < z.r;
      }).map((z) => z.name);
      detail.classList.remove("hidden");
      detail.innerHTML = `<div class="row space-between">
        <h3 style="margin:0">${esc(name)}</h3>
        <button class="icon-btn" id="algeria-detail-close">✕</button></div>
        <div class="small">${cropHits.length ? cropHits.map((h) => `<div>${pill("info", h)}</div>`).join("") : pill("gray", "No mapped crop zones here")}</div>`;
      detail.querySelector("#algeria-detail-close").addEventListener("click", () => detail.classList.add("hidden"));
    });
  });
}