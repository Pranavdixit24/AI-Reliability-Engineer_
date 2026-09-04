from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.schemas.batch_evaluations import BatchEvaluationRequest, BatchEvaluationResponse
from app.services.batch_evaluation_service import BatchEvaluationService

router = APIRouter(prefix="/evaluations", tags=["Batch Evaluations"])
service = BatchEvaluationService()

@router.post("/batch", response_model=BatchEvaluationResponse, status_code=status.HTTP_200_OK)
def evaluate_batch(request: BatchEvaluationRequest, db: Session = Depends(get_db)):
    """
    Evaluates a small, representative, controlled set of existing traces automatically.
    This safely orchestrates Phase 5-8 services for each trace without duplicating logic.
    Maximum batch size is enforced to prevent unchecked LLM usage.
    """
    return service.evaluate_batch(request, db)
