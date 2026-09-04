from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.domain.models.core import ExecutionTraceModel, TaskSuccessEvaluationModel
from app.schemas.evaluations import TaskSuccessEvaluationResult
from app.services.trace_fact_extractor import TraceFactExtractor
from app.services.task_success_evaluator import TaskSuccessEvaluator

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

class TaskSuccessEvaluationRequest(BaseModel):
    trace_id: int

@router.post("/task-success", response_model=TaskSuccessEvaluationResult, status_code=status.HTTP_201_CREATED)
def evaluate_task_success(request: TaskSuccessEvaluationRequest, db: Session = Depends(get_db)):
    """
    Evaluates whether a task succeeded based purely on deterministic trace evidence.
    """
    trace_id = request.trace_id
    
    # 1. Fetch the trace
    db_trace = db.get(ExecutionTraceModel, trace_id)
    if not db_trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    # 2. Extract facts
    extractor = TraceFactExtractor()
    trace_facts = extractor.extract_facts(db_trace)
    
    # 3. Load Success Specification
    test_case = db_trace.test_case
    if not test_case:
        raise HTTPException(status_code=400, detail="Trace is not associated with a test case")
        
    success_spec_model = test_case.success_specification
    if not success_spec_model:
        raise HTTPException(status_code=400, detail="Test case is missing success specification")
        
    # Convert success specification model to schema
    # Create the schema representation needed by the evaluator
    from app.schemas.core import SuccessSpecification
    success_spec = SuccessSpecification.model_validate(success_spec_model)

    # 4. Evaluate Task Success
    evaluator = TaskSuccessEvaluator()
    evaluation_result = evaluator.evaluate(success_spec, trace_facts)
    
    # 5. Persist the Evaluation
    # Check if one already exists for this trace
    db_eval = db.scalar(
        select(TaskSuccessEvaluationModel).where(TaskSuccessEvaluationModel.trace_id == trace_id)
    )
    
    if db_eval:
        # Update existing
        db_eval.task_outcome = evaluation_result.task_success.value
        db_eval.determination_method = evaluation_result.determination_method.value
        db_eval.structured_details = evaluation_result.model_dump(mode='json')
    else:
        # Create new
        db_eval = TaskSuccessEvaluationModel(
            trace_id=trace_id,
            test_case_id=test_case.id,
            task_outcome=evaluation_result.task_success.value,
            determination_method=evaluation_result.determination_method.value,
            structured_details=evaluation_result.model_dump(mode='json')
        )
        db.add(db_eval)
        
    db.commit()
    
    # Add the evaluation DB ID to the result
    evaluation_result.id = db_eval.id
    
    return evaluation_result
