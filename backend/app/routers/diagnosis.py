"""Image upload and AI diagnosis routes."""

import json
import os
import uuid
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from ..ai.pipeline import (
    ImageAnalysisResult, ImageAnalyzer, ImageValidationError, capture_guidance,
)
from ..config import settings
from ..database import get_db
from ..engines.differential import ContextData
from ..models import AIDiagnosis, Farm, ImageUpload, Zone
from ..schemas import DiagnosisReviewRequest
from ..security import get_current_user, require_min_role

router = APIRouter(tags=["ai-diagnosis"])


@router.get("/diagnosis/guidance")
def guidance(user=Depends(get_current_user)):
    return {"guidance": capture_guidance()}


@router.post("/images/upload")
async def upload_image(
    uploader: str = Form(...),
    zone_id: int = Form(None),
    tree_id: int = Form(None),
    caption: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    content = await file.read()
    try:
        pil_image = Image.open(BytesIO(content))
        pil_image.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupt image file")

    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.upload_dir, name)
    with open(path, "wb") as fh:
        fh.write(content)

    img = ImageUpload(
        uploader_id=user.id,
        zone_id=zone_id,
        tree_id=tree_id,
        file_path=path,
        caption=caption,
        captured_at=datetime.utcnow(),
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return {"id": img.id, "file_path": path, "zone_id": zone_id, "tree_id": tree_id}


@router.post("/images/{image_id}/analyze")
def analyze_image(image_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    image = db.query(ImageUpload).filter_by(id=image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    pil_image = Image.open(image.file_path)
    pil_image.load()

    # build context from zone if available
    context: ContextData | None = None
    if image.zone_id:
        zone = db.query(Zone).filter_by(id=image.zone_id).first()
        if zone:
            context = ContextData(
                soil_ec_ds_m=zone.soil_ec_ds_m,
                water_ec_ds_m=zone.water_ec_ds_m,
                soil_ph=zone.soil_ph,
            )

    analyzer = ImageAnalyzer()
    try:
        result: ImageAnalysisResult = analyzer.analyze(pil_image, context)
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    diag = AIDiagnosis(
        image_upload_id=image.id,
        zone_id=image.zone_id,
        tree_id=image.tree_id,
        primary_diagnosis=result.primary_diagnosis,
        confidence_pct=result.confidence_pct,
        alternatives=json.dumps(result.alternatives),
        severity=result.severity,
        affected_part=result.affected_part,
        visible_symptoms=json.dumps(result.visible_symptoms),
        recommended_action=result.recommended_action,
        requires_expert=result.requires_expert,
        status="pending",
        model_version=result.model_version,
    )
    db.add(diag)
    db.commit()
    db.refresh(diag)

    return {
        "id": diag.id,
        "possible_primary_diagnosis": result.primary_diagnosis,
        "confidence_pct": result.confidence_pct,
        "alternative_diagnoses": result.alternatives,
        "severity": result.severity,
        "affected_part": result.affected_part,
        "visible_symptoms": result.visible_symptoms,
        "recommended_action": result.recommended_action,
        "requires_expert": result.requires_expert,
        "status": diag.status,
        "model_version": result.model_version,
    }


@router.get("/diagnoses/{diag_id}")
def get_diagnosis(diag_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    diag = db.query(AIDiagnosis).filter_by(id=diag_id).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return _serialize_diag(diag)


@router.post("/diagnoses/{diag_id}/review")
def review_diagnosis(diag_id: int, payload: DiagnosisReviewRequest, db: Session = Depends(get_db),
                     user=Depends(require_min_role("agronomist"))):
    diag = db.query(AIDiagnosis).filter_by(id=diag_id).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    diag.review_decision = payload.decision
    diag.reviewed_by = user.id
    diag.reviewed_at = datetime.utcnow()
    diag.status = "reviewed"
    if payload.decision == "modify" and payload.modified_diagnosis:
        diag.primary_diagnosis = payload.modified_diagnosis
    db.commit()
    db.refresh(diag)
    return _serialize_diag(diag)


def _serialize_diag(diag: AIDiagnosis):
    return {
        "id": diag.id,
        "possible_primary_diagnosis": diag.primary_diagnosis,
        "confidence_pct": diag.confidence_pct,
        "alternative_diagnoses": json.loads(diag.alternatives) if diag.alternatives else [],
        "severity": diag.severity,
        "affected_part": diag.affected_part,
        "visible_symptoms": json.loads(diag.visible_symptoms) if diag.visible_symptoms else [],
        "recommended_action": diag.recommended_action,
        "requires_expert": diag.requires_expert,
        "status": diag.status,
        "review_decision": diag.review_decision,
        "reviewed_by": diag.reviewed_by,
        "model_version": diag.model_version,
    }
