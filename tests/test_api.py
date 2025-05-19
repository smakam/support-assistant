import pytest
from fastapi.testclient import TestClient
from app.main import app

# Use your actual DEMO_TOKEN here
DEMO_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlIjoiZ2FtZXIifQ.8qPWSSvIY7TfRjd0pc-oYKbpodM6wPVSbI_O_Y9jD20"

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to AI Customer Assistant API" in response.text

def test_support_query():
    headers = {"Authorization": f"Bearer {DEMO_TOKEN}"}
    data = {"text": "What is the VIP status of ShadowNinja?"}
    response = client.post("/api/v1/support/query", json=data, headers=headers)
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "query_id" in response.json()

def test_feedback():
    headers = {"Authorization": f"Bearer {DEMO_TOKEN}"}
    # First, create a query to get a query_id
    data = {"text": "What is the VIP status of ShadowNinja?"}
    query_response = client.post("/api/v1/support/query", json=data, headers=headers)
    query_id = query_response.json()["query_id"]

    # Now, submit feedback for that query
    feedback_data = {
        "query_id": query_id,
        "feedback_type": "positive",
        "comment": "Great answer!"
    }
    feedback_response = client.post("/api/v1/support/feedback", json=feedback_data, headers=headers)
    assert feedback_response.status_code == 201
    assert feedback_response.json()["status"] == "success" 