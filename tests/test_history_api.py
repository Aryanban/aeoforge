import pytest
from fastapi.testclient import TestClient
from aeoforge.main import app
from aeoforge.storage import storage


@pytest.fixture
def client():
    return TestClient(app)


def test_history_and_progression_endpoints(client):
    # Clear any previous test history
    storage.clear_history()

    # Save mock audits
    res1 = {
        "url": "https://python.org",
        "overall_score": 50.0,
        "grade": "C",
        "pillars": {
            "pillar_a_citability": {"score": 12.0},
            "pillar_b_navigability": {"score": 13.0},
            "pillar_c_protocols": {"score": 10.0},
            "pillar_d_structured_data": {"score": 15.0}
        },
        "recommendations": []
    }
    id1, _ = storage.save_audit("https://python.org", res1)

    res2 = {
        "url": "https://python.org",
        "overall_score": 82.5,
        "grade": "A",
        "pillars": {
            "pillar_a_citability": {"score": 20.0},
            "pillar_b_navigability": {"score": 21.0},
            "pillar_c_protocols": {"score": 20.0},
            "pillar_d_structured_data": {"score": 21.5}
        },
        "recommendations": []
    }
    id2, _ = storage.save_audit("https://python.org", res2)

    # 1. Test GET /api/v1/history
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert data[0]["domain"] == "python.org"

    # 2. Test GET /api/v1/history/{id}
    res_detail = client.get(f"/api/v1/history/{id1}")
    assert res_detail.status_code == 200
    assert res_detail.json()["overall_score"] == 50.0

    # 3. Test GET /api/v1/progression/{domain}
    res_prog = client.get("/api/v1/progression/python.org")
    assert res_prog.status_code == 200
    prog_data = res_prog.json()
    assert prog_data["audit_count"] == 2
    assert prog_data["initial_score"] == 50.0
    assert prog_data["latest_score"] == 82.5
    assert prog_data["delta_since_previous"] == 32.5
    assert prog_data["trend"] == "improving"

    # 4. Test Settings API
    save_s = client.post("/api/v1/settings", json={"settings": {"crawl_depth": 5, "groq_api_key": "gsk_secret12345"}})
    assert save_s.status_code == 200

    get_s = client.get("/api/v1/settings")
    assert get_s.status_code == 200
    settings_dict = get_s.json()["settings"]
    assert settings_dict["crawl_depth"] == 5
    assert "••••••••" in settings_dict["groq_api_key"]

    # 5. Delete single audit
    del_res = client.delete(f"/api/v1/history/{id1}")
    assert del_res.status_code == 200

    # 6. Clear history
    clear_res = client.delete("/api/v1/history")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "cleared"
