from typing import Any, Dict
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SuccessSpecificationModel(Base):
    __tablename__ = "success_specifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    required_intent: Mapped[str | None] = mapped_column(String, nullable=True)
    required_entities: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    required_operations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    required_final_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    test_specific_constraints: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    test_cases: Mapped[list["TestCaseModel"]] = relationship(
        back_populates="success_specification"
    )

class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_type: Mapped[str] = mapped_column(String, index=True)
    task_description: Mapped[str] = mapped_column(String)
    scenario_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    success_specification_id: Mapped[int | None] = mapped_column(
        ForeignKey("success_specifications.id"), nullable=True
    )
    
    success_specification: Mapped[SuccessSpecificationModel | None] = relationship(
        back_populates="test_cases"
    )
    traces: Mapped[list["ExecutionTraceModel"]] = relationship(
        back_populates="test_case"
    )

class ExecutionTraceModel(Base):
    __tablename__ = "execution_traces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    trace_identifier: Mapped[str] = mapped_column(String, unique=True, index=True)
    final_response: Mapped[str | None] = mapped_column(String, nullable=True)
    final_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metadata_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    test_case: Mapped[TestCaseModel] = relationship(back_populates="traces")
    steps: Mapped[list["TraceStepModel"]] = relationship(
        back_populates="trace", order_by="TraceStepModel.step_number"
    )

class TraceStepModel(Base):
    __tablename__ = "trace_steps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("execution_traces.id"))
    step_number: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    action_type: Mapped[str] = mapped_column(String)
    intent: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_result: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    error_information: Mapped[str | None] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entity_identifiers: Mapped[list[str]] = mapped_column(JSON, default=list)

    trace: Mapped[ExecutionTraceModel] = relationship(back_populates="steps")

class TaskSuccessEvaluationModel(Base):
    __tablename__ = "task_success_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("execution_traces.id"), unique=True, index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"))
    task_outcome: Mapped[str] = mapped_column(String)
    determination_method: Mapped[str] = mapped_column(String)
    structured_details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trace: Mapped["ExecutionTraceModel"] = relationship()
    test_case: Mapped["TestCaseModel"] = relationship()

class ResponseTruthfulnessEvaluationModel(Base):
    __tablename__ = "response_truthfulness_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("execution_traces.id"), unique=True, index=True)
    task_success_evaluation_id: Mapped[int | None] = mapped_column(ForeignKey("task_success_evaluations.id"), nullable=True)
    response_truthfulness: Mapped[str] = mapped_column(String)
    response_outcome_claim: Mapped[str] = mapped_column(String)
    material_claims: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    contradictions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    unsupported_claims: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    reasoning_summary: Mapped[str] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trace: Mapped["ExecutionTraceModel"] = relationship()
    task_success_evaluation: Mapped["TaskSuccessEvaluationModel"] = relationship()

class ReliabilityVerdictEvaluationModel(Base):
    __tablename__ = "reliability_verdict_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("execution_traces.id"), unique=True, index=True)
    task_success_evaluation_id: Mapped[int | None] = mapped_column(ForeignKey("task_success_evaluations.id"), nullable=True)
    response_truthfulness_evaluation_id: Mapped[int | None] = mapped_column(ForeignKey("response_truthfulness_evaluations.id"), nullable=True)
    
    task_outcome: Mapped[str] = mapped_column(String)
    response_truthfulness: Mapped[str] = mapped_column(String)
    overall_evaluation_verdict: Mapped[str] = mapped_column(String)
    reliability_classification: Mapped[str] = mapped_column(String)
    failure_type: Mapped[str | None] = mapped_column(String, nullable=True)
    determination_method: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trace: Mapped["ExecutionTraceModel"] = relationship()
    task_success_evaluation: Mapped["TaskSuccessEvaluationModel"] = relationship()
    response_truthfulness_evaluation: Mapped["ResponseTruthfulnessEvaluationModel"] = relationship()
