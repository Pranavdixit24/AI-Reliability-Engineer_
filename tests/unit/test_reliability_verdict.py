import pytest
from app.services.reliability_verdict_evaluator import ReliabilityVerdictEvaluator
from app.domain.enums import (
    TaskOutcome,
    ResponseTruthfulness,
    ReliabilityClassification,
    EvaluationVerdict,
    FailureType,
    DeterminationMethod
)
from app.domain.models.core import TaskSuccessEvaluationModel, ResponseTruthfulnessEvaluationModel

@pytest.fixture
def evaluator():
    return ReliabilityVerdictEvaluator()

def create_models(task_outcome: str, response_truthfulness: str):
    task_success_eval = TaskSuccessEvaluationModel(id=1, trace_id=1, task_outcome=task_outcome, determination_method="DETERMINISTIC_RULE")
    truthfulness_eval = ResponseTruthfulnessEvaluationModel(id=1, trace_id=1, response_truthfulness=response_truthfulness, response_outcome_claim="SUCCESS", reasoning_summary="test")
    return task_success_eval, truthfulness_eval

def test_reliable_success(evaluator):
    task, truth = create_models(TaskOutcome.SUCCESS.value, ResponseTruthfulness.TRUTHFUL.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.PASS.value
    assert result.reliability_classification == ReliabilityClassification.RELIABLE_SUCCESS.value
    assert result.failure_type is None
    assert result.determination_method == DeterminationMethod.DETERMINISTIC_RULE

def test_honest_failure(evaluator):
    task, truth = create_models(TaskOutcome.FAILURE.value, ResponseTruthfulness.TRUTHFUL.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.FAIL.value
    assert result.reliability_classification == ReliabilityClassification.HONEST_FAILURE.value
    assert result.failure_type == FailureType.TASK_EXECUTION_FAILURE.value

def test_false_failure(evaluator):
    task, truth = create_models(TaskOutcome.SUCCESS.value, ResponseTruthfulness.FALSE_FAILURE.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.FAIL.value
    assert result.reliability_classification == ReliabilityClassification.FALSE_FAILURE.value
    assert result.failure_type == FailureType.FALSE_FAILURE_CLAIM.value

def test_false_success(evaluator):
    task, truth = create_models(TaskOutcome.FAILURE.value, ResponseTruthfulness.FALSE_SUCCESS.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.FAIL.value
    assert result.reliability_classification == ReliabilityClassification.FALSE_SUCCESS.value
    assert result.failure_type == FailureType.FALSE_SUCCESS_CLAIM.value

def test_unknown_task_outcome(evaluator):
    task, truth = create_models(TaskOutcome.UNKNOWN.value, ResponseTruthfulness.TRUTHFUL.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.UNCERTAIN.value
    assert result.reliability_classification == ReliabilityClassification.EVALUATION_INCOMPLETE.value
    assert result.failure_type == FailureType.EVALUATION_INCOMPLETE.value

def test_unknown_truthfulness(evaluator):
    task, truth = create_models(TaskOutcome.SUCCESS.value, ResponseTruthfulness.UNKNOWN.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.UNCERTAIN.value
    assert result.reliability_classification == ReliabilityClassification.EVALUATION_INCOMPLETE.value
    assert result.failure_type == FailureType.EVALUATION_INCOMPLETE.value

def test_both_unknown(evaluator):
    task, truth = create_models(TaskOutcome.UNKNOWN.value, ResponseTruthfulness.UNKNOWN.value)
    result = evaluator.evaluate(1, task, truth)
    
    assert result.overall_evaluation_verdict == EvaluationVerdict.UNCERTAIN.value
    assert result.reliability_classification == ReliabilityClassification.EVALUATION_INCOMPLETE.value
    assert result.failure_type == FailureType.EVALUATION_INCOMPLETE.value
