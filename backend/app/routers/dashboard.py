"""Dashboard aggregates, KPIs, and reports."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Alert, Block, CropSpecies, Farm, Field, IrrigationEvent, Sensor, SensorMeasurement,
    SoilTest, Task, Zone,
)
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/farms/{farm_id}", tags=["dashboard"])


def _farm_zones(db, farm_id):
    return (
        db.query(Zone)
        .join(Block, Zone.block_id == Block.id)
        .join(Field, Block.field_id == Field.id)
        .filter(Field.farm_id == farm_id)
        .all()
    )


@router.get("/dashboard")
def dashboard(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    farm = db.query(Farm).filter_by(id=farm_id).first()
    zones = _farm_zones(db, farm_id)

    # salinity & moisture status per zone
    low_moisture, high_salinity = 0, 0
    zone_status = []
    for zone in zones:
        st = db.query(SoilTest).filter_by(zone_id=zone.id).order_by(SoilTest.sampled_at.desc()).first()
        s = db.query(Sensor).filter_by(zone_id=zone.id, sensor_type="soil_moisture", status="active").first()
        moisture = None
        if s:
            m = db.query(SensorMeasurement).filter_by(sensor_id=s.id).order_by(SensorMeasurement.measured_at.desc()).first()
            if m and m.quality != "invalid":
                moisture = m.value
        ec = st.ec_ds_m if st else None
        se = db.query(Sensor).filter_by(zone_id=zone.id, sensor_type="soil_ec", status="active").first()
        if se:
            me = db.query(SensorMeasurement).filter_by(sensor_id=se.id).order_by(SensorMeasurement.measured_at.desc()).first()
            if me and me.quality != "invalid":
                ec = me.value

        if moisture is not None and moisture < 12:
            low_moisture += 1
        if ec is not None and ec > 3.5:
            high_salinity += 1

        threshold = 4.0
        if zone.block and zone.block.crop_species_id:
            sp = db.query(CropSpecies).filter_by(id=zone.block.crop_species_id).first()
            if sp:
                threshold = sp.salinity_threshold_ds_m
        sal_level = "ok"
        if ec is not None:
            if ec > threshold * 1.5:
                sal_level = "critical"
            elif ec > threshold:
                sal_level = "high"
        zone_status.append({
            "zone_id": zone.id, "zone_name": zone.name, "crop": (zone.block.name if zone.block else None),
            "moisture_pct": moisture, "soil_ec": ec, "soil_texture": zone.soil_texture,
            "salinity_level": sal_level,
        })

    alerts = db.query(Alert).filter_by(farm_id=farm_id).all()
    critical = [a for a in alerts if a.severity in ("critical", "high") and a.status != "resolved"]

    # disease/nutrient detections from diagnoses
    from ..models import AIDiagnosis
    pending_dx = db.query(AIDiagnosis).filter(AIDiagnosis.status == "pending").count()

    # trees needing inspection (with low age or issues)
    trees_needing = 0
    for zone in zones:
        for t in zone.trees:
            if t.age_years is not None and t.age_years < 3:
                trees_needing += 1

    return {
        "farm": {"id": farm.id, "name": farm.name, "area_m2": farm.area_m2},
        "total_zones": len(zones),
        "low_moisture_zones": low_moisture,
        "high_salinity_zones": high_salinity,
        "active_alerts": len([a for a in alerts if a.status != "resolved"]),
        "critical_alerts": len(critical),
        "trees_needing_inspection": trees_needing,
        "pending_diagnoses": pending_dx,
        "zone_status": zone_status,
    }


@router.get("/kpis")
def kpis(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    zones = _farm_zones(db, farm_id)
    month_start = datetime.utcnow() - timedelta(days=30)
    events = db.query(IrrigationEvent).filter(IrrigationEvent.irrigated_at >= month_start).all()
    total_water_m3 = sum(e.volume_m3 for e in events if e.volume_m3) or 0
    area_ha = 0
    for z in zones:
        if z.block and z.block.tree_count and z.block.tree_spacing_m:
            area_ha += z.block.tree_count * z.block.tree_spacing_m ** 2 / 10000.0

    alerts = db.query(Alert).filter(Alert.farm_id == farm_id, Alert.created_at >= month_start).all()
    tasks = db.query(Task).filter(Task.farm_id == farm_id, Task.created_at >= month_start).all()
    completed = [t for t in tasks if t.status == "completed"]

    return {
        "period": "last 30 days",
        "water_used_m3": round(total_water_m3, 1),
        "water_per_ha_m3": round(total_water_m3 / area_ha, 1) if area_ha else None,
        "critical_alerts": len([a for a in alerts if a.severity in ("critical", "high")]),
        "tasks_total": len(tasks),
        "tasks_completed": len(completed),
        "avg_response_for_tasks": round(sum((t.due_date - t.created_at).total_seconds() / 86400 for t in tasks if t.due_date) / len(tasks), 1) if tasks else None,
    }


@router.get("/reports")
def reports(farm_id: int, report_type: str = "daily", db: Session = Depends(get_db),
            user=Depends(require_min_role("manager"))):
    zones = _farm_zones(db, farm_id)
    alerts = db.query(Alert).filter_by(farm_id=farm_id).all()
    tasks = db.query(Task).filter_by(farm_id=farm_id).all()

    def trend(items, key):
        return [(getattr(i, key)) for i in items if getattr(i, key) is not None]

    return {
        "report_type": report_type,
        "total_zones": len(zones),
        "alert_summary": {
            "critical": len([a for a in alerts if a.severity == "critical"]),
            "high": len([a for a in alerts if a.severity == "high"]),
            "medium": len([a for a in alerts if a.severity == "medium"]),
            "low": len([a for a in alerts if a.severity == "low"]),
            "resolved": len([a for a in alerts if a.status == "resolved"]),
        },
        "tasks": {
            "open": len([t for t in tasks if t.status == "open"]),
            "completed": len([t for t in tasks if t.status == "completed"]),
        },
        "zone_salinity": [{"zone": z.name, "ec": z.soil_ec_ds_m} for z in zones],
    }
