from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.schemas.core import HealthResponse
from app.api.routes import test_cases, traces, evaluations, response_truthfulness, reliability_verdict, failure_diagnosis, evaluation_history, reliability_analytics, batch_evaluations

app = FastAPI(
    title=settings.app_name,
    description="Agent-Agnostic AI Reliability Evaluation and Improvement System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_url.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_cases.router)
app.include_router(traces.router)
app.include_router(evaluations.router)
app.include_router(response_truthfulness.router)
app.include_router(reliability_verdict.router)
app.include_router(failure_diagnosis.router)
app.include_router(evaluation_history.router)
app.include_router(reliability_analytics.router)
app.include_router(batch_evaluations.router)

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
