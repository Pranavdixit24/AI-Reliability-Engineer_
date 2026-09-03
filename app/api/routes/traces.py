from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.core import ExecutionTraceResponse
from app.domain.models.core import ExecutionTraceModel

router = APIRouter(prefix="/traces", tags=["Traces"])

@router.get("", response_model=List[ExecutionTraceResponse])
def list_traces(skip: int = 0, limit: int = 100, test_case_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    List stored traces, optionally filtered by test_case_id.
    """
    query = select(ExecutionTraceModel)
    if test_case_id is not None:
        query = query.where(ExecutionTraceModel.test_case_id == test_case_id)
        
    query = query.offset(skip).limit(limit)
    db_traces = db.scalars(query).all()
    
    responses = []
    for t in db_traces:
        responses.append(ExecutionTraceResponse(
            id=t.id,
            test_case_id=t.test_case_id,
            trace_identifier=t.trace_identifier,
            final_response=t.final_response,
            final_state=t.final_state,
            metadata=t.metadata_info,
            steps=t.steps
        ))
    return responses

@router.get("/{trace_id}", response_model=ExecutionTraceResponse)
def get_trace(trace_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single execution trace and its ordered steps.
    """
    db_trace = db.get(ExecutionTraceModel, trace_id)
    if not db_trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    return ExecutionTraceResponse(
        id=db_trace.id,
        test_case_id=db_trace.test_case_id,
        trace_identifier=db_trace.trace_identifier,
        final_response=db_trace.final_response,
        final_state=db_trace.final_state,
        metadata=db_trace.metadata_info,
        steps=db_trace.steps
    )
