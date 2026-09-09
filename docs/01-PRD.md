# Product Requirements Document (PRD)

## Smart Desert Orchard Management Platform (DoPalm / "Oasis")

### 1. Vision & Goals

**Oasis** is an intelligent decision-support platform for farmers and farm managers operating orchards in desert and arid regions. It helps manage large numbers of trees efficiently, detects problems early, prioritizes interventions, and makes daily management faster and data-driven.

**Core principle:** *Measure → Analyze → Diagnose → Predict → Recommend → Monitor → Learn*

Oasis does **not** replace agronomists. Every recommendation is traceable to available data, clearly flagged with confidence and uncertainty, and marked with the required expert-verification step before major action.

### 2. Target Users

| Role | Description | Key actions |
|------|-------------|-------------|
| Farm Owner | Owns farms, needs high-level oversight | View all farms, KPIs, alerts, manage users, configure settings |
| Farm Manager | Runs daily farm operations | Manage blocks/zones, register trees, approve irrigation recs, assign tasks, review reports |
| Agronomist | Agronomic authority | Review/confirm/reject AI diagnoses, modify fertilization, configure thresholds, record observations |
| Irrigation Technician | Operates irrigation systems | View schedules, monitor sensors/pumps, record events, report clogged lines/failures |
| Field Worker | Ground-truth data collection | View tasks, upload photos, record observations, mark interventions done |
| Administrator | System configuration | Manage users, crop models, databases, alert rules, sensors, AI models |

### 3. Supported Crops (extensible)

- Date palms
- Olive trees
- Pomegranate trees
- Citrus trees
- Grapevines
- Fig trees

Architecture allows new species/varieties to be added without code changes (data-driven crops/varieties tables).

### 4. Core Features

#### 4.1 Farm Hierarchy & Digital Mapping
Farm → Field → Block → Zone → Row → Tree. Every level selectable on an interactive map. Store geographic boundaries, area, climate zone, soil type, water source, irrigation system, crop, variety, planting date per farm/block/zone; store tree ID, GPS, species, variety, age, health, history for individual trees.

#### 4.2 Smart Farm Map
Interactive map with layers (irrigation status, soil moisture/temp/EC, crop health, disease/pest/nutrient detection, heat/wind/frost risk, inspection targets, completed interventions). Color-coded status:
- **Green** normal · **Yellow** attention · **Orange** high risk · **Red** urgent · **Gray** insufficient data
Clicking a zone/tree opens a detail panel (measurements, trends, alerts, photos, AI diagnosis, recommended actions, tasks).

#### 4.3 Intelligent Irrigation Module
Two levels:
- **A: Zone-based** (default for large farms without per-tree sensors)
- **B: Tree-level** (where per-tree data/sensors exist)

Recommendations: when to irrigate, how much water, duration, frequency, split cycles, delay/increase due to weather.

#### 4.4 Irrigation Calculation Engine
Scientific model based on `ETc = ETo × Kc`, considering crop/variety/age/canopy/root depth/growth stage/density, soil texture & water-holding capacity, measured moisture, current & forecast weather, rainfall, irrigation efficiency, emitter flow, emitter count, soil salinity, water salinity.

Water balance: `Previous Available Water + Effective Rainfall + Irrigation − Crop Water Use − Deep Percolation`

Sandy-soil aware: prefer shorter, more frequent cycles; detect deep percolation & nutrient leaching.

#### 4.5 Heat Stress & Extreme Temperature Module
Per-species/variety/age/stage configurable thresholds. Detects high air temp, high evaporative demand, rapid moisture depletion, young tree vulnerability, sunburn/leaf scorch risk. Displays current temp, forecast max, heat stress index, ET increase, risk level, recommended action. Heat wave recommendations (adjust timing, increase monitoring, avoid water stress, avoid pruning, flag young trees, check equipment, crop-specific measures).

#### 4.6 Water Scarcity Management
Water Efficiency Score (water applied vs demand, soil moisture response, deep percolation risk, uniformity, yield). Detects over-irrigation and under-irrigation with explicit uncertainty statements.

#### 4.7 Soil & Water Salinity Module
Monitor soil EC, water EC, pH, SAR/ions when available. Manual lab entry + IoT. Trends by date/depth/zone/crop. Detect gradual/sudden increase, high-risk zones, salt accumulation. Distinguish salinity vs water stress vs nutrient deficiency vs disease (these look similar).

#### 4.8 Salinity Early Warning System
Configurable alert rules (Warning / High Risk / Critical). Per-crop/variety tolerance — never universal threshold. Recommendations include increased monitoring, verification, multi-depth testing, water analysis, scheduling review, drainage evaluation, **cautious** leaching only with sufficient data.

#### 4.9 Sandy Soil Management Module
Considers low OM, low WHC, rapid leaching/infiltration, high frequency. Inputs: sand/silt/clay %, OM, bulk density, FC, PWP, root depth. Missing data → clearly-labeled assumptions based on texture.

#### 4.10 AI Leaf/Fruit Image Diagnosis
Upload/camera, multiple images, optional notes, image guidance. Model analyzes possible diseases, pests, nutrient deficiencies, heat/sunburn/salinity/water stress, sand abrasion, physical injury. Output: primary possible diagnosis, confidence %, differential (alternatives with %), severity, affected part, visible symptoms, recommended next step, expert-verification flag.

#### 4.11 Differential Diagnosis Engine
Rule + AI assisted; ranks possible causes given image + soil/water/weather/fertilizer/irrigation/history/crop/stage data. Always recommends verification. Distinguishes visual suspicion vs confirmed deficiency.

#### 4.12 Nutrient Deficiency Diagnosis
Supports N, P, K, Ca, Mg, S, Fe, Zn, Mn, B, Cu. Considers symptom location (old/young/whole), chlorosis pattern, interveinal chlorosis, marginal burn, necrosis, deformation, fruit symptoms, species. Labels as **"Possible nutrient deficiency"** unless confirmed by lab data.

#### 4.13 Fertilization & Fertigation Program
Inputs: crop, variety, age, density, yield, stage, soil test, leaf analysis, water quality, irrigation system, history, symptoms. Outputs: nutrient requirements, products, timing, split applications, fertigation schedule, quantities (per tree / ha / zone), safety warnings. Supports phenology stages (dormancy → post-harvest). Nutrient budget system (added vs requirement vs removed vs soil status). Never recommend fertilizer from image alone if salinity/disease/root/water could explain.

#### 4.14 Wind & Sandstorm Management
Monitor wind speed/direction, sandstorm conditions. Alerts for young/recently planted trees, exposed infrastructure. Post-storm auto inspection checklist (branches, fruit, drip emitters, filters, lines, sand burial, windbreaks).

#### 4.15 Disease & Pest Early Detection
Farm-wide surveillance — worker uploads, incident map, timeline, repeated detection alerts, outbreak clustering detection. Prioritizes high-value zones, spreading problems, young trees, severe symptoms. No automatic pesticide recs without confidence + expert validation. IPM-aligned (inspection, monitoring, traps, sanitation, expert ID, crop-specific options).

#### 4.16 Variety Selection Module
User enters climate (max summer/min winter temp, frost risk), water availability/salinity, soil salinity/type, market objective. Ranks varieties with scores across heat/drought/salinity/frost tolerance, soil compatibility, water requirements, disease susceptibility, market suitability. Shows strengths, limitations, risks, management intensity. Uses "more suitable under the selected conditions" — never "best."

#### 4.17 Climate Risk Module
Current + forecast weather, alerts for heat wave, strong wind, sandstorm, frost, sudden temperature drop. Each alert: risk level, timing, affected zones, why it matters, preventive actions.

#### 4.18 Large Farm Monitoring Dashboard
Central dashboard for thousands of trees: total area, active/critical alerts, low-moisture zones, high-salinity zones, trees needing inspection, disease/nutrient detections, today's irrigation plan, upcoming climate risks. Priority list (P1-Critical / P2-High / P3-Medium / P4-Low), sortable.

#### 4.19 Alert System
Channels: web dashboard, push, email (SMS later). Alert types: irrigation, salinity, disease, heat, frost, equipment. Each alert: problem, severity, location, evidence, recommended action, status (New/Acknowledged/In progress/Resolved).

#### 4.20 Task Management
Auto-convert recommendations into assignable tasks (manager, agronomist, technician, worker). Track assigned/due dates, status, completion evidence, before/after photos, notes.

#### 4.21 IoT Sensor Integration
Abstraction layer supporting soil moisture/temp/EC, air temp/RH, weather, water EC/pH/flow/pressure, tank level. Each record: sensor ID, farm, zone, GPS, type, unit, timestamp, value, quality. Detect missing data, malfunction, impossible values, abnormal jumps, calibration needs. Non-trusted values.

#### 4.22 Data Quality & Confidence System
Every recommendation has confidence indicator (High/Medium/Low) with reasons.

#### 4.23 Analytics & Reporting
Daily/weekly/monthly/seasonal reports. KPIs: water per ha/tree, water productivity, critical alerts, response time, salinity trend, % zones in optimal moisture, disease detection rate, fertilizer applications, yield.

### 5. Non-Functional Requirements

- **Science-first:** agronomically explainable, no invented measurements
- **Scalable:** small farm → thousands of trees
- **Mobile-friendly, multilingual** (EN/AR/FR, RTL for Arabic)
- **Offline-capable** field collection architecture
- **Secure, auditable, modular**
- **Uncertainty handling:** every recommendation tells: was detected, why it matters, data used, action, urgency, confidence, what to verify before acting
- Missing data → identify it, state assumptions, reduce confidence, ask user, never invent measurements

### 6. Safety & Agronomic Validation (Mandatory)

Use hedged language: *possible, suspected, likely, requires verification.* Require expert review for: low-confidence diagnoses, severe outbreaks, high-cost interventions, major fertilizer changes, complex salinity management, chemical treatments. Agronomists confirm/reject/modify; feedback improves future models.

### 7. Acceptance Criteria (high-level)

- [ ] User can create farm/field/block/zone/row/tree hierarchy and see it on map
- [ ] Irrigation rec generated from actual formulas and farm data, with confidence + assumptions
- [ ] Salinity alerts with per-crop thresholds, no universal claim
- [ ] Image diagnosis returns differential with confidence and verification steps
- [ ] Fertilization planner never recommends from image alone when other causes possible
- [ ] Alerts auto-generate tasks; priorities assignable
- [ ] Role-based access enforced across all actions
- [ ] All recommendations explainable (6 required fields)
- [ ] Missing data lowers confidence and flags assumptions
- [ ] Multi-language UI (EN at minimum; AR/FR scaffolding)
