"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_basic_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "checks" in data


def test_readiness_check(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert "environment" in data


def test_liveness_check(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "environment" in data