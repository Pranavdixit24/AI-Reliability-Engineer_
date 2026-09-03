def test_create_test_case(client):
    payload = {
        "task_type": "ORDER_CANCELLATION",
        "task_description": "Cancel order 123",
        "scenario_parameters": {
            "order_id": "123"
        },
        "success_specification": {
            "required_intent": "cancel_order",
            "required_entities": {
                "order_id": "123"
            },
            "required_operations": [
                {
                    "operation": "cancel_order",
                    "must_succeed": True
                }
            ],
            "required_final_state": {
                "status": "cancelled"
            }
        }
    }
    
    response = client.post("/test-cases", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["task_type"] == "ORDER_CANCELLATION"
    assert data["success_specification"]["required_intent"] == "cancel_order"
    assert data["success_specification"]["required_operations"][0]["operation"] == "cancel_order"

def helper_create_test_case(client):
    payload = {
        "task_type": "ORDER_CANCELLATION",
        "task_description": "Cancel order 123",
        "scenario_parameters": {
            "order_id": "123"
        },
        "success_specification": {
            "required_intent": "cancel_order",
            "required_entities": {
                "order_id": "123"
            },
            "required_operations": [
                {
                    "operation": "cancel_order",
                    "must_succeed": True
                }
            ],
            "required_final_state": {
                "status": "cancelled"
            }
        }
    }
    response = client.post("/test-cases", json=payload)
    return response.json()["id"]

def test_list_test_cases(client):
    # Create one first
    helper_create_test_case(client)
    
    response = client.get("/test-cases")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) > 0
    assert "success_specification" in data[0]
    
def test_get_test_case(client):
    tc_id = helper_create_test_case(client)
    
    response = client.get(f"/test-cases/{tc_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == tc_id
    assert data["task_type"] == "ORDER_CANCELLATION"
    assert "success_specification" in data
    assert data["success_specification"]["required_intent"] == "cancel_order"
    
def test_get_test_case_not_found(client):
    response = client.get("/test-cases/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Test case not found"
