from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from app.domain.enums import (
    TaskOutcome,
    ResponseTruthfulness,
    EvaluationVerdict,
    FailureType,
    RootCauseCategory
)

# API Schemas
class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str

# Domain Schemas

class FinalState(BaseModel):
    """Flexible typed representation for a final state"""
    state_data: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class RequiredOperation(BaseModel):
    operation: str = Field(min_length=1)
    must_succeed: bool = True

class SuccessSpecificationCreate(BaseModel):
    """Structured success specification creation payload"""
    required_intent: Optional[str] = Field(default=None, min_length=1)
    required_entities: Dict[str, Any] = Field(default_factory=dict)
    required_operations: List[RequiredOperation] = Field(default_factory=list)
    required_final_state: Optional[Dict[str, Any]] = None
    test_specific_constraints: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('required_entities')
    @classmethod
    def check_entity_keys(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        for k in v.keys():
            if not k.strip():
                raise ValueError('Entity constraint keys cannot be empty')
        return v

class SuccessSpecification(SuccessSpecificationCreate):
    """Structured success specification"""
    id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class TestCaseCreate(BaseModel):
    """Schema for creating a test case"""
    task_type: str = Field(min_length=1)
    task_description: str = Field(min_length=1)
    scenario_parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    success_specification: SuccessSpecificationCreate

class TestCase(BaseModel):
    """Core representation for a test case"""
    id: Optional[int] = None
    task_type: str
    task_description: str
    scenario_parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    success_specification_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class TestCaseResponse(TestCase):
    """API response for a test case including its success specification"""
    success_specification: Optional[SuccessSpecification] = None

class TraceStep(BaseModel):
    """Typed representation for an execution step"""
    id: Optional[int] = None
    trace_id: Optional[int] = None
    step_number: int = Field(gt=0)
    timestamp: datetime
    action_type: str
    intent: Optional[str] = None
    tool_name: Optional[str] = None
    tool_parameters: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    status: Optional[str] = None
    error_information: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)
    latency_ms: Optional[int] = Field(default=None, ge=0)
    entity_identifiers: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class ExecutionTrace(BaseModel):
    """Domain representation for an execution trace"""
    id: Optional[int] = None
    test_case_id: int
    trace_identifier: str
    final_response: Optional[str] = None
    final_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    steps: List[TraceStep] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationResultFoundation(BaseModel):
    """Core result representation"""
    id: Optional[int] = None
    trace_id: int
    task_success: TaskOutcome = TaskOutcome.UNKNOWN
    response_truthfulness: ResponseTruthfulness = ResponseTruthfulness.UNKNOWN
    final_verdict: EvaluationVerdict = EvaluationVerdict.UNCERTAIN
    evidence_references: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    model_config = ConfigDict(from_attributes=True)

class ExecutionTraceResponse(ExecutionTrace):
    """API response for a generated execution trace"""
    pass
