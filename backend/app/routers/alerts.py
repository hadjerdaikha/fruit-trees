"""Alert routing and alert-engine evaluation."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Alert, Block, CropSpecies, Field, IrrigationEvent, Sensor, SensorMeasurement,
    SoilTest, Task, WeatherForecast, Zone,
)
from ..schemas import AlertUpdate
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(farm_id: int = None, severity: str = None, status: str = None, limit: int = 100,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Alert)
    if farm_id:
        q = q.filter(Alert.farm_id == farm_id)
    if severity:
        q = q.filter(Alert.severity == severity)
    if status:
        q = q.filter(Alert.status == status)
    rows = q.order_by(Alert.priority.asc(), Alert.created_at.desc()).limit(limit).all()
    return rows


def _latest(db, zone_id, sensor_type):
    s = db.query(Sensor).filter_by(zone_id=zone_id, sensor_type=sensor_type, status="active").first()
    if not s:
        return None
    m = db.query(SensorMeasurement).filter_by(sensor_id=s.id).order_by(SensorMeasurement.measured_at.desc()).first()
    return m.value if m and m.quality != "invalid" else None


def _open_alerts(db, zone_id, alert_type):
    return db.query(Alert).filter(Alert.zone_id == zone_id, Alert.alert_type == alert_type,
                                  Alert.status.in_(["new", "acknowledged", "in_progress"])).first()


def _make_alert(db, farm_id, zone_id, alert_type, severity, priority, title, description, evidence, action):
    import json
    alert = Alert(
        farm_id=farm_id, zone_id=zone_id, alert_type=alert_type, severity=severity,
        priority=priority, title=title, description=description,
        evidence=json.dumps(evidence) if evidence and not isinstance(evidence, str) else evidence,
        recommended_action=action, status="new",
    )
    db.add(alert)
    db.commit()
    return alert


@router.post("/analyze", )
def analyze_farm(farm_id: int, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    zones = (
        db.query(Zone)
        .join(Block, Zone.block_id == Block.id)
        .join(Field, Block.field_id == Field.id)
        .filter(Field.farm_id == farm_id)
        .all()
    )
    created = []

    for zone in zones:
        threshold = 4.0
        block = zone.block
        if block and block.crop_species_id:
            sp = db.query(CropSpecies).filter_by(id=block.crop_species_id).first()
            if sp:
                threshold = sp.salinity_threshold_ds_m

        # ---- Salinity alert ----
        moisture = _latest(db, zone.id, "soil_moisture")
        soil_ec = _latest(db, zone.id, "soil_ec")
        if soil_ec is None:
            st = db.query(SoilTest).filter_by(zone_id=zone.id).order_by(SoilTest.sampled_at.desc()).first()
            soil_ec = st.ec_ds_m if st else None
        if soil_ec is not None:
            existing = _open_alerts(db, zone.id, "salinity")
            if soil_ec > threshold * 1.5 and not existing:
                a = _make_alert(
                    db, farm_id, zone.id, "salinity", "critical", 1,
                    f"Critical salinity in {zone.name}",
                    f"Soil EC {soil_ec:.2f} dS/m exceeds critical threshold.",
                    {"ec_ds_m": soil_ec, "threshold": threshold}, 
                    "Inspect soil EC and irrigation water quality; consult agronomist.",
                )
                created.append(a)
            elif soil_ec > threshold and not existing:
                severity = "high"
                existing_ec = db.query(Alert).filter(Alert.zone_id == zone.id, Alert.alert_type == "salinity").first()
                if existing_ec and existing_ec.status in ("acknowledged", "new"):
                    # potential escalation if has symptoms
                    severity = "high"
                a = _make_alert(
                    db, farm_id, zone.id, "salinity", severity, 2,
                    f"High salinity risk in {zone.name}",
                    f"Soil EC {soil_ec:.2f} dS/m exceeds crop threshold {threshold:.2f} dS/m.",
                    {"ec_ds_m": soil_ec, "threshold": threshold},
                    "Test soil at multiple depths and review irrigation/leaching.",
                )
                created.append(a)

        # ---- Irrigation / moisture alert ----
        if moisture is not None:
            existing = _open_alerts(db, zone.id, "irrigation")
            if moisture < 12 and not existing and zone.soil_texture == "sandy":
                a = _make_alert(
                    db, farm_id, zone.id, "irrigation", "high", 2,
                    f"Low soil moisture in {zone.name}",
                    f"Soil moisture {moisture:.1f}% is below the target range for sandy soil.",
                    {"moisture_pct": moisture},
                    "Check irrigation schedule and emitter operation; consider adjusting frequency.",
                )
                created.append(a)

    # ---- Heat / frost from forecast ----
    forecast = db.query(WeatherForecast).filter_by(farm_id=farm_id).order_by(WeatherForecast.forecast_for.desc()).first()
    if forecast:
        zones_for_heat = zones
        for zone in zones_for_heat:
            sp = None
            if zone.block and zone.block.crop_species_id:
                sp = db.query(CropSpecies).filter_by(id=zone.block.crop_species_id).first()
            heat_thr = sp.heat_threshold_c if sp else 40.0
            frost_thr = sp.frost_threshold_c if sp else 0.0
            if forecast.max_temp_c and forecast.max_temp_c > heat_thr:
                existing = _open_alerts(db, zone.id, "heat")
                if not existing:
                    a = _make_alert(
                        db, farm_id, zone.id, "heat", "high", 2,
                        f"Extreme heat forecast for {zone.name}",
                        f"Max temp forecast {forecast.max_temp_c:.0f}C exceeds crop threshold {heat_thr:.0f}C.",
                        {"max_temp_c": forecast.max_temp_c, "threshold": heat_thr},
                        "Irrigate in cooler window, monitor soil moisture, flag young trees, check irrigation system.",
                    )
                    created.append(a)
            if forecast.min_temp_c and forecast.min_temp_c < frost_thr:
                existing = _open_alerts(db, zone.id, "frost")
                if not existing:
                    a = _make_alert(
                        db, farm_id, zone.id, "frost", "high", 2,
                        f"Frost risk for {zone.name}",
                        f"Min temp forecast {forecast.min_temp_c:.0f}C below threshold {frost_thr:.0f}C.",
                        {"min_temp_c": forecast.min_temp_c, "threshold": frost_thr},
                        "Implement frost protection if crop at sensitive stage.",
                    )
                    created.append(a)

    # ---- Wind/sandstorm ----
    if forecast and forecast.wind_speed_ms and forecast.wind_speed_ms > 15:
        # create one wind alert per farm
        existing = db.query(Alert).filter(Alert.farm_id == farm_id, Alert.alert_type == "wind",
                                          Alert.status.in_(["new", "acknowledged", "in_progress"])).first()
        if not existing:
            a = _make_alert(
                db, farm_id, None, "wind", "high" if forecast.wind_speed_ms > 22 else "medium", 2,
                "Strong wind / sandstorm forecast",
                f"Wind speed forecast {forecast.wind_speed_ms:.0f} m/s.",
                {"wind_speed_ms": forecast.wind_speed_ms},
                "After event: generate inspection checklist for branches, fruit, emitters, filters, young trees.",
            )
            created.append(a)

    return {"created": len(created), "alerts": [a.id for a in created]}


@router.patch("/{alert_id}")
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db),
                 user=Depends(require_min_role("manager"))):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if payload.status:
        alert.status = payload.status
        if payload.status == "resolved":
            alert.resolved_at = datetime.utcnow()
    if payload.priority:
        alert.priority = payload.priority
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    alerts = db.query(Alert).all()
    return {
        "total": len(alerts),
        "critical": len([a for a in alerts if a.severity == "critical" and a.status != "resolved"]),
        "high": len([a for a in alerts if a.severity == "high" and a.status != "resolved"]),
        "medium": len([a for a in alerts if a.severity == "medium" and a.status != "resolved"]),
        "low": len([a for a in alerts if a.severity == "low" and a.status != "resolved"]),
        "open": len([a for a in alerts if a.status != "resolved"]),
    }
