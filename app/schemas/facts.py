from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class OperationAttempt(BaseModel):
    attempt_number: int
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tool_result: Optional[str] = None
    error_information: Optional[str] = None

class ObservedOperation(BaseModel):
    operation_name: str
    attempt_count: int = 0
    attempts: List[OperationAttempt] = Field(default_factory=list)
    final_observed_status: Optional[str] = None

class TraceFacts(BaseModel):
    trace_id: Optional[int] = None
    observed_intents: List[str] = Field(default_factory=list)
    observed_entities: Dict[str, List[Any]] = Field(default_factory=dict)
    observed_operations: List[ObservedOperation] = Field(default_factory=list)
    observed_final_state: Optional[Dict[str, Any]] = None
    observed_final_response: Optional[str] = None
    timeline_summary: List[Dict[str, Any]] = Field(default_factory=list)
