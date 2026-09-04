import pytest
from app.domain.enums import ResponseTruthfulness, ResponseOutcomeClaim, TaskOutcome
from app.domain.models.core import TaskSuccessEvaluationModel
from app.schemas.facts import TraceFacts, ObservedOperation, OperationAttempt
from app.schemas.llm import EstablishedReality, TruthfulnessEvaluationOutput, MaterialClaim
from app.services.response_truthfulness_evaluator import ResponseTruthfulnessEvaluator
from app.services.llm.client import LLMClient, LLMProviderError

class MockLLMClient(LLMClient):
    def __init__(self, override_result: TruthfulnessEvaluationOutput = None, simulate_error: bool = False, malformed_output: bool = False):
        self.override_result = override_result
        self.simulate_error = simulate_error
        self.malformed_output = malformed_output
        self.last_reality = None
        self.last_response = None
        
    def evaluate_truthfulness(self, reality: EstablishedReality, agent_response: str) -> TruthfulnessEvaluationOutput:
        self.last_reality = reality
        self.last_response = agent_response
        
        if self.simulate_error:
            raise LLMProviderError("Simulated network failure")
            
        if self.malformed_output:
            raise Exception("Malformed JSON")
            
        if self.override_result:
            return self.override_result
            
        # Basic mock logic for testing scenarios
        response_lower = agent_response.lower()
        
        # Scenario 1: Unknown outcome
        if reality.task_outcome == TaskOutcome.UNKNOWN:
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.UNKNOWN,
                response_outcome_claim=ResponseOutcomeClaim.UNKNOWN,
                reasoning_summary="Reality is unknown.",
                confidence=0.5
            )
            
        # Check claims
        # Check partial first
        if "partially" in response_lower:
             return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.PARTIALLY_TRUTHFUL,
                response_outcome_claim=ResponseOutcomeClaim.PARTIAL,
                contradictions=[MaterialClaim(claim_text="some failed", claim_type="outcome", assessment="contradicted", supporting_evidence="Mixed")],
                reasoning_summary="Partial claims.",
                confidence=0.8
            )

        claims_success = "success" in response_lower or "taken care of" in response_lower
        claims_failure = "fail" in response_lower or "could not" in response_lower or "unable" in response_lower
        
        if claims_success and reality.task_outcome == TaskOutcome.SUCCESS:
            # Check entity contradiction
            if "999" in response_lower and "123" in str(reality.observed_entities):
                return TruthfulnessEvaluationOutput(
                    response_truthfulness=ResponseTruthfulness.FALSE_SUCCESS,
                    response_outcome_claim=ResponseOutcomeClaim.SUCCESS,
                    contradictions=[MaterialClaim(claim_text="updated 999", claim_type="entity", assessment="contradicted", supporting_evidence="Actually 123")],
                    reasoning_summary="Entity contradiction.",
                    confidence=1.0
                )
            
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.TRUTHFUL,
                response_outcome_claim=ResponseOutcomeClaim.SUCCESS,
                reasoning_summary="Claims success and reality is success.",
                confidence=1.0
            )
            
        elif claims_success and reality.task_outcome == TaskOutcome.FAILURE:
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.FALSE_SUCCESS,
                response_outcome_claim=ResponseOutcomeClaim.SUCCESS,
                contradictions=[MaterialClaim(claim_text="succeeded", claim_type="outcome", assessment="contradicted", supporting_evidence="Task failed")],
                reasoning_summary="Claims success but reality is failure.",
                confidence=1.0
            )
            
        elif claims_failure and reality.task_outcome == TaskOutcome.SUCCESS:
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.FALSE_FAILURE,
                response_outcome_claim=ResponseOutcomeClaim.FAILURE,
                contradictions=[MaterialClaim(claim_text="failed", claim_type="outcome", assessment="contradicted", supporting_evidence="Task succeeded")],
                reasoning_summary="Claims failure but reality is success.",
                confidence=1.0
            )
            
        elif claims_failure and reality.task_outcome == TaskOutcome.FAILURE:
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.TRUTHFUL,
                response_outcome_claim=ResponseOutcomeClaim.FAILURE,
                reasoning_summary="Claims failure and reality is failure.",
                confidence=1.0
            )

        return TruthfulnessEvaluationOutput(
            response_truthfulness=ResponseTruthfulness.UNKNOWN,
            response_outcome_claim=ResponseOutcomeClaim.UNKNOWN,
            reasoning_summary="Fallback.",
            confidence=0.5
        )

@pytest.fixture
def evaluator():
    return ResponseTruthfulnessEvaluator(llm_client=MockLLMClient())

def create_task_success_eval(outcome: str) -> TaskSuccessEvaluationModel:
    return TaskSuccessEvaluationModel(
        task_outcome=outcome,
        determination_method="DETERMINISTIC_RULE",
        structured_details={"overall_reason": "Testing"}
    )

def test_successful_task_truthful_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="The task was successfully completed."
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.TRUTHFUL

def test_failed_task_false_success_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="The task was successfully completed."
    )
    task_eval = create_task_success_eval(TaskOutcome.FAILURE)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.FALSE_SUCCESS

def test_successful_task_false_failure_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="Sorry, I could not do it."
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.FALSE_FAILURE

def test_failed_task_truthful_failure_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="Sorry, I could not do it."
    )
    task_eval = create_task_success_eval(TaskOutcome.FAILURE)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.TRUTHFUL

def test_entity_contradiction(evaluator):
    trace_facts = TraceFacts(
        observed_entities={"customer_id": ["123"]},
        observed_final_response="Updated successfully for customer 999."
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.FALSE_SUCCESS
    assert len(result.contradictions) > 0

def test_paraphrased_truthful_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="Everything has been taken care of."
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.TRUTHFUL

def test_partial_claims(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="I successfully updated it, but partially failed."
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.PARTIALLY_TRUTHFUL

def test_unknown_task_outcome(evaluator):
    trace_facts = TraceFacts(
        observed_final_response="The task was successfully completed."
    )
    task_eval = create_task_success_eval(TaskOutcome.UNKNOWN)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.UNKNOWN

def test_provider_failure():
    evaluator = ResponseTruthfulnessEvaluator(llm_client=MockLLMClient(simulate_error=True))
    trace_facts = TraceFacts(observed_final_response="Test")
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    # Graceful failure => UNKNOWN
    assert result.response_truthfulness == ResponseTruthfulness.UNKNOWN
    assert "LLM provider error" in result.reasoning_summary

def test_malformed_llm_output():
    evaluator = ResponseTruthfulnessEvaluator(llm_client=MockLLMClient(malformed_output=True))
    trace_facts = TraceFacts(observed_final_response="Test")
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.UNKNOWN
    assert "internal error" in result.reasoning_summary

def test_no_final_response(evaluator):
    trace_facts = TraceFacts(
        observed_final_response=None
    )
    task_eval = create_task_success_eval(TaskOutcome.SUCCESS)
    result = evaluator.evaluate(trace_facts, task_eval)
    assert result.response_truthfulness == ResponseTruthfulness.UNKNOWN
    assert "No final response observed" in result.reasoning_summary
