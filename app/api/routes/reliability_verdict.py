from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.domain.models.core import ExecutionTraceModel, TaskSuccessEvaluationModel, ResponseTruthfulnessEvaluationModel, ReliabilityVerdictEvaluationModel
from app.schemas.evaluations import ReliabilityVerdictResult
from app.services.reliability_verdict_evaluator import ReliabilityVerdictEvaluator

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class ReliabilityVerdictRequest(BaseModel):
    trace_id: int

@router.post("/reliability-verdict", response_model=ReliabilityVerdictResult, status_code=status.HTTP_201_CREATED)
def evaluate_reliability_verdict(request: ReliabilityVerdictRequest, db: Session = Depends(get_db)):
    """
    Deterministically aggregates Task Success (Phase 5) and Response Truthfulness (Phase 6)
    into a combined Reliability Verdict.
    """
    trace_id = request.trace_id

    # 1. Fetch the trace
    db_trace = db.get(ExecutionTraceModel, trace_id)
    if not db_trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    # 2. Retrieve Task Success Evaluation
    task_success_eval = db.scalar(
        select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
    )
    if not task_success_eval:
        raise HTTPException(
            status_code=400, 
            detail="Deterministic task success evaluation must be completed before reliability verdict evaluation."
        )

    # 3. Retrieve Response Truthfulness Evaluation
    truthfulness_eval = db.scalar(
        select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == trace_id)
    )
    if not truthfulness_eval:
        raise HTTPException(
            status_code=400, 
            detail="Response truthfulness evaluation must be completed before reliability verdict evaluation."
        )

    # 4. Evaluate
    evaluator = ReliabilityVerdictEvaluator()
    evaluation_result = evaluator.evaluate(trace_id, task_success_eval, truthfulness_eval)

    # 5. Persist the Evaluation
    db_eval = db.scalar(
        select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == trace_id)
    )

    if db_eval:
        # Update existing
        db_eval.task_success_evaluation_id = evaluation_result.task_success_evaluation_id
        db_eval.response_truthfulness_evaluation_id = evaluation_result.response_truthfulness_evaluation_id
        db_eval.task_outcome = evaluation_result.task_outcome
        db_eval.response_truthfulness = evaluation_result.response_truthfulness
        db_eval.overall_evaluation_verdict = evaluation_result.overall_evaluation_verdict
        db_eval.reliability_classification = evaluation_result.reliability_classification
        db_eval.failure_type = evaluation_result.failure_type
        db_eval.determination_method = evaluation_result.determination_method.value
        db_eval.summary = evaluation_result.summary
    else:
        # Create new
        db_eval = ReliabilityVerdictEvaluationModel(
            trace_id=trace_id,
            task_success_evaluation_id=evaluation_result.task_success_evaluation_id,
            response_truthfulness_evaluation_id=evaluation_result.response_truthfulness_evaluation_id,
            task_outcome=evaluation_result.task_outcome,
            response_truthfulness=evaluation_result.response_truthfulness,
            overall_evaluation_verdict=evaluation_result.overall_evaluation_verdict,
            reliability_classification=evaluation_result.reliability_classification,
            failure_type=evaluation_result.failure_type,
            determination_method=evaluation_result.determination_method.value,
            summary=evaluation_result.summary
        )
        db.add(db_eval)

    db.commit()
    db.refresh(db_eval)
    
    evaluation_result.id = db_eval.id

    return evaluation_result
