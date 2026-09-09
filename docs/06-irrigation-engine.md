# Irrigation Calculation Engine

## Purpose
Recommend *when* and *how much* to irrigate per zone (Level A) or per tree (Level B), agronomically explainable and traceable to data.

## Inputs

**Crop:** species, variety, age, tree count, spacing, canopy size, root zone depth, growth stage (phenology).

**Climate:** ETo (reference ET), current & forecast temp, RH, wind, solar radiation, rainfall (effective).

**Soil:** texture (sand/silt/clay %), OM, bulk density, field capacity (FC), permanent wilting point (PWP), measured soil moisture (per depth).

**Water/Salinity:** irrigation water EC, soil EC, leaching requirement.

**System:** irrigation efficiency, emitter flow (L/h), emitters per tree, coverage.

**Historical:** prior irrigation events, prior moisture response.

## Equations

### 1. Crop Evapotranspiration
```
ETc = ETo × Kc
```
where `Kc` = crop coefficient (per species per phenology stage).

### 2. Available Water / Allowed Depletion
```
AW (mm/m) = (FC − PWP) × depth(m) × 1000 × (bulk_density/1000)
Readily Available Water: RAW = AW × management_allowed_depletion (MAD)
```
For sandy soils, MAD lowered (e.g. 0.3–0.4) → shorter, more frequent cycles.

### 3. Net Irrigation Requirement (per event)
```
NIR (mm) = (target_moisture − current_moisture) × root_zone_depth
```
Target moisture set between FC and MAD; below → deficit.

### 4. Water Balance (over a period)
```
Balance = Prev_available + Effective_rainfall + Irrigation − ETc − Deep_percolation − Runoff
```

### 5. Gross Irrigation Volume
```
Gross_mm = NIR / irrigation_efficiency
Volume_m3 = Gross_mm/1000 × area_m2
```

### 6. Duration & Frequency
```
Duration_min = (Gross_mm/1000 × area_m2) / (emitter_flow_lph × emitters_per_tree × tree_count/1000)
```
Wait: duration computed from application rate:
```
Application_rate_mm_h = (emitter_flow_lph × emitters_per_tree × 1000) / (spacing × 0.6)   # wetting area approx
Duration_h = Gross_mm / Application_rate_mm_h
```
Frequency from demand: `Freq_days = RAW / daily_ETc` (capped for sandy soils).

### 7. Split Cycles (sandy soils)
If `Duration > max_run_time` (soil infiltration limit) → split into N cycles with rest interval to avoid ponding/deep percolation.

### 8. Salinity Leaching Requirement
Only when data supports it:
```
LR = ECw / (5 × ECe − ECw)
```
Applied **cautiously** — never automatically over-leach.

### 9. Weather Adjustment / Heat Rule
- If forecast max temp > crop heat threshold and soil moisture near stress → pull irrigation earlier, raise volume by heat factor, increase monitoring.
- If rain forecast high → delay.

## Assumptions (always surfaced)
- Missing emitter flow → use typical value, lower confidence.
- Missing moisture sensor → use estimated soil balance, mark assumption.
- Seed parameters flagged `is_assumed`.

## Output Format
```
Zone: X, Crop: date palm, Age: 6y
Current soil moisture: below target
Forecast: extreme heat
ETc = ETo×Kc = 7.5×0.9 = 6.75 mm/day
Recommendation: Apply 38.2 m³ to Zone within 06:00–10:00, 3 split cycles of 40 min, repeat every 3 days.
Why: high evaporative demand, soil moisture below target, extreme temp forecast.
Confidence: Medium
Assumption: emitter flow not recently verified.
```

## Validation Rules
- Reject negative volumes, unreasonable ETc, non-finite values.
- Clamp values to plausible agronomic ranges.
- Raise error if required data (species-stage Kc) missing.
