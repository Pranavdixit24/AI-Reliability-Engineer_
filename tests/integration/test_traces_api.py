def test_list_traces_empty(client):
    response = client.get("/traces")
    assert response.status_code == 200
    assert response.json() == []

def test_traces_api_lifecycle(client):
    # 1. Create a test case
    tc_payload = {
        "task_type": "TEST",
        "task_description": "test desc",
        "success_specification": {
            "required_intent": "test",
            "required_entities": {"id": "1"},
            "required_operations": [{"operation": "op", "must_succeed": True}]
        }
    }
    tc_resp = client.post("/test-cases", json=tc_payload)
    tc_id = tc_resp.json()["id"]
    
    # 2. Run seed directly (or we can just mock it, but integration test should test retrieving traces)
    # Since we can't easily run the CLI in the same DB session without calling a function,
    # let's just create a trace via DB directly and fetch it.
    from app.services.trace_generator import SyntheticTraceGenerator
    from app.domain.enums import ScenarioType
    from app.domain.models.core import TestCaseModel
    
    generator = SyntheticTraceGenerator(seed=1)
    
    # We must do this in the test client's overridden db_session
    # The client fixture overrides get_db, so we need to inject the trace into that DB
    # We can fetch the testcase via API then create the trace model in the DB
    pass

# A cleaner way to test the API is to rely on a fixture or just use the DB session directly
def test_traces_api_with_db(client, db_session):
    from app.services.trace_generator import SyntheticTraceGenerator
    from app.domain.enums import ScenarioType
    from app.domain.models.core import TestCaseModel, SuccessSpecificationModel
    
    # Setup test case
    spec = SuccessSpecificationModel(
        required_intent="test",
        required_entities={"id": "1"},
        required_operations=[{"operation": "op", "must_succeed": True}]
    )
    tc = TestCaseModel(task_type="T", task_description="D", success_specification=spec)
    db_session.add(tc)
    db_session.commit()
    db_session.refresh(tc)
    
    # Generate Trace
    generator = SyntheticTraceGenerator(seed=1)
    trace = generator.generate(tc, ScenarioType.SUCCESS)
    db_session.add(trace)
    db_session.commit()
    
    # Test GET /traces
    resp = client.get("/traces")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == trace.id
    
    # Test GET /traces/{id}
    resp = client.get(f"/traces/{trace.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["steps"]) > 0
    
def test_trace_not_found(client):
    resp = client.get("/traces/999")
    assert resp.status_code == 404
