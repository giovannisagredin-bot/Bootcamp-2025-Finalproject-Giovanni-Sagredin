"""Tests for API Endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint serves index.html"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_player_search_autocomplete(client):
    """Test player autocomplete search"""
    response = client.get("/api/players/search?q=Messi")
    assert response.status_code == 200
    data = response.json()
    
    # API returns {"count": int, "results": list}
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    
    # Should return players matching "Messi"
    if data["count"] > 0:
        assert "name" in data["results"][0]


def test_submit_report_missing_fields(client):
    """Test report submission with missing fields"""
    response = client.post("/api/reports", json={
        "player_id": 123,
        # Missing report_text
    })
    assert response.status_code == 422  # Validation error


def test_submit_report_toxic_content(client):
    """Test report submission with toxic content"""
    # First get a valid player_id
    search_response = client.get("/api/players/search?q=Messi")
    players_data = search_response.json()
    
    if players_data["count"] == 0:
        # Skip test if no players in DB
        return
    
    player_id = players_data["results"][0]["id"]
    
    response = client.post("/api/reports", json={
        "player_id": player_id,
        "report_text": "This player is absolutely terrible and should quit football"
    })
    # Should either reject (400) or accept depending on toxicity threshold
    assert response.status_code in [200, 400]


def test_search_endpoint_missing_query(client):
    """Test search endpoint without query"""
    response = client.post("/api/search", json={
        "top_k": 5,
        "provider": "mock"
        # Missing query
    })
    assert response.status_code == 422  # Validation error


def test_search_endpoint_valid(client):
    """Test search endpoint with valid query"""
    response = client.post("/api/search", json={
        "query": "fast striker",
        "top_k": 3,
        "provider": "mock"
    })
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_search_endpoint_invalid_provider(client):
    """Test search with invalid LLM provider"""
    response = client.post("/api/search", json={
        "query": "test query",
        "top_k": 3,
        "provider": "invalid_provider"
    })
    assert response.status_code == 422  # Validation error
