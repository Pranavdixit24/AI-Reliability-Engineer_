from sqlalchemy.orm import Session
from sqlalchemy import func
from app.domain.models.core import ReliabilityVerdictEvaluationModel, FailureDiagnosisEvaluationModel
from app.schemas.reliability_analytics import ReliabilityAnalyticsResponse

class ReliabilityAnalyticsService:
    
    def get_analytics(self, db: Session) -> ReliabilityAnalyticsResponse:
        # 1. Total Evaluated Traces
        total = db.query(ReliabilityVerdictEvaluationModel).count()
        
        # 2. Verdict Counts
        verdict_rows = db.query(
            ReliabilityVerdictEvaluationModel.overall_evaluation_verdict,
            func.count(ReliabilityVerdictEvaluationModel.id)
        ).group_by(ReliabilityVerdictEvaluationModel.overall_evaluation_verdict).all()
        verdict_counts = {row[0]: row[1] for row in verdict_rows if row[0]}
        
        # 3. Reliability Classification Counts
        classification_rows = db.query(
            ReliabilityVerdictEvaluationModel.reliability_classification,
            func.count(ReliabilityVerdictEvaluationModel.id)
        ).group_by(ReliabilityVerdictEvaluationModel.reliability_classification).all()
        classification_counts = {row[0]: row[1] for row in classification_rows if row[0]}
        
        # 4. Failure Type Counts
        failure_type_rows = db.query(
            ReliabilityVerdictEvaluationModel.failure_type,
            func.count(ReliabilityVerdictEvaluationModel.id)
        ).filter(ReliabilityVerdictEvaluationModel.failure_type.isnot(None)).group_by(ReliabilityVerdictEvaluationModel.failure_type).all()
        failure_type_counts = {row[0]: row[1] for row in failure_type_rows if row[0]}
        
        # 5. Root Cause Counts
        root_cause_rows = db.query(
            FailureDiagnosisEvaluationModel.root_cause_category,
            func.count(FailureDiagnosisEvaluationModel.id)
        ).group_by(FailureDiagnosisEvaluationModel.root_cause_category).all()
        root_cause_counts = {row[0]: row[1] for row in root_cause_rows if row[0]}
        
        return ReliabilityAnalyticsResponse(
            total_evaluated_traces=total,
            verdict_counts=verdict_counts,
            reliability_classification_counts=classification_counts,
            failure_type_counts=failure_type_counts,
            root_cause_counts=root_cause_counts
        )
