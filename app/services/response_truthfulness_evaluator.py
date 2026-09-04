import logging
from typing import Optional
from app.domain.models.core import ExecutionTraceModel, TaskSuccessEvaluationModel
from app.schemas.llm import EstablishedReality, TruthfulnessEvaluationOutput
from app.schemas.facts import TraceFacts
from app.services.llm.client import LLMClient, LLMProviderError
from app.domain.enums import ResponseTruthfulness, ResponseOutcomeClaim

logger = logging.getLogger(__name__)

class ResponseTruthfulnessEvaluator:
    """
    Evaluates whether the agent's final response accurately describes the 
    established reality of what happened during execution.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def evaluate(self, trace_facts: TraceFacts, task_success_eval: TaskSuccessEvaluationModel) -> TruthfulnessEvaluationOutput:
        
        # Ensure we have a response to evaluate
        agent_response = trace_facts.observed_final_response
        if not agent_response:
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.UNKNOWN,
                response_outcome_claim=ResponseOutcomeClaim.UNKNOWN,
                reasoning_summary="No final response observed in trace facts to evaluate.",
                confidence=1.0
            )

        # 1. Construct Established Reality
        reality = self._construct_established_reality(trace_facts, task_success_eval)
        
        # 2. Call LLM for Semantic Evaluation
        try:
            llm_result = self.llm_client.evaluate_truthfulness(reality, agent_response)
            return llm_result
        except LLMProviderError as e:
            logger.error(f"LLM evaluation failed: {str(e)}")
            # Handle gracefully by returning UNKNOWN truthfulness due to infrastructure failure.
            # Do NOT claim UNTRUTHFUL just because the LLM failed.
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.UNKNOWN,
                response_outcome_claim=ResponseOutcomeClaim.UNKNOWN,
                reasoning_summary=f"Evaluation failed due to LLM provider error: {str(e)}",
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Unexpected error during truthfulness evaluation: {str(e)}")
            return TruthfulnessEvaluationOutput(
                response_truthfulness=ResponseTruthfulness.UNKNOWN,
                response_outcome_claim=ResponseOutcomeClaim.UNKNOWN,
                reasoning_summary="Evaluation failed due to internal error.",
                confidence=0.0
            )

    def _construct_established_reality(self, trace_facts: TraceFacts, task_success_eval: TaskSuccessEvaluationModel) -> EstablishedReality:
        """
        Builds a structured object representing the definitive truth of what happened.
        """
        successful_ops = []
        failed_ops = []
        
        for op in trace_facts.observed_operations:
            # Based on final observed status or attempt statuses
            has_success = False
            for attempt in op.attempts:
                if attempt.status == "success" or attempt.tool_result == "success":
                    has_success = True
                    break
            
            if op.final_observed_status == "success" or has_success:
                successful_ops.append(op.operation_name)
            else:
                failed_ops.append(op.operation_name)

        # The deterministic_evidence_summary could be derived from task_success_eval.structured_details
        overall_reason = task_success_eval.structured_details.get("overall_reason", "No reason provided.")

        return EstablishedReality(
            task_outcome=task_success_eval.task_outcome,
            observed_intents=trace_facts.observed_intents,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            observed_entities=trace_facts.observed_entities,
            final_state=trace_facts.observed_final_state or {},
            deterministic_evidence_summary=overall_reason
        )
