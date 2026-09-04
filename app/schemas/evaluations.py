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
