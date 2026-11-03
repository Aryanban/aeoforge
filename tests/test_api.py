"""Unit and integration tests for FastAPI REST endpoints."""

from fastapi.testclient import TestClient
from aeoforge.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["engine"] == "AEOForge"
    assert "version" in data


def test_deobfuscate_endpoint():
    # Test valid Cloudflare hex string
    resp = client.post("/api/v1/deobfuscate-email", json={"cf_hex": "582c3d2b2c183d20393528343d763b3735"})
    assert resp.status_code == 200
    assert resp.json()["decoded_email"] == "test@example.com"

    # Test HTML extraction
    html = '<p>Write to <a href="mailto:info@aeoforge.dev">Info</a></p>'
    resp = client.post("/api/v1/deobfuscate-email", json={"html": html})
    assert resp.status_code == 200
    assert "info@aeoforge.dev" in resp.json()["extracted_emails"]
