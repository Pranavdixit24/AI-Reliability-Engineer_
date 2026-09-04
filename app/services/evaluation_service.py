from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from app.domain.models.core import (
    ExecutionTraceModel,
    TaskSuccessEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    FailureDiagnosisEvaluationModel,
    TestCaseModel,
    SuccessSpecificationModel
)
from app.schemas.core import SuccessSpecification
from app.schemas.evaluations import (
    TaskSuccessEvaluationResult,
    ReliabilityVerdictResult,
    FailureDiagnosisResult
)
from app.schemas.llm import TruthfulnessEvaluationOutput

from app.services.trace_fact_extractor import TraceFactExtractor
from app.services.task_success_evaluator import TaskSuccessEvaluator
from app.services.response_truthfulness_evaluator import ResponseTruthfulnessEvaluator
from app.services.reliability_verdict_evaluator import ReliabilityVerdictEvaluator
from app.services.failure_diagnosis_evaluator import FailureDiagnosisEvaluator

class EvaluationService:
    @staticmethod
    def run_task_success_evaluation(trace_id: int, db: Session) -> TaskSuccessEvaluationResult:
        # 1. Fetch the trace
        db_trace = db.get(ExecutionTraceModel, trace_id)
        if not db_trace:
            raise HTTPException(status_code=404, detail="Trace not found")
            
        # 2. Extract facts
        extractor = TraceFactExtractor()
        trace_facts = extractor.extract_facts(db_trace)
        
        # 3. Load Success Specification
        test_case = db_trace.test_case
        if not test_case:
            raise HTTPException(status_code=400, detail="Trace is not associated with a test case")
            
        success_spec_model = test_case.success_specification
        if not success_spec_model:
            raise HTTPException(status_code=400, detail="Test case is missing success specification")
            
        success_spec = SuccessSpecification.model_validate(success_spec_model)

        # 4. Evaluate Task Success
        evaluator = TaskSuccessEvaluator()
        evaluation_result = evaluator.evaluate(success_spec, trace_facts)
        
        # 5. Persist the Evaluation
        db_eval = db.scalar(
            select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
        )
        
        if db_eval:
            # Update existing
            db_eval.task_outcome = evaluation_result.task_success.value
            db_eval.determination_method = evaluation_result.determination_method.value
            db_eval.structured_details = evaluation_result.model_dump(mode='json')
        else:
            # Create new
            db_eval = TaskSuccessEvaluationModel(
                trace_id=trace_id,
                test_case_id=test_case.id,
                task_outcome=evaluation_result.task_success.value,
                determination_method=evaluation_result.determination_method.value,
                structured_details=evaluation_result.model_dump(mode='json')
            )
            db.add(db_eval)
            
        db.commit()
        evaluation_result.id = db_eval.id
        
        return evaluation_result

    @staticmethod
    def run_response_truthfulness_evaluation(trace_id: int, db: Session) -> TruthfulnessEvaluationOutput:
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

    @staticmethod
    def run_reliability_verdict_evaluation(trace_id: int, db: Session) -> ReliabilityVerdictResult:
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

    @staticmethod
    def run_failure_diagnosis_evaluation(trace_id: int, db: Session) -> FailureDiagnosisResult:
        # 1. Validate trace exists
        trace = db.execute(
            select(ExecutionTraceModel).where(ExecutionTraceModel.id == trace_id)
        ).scalar_one_or_none()
        if not trace:
            raise HTTPException(status_code=404, detail="Execution trace not found")

        # 2. Retrieve Phase 5 Task Success Evaluation
        task_success_eval = db.execute(
            select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
        ).scalar_one_or_none()
        if not task_success_eval:
            raise HTTPException(status_code=400, detail="Missing dependency: Task Success Evaluation (Phase 5) is required.")

        # 3. Retrieve Phase 7 Reliability Verdict Evaluation
        reliability_verdict_eval = db.execute(
            select(ReliabilityVerdictEvaluationModel).where(ReliabilityVerdictEvaluationModel.trace_id == trace_id)
        ).scalar_one_or_none()
        if not reliability_verdict_eval:
            raise HTTPException(status_code=400, detail="Missing dependency: Reliability Verdict Evaluation (Phase 7) is required.")

        # 4. Retrieve Phase 6 (only when available)
        response_truthfulness_eval = db.execute(
            select(ResponseTruthfulnessEvaluationModel).where(ResponseTruthfulnessEvaluationModel.trace_id == trace_id)
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
        evaluator = FailureDiagnosisEvaluator()
        result = evaluator.evaluate(
            trace_id=trace_id,
            task_success_eval=task_success_eval,
            reliability_verdict_eval=reliability_verdict_eval,
            trace_facts=trace_facts,
            success_spec=success_spec,
            response_truthfulness_eval=response_truthfulness_eval
        )

        # 8. Persist diagnosis
        diagnosis_model = db.execute(
            select(FailureDiagnosisEvaluationModel).where(FailureDiagnosisEvaluationModel.trace_id == trace_id)
        ).scalar_one_or_none()

        if not diagnosis_model:
            diagnosis_model = FailureDiagnosisEvaluationModel(
                trace_id=trace_id,
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

        result.id = diagnosis_model.id
        return result
