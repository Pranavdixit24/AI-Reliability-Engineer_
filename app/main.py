from fastapi import FastAPI
from app.core.config import settings
from app.schemas.core import HealthResponse
from app.api.routes import test_cases, traces, evaluations, response_truthfulness, reliability_verdict, failure_diagnosis, evaluation_history

app = FastAPI(
    title=settings.app_name,
    description="Agent-Agnostic AI Reliability Evaluation and Improvement System",
    version="0.1.0",
)

app.include_router(test_cases.router)
app.include_router(traces.router)
app.include_router(evaluations.router)
app.include_router(response_truthfulness.router)
app.include_router(reliability_verdict.router)
app.include_router(failure_diagnosis.router)
app.include_router(evaluation_history.router)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Basic health check endpoint.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment
    )
