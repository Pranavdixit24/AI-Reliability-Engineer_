from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.evaluations import TaskSuccessEvaluationResult, ReliabilityVerdictResult, FailureDiagnosisResult

class ResponseTruthfulnessHistory(BaseModel):
    id: int
    trace_id: int
    task_success_evaluation_id: Optional[int] = None
    response_truthfulness: str
    response_outcome_claim: str
    material_claims: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    unsupported_claims: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_summary: str
    confidence: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationHistoryResult(BaseModel):
    trace_id: int
    task_success: Optional[TaskSuccessEvaluationResult] = None
    response_truthfulness: Optional[ResponseTruthfulnessHistory] = None
    reliability_verdict: Optional[ReliabilityVerdictResult] = None
    failure_diagnosis: Optional[FailureDiagnosisResult] = None
