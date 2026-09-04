from typing import Dict, List, Any
from app.domain.models.core import ExecutionTraceModel
from app.domain.enums import TraceActionType
from app.schemas.facts import TraceFacts, ObservedOperation, OperationAttempt

class TraceFactExtractor:
    """
    Deterministically extracts normalized facts from a raw execution trace.
    Does NOT make evaluative judgments or read generation metadata.
    """
    
    @staticmethod
    def extract_facts(trace: ExecutionTraceModel) -> TraceFacts:
        facts = TraceFacts(trace_id=trace.id)
        
        # State tracking for operations
        operations_map: Dict[str, ObservedOperation] = {}
        active_attempts: Dict[str, OperationAttempt] = {}
        
        # Process steps chronologically
        for step in trace.steps:
            action = step.action_type
            
            # 1. Intent Extraction
            if action == TraceActionType.INTENT_RECOGNITION.value and step.intent:
                facts.observed_intents.append(step.intent)
                facts.timeline_summary.append({
                    "event": "intent_recognized",
                    "intent": step.intent,
                    "step_number": step.step_number
                })
                
            # 2. Entity Extraction
            elif action == TraceActionType.ENTITY_EXTRACTION.value and step.tool_parameters:
                for k, v in step.tool_parameters.items():
                    if k not in facts.observed_entities:
                        facts.observed_entities[k] = []
                    facts.observed_entities[k].append(v)
                    facts.timeline_summary.append({
                        "event": "entity_observed",
                        "entity": k,
                        "value": v,
                        "step_number": step.step_number
                    })
                    
            # 3. Tool Call
            elif action == TraceActionType.TOOL_CALL.value and step.tool_name:
                op_name = step.tool_name
                if op_name not in operations_map:
                    operations_map[op_name] = ObservedOperation(operation_name=op_name)
                    facts.observed_operations.append(operations_map[op_name])
                
                op = operations_map[op_name]
                op.attempt_count += 1
                
                attempt = OperationAttempt(
                    attempt_number=op.attempt_count,
                    parameters=step.tool_parameters
                )
                op.attempts.append(attempt)
                active_attempts[op_name] = attempt
                
                facts.timeline_summary.append({
                    "event": "operation_attempted",
                    "operation": op_name,
                    "attempt_number": attempt.attempt_number,
                    "parameters": step.tool_parameters,
                    "step_number": step.step_number
                })
                
            # 4. Tool Result
            elif action == TraceActionType.TOOL_RESULT.value and step.tool_name:
                op_name = step.tool_name
                
                # If there's no preceding TOOL_CALL, we gracefully create the operation
                if op_name not in operations_map:
                    operations_map[op_name] = ObservedOperation(operation_name=op_name)
                    facts.observed_operations.append(operations_map[op_name])
                    
                op = operations_map[op_name]
                
                # If there's no active attempt, create a dummy one to attach the result
                if op_name not in active_attempts:
                    op.attempt_count += 1
                    attempt = OperationAttempt(attempt_number=op.attempt_count)
                    op.attempts.append(attempt)
                    active_attempts[op_name] = attempt
                    
                attempt = active_attempts[op_name]
                attempt.status = step.status
                attempt.tool_result = step.tool_result
                attempt.error_information = step.error_information
                
                op.final_observed_status = step.status
                
                facts.timeline_summary.append({
                    "event": "operation_result",
                    "operation": op_name,
                    "status": step.status,
                    "error_information": step.error_information,
                    "step_number": step.step_number
                })
                
            # 5. Retry
            elif action == TraceActionType.RETRY.value and step.tool_name:
                facts.timeline_summary.append({
                    "event": "retry_observed",
                    "operation": step.tool_name,
                    "step_number": step.step_number
                })
                
            # 6. Final Response
            elif action == TraceActionType.FINAL_RESPONSE.value and step.tool_result:
                facts.observed_final_response = step.tool_result
                facts.timeline_summary.append({
                    "event": "final_response",
                    "response": step.tool_result,
                    "step_number": step.step_number
                })

        # Final State
        if trace.final_state is not None:
            facts.observed_final_state = trace.final_state
            
        # Final Response fallback if it wasn't captured in a step
        if not facts.observed_final_response and trace.final_response:
            facts.observed_final_response = trace.final_response
            
        return facts
