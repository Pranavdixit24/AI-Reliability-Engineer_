from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import TaskOutcome, DeterminationMethod
from app.schemas.core import EvaluationResultFoundation

class OperationEvaluation(BaseModel):
    operation: str
    requirement: str  # "attempted" or "must_succeed"
    satisfied: bool
    evidence: Optional[str] = None
    reason: Optional[str] = None
    attempt_count: int = 0

class EntityEvaluation(BaseModel):
    entity: str
    required_value: Any
    observed_value: Any = None
    match_status: str  # "MATCH", "MISMATCH", "MISSING_EVIDENCE"

class ConstraintEvaluation(BaseModel):
    constraint_type: str
    satisfied: bool
    reason: Optional[str] = None

class TaskSuccessEvaluationResult(EvaluationResultFoundation):
    determination_method: DeterminationMethod = DeterminationMethod.DETERMINISTIC_RULE
    overall_reason: str
    operation_evaluations: List[OperationEvaluation] = Field(default_factory=list)
    entity_evaluations: List[EntityEvaluation] = Field(default_factory=list)
    constraint_evaluations: List[ConstraintEvaluation] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class ReliabilityVerdictResult(BaseModel):
    id: Optional[int] = None
    trace_id: int
    task_success_evaluation_id: Optional[int] = None
    response_truthfulness_evaluation_id: Optional[int] = None
    task_outcome: str
    response_truthfulness: str
    overall_evaluation_verdict: str
    reliability_classification: str
    failure_type: Optional[str] = None
    determination_method: DeterminationMethod = DeterminationMethod.DETERMINISTIC_RULE
    summary: str
    
    model_config = ConfigDict(from_attributes=True)

class FailureDiagnosisResult(BaseModel):
    id: Optional[int] = None
    trace_id: int
    task_success_evaluation_id: int
    response_truthfulness_evaluation_id: Optional[int] = None
    reliability_verdict_evaluation_id: int
    
    failure_type: Optional[str] = None
    reliability_classification: str
    root_cause_category: str
    determination_method: DeterminationMethod = DeterminationMethod.DETERMINISTIC_RULE
    
    summary: str
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    contributing_signals: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
