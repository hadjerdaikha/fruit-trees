"""Task management routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Task
from ..schemas import TaskComplete, TaskCreate, TaskUpdate
from ..security import get_current_user, require_min_role

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def list_tasks(farm_id: int = None, status: str = None, assignee_id: int = None, limit: int = 200,
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Task)
    if farm_id:
        q = q.filter(Task.farm_id == farm_id)
    if status:
        q = q.filter(Task.status == status)
    if assignee_id:
        q = q.filter(Task.assignee_id == assignee_id)
    rows = q.order_by(Task.due_date.asc(), Task.created_at.desc()).limit(limit).all()
    return rows


@router.post("")
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user=Depends(require_min_role("manager"))):
    task = Task(**payload.model_dump())
    task.assigned_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/me")
def my_tasks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    tasks = db.query(Task).filter(
        (Task.assignee_id == user.id) | (Task.assignee_role == user.role)
    ).order_by(Task.due_date.asc()).all()
    return tasks


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db),
                user=Depends(require_min_role("manager"))):
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/complete")
def complete_task(task_id: int, payload: TaskComplete, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "completed"
    if payload.completion_evidence:
        task.completion_evidence = payload.completion_evidence
    if payload.after_photo_id:
        task.after_photo_id = payload.after_photo_id
    if payload.notes:
        task.notes = payload.notes
    db.commit()

    # if linked to an alert, mark it resolved
    if task.alert_id:
        alert = db.query(Alert).filter_by(id=task.alert_id).first()
        if alert and alert.status != "resolved":
            alert.status = "in_progress"
            db.commit()
    return task


@router.post("/auto-from-alert/{alert_id}")
def create_task_from_alert(alert_id: int, db: Session = Depends(get_db),
                           user=Depends(require_min_role("manager"))):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    existing = db.query(Task).filter_by(alert_id=alert_id).first()
    title = alert.title if alert.title else alert.alert_type
    description = alert.recommended_action or alert.description
    role = "technician" if alert.alert_type in ("irrigation", "wind", "equipment") else "manager"
    if not existing:
        task = Task(
            farm_id=alert.farm_id, zone_id=alert.zone_id, alert_id=alert.id,
            title=f"Action: {title}", description=description,
            assignee_role=role, assigned_at=datetime.utcnow(), status="open",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    return existing
