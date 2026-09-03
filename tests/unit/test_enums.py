from app.domain.enums import (
    TaskOutcome,
    ResponseTruthfulness,
    EvidencePriority,
    FailureType,
    RootCauseCategory
)

def test_task_outcome_values():
    assert TaskOutcome.SUCCESS == "SUCCESS"
    assert TaskOutcome.FAILURE == "FAILURE"
    assert TaskOutcome.UNKNOWN == "UNKNOWN"

def test_response_truthfulness_values():
    assert ResponseTruthfulness.TRUTHFUL == "TRUTHFUL"
    assert ResponseTruthfulness.FALSE_SUCCESS == "FALSE_SUCCESS"

def test_evidence_priority_ordering_conceptual():
    # Verify that the enum values expected by the architecture exist
    assert EvidencePriority.HARD_TRACE == "HARD_TRACE"
    assert EvidencePriority.DETERMINISTIC == "DETERMINISTIC"
    assert EvidencePriority.SEMANTIC == "SEMANTIC"

def test_failure_type_and_root_cause_separation():
    # Verify that failure types and root causes are separate enums
    failure_types = {e.value for e in FailureType}
    root_causes = {e.value for e in RootCauseCategory}
    
    # Check that they represent distinct concepts
    assert "TOOL_FAILURE" in failure_types
    assert "MODEL_REASONING" in root_causes
    
    # While they might share "UNKNOWN", they are fundamentally different enums
    assert FailureType.UNKNOWN_FAILURE != RootCauseCategory.UNKNOWN
