"""SQLAlchemy ORM models for the Oasis platform."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Role(str, PyEnum):
    owner = "owner"
    manager = "manager"
    agronomist = "agronomist"
    technician = "technician"
    worker = "worker"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(32), default=Role.worker.value, nullable=False)
    preferred_language = Column(String(8), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    climate_zone = Column(String(100))
    soil_type = Column(String(100))
    water_source = Column(String(100))
    irrigation_system_type = Column(String(100))
    area_m2 = Column(Float)
    country = Column(String(100))
    boundary_wkt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    name = Column(String(255))
    boundary_wkt = Column(Text)
    area_m2 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="fields")
    blocks = relationship("Block", back_populates="field", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"))
    name = Column(String(255))
    crop_species_id = Column(Integer)
    variety_id = Column(Integer)
    tree_count = Column(Integer)
    tree_spacing_m = Column(Float)
    tree_age_years = Column(Float)
    rootstock = Column(String(100))
    irrigation_system_type = Column(String(100))
    boundary_wkt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="blocks")
    zones = relationship("Zone", back_populates="block", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    name = Column(String(255), nullable=False)
    soil_texture = Column(String(100))
    organic_matter_pct = Column(Float)
    soil_ph = Column(Float)
    soil_ec_ds_m = Column(Float)
    water_ec_ds_m = Column(Float)
    water_ph = Column(Float)
    root_zone_depth_m = Column(Float)
    boundary_wkt = Column(Text)
    planting_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    block = relationship("Block", back_populates="zones")
    trees = relationship("Tree", back_populates="zone", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="zone", cascade="all, delete-orphan")


class Row(Base):
    __tablename__ = "rows"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    name = Column(String(255))
    orientation = Column(Float)
    geometry_wkt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Tree(Base):
    __tablename__ = "trees"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    row_id = Column(Integer)
    tree_code = Column(String(100))
    species_id = Column(Integer)
    variety_id = Column(Integer)
    age_years = Column(Float)
    planting_date = Column(DateTime)
    health_status = Column(String(100))
    geo_wkt = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="trees")


class CropSpecies(Base):
    __tablename__ = "crop_species"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True)
    name_en = Column(String(255))
    name_ar = Column(String(255))
    name_fr = Column(String(255))
    family = Column(String(100))
    default_kc = Column(Float)
    salinity_threshold_ds_m = Column(Float)
    critical_ec_ds_m = Column(Float)
    heat_threshold_c = Column(Float)
    frost_threshold_c = Column(Float)


class Variety(Base):
    __tablename__ = "varieties"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("crop_species.id"))
    name = Column(String(255))
    heat_tolerance = Column(Float, default=0.5)
    drought_tolerance = Column(Float, default=0.5)
    salinity_tolerance = Column(Float, default=0.5)
    frost_tolerance = Column(Float, default=0.5)
    soil_compatibility = Column(Float, default=0.5)
    water_requirement = Column(Float)
    disease_susceptibility = Column(Float, default=0.5)
    market_suitability = Column(Float, default=0.5)
    management_intensity = Column(Float, default=0.5)
    notes = Column(Text)


class PhenologyStage(Base):
    __tablename__ = "phenology_stages"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("crop_species.id"))
    stage_key = Column(String(50))
    name = Column(String(255))
    day_range = Column(String(50))


class CropCoefficient(Base):
    __tablename__ = "crop_coefficients"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("crop_species.id"))
    stage_key = Column(String(50))
    kc = Column(Float)
    root_depth_m = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class SoilProfile(Base):
    __tablename__ = "soil_profiles"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    sand_pct = Column(Float)
    silt_pct = Column(Float)
    clay_pct = Column(Float)
    organic_matter_pct = Column(Float)
    bulk_density = Column(Float)
    field_capacity_pct = Column(Float)
    permanent_wilting_point_pct = Column(Float)
    root_zone_depth_m = Column(Float)
    is_assumed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SoilTest(Base):
    __tablename__ = "soil_tests"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    sampled_at = Column(DateTime)
    depth_m = Column(Float)
    ph = Column(Float)
    ec_ds_m = Column(Float)
    n_ppm = Column(Float)
    p_ppm = Column(Float)
    k_ppm = Column(Float)
    ca_ppm = Column(Float)
    mg_ppm = Column(Float)
    fe_ppm = Column(Float)
    zn_ppm = Column(Float)
    mn_ppm = Column(Float)
    b_ppm = Column(Float)
    cu_ppm = Column(Float)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)


class WaterSource(Base):
    __tablename__ = "water_sources"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    name = Column(String(255))
    source_type = Column(String(100))
    ec_ds_m = Column(Float)
    ph = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class WaterTest(Base):
    __tablename__ = "water_tests"

    id = Column(Integer, primary_key=True, index=True)
    water_source_id = Column(Integer, ForeignKey("water_sources.id"))
    sampled_at = Column(DateTime)
    ec_ds_m = Column(Float)
    ph = Column(Float)
    sar = Column(Float)
    chloride_ppm = Column(Float)
    nitrate_ppm = Column(Float)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    zone_id = Column(Integer, ForeignKey("zones.id"))
    sensor_code = Column(String(100), unique=True)
    sensor_type = Column(String(100))
    unit = Column(String(50))
    geo_wkt = Column(Text)
    brand = Column(String(100))
    model = Column(String(100))
    status = Column(String(50), default="active")
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="sensors")


class SensorMeasurement(Base):
    __tablename__ = "sensor_measurements"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    measured_at = Column(DateTime)
    value = Column(Float)
    quality = Column(String(20), default="good")
    created_at = Column(DateTime, default=datetime.utcnow)


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    observed_at = Column(DateTime)
    air_temp_c = Column(Float)
    rel_humidity_pct = Column(Float)
    wind_speed_ms = Column(Float)
    wind_dir_deg = Column(Float)
    rainfall_mm = Column(Float)
    solar_radiation = Column(Float)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    forecast_at = Column(DateTime)
    forecast_for = Column(DateTime)
    min_temp_c = Column(Float)
    max_temp_c = Column(Float)
    humidity_pct = Column(Float)
    wind_speed_ms = Column(Float)
    rain_probability = Column(Float)
    heat_wave_risk = Column(Float)
    frost_risk = Column(Float)
    sandstorm_risk = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class IrrigationSystem(Base):
    __tablename__ = "irrigation_systems"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    system_type = Column(String(100))
    emitter_flow_lph = Column(Float)
    emitters_per_tree = Column(Integer)
    irrigation_efficiency_pct = Column(Float, default=85.0)
    max_run_time_min = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    irrigated_at = Column(DateTime)
    duration_min = Column(Float)
    volume_m3 = Column(Float)
    applied_by = Column(String(255))
    reason = Column(String(255))
    recorded_at = Column(DateTime, default=datetime.utcnow)


class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    tree_id = Column(Integer)
    level = Column(String(20), default="zone")
    generated_at = Column(DateTime)
    etc_mm = Column(Float)
    eto_mm = Column(Float)
    kc = Column(Float)
    irrigation_volume_m3 = Column(Float)
    duration_min = Column(Float)
    frequency_days = Column(Float)
    split_cycles = Column(Integer)
    rationale = Column(Text)
    confidence = Column(String(20), default="medium")
    assumptions = Column(Text)
    status = Column(String(20), default="draft")
    approved_by = Column(Integer)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ImageUpload(Base):
    __tablename__ = "image_uploads"

    id = Column(Integer, primary_key=True, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    zone_id = Column(Integer)
    tree_id = Column(Integer)
    file_path = Column(String(500))
    caption = Column(String(500))
    captured_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIDiagnosis(Base):
    __tablename__ = "ai_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    image_upload_id = Column(Integer)
    zone_id = Column(Integer)
    tree_id = Column(Integer)
    primary_diagnosis = Column(String(255))
    confidence_pct = Column(Float)
    alternatives = Column(Text)
    severity = Column(String(50))
    affected_part = Column(String(100))
    visible_symptoms = Column(Text)
    recommended_action = Column(Text)
    requires_expert = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    review_decision = Column(String(50))
    reviewed_by = Column(Integer)
    reviewed_at = Column(DateTime)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer)
    code = Column(String(100))
    name = Column(String(255))
    symptoms = Column(Text)
    risk_factors = Column(Text)
    ipm_options = Column(Text)


class Pest(Base):
    __tablename__ = "pests"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer)
    code = Column(String(100))
    name = Column(String(255))
    symptoms = Column(Text)
    damage = Column(Text)
    monitoring_method = Column(Text)
    ipm_options = Column(Text)


class NutrientDeficiency(Base):
    __tablename__ = "nutrient_deficiencies"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer)
    nutrient_code = Column(String(20))
    symptoms = Column(Text)
    symptom_location = Column(String(255))
    notes = Column(Text)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    zone_id = Column(Integer)
    tree_id = Column(Integer)
    alert_type = Column(String(50))
    severity = Column(String(20))
    priority = Column(Integer, default=4)
    title = Column(String(255))
    description = Column(Text)
    evidence = Column(Text)
    recommended_action = Column(Text)
    status = Column(String(20), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    zone_id = Column(Integer)
    alert_id = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    assignee_id = Column(Integer)
    assignee_role = Column(String(32))
    assigned_at = Column(DateTime)
    due_date = Column(DateTime)
    status = Column(String(20), default="open")
    completion_evidence = Column(Text)
    before_photo_id = Column(Integer)
    after_photo_id = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class FertilizerProduct(Base):
    __tablename__ = "fertilizer_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    n_pct = Column(Float)
    p2o5_pct = Column(Float)
    k2o_pct = Column(Float)
    ca_pct = Column(Float)
    mg_pct = Column(Float)
    other = Column(String(255))
    description = Column(Text)


class FertilizerApplication(Base):
    __tablename__ = "fertilizer_applications"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    product_id = Column(Integer)
    applied_at = Column(DateTime)
    amount_per_tree_g = Column(Float)
    amount_total_kg = Column(Float)
    method = Column(String(100))
    applied_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class FertilizationProgram(Base):
    __tablename__ = "fertilization_programs"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer)
    species_id = Column(Integer)
    variety_id = Column(Integer)
    stage_key = Column(String(50))
    generated_at = Column(DateTime)
    nutrient_req = Column(Text)
    recommendations = Column(Text)
    nutrient_budget = Column(Text)
    status = Column(String(20), default="draft")
    approved_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class LeafAnalysis(Base):
    __tablename__ = "leaf_analyses"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer)
    sampled_at = Column(DateTime)
    nutrient = Column(Text)
    lab_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer)
    zone_id = Column(Integer)
    name = Column(String(255))
    equipment_type = Column(String(100))
    status = Column(String(50))
    notes = Column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer)
    action = Column(String(100))
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    changes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    report_type = Column(String(50))
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
