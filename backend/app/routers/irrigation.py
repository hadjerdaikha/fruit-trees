"""Irrigation recommendation, schedule, and event routes."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.irrigation import (
    ClimateParams, CropParams, IrrigationEngine, IrrigationResult, SoilParams, SystemParams,
)
from ..models import (
    Block, CropCoefficient, CropSpecies, Field, IrrigationEvent, IrrigationRecommendation,
    IrrigationSystem, Sensor, SensorMeasurement, SoilProfile, WeatherForecast, Zone,
)
from ..schemas import (
    ApprovalRequest, IrrigationEventCreate, IrrigationRequest, IrrigationSystemCreate,
)
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/irrigation", tags=["irrigation"])


def _latest_sensor_value(db, zone_id: int, sensor_type: str):
    sensor = db.query(Sensor).filter_by(zone_id=zone_id, sensor_type=sensor_type, status="active").first()
    if not sensor:
        return None, False
    m = db.query(SensorMeasurement).filter_by(sensor_id=sensor.id).order_by(SensorMeasurement.measured_at.desc()).first()
    if not m or m.quality == "invalid":
        return None, False
    return m.value, True


def _get_zone_context(db, zone: Zone):
    """Gather engine inputs for a zone. Returns (SoilParams, SystemParams, CropParams, ClimateParams, zone_info)."""

    soil_profile = db.query(SoilProfile).filter_by(zone_id=zone.id).order_by(SoilProfile.created_at.desc()).first()

    moisture, moisture_measured = _latest_sensor_value(db, zone.id, "soil_moisture")
    soiltemp, _ = _latest_sensor_value(db, zone.id, "soil_temperature")

    soil = SoilParams(
        texture=zone.soil_texture,
        field_capacity_pct=soil_profile.field_capacity_pct if soil_profile else None,
        wilting_point_pct=soil_profile.permanent_wilting_point_pct if soil_profile else None,
        sand_pct=soil_profile.sand_pct if soil_profile else None,
        clay_pct=soil_profile.clay_pct if soil_profile else None,
        organic_matter_pct=soil_profile.organic_matter_pct if soil_profile else None,
        bulk_density=soil_profile.bulk_density if soil_profile else None,
        root_zone_depth_m=zone.root_zone_depth_m or (soil_profile.root_zone_depth_m if soil_profile else None),
        measured_moisture_pct=moisture,
        is_assumed=(soil_profile.is_assumed if soil_profile else True),
    )

    isys = db.query(IrrigationSystem).filter_by(zone_id=zone.id).order_by(IrrigationSystem.created_at.desc()).first()
    block = zone.block
    tree_count = (block.tree_count or 0) if block else 0

    system = SystemParams(
        emitter_flow_lph=isys.emitter_flow_lph if isys else None,
        emitters_per_tree=isys.emitters_per_tree if isys else None,
        irrigation_efficiency_pct=(isys.irrigation_efficiency_pct if isys else 85.0),
        max_run_time_min=isys.max_run_time_min if isys else None,
        tree_count=tree_count or 1,
        spacing_m=block.tree_spacing_m or 4.0 if block else 4.0,
        row_spacing_m=6.0,
        wetted_width_m=2.0,
        emitter_flow_assumed=(isys is None or isys.emitter_flow_lph is None),
    )

    # crop
    species = db.query(CropSpecies).filter_by(id=block.crop_species_id).first() if block and block.crop_species_id else None
    kc = species.default_kc if species else 0.8
    root_depth = 1.0
    coeff = db.query(CropCoefficient).filter_by(species_id=block.crop_species_id).first() if block and block.crop_species_id else None
    if coeff:
        kc = coeff.kc
        root_depth = coeff.root_depth_m

    crop = CropParams(
        species_id=block.crop_species_id if block else 0,
        species_name=species.name_en if species else "unknown",
        kc=kc,
        root_depth_m=root_depth,
        tree_age_years=block.tree_age_years if block else None,
        heat_threshold_c=species.heat_threshold_c if species else None,
    )

    # climate: use forecast + recent observation for Hargreaves ETo estimate
    forecast = db.query(WeatherForecast).filter_by(
        farm_id=block.field.farm_id if (block and block.field) else None
    ).order_by(WeatherForecast.forecast_for.desc()).first()

    eto = None
    max_temp = None
    rainfall = 0.0
    eff_rain = 0.0
    if forecast:
        max_temp = forecast.max_temp_c
    from ..models import WeatherObservation
    recent_obs = db.query(WeatherObservation).filter_by(
        farm_id=block.field.farm_id if (block and block.field) else None
    ).order_by(WeatherObservation.observed_at.desc()).first()
    # Hargreaves-Samani: ET0 = 0.0023 * Ra * (Tmean + 17.8) * sqrt(Tmax - Tmin)
    # Ra ~ 16 mm/day water-equivalent for desert latitudes in summer (estimate).
    if (recent_obs and recent_obs.air_temp_c) or forecast:
        ra_eq = 16.0  # mm/day equivalent, desert-summer estimate (assumption surfaced in output)
        t_mean = (recent_obs.air_temp_c if recent_obs and recent_obs.air_temp_c else 32.0)
        t_max = max_temp if max_temp else t_mean + 8.0
        t_min = (recent_obs.air_temp_c - 8.0) if recent_obs and recent_obs.air_temp_c else t_mean - 8.0
        t_range = max(1.0, t_max - t_min)
        eto = round(0.0023 * ra_eq * (t_mean + 17.8) * (t_range ** 0.5), 1)
    if eto is None:
        eto = 8.0  # default desert reference ETo (assumption, surfaced below)

    climate = ClimateParams(
        eto_mm=eto,
        max_forecast_temp_c=max_temp,
        rainfall_mm=rainfall,
        effective_rainfall_mm=eff_rain,
    )

    zone_info = {
        "zone_id": zone.id, "zone_name": zone.name,
        "crop": crop.species_name, "tree_age": crop.tree_age_years,
        "soil_texture": zone.soil_texture,
    }
    return soil, system, crop, climate, zone_info


@router.post("/recommendation")
def generate_recommendation(payload: IrrigationRequest, db: Session = Depends(get_db),
                            user=Depends(require_min_role("manager"))):
    zone = db.query(Zone).filter_by(id=payload.zone_id).first() if payload.zone_id else None
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    soil, system, crop, climate, zone_info = _get_zone_context(db, zone)
    engine = IrrigationEngine()
    result: IrrigationResult = engine.compute(soil, system, crop, climate)

    rec = IrrigationRecommendation(
        zone_id=zone.id,
        level=payload.level or "zone",
        generated_at=datetime.utcnow(),
        etc_mm=result.etc_mm,
        eto_mm=result.eto_mm,
        kc=result.kc,
        irrigation_volume_m3=result.irrigation_volume_m3,
        duration_min=result.duration_min,
        frequency_days=result.frequency_days,
        split_cycles=result.split_cycles,
        rationale="\n".join(result.rationale),
        confidence=result.confidence,
        assumptions="\n".join(result.assumptions),
        status="draft",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    assumptions = list(result.assumptions)
    assumptions.append(
        "ETo estimated by Hargreaves-Samani with Ra=16 mm/day (desert-summer, latitude-adjusted estimate); "
        "use a weather station or FAO ETo source when available for higher confidence."
    )
    if result.current_moisture_pct is None:
        assumptions.append("Soil moisture not measured; deficit derived from the daily water balance (assumption).")

    return {
        "id": rec.id,
        "zone": zone_info,
        "inputs": {
            "eto_mm": result.eto_mm,
            "kc": result.kc,
            "etc_mm": result.etc_mm,
            "available_water_mm": result.available_water_mm,
            "readily_available_water_mm": result.readily_available_water_mm,
            "current_moisture_pct": result.current_moisture_pct,
            "deficit_mm": result.deficit_mm,
        },
        "recommendation": {
            "text": result.recommendation_text,
            "volume_m3": result.irrigation_volume_m3,
            "duration_min": result.duration_min,
            "frequency_days": result.frequency_days,
            "split_cycles": result.split_cycles,
            "suggested_start": result.suggested_start,
        },
        "why": result.rationale,
        "assumptions": assumptions,
        "confidence": result.confidence,
        "heat_alert": result.heat_alert,
        "status": rec.status,
    }


@router.get("/zones/{zone_id}/recommendations")
def list_recommendations(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(IrrigationRecommendation).filter_by(zone_id=zone_id).order_by(IrrigationRecommendation.generated_at.desc()).limit(50).all()
    return rows


@router.post("/recommendations/{rec_id}/approve")
def approve_recommendation(rec_id: int, payload: ApprovalRequest, db: Session = Depends(get_db),
                           user=Depends(require_min_role("manager"))):
    rec = db.query(IrrigationRecommendation).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = "approved" if payload.decision == "approve" else "rejected"
    rec.approved_by = user.id
    rec.approved_at = datetime.utcnow()
    db.commit()
    return {"id": rec.id, "status": rec.status}


@router.get("/schedule")
def today_schedule(db: Session = Depends(get_db), user=Depends(get_current_user)):
    today = datetime.utcnow()
    approved = db.query(IrrigationRecommendation).filter(
        IrrigationRecommendation.status == "approved",
        IrrigationRecommendation.generated_at >= today - timedelta(days=1),
    ).order_by(IrrigationRecommendation.generated_at.desc()).limit(100).all()
    out = []
    for rec in approved:
        zone = db.query(Zone).filter_by(id=rec.zone_id).first()
        out.append({
            "zone_id": rec.zone_id, "zone_name": zone.name if zone else str(rec.zone_id),
            "volume_m3": rec.irrigation_volume_m3, "duration_min": rec.duration_min,
            "split_cycles": rec.split_cycles, "frequency_days": rec.frequency_days,
            "generated_at": rec.generated_at,
        })
    return out


@router.post("/events")
def log_event(payload: IrrigationEventCreate, db: Session = Depends(get_db),
              user=Depends(require_min_role("technician"))):
    event = IrrigationEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/zones/{zone_id}/events")
def list_events(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(IrrigationEvent).filter_by(zone_id=zone_id).order_by(IrrigationEvent.irrigated_at.desc()).limit(100).all()
    return rows


@router.post("/systems")
def create_system(payload: IrrigationSystemCreate, db: Session = Depends(get_db),
                  user=Depends(require_min_role("manager"))):
    system = IrrigationSystem(**payload.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system
