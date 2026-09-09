"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------- Auth / Users ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "worker"
    preferred_language: Optional[str] = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: Optional[str]
    role: str
    preferred_language: Optional[str]
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Farms ----------
class FarmCreate(BaseModel):
    name: str
    climate_zone: Optional[str] = None
    soil_type: Optional[str] = None
    water_source: Optional[str] = None
    irrigation_system_type: Optional[str] = None
    area_m2: Optional[float] = None
    country: Optional[str] = None
    boundary_wkt: Optional[str] = None


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    climate_zone: Optional[str]
    soil_type: Optional[str]
    water_source: Optional[str]
    irrigation_system_type: Optional[str]
    area_m2: Optional[float]
    country: Optional[str]
    created_at: Optional[datetime]


class FieldCreate(BaseModel):
    farm_id: int
    name: Optional[str] = None
    boundary_wkt: Optional[str] = None
    area_m2: Optional[float] = None


class BlockCreate(BaseModel):
    field_id: int
    name: str
    crop_species_id: Optional[int] = None
    variety_id: Optional[int] = None
    tree_count: Optional[int] = None
    tree_spacing_m: Optional[float] = None
    tree_age_years: Optional[float] = None
    rootstock: Optional[str] = None
    irrigation_system_type: Optional[str] = None
    boundary_wkt: Optional[str] = None


class ZoneCreate(BaseModel):
    block_id: int
    name: str
    soil_texture: Optional[str] = None
    organic_matter_pct: Optional[float] = None
    soil_ph: Optional[float] = None
    soil_ec_ds_m: Optional[float] = None
    water_ec_ds_m: Optional[float] = None
    water_ph: Optional[float] = None
    root_zone_depth_m: Optional[float] = None
    boundary_wkt: Optional[str] = None
    planting_date: Optional[datetime] = None


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    block_id: int
    name: str
    soil_texture: Optional[str]
    organic_matter_pct: Optional[float]
    soil_ph: Optional[float]
    soil_ec_ds_m: Optional[float]
    water_ec_ds_m: Optional[float]
    water_ph: Optional[float]
    root_zone_depth_m: Optional[float]


class TreeCreate(BaseModel):
    zone_id: int
    tree_code: Optional[str] = None
    species_id: Optional[int] = None
    variety_id: Optional[int] = None
    age_years: Optional[float] = None
    planting_date: Optional[datetime] = None
    health_status: Optional[str] = None
    geo_wkt: Optional[str] = None
    notes: Optional[str] = None


# ---------- Soil / Water ----------
class SoilProfileCreate(BaseModel):
    zone_id: int
    sand_pct: Optional[float] = None
    silt_pct: Optional[float] = None
    clay_pct: Optional[float] = None
    organic_matter_pct: Optional[float] = None
    bulk_density: Optional[float] = None
    field_capacity_pct: Optional[float] = None
    permanent_wilting_point_pct: Optional[float] = None
    root_zone_depth_m: Optional[float] = None
    is_assumed: Optional[bool] = False


class SoilTestCreate(BaseModel):
    zone_id: int
    sampled_at: datetime
    depth_m: Optional[float] = None
    ph: Optional[float] = None
    ec_ds_m: Optional[float] = None
    n_ppm: Optional[float] = None
    p_ppm: Optional[float] = None
    k_ppm: Optional[float] = None
    ca_ppm: Optional[float] = None
    mg_ppm: Optional[float] = None
    fe_ppm: Optional[float] = None
    zn_ppm: Optional[float] = None
    mn_ppm: Optional[float] = None
    b_ppm: Optional[float] = None
    cu_ppm: Optional[float] = None
    source: Optional[str] = "manual"


class WaterSourceCreate(BaseModel):
    farm_id: int
    name: str
    source_type: Optional[str] = None
    ec_ds_m: Optional[float] = None
    ph: Optional[float] = None


class WaterTestCreate(BaseModel):
    water_source_id: int
    sampled_at: datetime
    ec_ds_m: Optional[float] = None
    ph: Optional[float] = None
    sar: Optional[float] = None
    chloride_ppm: Optional[float] = None
    nitrate_ppm: Optional[float] = None
    source: Optional[str] = "manual"


# ---------- Sensors ----------
class SensorCreate(BaseModel):
    farm_id: int
    zone_id: Optional[int] = None
    sensor_code: str
    sensor_type: str
    unit: Optional[str] = None
    geo_wkt: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None


class SensorReading(BaseModel):
    measured_at: datetime
    value: float


class SensorReadingBatch(BaseModel):
    readings: list[SensorReading]


# ---------- Weather ----------
class WeatherObservationCreate(BaseModel):
    observed_at: datetime
    air_temp_c: Optional[float] = None
    rel_humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_dir_deg: Optional[float] = None
    rainfall_mm: Optional[float] = None
    solar_radiation: Optional[float] = None


class WeatherForecastCreate(BaseModel):
    forecast_for: datetime
    min_temp_c: Optional[float] = None
    max_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    rain_probability: Optional[float] = None


# ---------- Irrigation ----------
class IrrigationRequest(BaseModel):
    zone_id: Optional[int] = None
    tree_id: Optional[int] = None
    level: Optional[str] = "zone"


class IrrigationSystemCreate(BaseModel):
    zone_id: int
    system_type: Optional[str] = "drip"
    emitter_flow_lph: Optional[float] = None
    emitters_per_tree: Optional[int] = None
    irrigation_efficiency_pct: Optional[float] = 85.0
    max_run_time_min: Optional[float] = None


class IrrigationEventCreate(BaseModel):
    zone_id: int
    irrigated_at: datetime
    duration_min: Optional[float] = None
    volume_m3: Optional[float] = None
    applied_by: Optional[str] = None
    reason: Optional[str] = None


class ApprovalRequest(BaseModel):
    decision: str  # approve | reject
    note: Optional[str] = None


# ---------- Image / Diagnosis ----------
class ImageAnalysisRequest(BaseModel):
    zone_id: Optional[int] = None
    tree_id: Optional[int] = None
    caption: Optional[str] = None


class DiagnosisReviewRequest(BaseModel):
    decision: str  # confirm | reject | modify
    modified_diagnosis: Optional[str] = None
    note: Optional[str] = None


# ---------- Fertigation ----------
class FertigationRequest(BaseModel):
    zone_id: int
    expected_yield_kg: Optional[float] = None
    stage_key: Optional[str] = None


class FertilizerApplicationCreate(BaseModel):
    zone_id: int
    product_id: Optional[int] = None
    applied_at: datetime
    amount_per_tree_g: Optional[float] = None
    amount_total_kg: Optional[float] = None
    method: Optional[str] = None
    applied_by: Optional[str] = None


# ---------- Varieties ----------
class VarietySuitabilityRequest(BaseModel):
    max_summer_temp_c: float
    min_winter_temp_c: float
    frost_risk: Optional[float] = 0.5
    water_availability: Optional[float] = 0.5
    water_ec_ds_m: Optional[float] = None
    soil_ec_ds_m: Optional[float] = None
    soil_type: Optional[str] = "sandy"
    market_objective: Optional[str] = None


# ---------- Alerts / Tasks ----------
class AlertUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None


class TaskCreate(BaseModel):
    farm_id: int
    title: str
    description: Optional[str] = None
    zone_id: Optional[int] = None
    alert_id: Optional[int] = None
    assignee_id: Optional[int] = None
    assignee_role: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_role: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class TaskComplete(BaseModel):
    completion_evidence: Optional[str] = None
    after_photo_id: Optional[int] = None
    notes: Optional[str] = None


# ---------- Generic ----------
class Message(BaseModel):
    message: str
    detail: Optional[Any] = None
