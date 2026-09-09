# API Specification (REST, JSON)

Base URL: `/api/v1`. All endpoints require `Authorization: Bearer <JWT>` unless noted. Roles in parentheses indicate minimum permission.

## Auth
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | /auth/register | Create account (admin only for non-owner) | public/admin |
| POST | /auth/login | Get access+refresh tokens | public |
| POST | /auth/refresh | Refresh access token | any |
| GET | /auth/me | Current user | any |
| GET | /users | List users | admin/owner |
| PATCH | /users/{id} | Update user / role | admin |

## Farms & Hierarchy
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET/POST | /farms | List / create farm | owner/admin |
| GET/PATCH | /farms/{id} | Farm detail/update | owner/manager |
| DELETE | /farms/{id} | Delete farm | owner/admin |
| GET/POST | /farms/{id}/fields | Fields | manager+ |
| GET/POST | /farms/{id}/blocks | Blocks | manager+ |
| GET/POST | /blocks/{id}/zones | Zones | manager+ |
| GET/POST | /zones/{id}/trees | Trees | manager+ |
| GET | /farms/{id}/map | Hierarchy export for map rendering | manager+ |

## Crops & Varieties
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /species | List species | any |
| GET | /species/{id}/varieties | Varieties | any |
| GET | /species/{id}/coefficients | Crop coefficients by stage | any |
| POST | /species | Create species | admin |
| POST | /varieties | Create variety | admin |

## Soils & Water
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET/POST | /zones/{id}/soil-profiles | Soil profile | manager/agronomist |
| GET/POST | /zones/{id}/soil-tests | Soil tests | agronomist |
| GET/POST | /farms/{id}/water-sources | Water sources | manager |
| GET/POST | /water-sources/{id}/water-tests | Water tests | agronomist |

## Sensors
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET/POST | /sensors | List/register sensors | technician/admin |
| POST | /sensors/{id}/measurements | Ingest telemetry (batch) | sensors/tech |
| GET | /sensors/{id}/measurements?from=&to= | Query telemetry | technician/manager |
| GET | /sensors/quality | Data quality status | admin |
| PATCH | /sensors/{id} | Update/flag sensor | admin |

## Weather
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /farms/{id}/weather?from=&to= | Observations | manager+ |
| GET | /farms/{id}/forecast | Forecast | manager+ |
| POST | /farms/{id}/weather | Manual weather entry | manager |

## Irrigation
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | /irrigation/recommendation | Generate rec for zone/tree (Level A/B) | manager/agronomist |
| GET | /zones/{id}/irrigation-recommendations | List recs | manager+ |
| POST | /irrigation-recommendations/{id}/approve | Approve/reject | manager/agronomist |
| GET/POST | /zones/{id}/irrigation-events | Log events | technician |
| GET | /irrigation/schedule?date= | Today's schedule | manager/technician |

## Images & AI Diagnosis
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | /images/upload | Upload images (multipart) | any worker+ |
| POST | /images/{id}/analyze | Run AI diagnosis | agronomist/any |
| GET | /diagnoses/{id} | Get diagnosis | agronomist/manager |
| POST | /diagnoses/{id}/review | Confirm/reject/modify | agronomist |

## Fertigation
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | /fertigation/program | Generate fertilization program | agronomist |
| GET | /zones/{id}/fertigation-programs | List programs | manager+ |
| GET/POST | /zones/{id}/fertilizer-applications | Applications | technician |
| POST | /fertigation/programs/{id}/approve | Approve/modify | agronomist |

## Salinity
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /zones/{id}/salinity | Trends + risk assessment | manager+ |
| GET | /farms/{id}/salinity-overview | Farm-wide salinity | manager+ |

## Differential Diagnosis
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /diagnosis/differential?zoneId=&symptoms= | Rank possible causes | agronomist/manager |

## Alerts
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /alerts?farmId=&severity=&status= | List alerts | manager+ |
| POST | /alerts/analyze | Run alert engine for farm | manager |
| PATCH | /alerts/{id} | Update status | manager+ |
| GET | /alerts/summary | Dashboard alert summary | owner/manager |

## Tasks
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET/POST | /tasks | List/create tasks | manager+ |
| PATCH | /tasks/{id} | Update/assign/status | manager+ |
| POST | /tasks/{id}/complete | Mark complete w/ evidence | assignee |
| GET | /tasks/me | My tasks | any |

## Climate
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /farms/{id}/climate-risks | Active climate risks | manager+ |

## Variety Suitability
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | /variety/suitability | Rank varieties for conditions | owner/manager |

## Reports & Analytics
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /farms/{id}/dashboard | Dashboard aggregates | owner/manager |
| GET | /farms/{id}/reports?type= | Reports by period type | manager+ |
| GET | /farms/{id}/kpis | KPI calculation | manager+ |

## Audit
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | /audit/logs?entity=&actor= | Audit log | admin |
