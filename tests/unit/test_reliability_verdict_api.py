import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.database import get_db
from app.domain.enums import TaskOutcome, ResponseTruthfulness, ReliabilityClassification, EvaluationVerdict
from app.domain.models.core import ExecutionTraceModel, TaskSuccessEvaluationModel, ResponseTruthfulnessEvaluationModel, ReliabilityVerdictEvaluationModel

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides.clear()

def test_evaluate_reliability_verdict_missing_trace(mock_db_session):
    # Setup mock to return None for trace
    mock_db_session.get.return_value = None
    
    response = client.post("/evaluations/reliability-verdict", json={"trace_id": 999})
    assert response.status_code == 404
    assert response.json()["detail"] == "Trace not found"

def test_evaluate_reliability_verdict_missing_task_success(mock_db_session):
    mock_trace = ExecutionTraceModel(id=1, trace_identifier="test-trace")
    mock_db_session.get.return_value = mock_trace
    
    # Return None for the task success eval
    mock_db_session.scalar.side_effect = [None]
    
    response = client.post("/evaluations/reliability-verdict", json={"trace_id": 1})
    assert response.status_code == 400
    assert "Deterministic task success evaluation must be completed" in response.json()["detail"]

def test_evaluate_reliability_verdict_missing_truthfulness(mock_db_session):
    mock_trace = ExecutionTraceModel(id=1, trace_identifier="test-trace")
    mock_task_eval = TaskSuccessEvaluationModel(id=1, trace_id=1, task_outcome=TaskOutcome.SUCCESS.value, determination_method="DETERMINISTIC_RULE")
    
    mock_db_session.get.return_value = mock_trace
    # First scalar call: task_success_eval -> exists
    # Second scalar call: truthfulness_eval -> None
    mock_db_session.scalar.side_effect = [mock_task_eval, None]
    
    response = client.post("/evaluations/reliability-verdict", json={"trace_id": 1})
    assert response.status_code == 400
    assert "Response truthfulness evaluation must be completed" in response.json()["detail"]

def test_evaluate_reliability_verdict_success(mock_db_session):
    mock_trace = ExecutionTraceModel(id=1, trace_identifier="test-trace")
    mock_task_eval = TaskSuccessEvaluationModel(id=1, trace_id=1, task_outcome=TaskOutcome.SUCCESS.value, determination_method="DETERMINISTIC_RULE")
    mock_truthfulness_eval = ResponseTruthfulnessEvaluationModel(
        id=1, trace_id=1, response_truthfulness=ResponseTruthfulness.TRUTHFUL.value, 
        response_outcome_claim="SUCCESS", reasoning_summary="test"
    )
    
    mock_db_session.get.return_value = mock_trace
    # First: task_success, Second: truthfulness, Third: existing reliability eval (None for new)
    mock_db_session.scalar.side_effect = [mock_task_eval, mock_truthfulness_eval, None]
    
    def mock_refresh(obj):
        obj.id = 1
    mock_db_session.refresh.side_effect = mock_refresh
    
    response = client.post("/evaluations/reliability-verdict", json={"trace_id": 1})
    
    assert response.status_code == 201
    data = response.json()
    assert data["trace_id"] == 1
    assert data["task_outcome"] == TaskOutcome.SUCCESS.value
    assert data["response_truthfulness"] == ResponseTruthfulness.TRUTHFUL.value
    assert data["reliability_classification"] == ReliabilityClassification.RELIABLE_SUCCESS.value
    assert data["overall_evaluation_verdict"] == EvaluationVerdict.PASS.value
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
