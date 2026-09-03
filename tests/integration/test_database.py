from datetime import datetime, timezone
from app.domain.models.core import TestCaseModel, ExecutionTraceModel, TraceStepModel

def test_create_test_case(db_session):
    tc = TestCaseModel(
        task_type="test_task",
        task_description="A test task"
    )
    db_session.add(tc)
    db_session.commit()
    db_session.refresh(tc)
    
    assert tc.id is not None
    assert tc.task_type == "test_task"

def test_trace_step_ordering_and_foreign_keys(db_session):
    tc = TestCaseModel(
        task_type="trace_test",
        task_description="Testing traces"
    )
    db_session.add(tc)
    db_session.commit()
    
    trace = ExecutionTraceModel(
        test_case_id=tc.id,
        trace_identifier="trace-123"
    )
    db_session.add(trace)
    db_session.commit()
    
    step1 = TraceStepModel(
        trace_id=trace.id,
        step_number=1,
        timestamp=datetime.now(timezone.utc),
        action_type="start"
    )
    step2 = TraceStepModel(
        trace_id=trace.id,
        step_number=2,
        timestamp=datetime.now(timezone.utc),
        action_type="end"
    )
    
    db_session.add_all([step2, step1]) # Adding out of order
    db_session.commit()
    
    # Refresh trace to load relationship
    db_session.refresh(trace)
    
    assert len(trace.steps) == 2
    # Ensure they are ordered by step_number
    assert trace.steps[0].step_number == 1
    assert trace.steps[1].step_number == 2
