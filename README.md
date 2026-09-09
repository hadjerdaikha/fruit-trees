# Oasis — Smart Desert Orchard Management

Production-ready decision-support platform for irrigated desert orchards: irrigation scheduling, salinity monitoring, AI crop-diagnosis, fertigation, climate-risk alerts, tasks, and farm maps.

## Quick start

1. Start the backend server (from the `backend/` folder):
   ```
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Open the app in your browser:
   ```
   http://127.0.0.1:8000/app/
   ```
3. Sign in with the demo account (requires demo data to be seeded):
   - Email: `demo@oasis.farm`
   - Password: `demo1234`
   - Role: manager

To seed demo data, run once from `backend/`:
```
python -c "import os; os.chdir(r'C:\Users\hadje\Documents\fruit trees\backend'); import run; run.seed_demo()"
```
or set `SEED_DEMO=1` before starting uvicorn.

The SPA is served by FastAPI at `/app` — no separate frontend build step and no `npm install` required (the sandbox npm registry is offline). The frontend is a dependency-free vanilla ES-module SPA served as static files by FastAPI.

## Architecture

- **Backend:** FastAPI (Python) with SQLAlchemy + SQLite (`backend/oasis.db`). API prefix `/api/v1`, JWT Bearer auth.
- **Engines:** `irrigation` (Hargreaves-Samani ETo + water balance), `salinity` (crop-specific EC thresholds + leaching), `differential` (context-weighted diagnosis ranking), `fertigation` (N-P-K per-tree with safety blocks), `variety` (crop–climate–soil suitability), `climate` (Open-Meteo forecast + risk detection).
- **AI pipeline:** image upload → local model (MobileNet-style) → top-k differential diagnoses with confidence scores.
- **Frontend:** vanilla HTML/CSS/JS ES modules at `frontend/`. Hash routing (`#/dashboard`, `#/map`, etc.). i18n en/ar/fr with RTL for Arabic. SVG farm map with status layers. Inline SVG charts. No build tools.

## Pages

| Route | Page |
|---|---|
| `#/dashboard` | Today's priorities, KPIs, alerts, zone status |
| `#/map` | Interactive SVG farm map with layer toggles |
| `#/irrigation` | Irrigation planner, schedule, events |
| `#/soil` | Soil EC & salinity overview |
| `#/water` | Water balance & quality |
| `#/health` | Crop health + AI diagnosis upload |
| `#/fertigation` | Fertilizer program per zone |
| `#/climate` | Active climate risks & history |
| `#/tasks` | Task list, create, filter |
| `#/alerts` | Alert center, analyze, acknowledge |
| `#/sensors` | Registered sensors & readings |
| `#/variety` | Variety suitability ranking |
| `#/reports` | Export KPIs / audit log / farm summary |

## Demo data

The seeded demo farm "Al Waha Demo Farm" includes:
- 3 blocks: North Date Palm (Medjool), Young Pomegranate (Wonderful), Olive Grove (Arbequina)
- 4 zones with varying salinity (Zone 2 is high-risk)
- 7 pre-generated alerts, tasks, weather forecast (heat-wave risk)

## Project structure

```
backend/  app/   models.py, schemas.py, engines/, routers/, seed_data.py, main.py, run.py
docs/     01-PRD.md … 09-roadmap.md (+ 10-user-stories.md)
frontend/ index.html, styles.css, js/{app,api,ui,i18n,chart, pages/{...}}.js
```

## Security

- Passwords hashed with bcrypt (direct, not passlib).
- JWT access tokens; refresh endpoint available.
- Role hierarchy: worker < technician < manager/agronomist < owner < admin.
- Some endpoints require agronomist+ (fertigation) or technician+ (log events).
