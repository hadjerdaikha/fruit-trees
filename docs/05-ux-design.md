# UI / UX Design Specification

Design language: clean, high-contrast, farm-friendly (works in bright sunlight), mobile-first, responsive. Primary palette inspired by desert/water: sandy neutrals + green accents + status colors. Language toggle EN/AR/FR with RTL for Arabic. Large touch targets.

## Global

- Top app bar: farm selector, search, alerts bell (badge count), language switch, user menu.
- Main navigation (13 items): Dashboard, Farm Map, Irrigation, Soil, Water, Crop Health, AI Diagnosis, Fertilization, Climate Risks, Tasks, Sensors, Reports, Settings.
- "Today's Priorities" panel pinned at top of Dashboard.
- Every recommendation renders as an **Explainability Card** with the 6 required fields: *What was detected · Why it matters · Data used · Action · Urgency · Confidence · Verify before acting.*

## Pages

### 1. Login
- Email + password, language select, remember me, demo access button.

### 2. Main Dashboard
- Top: Today's Priorities list (clickable → jump to queue).
- KPI cards: total area, active alerts (split critical), low-moisture zones, high-salinity zones, trees needing inspection, disease detections, today's irrigation plan.
- Priority queue: P1–P4 tabbed list, sortable (severity/zone/crop/type/date).
- Upcoming climate risks banner.

### 3. Farm Creation Wizard
- Multistep: Farm info → climate/soil/water → blocks/zones → crop/variety → irrigation system → review/create. Fields validated; optional fields marked; assumptions flagged.

### 4. Interactive Farm Map
- Leaflet map. Left: layer toggles (irrigation, soil moisture/temp/EC, crop health, disease, pest, nutrient, heat/wind/frost risk, inspection, completed). Zone polygons colored by status (green/yellow/orange/red/gray).
- Click zone/tree → detail panel: measurements, trends, alerts, photos, AI diagnosis, recommended actions, tasks.
- Toolbar: zoom, search zone, filter.

### 5. Zone Details
- Tabs: Overview, Soil, Water, Irrigation, Health, History, Tasks, Photos.

### 6. Individual Tree Profile
- Tree info, GPS, species/variety/age, health status, history (irrigation, fert, problems), images, per-tree sensors, actions.

### 7. Irrigation Dashboard
- Today's plan (per zone: volume, duration, frequency, split, time window). Table + map. Show pending approvals.

### 8. Irrigation Recommendation Page
- Select zone/tree. Shows inputs (measured/calculated/assumed flagged), ETc/ETo/Kc, water balance, recommendation, "Why" list, Confidence, Assumptions. Approve/Reject buttons (manager/agronomist).

### 9. Soil & Salinity Dashboard
- Zone salinity status, EC trends by depth/date, soil test listing, add new test, risk assessment, salinity module recommendations.

### 10. Water Quality Dashboard
- Water source status, EC/pH/SAR trends, add water test, quality alerts.

### 11. Sensor Management
- Sensor list w/ type, location, status, quality. Telemetry charts. Add sensor, flag calibration, ingest API docs.

### 12. Leaf & Fruit Diagnosis
- Image guidance (sharp, lighting, affected+healthy, multiple, context). Upload/camera, notes. Result: primary diagnosis + confidence + differential + severity + symptoms + action + expert-verification flag. Requires agronomist review workflow UI.

### 13. Nutrient Deficiency Page
- Deficiencies by zone, symptom categorization (location/pattern), possible vs confirmed labeling, differential to other causes, verification steps link.

### 14. Fertilization Planner
- Inputs (crop/variety/age/density/yield/stage/soil/leaf/water/system/history/symptoms). Output program: nutrient requirements, products, timing, splits, quantities (tree/ha/zone), safety warnings, nutrient budget. Safety: refuses to recommend from image alone if other causes possible.

### 15. Disease & Pest Monitoring
- Incident map + timeline. Cluster alerts. IPM-aligned recommendations. No automatic pesticide rec without confidence + expert validation.

### 16. Climate Risk Dashboard
- Current + forecast. Heat wave / wind / sandstorm / frost / sudden drop cards: risk level, timing, affected zones, why, preventive actions.

### 17. Variety Suitability Tool
- Form: climate, water, soil, market objective. Ranked variety cards: suitability score, strengths, limitations, risks, management intensity. Wording: "more suitable under the selected conditions."

### 18. Alert Center
- Alert list w/ filters. Each alert: problem, severity, location, evidence, recommended action, status workflow (new/acknowledged/in progress/resolved). Auto-create-task button.

### 19. Task Management
- Queue, assign, due dates, status, completion evidence (before/after photos, notes). "My Tasks" for workers.

### 20. Historical Trends & Analytics
- Charts for moisture, salinity, weather, water use over time. Zone comparisons.

### 21. Reports
- Daily/weekly/monthly/seasonal reports. KPIs. Export.

### 22. Settings
- Farm settings, users & roles, crop models, thresholds, alert rules, sensor integrations, AI models, language.
