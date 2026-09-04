from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.evaluations import ReliabilityVerdictResult
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class ReliabilityVerdictRequest(BaseModel):
    trace_id: int

@router.post("/reliability-verdict", response_model=ReliabilityVerdictResult, status_code=status.HTTP_201_CREATED)
def evaluate_reliability_verdict(request: ReliabilityVerdictRequest, db: Session = Depends(get_db)):
    """
    Deterministically aggregates Task Success (Phase 5) and Response Truthfulness (Phase 6)
    into a combined Reliability Verdict.
    """
    return EvaluationService.run_reliability_verdict_evaluation(request.trace_id, db)
