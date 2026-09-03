import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.core import TraceStep, TestCase

def test_valid_trace_step():
    step = TraceStep(
        step_number=1,
        timestamp=datetime.now(timezone.utc),
        action_type="tool_call",
        tool_name="test_tool",
        latency_ms=100
    )
    assert step.step_number == 1
    assert step.latency_ms == 100

def test_invalid_trace_step_number():
    with pytest.raises(ValidationError):
        TraceStep(
            step_number=0,  # Must be > 0
            timestamp=datetime.now(timezone.utc),
            action_type="tool_call"
        )

def test_invalid_trace_step_latency():
    with pytest.raises(ValidationError):
        TraceStep(
            step_number=1,
            timestamp=datetime.now(timezone.utc),
            action_type="tool_call",
            latency_ms=-10  # Must be >= 0
        )

def test_test_case_creation():
    tc = TestCase(
        task_type="web_navigation",
        task_description="Navigate to the login page",
        scenario_parameters={"url": "https://example.com"}
    )
    assert tc.task_type == "web_navigation"
    assert "url" in tc.scenario_parameters

def test_success_specification_validation():
    from app.schemas.core import SuccessSpecificationCreate
    
    # Valid spec
    spec = SuccessSpecificationCreate(
        required_intent="test_intent",
        required_entities={"id": "123"},
        required_operations=[{"operation": "test_op", "must_succeed": True}]
    )
    assert spec.required_intent == "test_intent"
    
    # Invalid empty intent
    with pytest.raises(ValidationError):
        SuccessSpecificationCreate(required_intent="")
        
    # Invalid empty entity key
    with pytest.raises(ValidationError):
        SuccessSpecificationCreate(required_entities={"": "123"})
        
    # Invalid empty operation
    with pytest.raises(ValidationError):
        SuccessSpecificationCreate(required_operations=[{"operation": ""}])
