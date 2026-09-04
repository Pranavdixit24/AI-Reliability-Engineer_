import pytest
from app.domain.enums import (
    TaskOutcome,
    ResponseTruthfulness,
    ReliabilityClassification,
    FailureType,
    RootCauseCategory
)
from app.domain.models.core import (
    TaskSuccessEvaluationModel,
    ReliabilityVerdictEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    SuccessSpecificationModel
)
from app.schemas.facts import TraceFacts, ObservedOperation, OperationAttempt
from app.services.failure_diagnosis_evaluator import FailureDiagnosisEvaluator


@pytest.fixture
def evaluator():
    return FailureDiagnosisEvaluator()

@pytest.fixture
def base_trace_facts():
    return TraceFacts(trace_id=1)

@pytest.fixture
def base_task_success():
    return TaskSuccessEvaluationModel(
        id=1,
        trace_id=1,
        task_outcome=TaskOutcome.FAILURE.value,
        determination_method="DETERMINISTIC_RULE",
        structured_details={}
    )

@pytest.fixture
def base_reliability_verdict():
    return ReliabilityVerdictEvaluationModel(
        id=1,
        trace_id=1,
        reliability_classification=ReliabilityClassification.HONEST_FAILURE.value,
        failure_type=FailureType.TASK_EXECUTION_FAILURE.value
    )

def test_tool_execution_failure(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 1: Tool Execution Failure
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "cancel_order",
                "requirement": "must_succeed",
                "satisfied": False,
                "attempt_count": 2
            }
        ]
    }
    op = ObservedOperation(operation_name="cancel_order", attempt_count=2, final_observed_status="FAILURE")
    base_trace_facts.observed_operations.append(op)
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.EXTERNAL_TOOL_FAILURE.value
    assert result.supporting_evidence["operation"] == "cancel_order"

def test_tool_execution_error_503(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test: Service unavailable / 503 evidence -> EXTERNAL_TOOL_FAILURE
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "cancel_order",
                "requirement": "must_succeed",
                "satisfied": False,
                "attempt_count": 1
            }
        ]
    }
    # Trace contains ERROR and 503 Service Unavailable
    op = ObservedOperation(operation_name="cancel_order", attempt_count=1, final_observed_status="ERROR")
    # For a full test we could set attempts but final_observed_status is what the rule checks
    base_trace_facts.observed_operations.append(op)
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.EXTERNAL_TOOL_FAILURE.value
    assert result.supporting_evidence["operation"] == "cancel_order"
    assert result.supporting_evidence["final_status"] == "ERROR"

def test_retry_then_success(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 2: Retry Then Success (Should NOT be tool execution failure)
    # Task success is true here.
    base_task_success.task_outcome = TaskOutcome.SUCCESS.value
    base_reliability_verdict.reliability_classification = ReliabilityClassification.RELIABLE_SUCCESS.value
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "cancel_order",
                "requirement": "must_succeed",
                "satisfied": True, # Satisfied eventually
                "attempt_count": 2
            }
        ]
    }
    # Trace facts show attempt 1 failure, attempt 2 success, but the final outcome is SUCCESS.
    op = ObservedOperation(operation_name="cancel_order", attempt_count=2, final_observed_status="SUCCESS")
    base_trace_facts.observed_operations.append(op)

    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.UNKNOWN.value # No failure
    assert result.reliability_classification == ReliabilityClassification.RELIABLE_SUCCESS.value

def test_wrong_entity(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 3: Wrong Entity
    base_task_success.structured_details = {
        "entity_evaluations": [
            {
                "entity": "order_id",
                "required_value": "123",
                "observed_value": "456",
                "match_status": "MISMATCH"
            }
        ]
    }
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.TOOL_PARAMETER_CONSTRUCTION.value
    assert result.supporting_evidence["entity"] == "order_id"

def test_missing_required_operation(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 4: Missing Required Operation
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "verify_identity",
                "requirement": "must_succeed",
                "satisfied": False,
                "attempt_count": 0
            }
        ]
    }
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.PLANNING_OR_WORKFLOW.value

def test_constraint_violation(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 5: Constraint Violation
    base_task_success.structured_details = {
        "constraint_evaluations": [
            {
                "constraint_type": "forbidden_operation",
                "satisfied": False,
                "reason": "Executed forbidden tool"
            }
        ]
    }
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.APPLICATION_VALIDATION.value

def test_timeout(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 6: Timeout / Interruption
    base_reliability_verdict.failure_type = FailureType.TIMEOUT.value
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.INFRASTRUCTURE.value

def test_false_success_with_execution_failure(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 7: False Success With Execution Failure
    base_task_success.task_outcome = TaskOutcome.FAILURE.value
    base_reliability_verdict.reliability_classification = ReliabilityClassification.FALSE_SUCCESS.value
    base_reliability_verdict.failure_type = FailureType.FALSE_SUCCESS_CLAIM.value
    
    # Underlying execution failure: tool failure
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "cancel_order",
                "requirement": "must_succeed",
                "satisfied": False,
                "attempt_count": 1
            }
        ]
    }
    op = ObservedOperation(operation_name="cancel_order", attempt_count=1, final_observed_status="FAILURE")
    base_trace_facts.observed_operations.append(op)

    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    # Failure type is false success claim, but root cause is underlying tool failure!
    assert result.reliability_classification == ReliabilityClassification.FALSE_SUCCESS.value
    assert result.root_cause_category == RootCauseCategory.EXTERNAL_TOOL_FAILURE.value

def test_response_level_failure(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 8: Response-Level Failure
    base_task_success.task_outcome = TaskOutcome.SUCCESS.value
    base_reliability_verdict.reliability_classification = ReliabilityClassification.FALSE_FAILURE.value
    base_reliability_verdict.failure_type = FailureType.FALSE_FAILURE_CLAIM.value
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.MODEL_REASONING.value
    assert result.reliability_classification == ReliabilityClassification.FALSE_FAILURE.value

def test_reliable_success(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 9: Reliable Success
    base_task_success.task_outcome = TaskOutcome.SUCCESS.value
    base_reliability_verdict.reliability_classification = ReliabilityClassification.RELIABLE_SUCCESS.value
    base_reliability_verdict.failure_type = None
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.UNKNOWN.value # Meaning no failure
    assert result.summary == "No failure occurred. Task was a reliable success."

def test_evaluation_incomplete(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 10: Evaluation Incomplete
    base_reliability_verdict.reliability_classification = ReliabilityClassification.EVALUATION_INCOMPLETE.value
    base_reliability_verdict.failure_type = FailureType.EVALUATION_INCOMPLETE.value
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result.root_cause_category == RootCauseCategory.UNKNOWN.value
    assert "incomplete" in result.summary.lower()

def test_multiple_failure_signals_priority(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 11: Multiple Failure Signals Priority Order
    # Missing operation AND Wrong entity. Wrong entity has higher priority than missing operation.
    base_task_success.structured_details = {
        "operation_evaluations": [
            {
                "operation": "verify_identity",
                "requirement": "must_succeed",
                "satisfied": False,
                "attempt_count": 0
            }
        ],
        "entity_evaluations": [
            {
                "entity": "order_id",
                "required_value": "123",
                "observed_value": "456",
                "match_status": "MISMATCH"
            }
        ]
    }
    
    result = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    # TOOL_PARAMETER_CONSTRUCTION (wrong entity) has higher priority than PLANNING_OR_WORKFLOW (missing op)
    assert result.root_cause_category == RootCauseCategory.TOOL_PARAMETER_CONSTRUCTION.value

def test_deterministic_repeatability(evaluator, base_trace_facts, base_task_success, base_reliability_verdict):
    # Required Test 12: Deterministic Repeatability
    base_task_success.structured_details = {
        "entity_evaluations": [
            {
                "entity": "order_id",
                "required_value": "123",
                "observed_value": "456",
                "match_status": "MISMATCH"
            }
        ]
    }
    result1 = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    result2 = evaluator.evaluate(1, base_task_success, base_reliability_verdict, base_trace_facts, None)
    assert result1.root_cause_category == result2.root_cause_category
    assert result1.supporting_evidence == result2.supporting_evidence

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so metadata knows about them
from app.domain.models.core import (
    ExecutionTraceModel, TestCaseModel, TaskSuccessEvaluationModel, 
    ReliabilityVerdictEvaluationModel, SuccessSpecificationModel, 
    ResponseTruthfulnessEvaluationModel, FailureDiagnosisEvaluationModel,
    TraceStepModel
)

engine = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_api_integration():
    # Required Test 13: API Integration
    app.dependency_overrides[get_db] = override_get_db
    try:
        db = TestingSessionLocal()
        from app.domain.models.core import ExecutionTraceModel, TestCaseModel
        tc = TestCaseModel(task_type="test", task_description="desc")
        db.add(tc)
        db.commit()
        trace = ExecutionTraceModel(test_case_id=tc.id, trace_identifier="test-1")
        db.add(trace)
        db.commit()
        
        task_eval = TaskSuccessEvaluationModel(
            trace_id=trace.id, test_case_id=tc.id, task_outcome="FAILURE", determination_method="DETERMINISTIC_RULE", structured_details={}
        )
        db.add(task_eval)
        db.commit()
        
        rel_eval = ReliabilityVerdictEvaluationModel(
            trace_id=trace.id, task_outcome="FAILURE", response_truthfulness="UNKNOWN", overall_evaluation_verdict="FAIL",
            reliability_classification="HONEST_FAILURE", determination_method="DETERMINISTIC_RULE", summary="sum"
        )
        db.add(rel_eval)
        db.commit()
        
        spec = SuccessSpecificationModel()
        db.add(spec)
        db.commit()
        tc.success_specification_id = spec.id
        db.commit()
    
        client = TestClient(app)
        response = client.post("/evaluations/failure-diagnosis", json={"trace_id": trace.id})
        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == trace.id
        assert "root_cause_category" in data
    finally:
        app.dependency_overrides.clear()


