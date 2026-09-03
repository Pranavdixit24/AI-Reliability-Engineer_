from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.core import TestCaseCreate, TestCaseResponse
from app.domain.models.core import TestCaseModel, SuccessSpecificationModel

router = APIRouter(prefix="/test-cases", tags=["Test Cases"])

@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def create_test_case(test_case: TestCaseCreate, db: Session = Depends(get_db)):
    """
    Create a new test case along with its structured success specification.
    """
    # Create the SuccessSpecificationModel
    spec_data = test_case.success_specification.model_dump()
    db_spec = SuccessSpecificationModel(**spec_data)
    
    # Create the TestCaseModel
    db_test_case = TestCaseModel(
        task_type=test_case.task_type,
        task_description=test_case.task_description,
        scenario_parameters=test_case.scenario_parameters,
        metadata_info=test_case.metadata,
        success_specification=db_spec
    )
    
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    
    # The Pydantic model expects "metadata" instead of "metadata_info", 
    # we use model_validate and alias or just construct it.
    # Fortunately model_config(from_attributes=True) might handle some, 
    # but let's manually construct or adapt if needed.
    # Wait, the simplest is to rename metadata_info in response or use alias.
    # Pydantic's from_attributes can't map metadata_info to metadata automatically unless we set alias_generator or populate_by_name.
    # I'll just map it explicitly to ensure absolute correctness.
    
    result = TestCaseResponse(
        id=db_test_case.id,
        task_type=db_test_case.task_type,
        task_description=db_test_case.task_description,
        scenario_parameters=db_test_case.scenario_parameters,
        metadata=db_test_case.metadata_info,
        created_at=db_test_case.created_at,
        success_specification_id=db_test_case.success_specification_id,
        success_specification=db_test_case.success_specification
    )
    return result

@router.get("", response_model=List[TestCaseResponse])
def list_test_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List stored test cases.
    """
    db_test_cases = db.scalars(
        select(TestCaseModel).offset(skip).limit(limit)
    ).all()
    
    responses = []
    for tc in db_test_cases:
        responses.append(TestCaseResponse(
            id=tc.id,
            task_type=tc.task_type,
            task_description=tc.task_description,
            scenario_parameters=tc.scenario_parameters,
            metadata=tc.metadata_info,
            created_at=tc.created_at,
            success_specification_id=tc.success_specification_id,
            success_specification=tc.success_specification
        ))
    return responses

@router.get("/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single test case and its structured success specification.
    """
    db_test_case = db.get(TestCaseModel, test_case_id)
    if not db_test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
        
    return TestCaseResponse(
        id=db_test_case.id,
        task_type=db_test_case.task_type,
        task_description=db_test_case.task_description,
        scenario_parameters=db_test_case.scenario_parameters,
        metadata=db_test_case.metadata_info,
        created_at=db_test_case.created_at,
        success_specification_id=db_test_case.success_specification_id,
        success_specification=db_test_case.success_specification
    )
