import pytest
from app.schemas.core import SuccessSpecification, RequiredOperation
from app.schemas.facts import TraceFacts, ObservedOperation, OperationAttempt
from app.services.task_success_evaluator import TaskSuccessEvaluator
from app.domain.enums import TaskOutcome

@pytest.fixture
def evaluator():
    return TaskSuccessEvaluator()

def test_complete_success(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True),
            RequiredOperation(operation="op2", must_succeed=False)
        ],
        required_entities={"city": "Delhi"},
        test_specific_constraints=[
            {"type": "required_operation_sequence", "operation_before": "op1", "operation_after": "op2"}
        ]
    )
    
    facts = TraceFacts(
        trace_id=1,
        observed_operations=[
            ObservedOperation(
                operation_name="op1",
                attempt_count=1,
                attempts=[OperationAttempt(attempt_number=1, status="success")]
            ),
            ObservedOperation(
                operation_name="op2",
                attempt_count=1,
                attempts=[OperationAttempt(attempt_number=1, status="failure")]
            )
        ],
        observed_entities={"city": ["Delhi"]},
        timeline_summary=[
            {"action_type": "TOOL_CALL", "tool_name": "op1"},
            {"action_type": "TOOL_CALL", "tool_name": "op2"}
        ]
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.SUCCESS
    assert len(result.operation_evaluations) == 2
    assert all(op.satisfied for op in result.operation_evaluations)
    assert result.entity_evaluations[0].match_status == "MATCH"
    assert result.constraint_evaluations[0].satisfied

def test_required_operation_missing(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True)
        ]
    )
    facts = TraceFacts(trace_id=1, observed_operations=[])
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.FAILURE
    assert not result.operation_evaluations[0].satisfied

def test_required_operation_failed(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True)
        ]
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_operations=[
            ObservedOperation(
                operation_name="op1",
                attempt_count=1,
                attempts=[OperationAttempt(attempt_number=1, status="failure")]
            )
        ]
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.FAILURE
    assert not result.operation_evaluations[0].satisfied

def test_retry_then_success(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True)
        ]
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_operations=[
            ObservedOperation(
                operation_name="op1",
                attempt_count=2,
                attempts=[
                    OperationAttempt(attempt_number=1, status="failure"),
                    OperationAttempt(attempt_number=2, status="success")
                ]
            )
        ]
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.SUCCESS
    assert result.operation_evaluations[0].satisfied

def test_wrong_entity(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_entities={"city": "Delhi"}
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_entities={"city": ["Mumbai"]}
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.FAILURE
    assert result.entity_evaluations[0].match_status == "MISMATCH"

def test_missing_entity_evidence(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_entities={"city": "Delhi"}
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_entities={}
    )
    
    result = evaluator.evaluate(spec, facts)
    # The requirement states: "The result must clearly preserve the missing evidence condition."
    # Our evaluator returns UNKNOWN if the only issues are MISSING_EVIDENCE
    assert result.task_success == TaskOutcome.UNKNOWN
    assert result.entity_evaluations[0].match_status == "MISSING_EVIDENCE"

def test_constraint_violation(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        test_specific_constraints=[
            {"type": "forbidden_operation", "operation": "delete_all"}
        ]
    )
    facts = TraceFacts(
        trace_id=1,
        observed_operations=[
            ObservedOperation(operation_name="delete_all")
        ]
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.FAILURE
    assert not result.constraint_evaluations[0].satisfied

def test_response_contradiction(evaluator):
    # trace shows deterministic success, but response claims failure
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True)
        ]
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_operations=[
            ObservedOperation(
                operation_name="op1",
                attempt_count=1,
                attempts=[OperationAttempt(attempt_number=1, status="success")]
            )
        ],
        observed_final_response="Sorry, I could not complete the task."
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.SUCCESS

def test_false_success_response(evaluator):
    # trace shows deterministic failure, but response claims success
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_operations=[
            RequiredOperation(operation="op1", must_succeed=True)
        ]
    )
    facts = TraceFacts(
        trace_id=1, 
        observed_operations=[
            ObservedOperation(
                operation_name="op1",
                attempt_count=1,
                attempts=[OperationAttempt(attempt_number=1, status="failure")]
            )
        ],
        observed_final_response="Task completed successfully."
    )
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.FAILURE

def test_insufficient_evidence(evaluator):
    spec = SuccessSpecification(
        task_type="test",
        task_description="test",
        required_entities={"critical_id": "123"}
    )
    facts = TraceFacts(trace_id=1)
    
    result = evaluator.evaluate(spec, facts)
    assert result.task_success == TaskOutcome.UNKNOWN
    assert "Insufficient evidence" in result.overall_reason
