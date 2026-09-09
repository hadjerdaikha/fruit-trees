# System Architecture

## Overview

Oasis is built as a **modular monolith** for the MVP (easier operational deployment on a farm) with clear service boundaries so it can be decomposed into microservices later.

```
┌──────────────────────────────────┐
│         Frontend (Web)           │
│  Vanilla HTML/CSS/JS ES modules  │
│  Hash routing, i18n, RTL         │
│  Served by FastAPI at /app       │
└───────────────┬──────────────────┘
                │ REST / JSON
┌───────────────▼──────────────────┐
│         Backend (API)            │
│        FastAPI (Python)          │
│  ┌────────────────────────────┐  │
│  │ Routers: Auth·Farm·Irrig. │  │
│  │ Sensors·Image AI·Fertig.  │  │
│  │ Alerts·Tasks·Climate·Soil │  │
│  │ Variety·Dashboard·Audit   │  │
│  └────────────────────────────┘  │
└────────┬────────────┬────────────┘
         │            │
   ┌─────▼────┐ ┌─────▼────┐
   │Postgres  │ │SQLite    │
   │(prod)    │ │(MVP dev) │
   └──────────┘ └──────────┘
```

## Layer: Backend Modules (FastAPI)

Each module is a self-contained FastAPI `APIRouter` with its own service + repository layer.

1. **auth** — JWT access/refresh, role-based access control (RBAC), user management.
2. **farms** — farm/field/block/zone/row/tree hierarchy, geo boundaries.
3. **crops** — species, varieties, phenology stages, crop coefficients.
4. **soils** — soil profiles, soil tests, texture parameters.
5. **water** — water sources, water tests, water EC/pH/SAR.
6. **sensors** — sensor registry, telemetry ingestion, data quality checks.
7. **weather** — observations & forecasts, climate risk evaluation.
8. **irrigation** — recommendation engine (Level A/B), events, schedules.
9. **image** — upload, validation, preprocessing, AI analysis pipeline.
10. **diagnosis** — differential diagnosis engine (rule-based + AI-assisted).
11. **fertigation** — fertilization planner, nutrient budget.
12. **alerts** — rule engine, priority, escalation, status workflow.
13. **tasks** — auto-generated + manual tasks, assignments, completion.
14. **reports** — analytics, KPIs, aggregations.
15. **variety** — suitability scoring engine.
16. **audit** — audit log of all state-changing operations.

## Layer: AI Architecture

Four independent components (separated for testability):

1. **Computer Vision** — analyzes leaf/fruit images. MVP uses a deterministic symptom-extraction + probabilistic classifier pipeline (overlapping diagnosis with confidence). Pluggable: real CV model (CNNs / external APIs) can be swapped in.
2. **Agronomic Rules Engine** — crop-specific knowledge: irrigation formulas (ETc=ETo×Kc), salinity thresholds (per crop/variety), nutrient deficiency logic, climate risk rules.
3. **Predictive Models** — soil moisture, water demand, salinity trend, climate risk. MVP uses lightweight statistical/trend models (linear regression, EWMA) — ML-ready interface.
4. **Recommendation Engine** — combines AI output + sensor data + weather + agronomic rules + historical farm data to produce explainable recommendations (always includes the 6 required explanatory fields).

## Layer: Data

- **PostgreSQL + PostGIS** (production) supporting spatial queries (farm boundaries, zones, trees).
- **SQLite + spatialite** (MVP/dev) via SQLAlchemy — same models, portable.
- **Object storage** (local filesystem in MVP; S3-compatible later) for images/reports.
- **Time-series** storage for sensor telemetry (MVP: partitioned telemetry table; later TimescaleDB).

## Layer: IoT Abstraction

`SensorProvider` interface (`read_*, validate_*, heartbeat`). Pluggable adapters: manual entry, HTTP/MQTT push, vendor bridges. Ingest pipeline: validate → quality-check → store → trigger alert evaluation.

## Layer: Security

- JWT bearer auth, encrypted at rest for secrets
- RBAC enforced via dependency injection per route
- Audit logs
- Input validation (Pydantic), rate limiting

## Layer: Frontend

The frontend is a **dependency-free vanilla HTML/CSS/JS SPA** (no build step) served by FastAPI as static files at `/app`. It uses hash routing, ES module imports, i18n catalogs (en/ar/fr with RTL for Arabic), and inline SVG charts. This design avoids npm registry dependency in offline environments.

## Multi-Language / RTL

- `i18n` JSON catalogs (en, ar, fr)
- `document.dir = "rtl"` handling for Arabic via CSS logical properties
- Language toggle cycles en → ar → fr

## Offline Capability

- Field-worker flows designed as PWA; MVP uses service workers + IndexedDB queue to buffer uploads; sync on reconnect.
