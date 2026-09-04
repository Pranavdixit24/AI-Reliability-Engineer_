from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.evaluation_history import EvaluationHistoryResult
from app.services.evaluation_history_service import EvaluationHistoryService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])
service = EvaluationHistoryService()

@router.get("/traces/{trace_id}", response_model=EvaluationHistoryResult)
def get_evaluation_history(trace_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the complete evaluation history (all completed phases) for a given trace.
    Returns 404 if the trace does not exist.
    Missing evaluation stages are represented as null.
    """
    return service.get_history(trace_id, db)
