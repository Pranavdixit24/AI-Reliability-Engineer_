import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.domain.models.core import (
    TestCaseModel,
    ExecutionTraceModel,
    TraceStepModel,
    TaskSuccessEvaluationModel,
    ResponseTruthfulnessEvaluationModel,
    SuccessSpecificationModel
)
from app.domain.enums import TraceActionType, TaskOutcome, ResponseTruthfulness, ResponseOutcomeClaim
from app.schemas.llm import TruthfulnessEvaluationOutput, MaterialClaim

def test_response_truthfulness_api_success(client: TestClient, db_session: Session):
    # Setup Data
    spec = SuccessSpecificationModel(
        required_operations=[],
        required_entities={}
    )
    db_session.add(spec)
    db_session.commit()
    
    test_case = TestCaseModel(
        task_type="test",
        task_description="test desc",
        success_specification_id=spec.id
    )
    db_session.add(test_case)
    db_session.commit()

    trace = ExecutionTraceModel(
        test_case_id=test_case.id,
        trace_identifier="trace_truthful_api"
    )
    db_session.add(trace)
    db_session.commit()

    step1 = TraceStepModel(
        trace_id=trace.id,
        step_number=1,
        timestamp=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
        action_type=TraceActionType.FINAL_RESPONSE.value,
        tool_result="I did it."
    )
    db_session.add(step1)
    
    # Needs TaskSuccessEvaluation
    task_success_eval = TaskSuccessEvaluationModel(
        trace_id=trace.id,
        test_case_id=test_case.id,
        task_outcome=TaskOutcome.SUCCESS.value,
        determination_method="DETERMINISTIC_RULE",
        structured_details={"overall_reason": "Testing"}
    )
    db_session.add(task_success_eval)
    db_session.commit()

    mock_output = TruthfulnessEvaluationOutput(
        response_truthfulness=ResponseTruthfulness.TRUTHFUL,
        response_outcome_claim=ResponseOutcomeClaim.SUCCESS,
        reasoning_summary="Mocked truthful reason",
        confidence=1.0
    )

    with patch('app.services.response_truthfulness_evaluator.LLMClient.evaluate_truthfulness', return_value=mock_output):
        response = client.post("/evaluations/response-truthfulness", json={"trace_id": trace.id})
        assert response.status_code == 201
        
        data = response.json()
        assert data["response_truthfulness"] == "TRUTHFUL"
        assert data["reasoning_summary"] == "Mocked truthful reason"

        # Verify Persistence
        db_eval = db_session.query(ResponseTruthfulnessEvaluationModel).filter_by(trace_id=trace.id).first()
        assert db_eval is not None
        assert db_eval.response_truthfulness == "TRUTHFUL"
        assert db_eval.task_success_evaluation_id == task_success_eval.id

def test_response_truthfulness_missing_dependency(client: TestClient, db_session: Session):
    # Setup Data without TaskSuccessEvaluationModel
    trace = ExecutionTraceModel(
        test_case_id=1,
        trace_identifier="trace_missing_dep"
    )
    db_session.add(trace)
    db_session.commit()

    response = client.post("/evaluations/response-truthfulness", json={"trace_id": trace.id})
    assert response.status_code == 400
    assert "must be completed before" in response.json()["detail"]
