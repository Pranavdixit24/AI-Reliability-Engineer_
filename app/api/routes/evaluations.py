from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.evaluations import TaskSuccessEvaluationResult
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class TaskSuccessEvaluationRequest(BaseModel):
    trace_id: int

@router.post("/task-success", response_model=TaskSuccessEvaluationResult, status_code=status.HTTP_201_CREATED)
def evaluate_task_success(request: TaskSuccessEvaluationRequest, db: Session = Depends(get_db)):
    """
    Evaluates whether a task succeeded based purely on deterministic trace evidence.
    """
    return EvaluationService.run_task_success_evaluation(request.trace_id, db)
