from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.domain.models.core import (
    TestCaseModel,
    SuccessSpecificationModel,
    ExecutionTraceModel,
    TraceStepModel,
    TaskSuccessEvaluationModel
)
from app.domain.enums import TraceActionType, TaskOutcome

def test_evaluate_task_success_api(client: TestClient, db_session: Session):
    # Setup Data
    spec = SuccessSpecificationModel(
        required_operations=[{"operation": "book_flight", "must_succeed": True}],
        required_entities={"destination": "Tokyo"}
    )
    db_session.add(spec)
    db_session.commit()
    
    test_case = TestCaseModel(
        task_type="booking",
        task_description="Book a flight to Tokyo",
        success_specification_id=spec.id
    )
    db_session.add(test_case)
    db_session.commit()
    
    trace = ExecutionTraceModel(
        test_case_id=test_case.id,
        trace_identifier="trace_123"
    )
    db_session.add(trace)
    db_session.commit()
    
    # Add steps
    step1 = TraceStepModel(
        trace_id=trace.id,
        step_number=1,
        timestamp=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
        action_type=TraceActionType.ENTITY_EXTRACTION.value,
        tool_parameters={"destination": "Tokyo"}
    )
    step2 = TraceStepModel(
        trace_id=trace.id,
        step_number=2,
        timestamp=datetime(2026, 9, 4, 12, 1, 0, tzinfo=timezone.utc),
        action_type=TraceActionType.TOOL_CALL.value,
        tool_name="book_flight"
    )
    step3 = TraceStepModel(
        trace_id=trace.id,
        step_number=3,
        timestamp=datetime(2026, 9, 4, 12, 2, 0, tzinfo=timezone.utc),
        action_type=TraceActionType.TOOL_RESULT.value,
        tool_name="book_flight",
        status="success"
    )
    db_session.add_all([step1, step2, step3])
    db_session.commit()
    
    # Run Evaluation API
    response = client.post("/evaluations/task-success", json={"trace_id": trace.id})
    assert response.status_code == 201
    
    data = response.json()
    assert data["task_success"] == "SUCCESS"
    assert len(data["operation_evaluations"]) == 1
    assert data["operation_evaluations"][0]["operation"] == "book_flight"
    assert data["operation_evaluations"][0]["satisfied"] is True
    
    assert len(data["entity_evaluations"]) == 1
    assert data["entity_evaluations"][0]["entity"] == "destination"
    assert data["entity_evaluations"][0]["match_status"] == "MATCH"
    
    # Verify Persistence
    db_eval = db_session.query(TaskSuccessEvaluationModel).filter_by(trace_id=trace.id).first()
    assert db_eval is not None
    assert db_eval.task_outcome == "SUCCESS"
    
def test_evaluate_task_success_not_found(client: TestClient):
    response = client.post("/evaluations/task-success", json={"trace_id": 9999})
    assert response.status_code == 404
