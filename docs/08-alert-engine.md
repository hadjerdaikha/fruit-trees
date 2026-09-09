# Alert Engine

## Rule Structure
Each rule: `{ type, condition (over data signals), severity, priority, message template, evidence fields, recommended_action, escalation }`. Rules are data-driven and configurable by admin/agronomist (per species/variety where applicable).

## Severity / Priority
- **Critical (P1):** immediate action — critical EC + symptoms, drought + heat at sensitive stage, disease cluster, equipment failure, frost/heat extreme.
- **High (P2):** action within 24h — EC rising fast, moisture below threshold, high heat forecast, possible disease.
- **Medium (P3):** monitor/schedule inspection — gradual EC increase, low moisture trend, moderate wind.
- **Low (P4):** informational — minor deviation, routine check.

## Thresholds (configurable, per crop/variety/age/stage)
- **Irrigation:** soil moisture < MAD threshold (zone), moisture depletion rate, ET demand spike.
- **Salinity:** EC rising consistently (Warning), EC > variety threshold (High), EC > critical AND symptoms (Critical). Never a single universal value.
- **Disease/Pest:** repeated symptom reports, cluster detection (≥N similar reports within M days in nearby trees), severe symptoms, young trees.
- **Heat:** forecast max temp > species/variety/age/stage threshold; heat stress index; low moisture during heat.
- **Frost:** min temp < frost threshold at sensitive stage.
- **Wind/Sandstorm:** wind speed > threshold, sandstorm condition → auto inspection checklist task.
- **Equipment:** abnormal sensor response (e.g., no moisture change after irrigation → possible clog), pump pressure drop, missing data.

## Evaluation Flow
On data ingestion and on-demand (`/alerts/analyze`):
1. Pull relevant signals (moisture, EC, weather forecast, recent reports, equipment).
2. Apply rules → candidate alerts with severity/priority.
3. De-duplicate against open alerts of same type+location (avoid spam; escalate if worsening).
4. Create alert + auto-generate task (per mapping).
5. Persist with evidence snapshot + recommended action + status New.

## Escalation
- If an open High/Critical alert is not acknowledged within configurable time → escalate by notifying owner/manager via next channel (dashboard → push/email).
- Priority escalation when additional confirming signals arrive.

## Status Workflow
`new → acknowledged → in_progress → resolved`. Reopen if re-triggered. Never delete history.

## Alert Types
irrigation · salinity · disease · pest · nutrient · heat · frost · wind · sandstorm · equipment · climate · data_quality

## Channels
- Web dashboard (always)
- Push (configurable)
- Email (configurable; SMTP stub in MVP)
- SMS (architecture reserved)
