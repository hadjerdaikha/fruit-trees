"""Sensor registration, telemetry ingestion, and data quality routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Sensor, SensorMeasurement
from ..schemas import Message, SensorCreate, SensorReadingBatch
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/sensors", tags=["sensors"])

# Reasonable ranges per sensor type (for data-quality validation)
VALID_RANGES = {
    "soil_moisture": (0.0, 100.0),   # volumetric %
    "soil_temperature": (-10.0, 60.0),
    "soil_ec": (0.0, 25.0),
    "air_temperature": (-15.0, 65.0),
    "humidity": (0.0, 100.0),
    "wind_speed": (0.0, 60.0),
    "water_ec": (0.0, 25.0),
    "water_ph": (0.0, 14.0),
    "water_flow": (0.0, 1000000.0),
    "pressure": (0.0, 1000.0),
    "tank_level": (0.0, 100.0),
}


def _quality_check(sensor_type: str, value: float) -> str:
    lo, hi = VALID_RANGES.get(sensor_type, (None, None))
    if lo is not None and (value < lo or value > hi):
        return "invalid"
    return "good"


@router.post("", response_model=Message)
def register_sensor(payload: SensorCreate, db: Session = Depends(get_db),
                    user=Depends(require_min_role("technician"))):
    existing = db.query(Sensor).filter_by(sensor_code=payload.sensor_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sensor code already registered")
    sensor = Sensor(**payload.model_dump())
    db.add(sensor)
    db.commit()
    return Message(message="Sensor registered", detail={"id": sensor.id})


@router.get("")
def list_sensors(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Sensor).all()


@router.patch("/{sensor_id}")
def update_sensor(sensor_id: int, status: str = None, zone_id: int = None, db: Session = Depends(get_db),
                  user=Depends(require_min_role("admin"))):
    sensor = db.query(Sensor).filter_by(id=sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    if status is not None:
        sensor.status = status
    if zone_id is not None:
        sensor.zone_id = zone_id
    db.commit()
    return {"id": sensor.id, "status": sensor.status, "zone_id": sensor.zone_id}


@router.post("/{sensor_id}/measurements/batch", response_model=Message)
def ingest_batch(sensor_id: int, payload: SensorReadingBatch, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    sensor = db.query(Sensor).filter_by(id=sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    inserted = 0
    for r in payload.readings:
        quality = _quality_check(sensor.sensor_type, r.value)
        db.add(SensorMeasurement(
            sensor_id=sensor_id, measured_at=r.measured_at, value=r.value, quality=quality,
        ))
        if quality == "good":
            inserted += 1
    sensor.last_heartbeat = datetime.utcnow()
    db.commit()
    return Message(message="Measurements stored", detail={"valid": inserted})


@router.post("/{sensor_id}/measurements", response_model=Message)
def ingest_single(sensor_id: int, value: float, measured_at: datetime = None, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    sensor = db.query(Sensor).filter_by(id=sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    quality = _quality_check(sensor.sensor_type, value)
    db.add(SensorMeasurement(
        sensor_id=sensor_id, measured_at=measured_at or datetime.utcnow(), value=value, quality=quality,
    ))
    sensor.last_heartbeat = datetime.utcnow()
    db.commit()
    return Message(message="Measurement stored", detail={"quality": quality})


@router.get("/{sensor_id}/measurements")
def list_measurements(sensor_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    data = db.query(SensorMeasurement).filter_by(sensor_id=sensor_id).order_by(SensorMeasurement.measured_at.desc()).limit(500).all()
    return [
        {"measured_at": m.measured_at, "value": m.value, "quality": m.quality, "id": m.id}
        for m in data
    ]


@router.get("/quality/summary")
def quality_summary(db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    sensors = db.query(Sensor).all()
    out = []
    for s in sensors:
        recent = db.query(SensorMeasurement).filter_by(sensor_id=s.id).order_by(SensorMeasurement.measured_at.desc()).limit(20).all()
        invalid = [m for m in recent if m.quality == "invalid"]
        out.append({
            "sensor_code": s.sensor_code, "sensor_type": s.sensor_type,
            "status": s.status, "last_heartbeat": s.last_heartbeat,
            "recent_invalid": len(invalid),
            "quality": "good" if not invalid else ("suspect" if len(invalid) < len(recent) else "invalid"),
        })
    return out
