import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from app.domain.models.core import TestCaseModel, ExecutionTraceModel, TraceStepModel
from app.domain.enums import ScenarioType, TraceActionType

class SyntheticTraceGenerator:
    """Generates synthetic structured execution traces deterministically."""

    def __init__(self, seed: int):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate(self, test_case: TestCaseModel, scenario: ScenarioType) -> ExecutionTraceModel:
        """
        Generates an ExecutionTraceModel based on the provided test case and scenario.
        """
        # Read test case specification
        spec = test_case.success_specification
        req_intent = spec.required_intent if spec else "unknown_intent"
        req_entities = spec.required_entities if spec else {}
        req_ops = spec.required_operations if spec else []
        req_final_state = spec.required_final_state if spec and spec.required_final_state else {}

        trace = ExecutionTraceModel(
            test_case_id=test_case.id,
            trace_identifier=f"trace-{test_case.id}-{scenario.value}-{self.seed}",
            metadata_info={"scenario_type": scenario.value, "seed": self.seed, "generator_version": "phase_3"}
        )

        steps: List[TraceStepModel] = []
        step_idx = 1
        current_time = datetime.now(timezone.utc)
        
        def add_step(action_type, **kwargs):
            nonlocal step_idx, current_time
            # Increment time slightly to ensure chronological ordering
            current_time += timedelta(milliseconds=self.rng.randint(50, 500))
            
            step = TraceStepModel(
                step_number=step_idx,
                timestamp=current_time,
                action_type=action_type.value,
                **kwargs
            )
            steps.append(step)
            step_idx += 1
            return step

        # Baseline generation logic based on scenario
        
        # 1. Intent recognition
        add_step(TraceActionType.INTENT_RECOGNITION, intent=req_intent)

        # 2. Entity extraction
        if scenario == ScenarioType.WRONG_ENTITY:
            # Inject a wrong entity
            wrong_entities = {k: f"wrong_{v}" for k, v in req_entities.items()}
            add_step(TraceActionType.ENTITY_EXTRACTION, entity_identifiers=list(wrong_entities.keys()), tool_parameters=wrong_entities)
            active_entities = wrong_entities
        else:
            add_step(TraceActionType.ENTITY_EXTRACTION, entity_identifiers=list(req_entities.keys()), tool_parameters=req_entities)
            active_entities = req_entities

        # 3. Operations
        success = True
        final_state = {}
        
        for op in req_ops:
            op_name = op.get("operation", "unknown_operation")
            
            if scenario == ScenarioType.MISSING_REQUIRED_OPERATION:
                success = False
                continue # Skip calling the required operation
                
            # Perform tool call
            add_step(TraceActionType.TOOL_CALL, tool_name=op_name, tool_parameters=active_entities)
            
            if scenario == ScenarioType.TIMEOUT:
                add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="TIMEOUT", error_information="Connection timed out after 30s")
                success = False
                break
                
            elif scenario == ScenarioType.REQUIRED_OPERATION_FAILURE:
                add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="ERROR", error_information="Service Unavailable (503)")
                success = False
                break
                
            elif scenario == ScenarioType.RETRY_THEN_SUCCESS:
                # Fail first
                add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="TIMEOUT", error_information="Connection timed out")
                # Retry
                add_step(TraceActionType.RETRY, tool_name=op_name, retry_count=1)
                add_step(TraceActionType.TOOL_CALL, tool_name=op_name, tool_parameters=active_entities)
                # Succeed
                add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="SUCCESS", tool_result=f"{op_name} succeeded")
                final_state.update(req_final_state)
                
            elif scenario == ScenarioType.PARTIAL_COMPLETION:
                # Succeed on the first operation, but then stop if there are multiple, or just mark overall as incomplete.
                add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="SUCCESS", tool_result=f"{op_name} succeeded")
                # For partial completion, we simply don't do subsequent operations
                success = False
                break # We skip other ops
                
            else:
                # SUCCESS, WRONG_ENTITY, FALSE_SUCCESS_RESPONSE, TRUTHFUL_FAILURE_RESPONSE
                # In WRONG_ENTITY, the tool might "succeed" but on the wrong entity.
                # In FALSE_SUCCESS and TRUTHFUL_FAILURE, the operation itself actually fails.
                if scenario in [ScenarioType.FALSE_SUCCESS_RESPONSE, ScenarioType.TRUTHFUL_FAILURE_RESPONSE]:
                    add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="ERROR", error_information="Failed to complete operation")
                    success = False
                    break
                else:
                    add_step(TraceActionType.TOOL_RESULT, tool_name=op_name, status="SUCCESS", tool_result=f"{op_name} succeeded")
                    final_state.update(req_final_state)

        # 4. Final Response and State
        if scenario == ScenarioType.FALSE_SUCCESS_RESPONSE:
            final_resp = self.rng.choice([
                "Your request was completed successfully.",
                "I have successfully performed the action.",
                "All done! It was a success."
            ])
            trace.final_state = {} # unchanged
        elif scenario == ScenarioType.TRUTHFUL_FAILURE_RESPONSE:
            final_resp = self.rng.choice([
                "I couldn't complete the requested action.",
                "The service failed to complete the operation.",
                "The operation failed before completion."
            ])
            trace.final_state = {}
        elif success:
            final_resp = self.rng.choice([
                f"The task was successfully completed.",
                "I have successfully finished your request.",
                "It's done!"
            ])
            trace.final_state = final_state
        else:
            final_resp = self.rng.choice([
                "I stopped processing the request.",
                "The task could not be completely finished.",
                "I encountered an issue."
            ])
            trace.final_state = final_state
            
        add_step(TraceActionType.FINAL_RESPONSE, tool_result=final_resp)
        trace.final_response = final_resp
        trace.steps = steps

        return trace
