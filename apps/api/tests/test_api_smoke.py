import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure apps/api is in the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_root = os.path.abspath(os.path.join(current_dir, '../../api'))
sys.path.append(api_root)

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_practices():
    response = client.get("/api/practices/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # If we have seeded data, we expect at least one practice
    if len(data) > 0:
        assert "locationGuid" in data[0]
        assert "name" in data[0]

def test_dashboard_stats():
    # Test global stats (no practice guid)
    response = client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "totalEncounters" in data
    assert "totalClaims" in data
