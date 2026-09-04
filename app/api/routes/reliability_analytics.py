from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.reliability_analytics import ReliabilityAnalyticsResponse
from app.services.reliability_analytics_service import ReliabilityAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
service = ReliabilityAnalyticsService()

@router.get("/reliability", response_model=ReliabilityAnalyticsResponse)
def get_reliability_analytics(db: Session = Depends(get_db)):
    """
    Retrieve aggregate reliability analytics across all evaluated traces.
    This reads persisted evaluation records without triggering any new evaluations or LLM calls.
    """
    return service.get_analytics(db)
