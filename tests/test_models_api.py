"""Unit tests for Model and Engine Configuration API."""

import pytest
from fastapi.testclient import TestClient
from aeoforge.main import app

client = TestClient(app)

def test_get_models_list():
    """Verify GET /api/v1/models returns active provider, models, and cloud presets."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "active_model" in data
    assert "cloud_presets" in data
    assert len(data["cloud_presets"]) >= 4

def test_update_model_config_ollama():
    """Verify POST /api/v1/models/config validates or connects to Ollama."""
    response = client.post(
        "/api/v1/models/config",
        json={
            "provider": "ollama",
            "model": "llama3.2:latest",
            "endpoint": "http://127.0.0.1:11434"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["connected", "error"]
    if data["status"] == "connected":
        assert data["model"] == "llama3.2:latest"

def test_update_model_config_cloud():
    """Verify POST /api/v1/models/config for cloud provider."""
    response = client.post(
        "/api/v1/models/config",
        json={
            "provider": "cloud",
            "model": "meta-llama/Llama-3.3-70B-Instruct",
            "api_key": "test_fake_key",
            "api_base": "https://api.groq.com/openai/v1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["provider"] == "cloud"
    assert data["model"] == "meta-llama/Llama-3.3-70B-Instruct"
