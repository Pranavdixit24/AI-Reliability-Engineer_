import pytest
import json
from app.services.trace_fact_extractor import TraceFactExtractor
from app.services.trace_generator import SyntheticTraceGenerator
from app.domain.enums import ScenarioType
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

def test_fact_extraction_success_scenario(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.SUCCESS)
    
    facts = TraceFactExtractor.extract_facts(trace)
    
    assert "test_intent" in facts.observed_intents
    assert "id" in facts.observed_entities
    assert "123" in facts.observed_entities["id"]
    
    assert len(facts.observed_operations) == 1
    op = facts.observed_operations[0]
    assert op.operation_name == "test_op"
    assert op.attempt_count == 1
    assert op.final_observed_status == "SUCCESS"
    assert op.attempts[0].status == "SUCCESS"
    
    assert facts.observed_final_state == {"status": "done"}

def test_fact_extraction_wrong_entity(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.WRONG_ENTITY)
    
    facts = TraceFactExtractor.extract_facts(trace)
    assert "id" in facts.observed_entities
    assert "wrong_123" in facts.observed_entities["id"]
    assert "123" not in facts.observed_entities["id"]

def test_fact_extraction_missing_operation(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.MISSING_REQUIRED_OPERATION)
    
    facts = TraceFactExtractor.extract_facts(trace)
    assert len(facts.observed_operations) == 0

def test_fact_extraction_timeout_and_retry(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.RETRY_THEN_SUCCESS)
    
    facts = TraceFactExtractor.extract_facts(trace)
    assert len(facts.observed_operations) == 1
    op = facts.observed_operations[0]
    assert op.attempt_count == 2
    assert op.attempts[0].status == "TIMEOUT"
    assert op.attempts[1].status == "SUCCESS"
    assert op.final_observed_status == "SUCCESS"

def test_fact_extraction_metadata_isolation(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace_a = generator.generate(test_case_model, ScenarioType.SUCCESS)
    
    facts_a = TraceFactExtractor.extract_facts(trace_a)
    
    # Intentionally taint the metadata
    trace_a.metadata_info["scenario_type"] = "FALSE_SUCCESS_RESPONSE"
    
    facts_b = TraceFactExtractor.extract_facts(trace_a)
    
    # Should produce identical facts regardless of metadata string
    assert facts_a.model_dump() == facts_b.model_dump()

def test_fact_extraction_determinism(test_case_model):
    generator = SyntheticTraceGenerator(seed=42)
    trace = generator.generate(test_case_model, ScenarioType.SUCCESS)
    
    # Run the extractor twice on the exact same trace
    facts_1 = TraceFactExtractor.extract_facts(trace)
    facts_2 = TraceFactExtractor.extract_facts(trace)
    
    assert facts_1.model_dump() == facts_2.model_dump()
