import pytest
from app.services.trace_generator import SyntheticTraceGenerator
from app.domain.enums import ScenarioType, TraceActionType
from app.domain.models.core import TestCaseModel, SuccessSpecificationModel

@pytest.fixture
def test_case_model():
    spec = SuccessSpecificationModel(
        required_intent="test_intent",
        required_entities={"id": "123"},
        required_operations=[{"operation": "test_op", "must_succeed": True}],
        required_final_state={"status": "done"}
    )
    tc = TestCaseModel(
        id=1,
        task_type="test",
        task_description="test",
        success_specification=spec
    )
    return tc

def test_generator_success_scenario(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.SUCCESS)
    
    assert trace.test_case_id == 1
    assert "status" in trace.final_state
    assert trace.final_state["status"] == "done"
    
    # Check steps
    action_types = [step.action_type for step in trace.steps]
    assert TraceActionType.INTENT_RECOGNITION.value in action_types
    assert TraceActionType.ENTITY_EXTRACTION.value in action_types
    assert TraceActionType.TOOL_CALL.value in action_types
    assert TraceActionType.TOOL_RESULT.value in action_types
    
    tool_result_step = next(s for s in trace.steps if s.action_type == TraceActionType.TOOL_RESULT.value)
    assert tool_result_step.status == "SUCCESS"

def test_generator_wrong_entity_scenario(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.WRONG_ENTITY)
    
    entity_step = next(s for s in trace.steps if s.action_type == TraceActionType.ENTITY_EXTRACTION.value)
    assert entity_step.tool_parameters["id"] == "wrong_123"

def test_generator_required_operation_failure(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.REQUIRED_OPERATION_FAILURE)
    
    tool_result_step = next(s for s in trace.steps if s.action_type == TraceActionType.TOOL_RESULT.value)
    assert tool_result_step.status == "ERROR"
    assert not trace.final_state # Final state should be empty
    
def test_generator_missing_required_operation(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.MISSING_REQUIRED_OPERATION)
    
    action_types = [step.action_type for step in trace.steps]
    assert TraceActionType.TOOL_CALL.value not in action_types

def test_generator_timeout(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.TIMEOUT)
    
    tool_result_step = next(s for s in trace.steps if s.action_type == TraceActionType.TOOL_RESULT.value)
    assert tool_result_step.status == "TIMEOUT"

def test_generator_retry_then_success(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.RETRY_THEN_SUCCESS)
    
    action_types = [step.action_type for step in trace.steps]
    assert TraceActionType.RETRY.value in action_types
    
    results = [step.status for step in trace.steps if step.action_type == TraceActionType.TOOL_RESULT.value]
    assert results == ["TIMEOUT", "SUCCESS"]
    
def test_generator_false_success_response(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.FALSE_SUCCESS_RESPONSE)
    
    tool_result_step = next(s for s in trace.steps if s.action_type == TraceActionType.TOOL_RESULT.value)
    assert tool_result_step.status == "ERROR"
    assert "success" in trace.final_response.lower() or "done" in trace.final_response.lower()

def test_generator_truthful_failure_response(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.TRUTHFUL_FAILURE_RESPONSE)
    
    tool_result_step = next(s for s in trace.steps if s.action_type == TraceActionType.TOOL_RESULT.value)
    assert tool_result_step.status == "ERROR"
    assert "fail" in trace.final_response.lower() or "couldn't" in trace.final_response.lower() or "could not" in trace.final_response.lower()
