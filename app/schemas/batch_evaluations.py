from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class BatchEvaluationRequest(BaseModel):
    """Schema for requesting a batch evaluation."""
    trace_ids: List[int] = Field(min_length=1, description="List of trace IDs to evaluate")

class TraceEvaluationResult(BaseModel):
    """Schema for the result of a single trace evaluation within a batch."""
    trace_id: int
    status: str
    error: Optional[str] = None
    skipped_reason: Optional[str] = None

class BatchEvaluationResponse(BaseModel):
    """Schema for the overall batch evaluation response."""
    requested_count: int
    unique_requested_count: int
    completed_count: int
    skipped_count: int
    failed_count: int
    results: List[TraceEvaluationResult]

    model_config = ConfigDict(from_attributes=True)
