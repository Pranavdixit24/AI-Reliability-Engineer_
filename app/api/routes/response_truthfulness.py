from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
import json

from app.core.database import get_db
from app.domain.models.core import ExecutionTraceModel, TaskSuccessEvaluationModel, ResponseTruthfulnessEvaluationModel
from app.schemas.llm import TruthfulnessEvaluationOutput
from app.services.trace_fact_extractor import TraceFactExtractor
from app.services.response_truthfulness_evaluator import ResponseTruthfulnessEvaluator

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class ResponseTruthfulnessRequest(BaseModel):
    trace_id: int

@router.post("/response-truthfulness", response_model=TruthfulnessEvaluationOutput, status_code=status.HTTP_201_CREATED)
def evaluate_response_truthfulness(request: ResponseTruthfulnessRequest, db: Session = Depends(get_db)):
    """
    Evaluates whether the agent's response truthfully aligns with established execution reality.
    Relies on the output of the Deterministic Task Success Evaluator (Phase 5).
    """
    trace_id = request.trace_id
    
    # 1. Fetch the trace
    db_trace = db.get(ExecutionTraceModel, trace_id)
    if not db_trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    # 2. Extract facts
    extractor = TraceFactExtractor()
    trace_facts = extractor.extract_facts(db_trace)
    
    # 3. Retrieve Task Success Evaluation (Established Reality context)
    task_success_eval = db.scalar(
        select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
    )
    if not task_success_eval:
        raise HTTPException(
            status_code=400, 
            detail="Deterministic task success evaluation must be completed before truthfulness evaluation."
        )
        
    # 4. Evaluate Response Truthfulness
    evaluator = ResponseTruthfulnessEvaluator()
    evaluation_result = evaluator.evaluate(trace_facts, task_success_eval)
    
    # 5. Persist the Evaluation
    db_eval = db.scalar(
        select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == trace_id)
    )
    
    material_claims_json = [c.model_dump() for c in evaluation_result.material_claims]
    contradictions_json = [c.model_dump() for c in evaluation_result.contradictions]
    unsupported_claims_json = [c.model_dump() for c in evaluation_result.unsupported_claims]
    
    if db_eval:
        # Update existing
        db_eval.task_success_evaluation_id = task_success_eval.id
        db_eval.response_truthfulness = evaluation_result.response_truthfulness.value
        db_eval.response_outcome_claim = evaluation_result.response_outcome_claim.value
        db_eval.material_claims = material_claims_json
        db_eval.contradictions = contradictions_json
        db_eval.unsupported_claims = unsupported_claims_json
        db_eval.reasoning_summary = evaluation_result.reasoning_summary
        db_eval.confidence = evaluation_result.confidence
    else:
        # Create new
        db_eval = ResponseTruthfulnessEvaluationModel(
            trace_id=trace_id,
            task_success_evaluation_id=task_success_eval.id,
            response_truthfulness=evaluation_result.response_truthfulness.value,
            response_outcome_claim=evaluation_result.response_outcome_claim.value,
            material_claims=material_claims_json,
            contradictions=contradictions_json,
            unsupported_claims=unsupported_claims_json,
            reasoning_summary=evaluation_result.reasoning_summary,
            confidence=evaluation_result.confidence
        )
        db.add(db_eval)
        
    db.commit()
    
    return evaluation_result
