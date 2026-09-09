# User Stories & Acceptance Criteria

## Personas
- **Owner** — full access to farm settings, audit log, all reports.
- **Manager** — can generate recommendations, approve irrigation, manage tasks.
- **Agronomist** — can run fertigation programs, diagnose crops, review salinity.
- **Technician** — can log irrigation events, upload images, complete tasks.
- **Worker** — view tasks and sensor readings for assigned zones.
- **Admin** — manages users and system configuration.

## Epic 1 — Dashboard & Priorities
**Story:** As a manager, I want to see today's open tasks and critical alerts at a glance so that I can focus on urgent actions first.
- **Acceptance:** Dashboard renders KPI cards (critical alerts, warnings, open tasks, zone count) within 2 seconds of login. Alerts are sorted by severity. Tasks show priority pills. Clicking "All tasks" or "View all alerts" navigates to the respective page.

## Epic 2 — Farm Map
**Story:** As an agronomist, I want an interactive map of my farm showing zone boundaries colored by salinity/moisture status so that I can quickly locate problem areas.
- **Acceptance:** Map renders all zones from `/farms/{id}/map`. Each zone is an SVG polygon colored by selected layer (salinity, moisture, crop). Legend shows status dots. Clicking a zone opens a detail panel with EC, texture, latest recommendation. Layer toggle switches coloring without reloading. Zone summary table appears below map.

## Epic 3 — Irrigation Planner
**Story:** As a manager, I want to generate irrigation recommendations per zone based on ET₀ and soil moisture, then approve and schedule them.
- **Acceptance:** Selecting a zone and clicking "Generate" calls `POST /irrigation/recommendation` and displays volume (m³), duration (min), ETo, rationale, assumptions, and confidence. Approved schedule appears in a table. Zone events are listed per zone. Split cycles are capped at 4 with a note about spreading windows.

## Epic 4 — Soil & Salinity
**Story:** As an agronomist, I want to see soil EC and salinity risk per zone with leaching recommendations so that I can prevent salt accumulation.
- **Acceptance:** Salinity overview table shows each zone's EC, leaching requirement, and status pill (ok/warning/high/critical). Zone detail shows soil/water EC, texture, tree count. A banner warns when EC exceeds crop thresholds.

## Epic 5 — Crop Health & AI Diagnosis
**Story:** As a technician, I want to upload a canopy photo and receive a ranked differential diagnosis with confidence scores so that I can prioritize scouting.
- **Acceptance:** Upload flow: `POST /images/upload` returns image ID, then `POST /images/{id}/analyze` returns summary and top diagnoses with confidence scores. Each diagnosis shows a severity pill. The health page also lists recent diagnoses from the guidance endpoint.

## Epic 6 — Fertigation
**Story:** As an agronomist, I want to generate a per-tree fertilization program with safety checks so that I can avoid over-application.
- **Acceptance:** Selecting a zone and clicking "Generate" calls `POST /fertigation/program` with `{zone_id}`. Result shows N/P/K rates per tree, safety status, and a note. Safety blocks prevent application when soil EC is too high.

## Epic 7 — Climate Risks
**Story:** As a manager, I want to see active climate risks (heat waves, frost, wind) with mitigation actions so that I can protect the orchard proactively.
- **Acceptance:** Climate risks page lists active risks with type, level, timing, detail, and actions. Weather summary KPI cards show max/min temp, humidity, wind. Recent history table shows past 14 days of observations.

## Epic 8 — Tasks
**Story:** As a technician, I want to view, create, and filter tasks by priority and status so that I can track my daily work.
- **Acceptance:** Tasks page lists tasks with title, priority pill, zone, due date, status. "New task" button opens a modal with title, description, priority, zone, due date. Tasks can be filtered by all/open/in_progress/done/overdue. Creating a task calls `POST /tasks`.

## Epic 9 — Alert Center
**Story:** As a manager, I want to see all alerts grouped by severity, acknowledge them, and re-run analysis so that I can stay on top of farm issues.
- **Acceptance:** Alert center shows summary counts (total, critical, high, medium, low, open). All alerts table shows severity, type, message, zone, time, status. "Analyze farm now" triggers `POST /alerts/analyze`. "Mark open as done" acknowledges alerts.

## Epic 10 — Sensors
**Story:** As a technician, I want to view registered sensors and recent readings with quality flags so that I can verify data health.
- **Acceptance:** Sensors page shows sensor code, type, zone, status, last heartbeat. Recent readings table shows sensor, value, unit, time, quality pill.

## Epic 11 — Variety Selector
**Story:** As an agronomist, I want to see variety suitability scores ranked under current climate/soil conditions so that I can plan crop changes.
- **Acceptance:** Variety page calls `POST /variety/suitability` with climate/soil fields and displays ranked results with suitability score, strengths, limitations. A "Refresh ranking" button re-runs the analysis.

## Epic 12 — Reports
**Story:** As an owner, I want to export KPIs and farm data as JSON so that I can analyze trends offline.
- **Acceptance:** Reports page has export buttons for KPIs, audit log, and farm summary. Each download produces a `.json` file. Zone summary table shows status per zone.

## Epic 13 — Internationalization & Accessibility
**Story:** As a user, I want to switch between English, Arabic, and French so that the interface matches my language preference, with RTL support for Arabic.
- **Acceptance:** Language toggle cycles en → ar → fr. Arabic sets `document.dir="rtl"`. All chrome labels (nav, buttons, headers) translate. Page content follows the same language.

## Acceptance Criteria (System-wide)
1. Login at `/app` with `demo@oasis.farm` / `demo1234` returns a JWT stored in localStorage.
2. All pages are reachable via hash routing (`#/dashboard`, `#/map`, `#/irrigation`, etc.).
3. Every API call includes `Authorization: Bearer <token>`.
4. On 401, the user is redirected to login automatically.
5. The farm selector dropdown lets users switch between farms.
6. All pages handle errors gracefully with toast notifications and banner messages.
7. The SPA is served by FastAPI at `/app` with no build step (vanilla ES modules).
8. Responsive layout works on desktop and tablet viewports.
