"""Differential diagnosis analysis routes (context-driven)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engines.differential import ContextData, DifferentialEngine, SymptomEvidence
from ..models import Block, CropSpecies, SoilTest, Zone
from ..security import require_min_role

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.post("/differential")
def differential(
    zone_id: int,
    symptoms: dict = None,
    db: Session = Depends(get_db),
    user=Depends(require_min_role("agronomist")),
):
    zone = db.query(Zone).filter_by(id=zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    symptoms = symptoms or {}
    evidence = SymptomEvidence(
        symptom=symptoms.get("symptom", ""),
        affected_part=symptoms.get("affected_part", "leaf"),
        interveinal=symptoms.get("interveinal"),
        marginal_burn=symptoms.get("marginal_burn"),
        chlorosis=symptoms.get("chlorosis"),
        necrosis=symptoms.get("necrosis"),
        wilting=symptoms.get("wilting"),
        lesion=symptoms.get("lesion"),
        spots=symptoms.get("spots"),
        powdery=symptoms.get("powdery"),
    )

    # build context
    st = db.query(SoilTest).filter_by(zone_id=zone.id).order_by(SoilTest.sampled_at.desc()).first()
    ctx = ContextData(
        soil_ph=zone.soil_ph,
        soil_ec_ds_m=zone.soil_ec_ds_m or (st.ec_ds_m if st else None),
        water_ec_ds_m=zone.water_ec_ds_m,
        species=zone.block.name if zone.block else None,
    )

    engine = DifferentialEngine()
    ranked = engine.rank(evidence, ctx)
    return {
        "zone_id": zone_id,
        "note": "These are ranked possibilities, not confirmed diagnoses. Verify before major action.",
        "ranking": [
            {"cause": h.cause, "probability": h.probability, "kind": h.kind,
             "verification": h.verification, "action_guidance": h.action_guidance}
            for h in ranked
        ],
    }
