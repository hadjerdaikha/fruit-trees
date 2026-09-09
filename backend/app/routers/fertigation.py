"""Fertigation planning, applications, and nutrient budget routes."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.fertigation import FertigationEngine, FertigationInput, FertigationResult
from ..models import (
    Block, CropSpecies, FertilizationProgram, FertilizerApplication, FertilizerProduct,
    LeafAnalysis, SoilTest, Variety, Zone,
)
from ..schemas import FertilizerApplicationCreate, FertigationRequest
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/fertigation", tags=["fertigation"])


@router.post("/program")
def generate_program(payload: FertigationRequest, db: Session = Depends(get_db),
                     user=Depends(require_min_role("agronomist"))):
    zone = db.query(Zone).filter_by(id=payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    block = db.query(Block).filter_by(id=zone.block_id).first()
    species = db.query(CropSpecies).filter_by(id=block.crop_species_id).first() if block and block.crop_species_id else None
    species_code = species.code if species else "olive"
    variety = db.query(Variety).filter_by(id=block.variety_id).first() if block and block.variety_id else None

    soil_test = db.query(SoilTest).filter_by(zone_id=zone.id).order_by(SoilTest.sampled_at.desc()).first()
    leaf = db.query(LeafAnalysis).filter_by(zone_id=zone.id).order_by(LeafAnalysis.sampled_at.desc()).first()

    inp = FertigationInput(
        species_code=species_code,
        tree_age_years=block.tree_age_years if block else None,
        tree_count=block.tree_count if block else 1,
        tree_spacing_m=block.tree_spacing_m if block else None,
        area_m2=area_m2_for(zone, block),
        expected_yield_kg=payload.expected_yield_kg,
        growth_stage=payload.stage_key or "fruit_development",
        soil_test={"p_ppm": soil_test.p_ppm, "k_ppm": soil_test.k_ppm} if soil_test else None,
        leaf_analysis=json.loads(leaf.nutrient) if leaf and leaf.nutrient else None,
        water_ec_ds_m=zone.water_ec_ds_m,
        soil_ec_ds_m=zone.soil_ec_ds_m,
    )

    engine = FertigationEngine()
    result: FertigationResult = engine.plan(inp)

    program = FertilizationProgram(
        zone_id=zone.id,
        species_id=block.crop_species_id if block else None,
        variety_id=block.variety_id if block else None,
        stage_key=payload.stage_key,
        generated_at=datetime.utcnow(),
        nutrient_req=json.dumps(result.nutrient_requirements),
        recommendations=json.dumps({
            "products": result.product_recommendations,
            "timing": result.application_timing,
            "splits": result.split_applications,
            "per_tree": result.quantity_per_tree,
            "per_ha": result.quantity_per_ha,
        }),
        nutrient_budget=json.dumps(result.nutrient_budget),
        status="draft",
    )
    db.add(program)
    db.commit()
    db.refresh(program)

    return {
        "id": program.id,
        "zone_id": zone.id,
        "species_code": species_code,
        "species_name": species.name_en if species else None,
        "variety": variety.name if variety else None,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "nutrient_requirements": result.nutrient_requirements,
        "products": result.product_recommendations,
        "timing": result.application_timing,
        "splits": result.split_applications,
        "quantity_per_tree": result.quantity_per_tree,
        "quantity_per_ha": result.quantity_per_ha,
        "safety_warnings": result.safety_warnings,
        "confidence": result.confidence,
        "status": program.status,
    }


def area_m2_for(zone: Zone, block: Block):
    if block and block.tree_count and block.tree_spacing_m:
        return block.tree_count * block.tree_spacing_m ** 2
    return None


@router.get("/zones/{zone_id}/programs")
def list_programs(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(FertilizationProgram).filter_by(zone_id=zone_id).order_by(FertilizationProgram.generated_at.desc()).all()


@router.get("/products")
def list_products(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(FertilizerProduct).all()


@router.post("/applications")
def log_application(payload: FertilizerApplicationCreate, db: Session = Depends(get_db),
                    user=Depends(require_min_role("technician"))):
    app = FertilizerApplication(**payload.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/zones/{zone_id}/applications")
def list_applications(zone_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(FertilizerApplication).filter_by(zone_id=zone_id).order_by(FertilizerApplication.applied_at.desc()).all()
