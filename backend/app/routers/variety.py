"""Variety suitability tool routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.variety import Conditions, VarietyEngine, VarietyRating
from ..models import CropSpecies, Variety
from ..schemas import VarietySuitabilityRequest
from ..security import get_current_user

router = APIRouter(prefix="/variety", tags=["variety"])


@router.post("/suitability")
def rank_varieties(payload: VarietySuitabilityRequest, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    conditions = Conditions(
        max_summer_temp_c=payload.max_summer_temp_c,
        min_winter_temp_c=payload.min_winter_temp_c,
        frost_risk=payload.frost_risk,
        water_availability=payload.water_availability,
        water_ec_ds_m=payload.water_ec_ds_m,
        soil_ec_ds_m=payload.soil_ec_ds_m,
        soil_type=payload.soil_type,
        market_objective=payload.market_objective,
    )

    engine = VarietyEngine()
    results = []
    species = db.query(CropSpecies).all()
    for sp in species:
        for var in db.query(Variety).filter_by(species_id=sp.id).all():
            dictv = {
                "id": var.id, "name": var.name, "species_name": sp.name_en,
                "heat_tolerance": var.heat_tolerance, "drought_tolerance": var.drought_tolerance,
                "salinity_tolerance": var.salinity_tolerance, "frost_tolerance": var.frost_tolerance,
                "soil_compatibility": var.soil_compatibility, "water_requirement": var.water_requirement,
                "disease_susceptibility": var.disease_susceptibility, "market_suitability": var.market_suitability,
                "management_intensity": var.management_intensity,
            }
            rating: VarietyRating = engine.evaluate(dictv, conditions)
            results.append({
                "variety_id": rating.variety_id,
                "variety_name": rating.variety_name,
                "species": rating.species,
                "suitability_score": rating.suitability_score,
                "strengths": rating.strengths,
                "limitations": rating.limitations,
                "main_risks": rating.main_risks,
                "management_intensity": rating.management_intensity,
            })

    results.sort(key=lambda r: r["suitability_score"], reverse=True)
    return {
        "note": "Varieties are ranked as 'more suitable under the selected conditions'; no variety is universally 'best'.",
        "conditions": payload.model_dump(),
        "results": results,
    }
