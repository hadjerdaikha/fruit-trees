"""Soil and water management routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.salinity import SalinityAssessment, SalinityData, SalinityEngine
from ..models import CropSpecies, Field, SoilProfile, SoilTest, WaterSource, WaterTest, Zone
from ..schemas import (
    SoilProfileCreate, SoilTestCreate, WaterSourceCreate, WaterTestCreate,
)
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="", tags=["soil-water"])


# ---------- Soil profiles ----------
@router.post("/zones/{zone_id}/soil-profiles")
def create_soil_profile(zone_id: int, payload: SoilProfileCreate, db: Session = Depends(get_db),
                        user=Depends(require_min_role("agronomist"))):
    payload = payload.model_copy(update={"zone_id": zone_id})
    prof = SoilProfile(**payload.model_dump())
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


@router.get("/zones/{zone_id}/soil-profiles")
def list_soil_profiles(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(SoilProfile).filter_by(zone_id=zone_id).order_by(SoilProfile.created_at.desc()).all()


@router.post("/zones/{zone_id}/soil-tests")
def create_soil_test(zone_id: int, payload: SoilTestCreate, db: Session = Depends(get_db),
                     user=Depends(require_min_role("agronomist"))):
    payload = payload.model_copy(update={"zone_id": zone_id})
    test = SoilTest(**payload.model_dump())
    db.add(test)
    db.commit()
    # update zone EC
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if zone and test.ec_ds_m is not None:
        zone.soil_ec_ds_m = test.ec_ds_m
        db.commit()
    db.refresh(test)
    return test


# ---------- Water sources & tests ----------
@router.post("/farms/{farm_id}/water-sources")
def create_water_source(farm_id: int, payload: WaterSourceCreate, db: Session = Depends(get_db),
                        user=Depends(require_min_role("manager"))):
    payload = payload.model_copy(update={"farm_id": farm_id})
    ws = WaterSource(**payload.model_dump())
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


@router.get("/farms/{farm_id}/water-sources")
def list_water_sources(farm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(WaterSource).filter_by(farm_id=farm_id).all()


@router.post("/water-sources/{wsid}/water-tests")
def create_water_test(wsid: int, payload: WaterTestCreate, db: Session = Depends(get_db),
                      user=Depends(require_min_role("agronomist"))):
    payload = payload.model_copy(update={"water_source_id": wsid})
    test = WaterTest(**payload.model_dump())
    db.add(test)
    db.commit()
    ws = db.query(WaterSource).filter_by(id=wsid).first()
    if ws and test.ec_ds_m is not None:
        ws.ec_ds_m = test.ec_ds_m
        db.commit()
    db.refresh(test)
    return test


@router.get("/water-sources/{wsid}/water-tests")
def list_water_tests(wsid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(WaterTest).filter_by(water_source_id=wsid).order_by(WaterTest.sampled_at.desc()).all()


# ---------- Salinity assessment ----------
@router.get("/zones/{zone_id}/salinity")
def zone_salinity(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    tests = db.query(SoilTest).filter_by(zone_id=zone_id).order_by(SoilTest.sampled_at.desc()).limit(10).all()
    tests.sort(key=lambda t: t.sampled_at or t.created_at)

    # crop threshold from block->species
    threshold = None
    critical = None
    block = zone.block
    if block and block.crop_species_id:
        sp = db.query(CropSpecies).filter_by(id=block.crop_species_id).first()
        if sp:
            threshold = sp.salinity_threshold_ds_m
            critical = sp.critical_ec_ds_m

    series = [t.ec_ds_m for t in tests if t.ec_ds_m is not None]
    latest = tests[-1] if tests else None
    prev = tests[-2] if len(tests) > 1 else None

    data = SalinityData(
        zone_name=zone.name,
        soil_ec_now=latest.ec_ds_m if latest else (zone.soil_ec_ds_m if zone.soil_ec_ds_m is not None else None),
        soil_ec_previous=prev.ec_ds_m if prev else None,
        soil_ec_series=series,
        water_ec=zone.water_ec_ds_m,
        crop_threshold_ds_m=threshold,
        crop_critical_ds_m=critical,
        soil_texture=zone.soil_texture,
    )
    engine = SalinityEngine()
    assessment: SalinityAssessment = engine.assess(data)

    return {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "assessment": {
            "level": assessment.level,
            "message": assessment.message,
            "rationale": assessment.rationale,
            "recommendations": assessment.recommendations,
            "confidence": assessment.confidence,
            "leaching_advisable": assessment.leaching_advisable,
        },
        "current_ec_ds_m": data.soil_ec_now,
        "threshold_ds_m": threshold,
        "critical_ds_m": critical,
        "series": [{"date": (t.sampled_at or t.created_at).isoformat() if t.sampled_at or t.created_at else None,
                    "ec": t.ec_ds_m, "depth": t.depth_m} for t in tests],
    }


@router.get("/farms/{farm_id}/salinity-overview")
def farm_salinity(farm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        zones = (
            db.query(Zone)
            .join(Block, Zone.block_id == Block.id)
            .join(Field, Block.field_id == Field.id)
            .filter(Field.farm_id == farm_id)
            .all()
        )
        out = []
        for z in zones:
            latest = db.query(SoilTest).filter_by(zone_id=z.id).order_by(SoilTest.sampled_at.desc()).first()
            level = "unknown"
            if latest and latest.ec_ds_m is not None and latest.ec_ds_m != 0:
                sp = None
                if z.block and z.block.crop_species_id:
                    sp = db.query(CropSpecies).filter_by(id=z.block.crop_species_id).first()
                thr = sp.salinity_threshold_ds_m if sp else 4.0
                crit = sp.critical_ec_ds_m if sp else thr * 1.5
                if latest.ec_ds_m >= crit:
                    level = "critical"
                elif latest.ec_ds_m >= thr:
                    level = "high"
                else:
                    level = "ok"
            out.append({"zone_id": z.id, "zone_name": z.name, "ec_ds_m": latest.ec_ds_m if latest else None,
                        "level": level})
        return out
    except Exception:
        import traceback; traceback.print_exc()
        return []
