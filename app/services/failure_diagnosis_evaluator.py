from typing import Optional, Dict, Any, List
from app.domain.enums import (
    TaskOutcome,
    ResponseTruthfulness,
    ReliabilityClassification,
    FailureType,
    RootCauseCategory,
    DeterminationMethod
)
from app.domain.models.core import (
    TaskSuccessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    SuccessSpecificationModel
)
from app.schemas.facts import TraceFacts
from app.schemas.evaluations import FailureDiagnosisResult, OperationEvaluation, EntityEvaluation, ConstraintEvaluation

class FailureDiagnosisEvaluator:
    """
    Deterministically diagnoses the root cause of an evaluation failure 
    using hard trace evidence and deterministic rules, without calling an LLM.
    """

    def evaluate(
        self,
        trace_id: int,
        task_success_eval: TaskSuccessEvaluationModel,
        reliability_verdict_eval: ReliabilityVerdictEvaluationModel,
        trace_facts: TraceFacts,
        success_spec: SuccessSpecificationModel,
        response_truthfulness_eval: Optional[ResponseTruthfulnessEvaluationModel] = None
    ) -> FailureDiagnosisResult:
        
        rel_class = ReliabilityClassification(reliability_verdict_eval.reliability_classification)
        failure_type = reliability_verdict_eval.failure_type

        # 1. Check for Unknown / Incomplete Evaluations
        if rel_class == ReliabilityClassification.EVALUATION_INCOMPLETE:
            return self._build_result(
                trace_id=trace_id,
                task_success_eval_id=task_success_eval.id,
                rel_verdict_eval_id=reliability_verdict_eval.id,
                resp_truth_eval_id=response_truthfulness_eval.id if response_truthfulness_eval else None,
                failure_type=failure_type,
                rel_class=rel_class.value,
                root_cause=RootCauseCategory.UNKNOWN.value,
                summary="Evaluation incomplete; insufficient evidence for a deterministic root cause.",
                supporting_evidence={"reason": "Reliability classification is EVALUATION_INCOMPLETE."}
            )

        # 2. Check for Reliable Success (No failure)
        if rel_class == ReliabilityClassification.RELIABLE_SUCCESS:
            return self._build_result(
                trace_id=trace_id,
                task_success_eval_id=task_success_eval.id,
                rel_verdict_eval_id=reliability_verdict_eval.id,
                resp_truth_eval_id=response_truthfulness_eval.id if response_truthfulness_eval else None,
                failure_type=failure_type,
                rel_class=rel_class.value,
                root_cause=RootCauseCategory.UNKNOWN.value, # Nullable/Not applicable conceptually, using UNKNOWN as there isn't a NONE category
                summary="No failure occurred. Task was a reliable success.",
                supporting_evidence={"reason": "Reliability classification is RELIABLE_SUCCESS."}
            )

        # We have a real failure (HONEST_FAILURE, FALSE_FAILURE, FALSE_SUCCESS). Let's deduce the root cause.
        # Priority Order:
        # 1. Explicit timeout/interruption
        # 2. Required operation attempted but failed
        # 3. Wrong entity selection
        # 4. Missing required operation
        # 5. Constraint violation
        # 6. Response-level failure
        
        # 1. Check for Timeout / Interrupted execution (INFRASTRUCTURE)
        # Assuming FailureType might be TIMEOUT, or facts show a timeout. 
        if failure_type == FailureType.TIMEOUT.value:
            return self._build_result(
                trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                response_truthfulness_eval.id if response_truthfulness_eval else None,
                failure_type, rel_class.value, RootCauseCategory.INFRASTRUCTURE.value,
                "The execution timed out or was interrupted.",
                {"failure_type_signal": "TIMEOUT"}
            )
            
        task_details = task_success_eval.structured_details
        op_evals = [OperationEvaluation(**op) for op in task_details.get("operation_evaluations", [])]
        entity_evals = [EntityEvaluation(**ent) for ent in task_details.get("entity_evaluations", [])]
        constraint_evals = [ConstraintEvaluation(**c) for c in task_details.get("constraint_evaluations", [])]

        # 2. Required operation attempted but failed (EXTERNAL_TOOL_FAILURE)
        # Check operations that were required but not satisfied, and where attempt_count > 0.
        for op_eval in op_evals:
            if not op_eval.satisfied and op_eval.attempt_count > 0:
                # To be absolutely sure, check trace facts for this operation. 
                # If it failed all attempts, it's a tool execution failure.
                op_fact = next((op for op in trace_facts.observed_operations if op.operation_name == op_eval.operation), None)
                if op_fact and op_fact.final_observed_status in ["FAILURE", "ERROR", "FAILED"]:
                    return self._build_result(
                        trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                        response_truthfulness_eval.id if response_truthfulness_eval else None,
                        failure_type, rel_class.value, RootCauseCategory.EXTERNAL_TOOL_FAILURE.value,
                        f"A required operation '{op_eval.operation}' was attempted but failed.",
                        {
                            "operation": op_eval.operation,
                            "attempt_count": op_eval.attempt_count,
                            "final_status": op_fact.final_observed_status
                        }
                    )

        # 3. Wrong entity selection (TOOL_PARAMETER_CONSTRUCTION)
        for ent_eval in entity_evals:
            if ent_eval.match_status == "MISMATCH":
                return self._build_result(
                    trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                    response_truthfulness_eval.id if response_truthfulness_eval else None,
                    failure_type, rel_class.value, RootCauseCategory.TOOL_PARAMETER_CONSTRUCTION.value,
                    f"A wrong entity was selected for '{ent_eval.entity}'.",
                    {
                        "entity": ent_eval.entity,
                        "required_value": ent_eval.required_value,
                        "observed_value": ent_eval.observed_value
                    }
                )

        # 4. Missing required operation (PLANNING_OR_WORKFLOW)
        for op_eval in op_evals:
            if not op_eval.satisfied and op_eval.attempt_count == 0:
                return self._build_result(
                    trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                    response_truthfulness_eval.id if response_truthfulness_eval else None,
                    failure_type, rel_class.value, RootCauseCategory.PLANNING_OR_WORKFLOW.value,
                    f"A required operation '{op_eval.operation}' was never attempted.",
                    {
                        "operation": op_eval.operation,
                        "attempt_count": 0
                    }
                )

        # 5. Constraint violation (APPLICATION_VALIDATION)
        for c_eval in constraint_evals:
            if not c_eval.satisfied:
                return self._build_result(
                    trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                    response_truthfulness_eval.id if response_truthfulness_eval else None,
                    failure_type, rel_class.value, RootCauseCategory.APPLICATION_VALIDATION.value,
                    f"A required constraint '{c_eval.constraint_type}' was violated.",
                    {
                        "constraint_type": c_eval.constraint_type,
                        "reason": c_eval.reason
                    }
                )

        # 6. Response-level failure (MODEL_REASONING)
        # e.g., FALSE_SUCCESS or FALSE_FAILURE where task outcome is not UNKNOWN, 
        # and there's no obvious execution failure from above.
        if rel_class in (ReliabilityClassification.FALSE_SUCCESS, ReliabilityClassification.FALSE_FAILURE):
            return self._build_result(
                trace_id, task_success_eval.id, reliability_verdict_eval.id, 
                response_truthfulness_eval.id if response_truthfulness_eval else None,
                failure_type, rel_class.value, RootCauseCategory.MODEL_REASONING.value,
                "The task executed, but the agent's response was untruthful or misleading.",
                {
                    "task_outcome": task_success_eval.task_outcome,
                    "reliability_classification": rel_class.value
                }
            )

        # 7. Fallback Unknown
        return self._build_result(
            trace_id, task_success_eval.id, reliability_verdict_eval.id, 
            response_truthfulness_eval.id if response_truthfulness_eval else None,
            failure_type, rel_class.value, RootCauseCategory.UNKNOWN.value,
            "Could not deterministically identify the root cause from the available evidence.",
            {"reason": "No deterministic rule matched the evidence."}
        )

    def _build_result(
        self,
        trace_id: int,
        task_success_eval_id: int,
        rel_verdict_eval_id: int,
        resp_truth_eval_id: Optional[int],
        failure_type: Optional[str],
        rel_class: str,
        root_cause: str,
        summary: str,
        supporting_evidence: Dict[str, Any]
    ) -> FailureDiagnosisResult:
        return FailureDiagnosisResult(
            trace_id=trace_id,
            task_success_evaluation_id=task_success_eval_id,
            response_truthfulness_evaluation_id=resp_truth_eval_id,
            reliability_verdict_evaluation_id=rel_verdict_eval_id,
            failure_type=failure_type,
            reliability_classification=rel_class,
            root_cause_category=root_cause,
            determination_method=DeterminationMethod.DETERMINISTIC_RULE,
            summary=summary,
            supporting_evidence=supporting_evidence,
            contributing_signals=[]
        )
