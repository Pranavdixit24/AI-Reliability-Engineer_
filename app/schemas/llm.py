from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.domain.enums import ResponseTruthfulness, ResponseOutcomeClaim

class EstablishedReality(BaseModel):
    """Structured representation of established reality for the LLM."""
    task_outcome: str
    observed_intents: List[str] = Field(default_factory=list)
    successful_operations: List[str] = Field(default_factory=list)
    failed_operations: List[str] = Field(default_factory=list)
    observed_entities: Dict[str, Any] = Field(default_factory=dict)
    final_state: Dict[str, Any] = Field(default_factory=dict)
    deterministic_evidence_summary: str

class MaterialClaim(BaseModel):
    """A claim made by the agent in its response."""
    claim_text: str = Field(description="The exact or paraphrased claim from the response")
    claim_type: str = Field(description="Type of claim (e.g., outcome, entity, state, action)")
    assessment: str = Field(description="Assessment of the claim (e.g., supported, contradicted, unsupported)")
    supporting_evidence: str = Field(description="Evidence from established reality supporting or contradicting this claim")

class TruthfulnessEvaluationOutput(BaseModel):
    """The structured output required from the LLM evaluator."""
    response_truthfulness: ResponseTruthfulness = Field(description="Overall truthfulness evaluation")
    response_outcome_claim: ResponseOutcomeClaim = Field(description="What outcome the agent claimed")
    material_claims: List[MaterialClaim] = Field(default_factory=list, description="All material claims evaluated")
    contradictions: List[MaterialClaim] = Field(default_factory=list, description="Claims that explicitly contradict reality")
    unsupported_claims: List[MaterialClaim] = Field(default_factory=list, description="Claims that lack evidence in reality")
    reasoning_summary: str = Field(description="Concise summary of why the truthfulness decision was made based on evidence")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the evaluation")
