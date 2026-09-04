from typing import Dict
from pydantic import BaseModel, ConfigDict

class ReliabilityAnalyticsResponse(BaseModel):
    """Schema for the reliability analytics aggregation response."""
    total_evaluated_traces: int
    verdict_counts: Dict[str, int]
    reliability_classification_counts: Dict[str, int]
    failure_type_counts: Dict[str, int]
    root_cause_counts: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)
