# Database Schema

Physical storage: PostgreSQL + PostGIS (production), SQLite (MVP/dev). All historical agronomic measurements are **immutable** (append-only); never overwritten.

## Core Entities

### auth.users
- id PK, email UNIQUE, password_hash, full_name, role (enum), preferred_language, is_active, created_at, updated_at

### farms
- id PK, owner_id FK users, name, climate_zone, soil_type, water_source, irrigation_system_type, country, created_at, updated_at
- spatial: boundary GEOMETRY(Polygon,4326)

### fields
- id PK, farm_id FK, name, boundary GEOMETRY, area_m2, created_at

### blocks
- id PK, field_id FK, name, crop_species_id FK, variety_id FK, tree_count, tree_spacing_m, tree_age_years, rootstock, irrigation_system_type, boundary GEOMETRY, created_at

### zones
- id PK, block_id FK, name, soil_texture, organic_matter_pct, soil_ph, soil_ec_ds_m, water_ec_ds_m, water_ph, root_zone_depth_m, boundary GEOMETRY, created_at

### rows
- id PK, block_id FK, name, orientation, geometry LINESTRING, created_at

### trees
- id PK, zone_id FK, row_id FK NULL, tree_code, species_id, variety_id, age_years, planting_date, health_status, geo_point GEOMETRY(Point,4326), notes, created_at

### crop_species / varieties / phenology_stages / crop_coefficients
- species: id, code, name_en/ar/fr, family, default_kc, salinity_threshold_ds_m, critical_ec_ds_m
- varieties: id, species_id, name, heat_tolerance, drought_tolerance, salinity_tolerance, frost_tolerance, disease_susceptibility, market_suitability, management_intensity, notes
- phenology_stages: id, species_id, stage_key, name, day_range
- crop_coefficients: id, species_id, stage_key, kc, root_depth_m, created_at

### soil_profiles / soil_tests
- soil_profiles: id, zone_id, sand_pct, silt_pct, clay_pct, organic_matter_pct, bulk_density, field_capacity_pct, permanent_wilting_point_pct, root_zone_depth_m, is_assumed BOOLEAN, created_at
- soil_tests: id, zone_id, sampled_at, depth_m, ph, ec_ds_m, n_ppm, p_ppm, k_ppm, ca_ppm, mg_ppm, fe_ppm, zn_ppm, mn_ppm, b_ppm, cu_ppm, source (manual/lab/sensor), created_at (immutable)

### water_sources / water_tests
- water_sources: id, farm_id, name, type, ec_ds_m default, ph default
- water_tests: id, water_source_id, sampled_at, ec_ds_m, ph, sar, chloride_ppm, nitrate_ppm, source, created_at (immutable)

### sensors / sensor_measurements
- sensors: id, farm_id, zone_id NULL, sensor_code, sensor_type (enum), unit, gps_point GEOMETRY, brand, model, status (active/inactive), last_heartbeat, created_at
- sensor_measurements: id, sensor_id, measured_at, value REAL, quality (enum: good/suspect/invalid), created_at (append-only; index on sensor_id, measured_at)

### weather_observations / weather_forecasts
- weather_observations: id, farm_id, observed_at, air_temp_c, rel_humidity_pct, wind_speed_ms, wind_dir_deg, rainfall_mm, solar_radiation, source
- weather_forecasts: id, farm_id, forecast_at, forecast_for, min_temp_c, max_temp_c, humidity_pct, wind_speed_ms, rain_probability, heat_wave_risk, frost_risk, sandstorm_risk

### irrigation_systems / irrigation_events / irrigation_recommendations
- irrigation_systems: id, zone_id, type, emitter_flow_lph, emitters_per_tree, irrigation_efficiency_pct, coverage_pct
- irrigation_events: id, zone_id, irrigated_at, duration_min, volume_m3, applied_by (user), reason, recorded_at (append-only)
- irrigation_recommendations: id, zone_id (or tree_id), level (zone/tree), generated_at, etc_mm, eto_mm, kc, irrigation_volume_m3, duration_min, frequency_days, split_cycles, rationale JSON, confidence, status (draft/approved/rejected), approved_by, approved_at

### image_uploads / ai_diagnoses
- image_uploads: id, uploader_id, zone_id NULL, tree_id NULL, file_path, caption, captured_at, created_at
- ai_diagnoses: id, image_upload_id NULL, zone_id NULL, tree_id NULL, primary_diagnosis, confidence_pct, alternatives JSON, severity, affected_part, visible_symptoms JSON, recommended_action, requires_expert BOOLEAN, status (pending/reviewed), review_decision (confirm/reject/modify), reviewed_by, reviewed_at, model_version

### diseases / pests / nutrient_deficiencies
- diseases: id, species_id, code, name, symptoms, risk_factors, ipm_options JSON
- pests: id, species_id, code, name, symptoms, damage, monitoring_method, ipm_options JSON
- nutrient_deficiencies: id, species_id, nutrient_code, symptoms, location, notes

### alerts / tasks / interventions
- alerts: id, farm_id, zone_id NULL, tree_id NULL, type, severity (critical/high/medium/low), title, description, evidence JSON, recommended_action, status (new/acknowledged/in_progress/resolved), priority (1-4), created_at, resolved_at
- tasks: id, farm_id, zone_id NULL, alert_id NULL, title, description, assignee_id FK users, assignee_role, assigned_at, due_date, status, completion_evidence JSON, before_photo_id, after_photo_id, notes
- interventions: id, task_id NULL, zone_id, type, performed_at, description, performed_by, result

### fertilizer_products / fertilizer_applications / fertilization_programs / leaf_analyses
- fertilizer_products: id, name, n_pct, p2o5_pct, k2o_pct, ca_pct, mg_pct, other, description
- fertilizer_applications: id, zone_id, product_id, applied_at, amount_per_tree_g, amount_total_kg, method, applied_by, created_at (append-only)
- fertilization_programs: id, zone_id, species_id, variety_id, stage_key, generated_at, nutrient_req JSON, recommendations JSON, nutrient_budget JSON, status, approved_by
- leaf_analyses: id, zone_id, sampled_at, nutrient JSON (element -> ppm), lab_name, created_at

### reports / equipment / audit_logs
- reports: id, farm_id, type (daily/weekly/monthly/seasonal), period_start, period_end, content JSON, generated_at
- equipment: id, farm_id, zone_id NULL, name, type, status, notes
- audit_logs: id, actor_id, action, entity_type, entity_id, changes JSON, created_at

## Indexes

- farms(farm_id), zones(block_id), trees(zone_id), trees(geo_point) [GIST]
- sensor_measurements(sensor_id, measured_at DESC)
- weather_forecasts(farm_id, forecast_for DESC)
- alerts(farm_id, created_at DESC, severity)
- tasks(status, assignee_id)
- ai_diagnoses(status, reviewed_by)
- soil_tests(zone_id, sampled_at DESC)
- water_tests(water_source_id, sampled_at DESC)
- spatial: GIST on farms.boundary, fields.boundary, blocks.boundary, zones.boundary, trees.geo_point, rows.geometry

## Relationships Summary

users 1—* farms 1—* fields 1—* blocks 1—* zones 1—* trees
blocks 1—* rows 1—* trees
zones 1—* soil_profiles/tests, sensors, irrigation_events/recommendations, alerts, tasks, applications
farms 1—* water_sources 1—* water_tests
zones 1—* image_uploads *—1 ai_diagnoses
