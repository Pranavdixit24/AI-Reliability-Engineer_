from typing import List, Dict, Any, Optional
from app.schemas.core import SuccessSpecification
from app.schemas.facts import TraceFacts, ObservedOperation
from app.schemas.evaluations import (
    TaskSuccessEvaluationResult,
    OperationEvaluation,
    EntityEvaluation,
    ConstraintEvaluation,
)
from app.domain.enums import TaskOutcome, EvaluationVerdict

class TaskSuccessEvaluator:
    def evaluate(
        self, success_specification: SuccessSpecification, trace_facts: TraceFacts
    ) -> TaskSuccessEvaluationResult:
        
        operation_evaluations = self._evaluate_operations(
            success_specification.required_operations, trace_facts.observed_operations
        )
        
        entity_evaluations = self._evaluate_entities(
            success_specification.required_entities, trace_facts.observed_entities
        )
        
        constraint_evaluations = self._evaluate_constraints(
            success_specification.test_specific_constraints, trace_facts
        )
        
        # Determine overall outcome
        all_satisfied = True
        missing_evidence = False
        reasons = []

        for op_eval in operation_evaluations:
            if not op_eval.satisfied:
                all_satisfied = False
                reasons.append(f"Operation failed: {op_eval.operation} - {op_eval.reason}")
        
        for ent_eval in entity_evaluations:
            if ent_eval.match_status == "MISMATCH":
                all_satisfied = False
                reasons.append(f"Entity mismatch: {ent_eval.entity}")
            elif ent_eval.match_status == "MISSING_EVIDENCE":
                all_satisfied = False
                missing_evidence = True
                reasons.append(f"Missing entity evidence: {ent_eval.entity}")
                
        for constraint_eval in constraint_evaluations:
            if not constraint_eval.satisfied:
                all_satisfied = False
                reasons.append(f"Constraint failed: {constraint_eval.constraint_type} - {constraint_eval.reason}")
                
        if all_satisfied:
            task_outcome = TaskOutcome.SUCCESS
            overall_reason = "All deterministic success conditions satisfied."
        elif missing_evidence and len(reasons) == sum(1 for e in entity_evaluations if e.match_status == "MISSING_EVIDENCE"):
            # If the only failures are missing evidence, it might be indeterminate depending on the rules,
            # but usually missing a required entity is a failure unless evidence is genuinely unextractable.
            # To meet the requirement "Do not force a false PASS or FAIL when evidence is genuinely insufficient",
            # we can return UNKNOWN.
            task_outcome = TaskOutcome.UNKNOWN
            overall_reason = "Insufficient evidence to determine task success."
        else:
            task_outcome = TaskOutcome.FAILURE
            overall_reason = " | ".join(reasons)
            
        verdict = EvaluationVerdict.PASS if task_outcome == TaskOutcome.SUCCESS else (EvaluationVerdict.FAIL if task_outcome == TaskOutcome.FAILURE else EvaluationVerdict.UNCERTAIN)

        return TaskSuccessEvaluationResult(
            trace_id=trace_facts.trace_id or 0,
            task_success=task_outcome,
            final_verdict=verdict,
            overall_reason=overall_reason,
            operation_evaluations=operation_evaluations,
            entity_evaluations=entity_evaluations,
            constraint_evaluations=constraint_evaluations
        )

    def _evaluate_operations(
        self, required_operations: List[Any], observed_operations: List[ObservedOperation]
    ) -> List[OperationEvaluation]:
        evaluations = []
        observed_map = {op.operation_name: op for op in observed_operations}

        for req_op in required_operations:
            op_name = req_op.operation
            must_succeed = req_op.must_succeed
            requirement = "must_succeed" if must_succeed else "attempted"
            
            observed_op = observed_map.get(op_name)
            
            if not observed_op:
                evaluations.append(OperationEvaluation(
                    operation=op_name,
                    requirement=requirement,
                    satisfied=False,
                    reason="Required operation missing from trace facts."
                ))
                continue
            
            attempt_count = observed_op.attempt_count
            
            if not must_succeed:
                # Just needs to be attempted
                satisfied = attempt_count > 0
                evaluations.append(OperationEvaluation(
                    operation=op_name,
                    requirement=requirement,
                    satisfied=satisfied,
                    evidence="Tool call observed." if satisfied else None,
                    reason="Operation was attempted." if satisfied else "Operation not attempted.",
                    attempt_count=attempt_count
                ))
            else:
                # Must succeed
                # Check if there is eventual success
                has_success = False
                for attempt in observed_op.attempts:
                    if attempt.status == "success" or attempt.tool_result == "success": # Adjust based on actual status representation
                        has_success = True
                        break
                
                # Sometimes final_observed_status holds it
                if observed_op.final_observed_status == "success":
                    has_success = True
                    
                # A fallback logic, if attempts have a successful result
                if not has_success:
                    for attempt in observed_op.attempts:
                        if attempt.status and attempt.status.lower() in ("success", "completed", "ok"):
                            has_success = True
                            break
                        
                evaluations.append(OperationEvaluation(
                    operation=op_name,
                    requirement=requirement,
                    satisfied=has_success,
                    reason="Operation returned success." if has_success else "Operation returned failure.",
                    attempt_count=attempt_count
                ))

        return evaluations

    def _evaluate_entities(
        self, required_entities: Dict[str, Any], observed_entities: Dict[str, List[Any]]
    ) -> List[EntityEvaluation]:
        evaluations = []
        
        for entity_key, required_value in required_entities.items():
            observed_values = observed_entities.get(entity_key, [])
            
            if not observed_values:
                evaluations.append(EntityEvaluation(
                    entity=entity_key,
                    required_value=required_value,
                    match_status="MISSING_EVIDENCE"
                ))
                continue
                
            # Deterministic matching
            match = False
            matched_value = None
            for obs_val in observed_values:
                if str(obs_val).strip().lower() == str(required_value).strip().lower():
                    match = True
                    matched_value = obs_val
                    break
            
            if match:
                evaluations.append(EntityEvaluation(
                    entity=entity_key,
                    required_value=required_value,
                    observed_value=matched_value,
                    match_status="MATCH"
                ))
            else:
                evaluations.append(EntityEvaluation(
                    entity=entity_key,
                    required_value=required_value,
                    observed_value=observed_values[0] if observed_values else None,
                    match_status="MISMATCH"
                ))
                
        return evaluations

    def _evaluate_constraints(
        self, constraints: List[Dict[str, Any]], trace_facts: TraceFacts
    ) -> List[ConstraintEvaluation]:
        evaluations = []
        for constraint in constraints:
            constraint_type = constraint.get("type")
            
            if constraint_type == "required_final_state":
                expected_state = constraint.get("expected_state", {})
                observed_state = trace_facts.observed_final_state or {}
                
                satisfied = True
                for k, v in expected_state.items():
                    if str(observed_state.get(k, "")).strip().lower() != str(v).strip().lower():
                        satisfied = False
                        break
                        
                evaluations.append(ConstraintEvaluation(
                    constraint_type=constraint_type,
                    satisfied=satisfied,
                    reason="Final state matches expected state." if satisfied else "Final state mismatch."
                ))
                
            elif constraint_type == "required_operation_sequence":
                op_before = constraint.get("operation_before")
                op_after = constraint.get("operation_after")
                
                # Check timeline_summary for order
                idx_before = -1
                idx_after = -1
                
                for idx, event in enumerate(trace_facts.timeline_summary):
                    if event.get("action_type") == "TOOL_CALL":
                        tool_name = event.get("tool_name")
                        if tool_name == op_before and idx_before == -1:
                            idx_before = idx
                        if tool_name == op_after and idx_after == -1:
                            idx_after = idx
                            
                if idx_before != -1 and idx_after != -1 and idx_before < idx_after:
                    evaluations.append(ConstraintEvaluation(
                        constraint_type=constraint_type,
                        satisfied=True,
                        reason=f"{op_before} occurred before {op_after}."
                    ))
                else:
                    evaluations.append(ConstraintEvaluation(
                        constraint_type=constraint_type,
                        satisfied=False,
                        reason=f"{op_before} did not occur before {op_after} or one is missing."
                    ))
            elif constraint_type == "forbidden_operation":
                forbidden_op = constraint.get("operation")
                
                observed = False
                for op in trace_facts.observed_operations:
                    if op.operation_name == forbidden_op:
                        observed = True
                        break
                        
                evaluations.append(ConstraintEvaluation(
                    constraint_type=constraint_type,
                    satisfied=not observed,
                    reason=f"Forbidden operation {forbidden_op} was observed." if observed else f"Forbidden operation {forbidden_op} not observed."
                ))
            else:
                evaluations.append(ConstraintEvaluation(
                    constraint_type=constraint_type or "unknown",
                    satisfied=False,
                    reason="Unsupported or indeterminate evaluation constraint type."
                ))
                
        return evaluations
