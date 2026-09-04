from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from typing import List

from app.schemas.batch_evaluations import BatchEvaluationRequest, BatchEvaluationResponse, TraceEvaluationResult
from app.domain.models.core import (
    ExecutionTraceModel,
    TaskSuccessEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    FailureDiagnosisEvaluationModel
)
from app.domain.enums import ReliabilityClassification

from app.services.evaluation_service import EvaluationService
import traceback

MAX_BATCH_SIZE = 15

class BatchEvaluationService:
    def evaluate_batch(self, request: BatchEvaluationRequest, db: Session) -> BatchEvaluationResponse:
        trace_ids = request.trace_ids
        
        if len(trace_ids) > MAX_BATCH_SIZE:
            raise HTTPException(status_code=400, detail=f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE}")
            
        # Deduplicate while preserving order
        unique_trace_ids = list(dict.fromkeys(trace_ids))
        
        results: List[TraceEvaluationResult] = []
        completed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for trace_id in unique_trace_ids:
            try:
                # 1. Verify Trace exists
                trace = db.get(ExecutionTraceModel, trace_id)
                if not trace:
                    raise HTTPException(status_code=404, detail="Execution trace not found")
                
                # Check what phases already exist
                has_p5 = db.execute(select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)).scalar_one_or_none() is not None
                has_p6 = db.execute(select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == trace_id)).scalar_one_or_none() is not None
                phase7 = db.execute(select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == trace_id)).scalar_one_or_none()
                has_p7 = phase7 is not None
                has_p8 = db.execute(select(FailureDiagnosisEvaluationModel).where(FailureDiagnosisEvaluationModel.trace_id == trace_id)).scalar_one_or_none() is not None
                
                if has_p5 and has_p6 and has_p7:
                    # check if phase 8 is applicable
                    requires_p8 = phase7.reliability_classification != ReliabilityClassification.RELIABLE_SUCCESS.value
                    if not requires_p8 or (requires_p8 and has_p8):
                        results.append(TraceEvaluationResult(trace_id=trace_id, status="SKIPPED", skipped_reason="Already fully evaluated"))
                        skipped_count += 1
                        continue
                
                # Run missing phases sequentially
                if not has_p5:
                    EvaluationService.run_task_success_evaluation(trace_id, db)
                
                if not has_p6:
                    EvaluationService.run_response_truthfulness_evaluation(trace_id, db)
                    
                if not has_p7:
                    EvaluationService.run_reliability_verdict_evaluation(trace_id, db)
                    
                # Re-fetch Phase 7 if we just generated it
                if not phase7:
                    phase7 = db.execute(select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == trace_id)).scalar_one_or_none()
                
                if phase7:
                    requires_p8 = phase7.reliability_classification != ReliabilityClassification.RELIABLE_SUCCESS.value
                    if requires_p8 and not has_p8:
                        EvaluationService.run_failure_diagnosis_evaluation(trace_id, db)
                    
                results.append(TraceEvaluationResult(trace_id=trace_id, status="COMPLETED"))
                completed_count += 1
                
            except HTTPException as e:
                db.rollback() # Important: clean the session state
                results.append(TraceEvaluationResult(trace_id=trace_id, status="FAILED", error=str(e.detail)))
                failed_count += 1
            except Exception as e:
                db.rollback() # Important: clean the session state
                results.append(TraceEvaluationResult(trace_id=trace_id, status="FAILED", error=str(e)))
                failed_count += 1
                
        return BatchEvaluationResponse(
            requested_count=len(trace_ids),
            unique_requested_count=len(unique_trace_ids),
            completed_count=completed_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results
        )
