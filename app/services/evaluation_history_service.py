from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.domain.models.core import (
    ExecutionTraceModel,
    TaskSuccessEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    FailureDiagnosisEvaluationModel
)
from app.schemas.evaluation_history import EvaluationHistoryResult, ResponseTruthfulnessHistory
from app.schemas.evaluations import TaskSuccessEvaluationResult, ReliabilityVerdictResult, FailureDiagnosisResult

class EvaluationHistoryService:
    @staticmethod
    def get_history(trace_id: int, db: Session) -> EvaluationHistoryResult:
        # 1. Verify trace exists
        trace = db.get(ExecutionTraceModel, trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Execution trace not found")

        # 2. Fetch all evaluation models
        task_success_eval = db.scalar(
            select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
        )
        response_truthfulness_eval = db.scalar(
            select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == trace_id)
        )
        reliability_verdict_eval = db.scalar(
            select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == trace_id)
        )
        failure_diagnosis_eval = db.scalar(
            select(FailureDiagnosisEvaluationModel).where(FailureDiagnosisEvaluationModel.trace_id == trace_id)
        )

        # 3. Construct schemas
        task_success = None
        if task_success_eval:
            details = task_success_eval.structured_details or {}
            task_success = TaskSuccessEvaluationResult(
                id=task_success_eval.id,
                trace_id=task_success_eval.trace_id,
                task_success=task_success_eval.task_outcome,
                determination_method=task_success_eval.determination_method,
                overall_reason=details.get("overall_reason", ""),
                operation_evaluations=details.get("operation_evaluations", []),
                entity_evaluations=details.get("entity_evaluations", []),
                constraint_evaluations=details.get("constraint_evaluations", [])
            )

        response_truthfulness = ResponseTruthfulnessHistory.model_validate(response_truthfulness_eval) if response_truthfulness_eval else None
        reliability_verdict = ReliabilityVerdictResult.model_validate(reliability_verdict_eval) if reliability_verdict_eval else None
        failure_diagnosis = FailureDiagnosisResult.model_validate(failure_diagnosis_eval) if failure_diagnosis_eval else None

        # 4. Construct overall response
        return EvaluationHistoryResult(
            trace_id=trace_id,
            task_success=task_success,
            response_truthfulness=response_truthfulness,
            reliability_verdict=reliability_verdict,
            failure_diagnosis=failure_diagnosis
        )
