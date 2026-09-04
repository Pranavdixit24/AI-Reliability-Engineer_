from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.evaluations import FailureDiagnosisResult
from app.services.evaluation_service import EvaluationService

router = APIRouter()

class FailureDiagnosisRequest(BaseModel):
    trace_id: int

@router.post("/evaluations/failure-diagnosis", response_model=FailureDiagnosisResult)
def evaluate_failure_diagnosis(
    request: FailureDiagnosisRequest,
    db: Session = Depends(get_db)
):
    return EvaluationService.run_failure_diagnosis_evaluation(request.trace_id, db)
