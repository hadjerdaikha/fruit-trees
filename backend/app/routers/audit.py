"""Audit log routes."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog
from ..security import get_current_user, require_roles

router = APIRouter(prefix="/audit", tags=["audit"])


def record_audit(db: Session, actor_id, action, entity_type, entity_id, changes=None):
    db.add(AuditLog(
        actor_id=actor_id, action=action, entity_type=entity_type,
        entity_id=entity_id, changes=json.dumps(changes) if changes else None,
    ))
    db.commit()


@router.get("/logs")
def list_logs(entity_type: str = None, entity_id: int = None, limit: int = 200,
              db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    rows = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return rows
