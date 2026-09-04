from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.llm import TruthfulnessEvaluationOutput
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class ResponseTruthfulnessRequest(BaseModel):
    trace_id: int

@router.post("/response-truthfulness", response_model=TruthfulnessEvaluationOutput, status_code=status.HTTP_201_CREATED)
def evaluate_response_truthfulness(request: ResponseTruthfulnessRequest, db: Session = Depends(get_db)):
    """
    Evaluates whether the agent's response truthfully aligns with established execution reality.
    Relies on the output of the Deterministic Task Success Evaluator (Phase 5).
    """
    return EvaluationService.run_response_truthfulness_evaluation(request.trace_id, db)
