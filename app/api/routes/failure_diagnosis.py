from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.domain.models.core import (
    ExecutionTraceModel,
    TaskSuccessEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    FailureDiagnosisEvaluationModel,
    TestCaseModel,
    SuccessSpecificationModel
)
from app.schemas.evaluations import FailureDiagnosisResult
from app.services.trace_fact_extractor import TraceFactExtractor
from app.services.failure_diagnosis_evaluator import FailureDiagnosisEvaluator

router = APIRouter()
evaluator = FailureDiagnosisEvaluator()

class FailureDiagnosisRequest(BaseModel):
    trace_id: int

@router.post("/evaluations/failure-diagnosis", response_model=FailureDiagnosisResult)
def evaluate_failure_diagnosis(
    request: FailureDiagnosisRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate trace exists
    trace = db.execute(
        select(ExecutionTraceModel).where(ExecutionTraceModel.id == request.trace_id)
    ).scalar_one_or_none()
    if not trace:
        raise HTTPException(status_code=404, detail="Execution trace not found")

    # 2. Retrieve Phase 5 Task Success Evaluation
    task_success_eval = db.execute(
        select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == request.trace_id)
    ).scalar_one_or_none()
    if not task_success_eval:
        raise HTTPException(status_code=400, detail="Missing dependency: Task Success Evaluation (Phase 5) is required.")

    # 3. Retrieve Phase 7 Reliability Verdict Evaluation
    reliability_verdict_eval = db.execute(
        select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == request.trace_id)
    ).scalar_one_or_none()
    if not reliability_verdict_eval:
        raise HTTPException(status_code=400, detail="Missing dependency: Reliability Verdict Evaluation (Phase 7) is required.")

    # 4. Retrieve Phase 6 (only when available)
    response_truthfulness_eval = db.execute(
        select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == request.trace_id)
    ).scalar_one_or_none()

    # 5. Extract Trace Facts
    trace_facts = TraceFactExtractor.extract_facts(trace)

    # 6. Retrieve Success Specification
    test_case = db.execute(
        select(TestCaseModel).where(TestCaseModel.id == trace.test_case_id)
    ).scalar_one_or_none()
    
    success_spec = None
    if test_case and test_case.success_specification_id:
        success_spec = db.execute(
            select(SuccessSpecificationModel).where(SuccessSpecificationModel.id == test_case.success_specification_id)
        ).scalar_one_or_none()

    if not success_spec:
        raise HTTPException(status_code=400, detail="Missing dependency: Success Specification is required.")

    # 7. Run deterministic evaluation
    result = evaluator.evaluate(
        trace_id=request.trace_id,
        task_success_eval=task_success_eval,
        reliability_verdict_eval=reliability_verdict_eval,
        trace_facts=trace_facts,
        success_spec=success_spec,
        response_truthfulness_eval=response_truthfulness_eval
    )

    # 8. Persist diagnosis
    diagnosis_model = db.execute(
        select(FailureDiagnosisEvaluationModel).where(FailureDiagnosisEvaluationModel.trace_id == request.trace_id)
    ).scalar_one_or_none()

    if not diagnosis_model:
        diagnosis_model = FailureDiagnosisEvaluationModel(
            trace_id=request.trace_id,
            task_success_evaluation_id=task_success_eval.id,
            response_truthfulness_evaluation_id=response_truthfulness_eval.id if response_truthfulness_eval else None,
            reliability_verdict_evaluation_id=reliability_verdict_eval.id
        )
        db.add(diagnosis_model)

    diagnosis_model.failure_type = result.failure_type
    diagnosis_model.reliability_classification = result.reliability_classification
    diagnosis_model.root_cause_category = result.root_cause_category
    diagnosis_model.determination_method = result.determination_method.value
    diagnosis_model.summary = result.summary
    diagnosis_model.supporting_evidence = result.supporting_evidence
    diagnosis_model.contributing_signals = result.contributing_signals

    db.commit()
    db.refresh(diagnosis_model)

    # Convert model to result schema to include generated ID
    result.id = diagnosis_model.id
    return result
