"""Weather observation, forecast, and climate risk routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.climate import ClimateEngine, RiskAssessment, WeatherSnapshot
from ..models import (
    Block, CropSpecies, Farm, Field, WeatherForecast, WeatherObservation, Zone,
)
from ..schemas import WeatherForecastCreate, WeatherObservationCreate
from ..security import require_min_role

router = APIRouter(prefix="/farms/{farm_id}/weather", tags=["weather"])


@router.post("/observations")
def add_observation(farm_id: int, payload: WeatherObservationCreate, db: Session = Depends(get_db),
                    user=Depends(require_min_role("manager"))):
    obs = WeatherObservation(farm_id=farm_id, **payload.model_dump())
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/observations")
def list_observations(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    rows = db.query(WeatherObservation).filter_by(farm_id=farm_id).order_by(WeatherObservation.observed_at.desc()).limit(200).all()
    return rows


@router.post("/forecast")
def add_forecast(farm_id: int, payload: WeatherForecastCreate, db: Session = Depends(get_db),
                 user=Depends(require_min_role("manager"))):
    fc = WeatherForecast(farm_id=farm_id, forecast_at=None, **payload.model_dump())
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return fc


@router.get("/forecast")
def get_forecast(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    rows = db.query(WeatherForecast).filter_by(farm_id=farm_id).order_by(WeatherForecast.forecast_for.desc()).limit(10).all()
    return rows


@router.get("/climate-risks")
def climate_risks(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    latest = db.query(WeatherForecast).filter_by(farm_id=farm_id).order_by(WeatherForecast.forecast_for.desc()).first()

    # gather crop thresholds across all crops in the farm
    thresholds = {}
    zones = db.query(Zone).join(Block).join(Field).filter(Field.farm_id == farm_id).all()
    young_trees = False
    for z in zones:
        if z.block and z.block.crop_species_id:
            sp = db.query(CropSpecies).filter_by(id=z.block.crop_species_id).first()
            if sp:
                thresholds.setdefault("heat_threshold_c", sp.heat_threshold_c)
                thresholds.setdefault("frost_threshold_c", sp.frost_threshold_c)
        for t in z.trees:
            if t.age_years is not None and t.age_years < 3:
                young_trees = True

    if not latest:
        return {"message": "No forecast data available.", "risks": []}

    snapshot = WeatherSnapshot(
        max_forecast_temp_c=latest.max_temp_c,
        min_forecast_temp_c=latest.min_temp_c,
        wind_speed_ms=latest.wind_speed_ms,
        heat_wave_risk=latest.heat_wave_risk,
        frost_risk=latest.frost_risk,
        sandstorm_risk=latest.sandstorm_risk,
        forecast_for=latest.forecast_for.isoformat() if latest.forecast_for else None,
    )
    engine = ClimateEngine()
    assessment: RiskAssessment = engine.evaluate(snapshot, thresholds, young_trees=young_trees)
    return {"risks": assessment.risks}
