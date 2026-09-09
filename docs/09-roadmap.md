# Development Roadmap

## Sprint 1 — Foundation & Core Data (MVP)
- Project scaffolding: Next.js frontend + FastAPI backend, repo conventions, CI lint.
- Auth (register/login/JWT, RBAC roles).
- Farm/field/block/zone/row/tree CRUD + hierarchy.
- Crop species/varieties/phenology/crop-coefficients seed data (date, olive, pomegranate, citrus, grape, fig).
- Database schema + migrations + seed.

## Sprint 2 — Irrigation & Sensors (MVP)
- Irrigation calculation engine (ETc=ETo×Kc, water balance, sandy-soil splits, heat adjustment).
- Irrigation recommendations (Level A/B) + approve/reject.
- Irrigation events logging; today's schedule.
- Sensor registry + telemetry ingestion + data-quality checks.
- Manual soil test & water test entry.
- Soil & salinity dashboards (trends, risk).

## Sprint 3 — Alerts, Tasks, Map (MVP)
- Alert engine (irrigation/salinity/disease/heat/frost/wind/equipment) + status workflow.
- Task management + auto-generation from alerts; "Today's Priorities."
- Interactive farm map with status layers + zone/tree detail panel.
- Dashboard aggregates + priority queue.

## Sprint 4 — AI Diagnosis & Fertigation (MVP)
- Image upload/guidance/preprocessing.
- AI image diagnosis pipeline (differential, confidence, severity, expert-verification).
- Differential diagnosis engine.
- Fertilization/fertigation planner + nutrient budget (with safety rules).
- Variety suitability tool (basic).
- Climate risk dashboard (heat/wind/frost/sandstorm).

## Phase 2 (post-MVP)
- IoT sensor integrations + vendor adapters + MQTT/HTTP push.
- Advanced weather forecasting integration (API providers).
- Advanced disease/pest clustering + IPM recommendation library.
- Automated climate alerts with location-specific forecast.
- Fertilizer product library + fertigation schedule generator.
- Reports & analytics (daily/weekly/monthly/seasonal, KPIs).
- PWA offline field-collection + sync.

## Phase 3
- Machine learning: soil moisture forecasting, salinity prediction, yield prediction.
- Deficit irrigation optimization.
- Remote sensing / satellite (NDVI) integration.
- Automated irrigation system control integration.
- Model retraining pipeline from agronomist feedback.

## Cross-cutting (all sprints)
- Multi-language (EN first, AR/FR scaffolding + RTL).
- Explainability requirement (6-field cards) across all recommendations.
- Audit logging.
- Security: input validation, RBAC, secrets management.

## Definition of Done (per sprint)
- Lint + typecheck pass; unit tests for engines (irrigation, salinity, alert); integration smoke test; seeded demo farm; docs updated.
